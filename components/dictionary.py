from datetime import datetime

from components_utils.batch_operations import BatchUpdateMixin
from models import Dictionary, DictionaryVersion
from nlab.job import get_create_request, post_request
from nlab.rpc import ApiError, RpcGroup
from nlab.rpc.object import VersionNoObject, VersionObject
from processor import transform_template_text
from settings import PROCESSOR_HOST

TYPE = "dictionary"


class DictionaryRpc(RpcGroup, BatchUpdateMixin):
    def __init__(self, tracer, create_session):

        super().__init__(name="dictionary", tracer=tracer,
                         create_session=create_session)
        self.dictionary = VersionObject(
            name=self.name, primary_key="dictionary_id",
            entity=Dictionary, versions_entity=DictionaryVersion,
            create_session=create_session,
        )

    def create(self, code=None, description=None, content=None, common=None,
               state=None, meta=None, profile_ids=None, is_enabled=None,
               hidden=None, kind=None, parts=None, ):

        with self.create_session() as session:
            result = self._store(
                id=None, code=code, description=description,
                content=content, common=common, state=state,
                meta=meta, profile_ids=profile_ids,
                is_enabled=is_enabled, hidden=hidden,
                session=session, kind=kind, parts=parts,
            )
            session.commit()
            return result

    def list(self, profile_id=None, offset=None, limit=None, search=None,
             common=None, order=None, code=None, id=None, kind=None,
             _with_content=None, _process=None):

        filter_q = []

        if id is not None:
            filter_q.append(Dictionary.dictionary_id.in_(id))

        if profile_id is not None and profile_id != "":
            if isinstance(profile_id, str):
                profile_id = [profile_id]
            filter_q.append(Dictionary.profile_ids.contains(profile_id))

        if code is not None:
            filter_q.append(Dictionary.code == code)

        if kind is not None:
            filter_q.append(Dictionary.kind == kind)

        if common is not None:
            filter_q.append(Dictionary.common == common)

        form_items = lambda items: [  # noqa
            item[0].to_dict() if _with_content else item[0].to_short_dict()
            for item in items
        ]

        items, total_items = self.dictionary.filter(filter_q=filter_q,
                                                    offset=offset,
                                                    limit=limit,
                                                    form_items=form_items,
                                                    order=order)

        if _process:
            items = [_process_dictionary_inplace(item) for item in items]

        return {
            "items": items,
            "total": total_items,
        }

    def list_versions(self, id, order=None, offset=None, limit=None):
        items, total_items = self.dictionary.versions(
            id, order=order, offset=offset, limit=limit,
        )

        return {
            "items": items,
            "total": total_items,
        }

    def fetch(self, id, _process=None):

        with self.create_session() as session:
            profile_model = self.dictionary.get(id, session=session)
            if not profile_model:
                raise ApiError(code="NOT_EXISTS",
                               message="Can't find profile with id=%r" % id)
            item = profile_model.to_dict()

            if _process:
                item = _process_dictionary_inplace(item)

            return item

    def remove(self, id):

        try:
            result = self.dictionary.remove(id)
            return result
        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e

    def _store(self, id=None, code=None, description=None, content=None,
               common=None, state=None, meta=None, profile_ids=None,
               is_enabled=None, hidden=None, action=None, kind=None,
               parts=None, session=None):

        if action == 'update':
            dictionary_model = self.dictionary.get(id, session=session)
            if not dictionary_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find dictionary with id=%r" % id
                )
        else:
            dictionary_model = Dictionary(
                created=datetime.now(),
                version=0,
            )

        if code is not None:
            dictionary_model.code = code

        if description is not None:
            dictionary_model.description = description

        if content is not None:
            dictionary_model.content = content

        if common is not None:
            dictionary_model.common = common

        if kind is not None:
            dictionary_model.kind = kind

        if state is not None:
            dictionary_model.state = state

        if meta is not None:
            dictionary_model.meta = meta

        if profile_ids is not None:
            dictionary_model.profile_ids = profile_ids

        if is_enabled is not None:
            dictionary_model.is_enabled = is_enabled

        if hidden is not None:
            dictionary_model.hidden = hidden

        if parts is not None:
            dictionary_model.parts = parts

        dictionary_model.version += 1

        session.add(dictionary_model)
        session.flush()

        data = dictionary_model.to_dict()

        return data

    @staticmethod
    def import_file(profile_ids, file_name, data):
        """
        Импортирование словарей из файла
        """
        result = post_request(
            url=PROCESSOR_HOST,
            headers=None,
            request_data=get_create_request(
                method="task.create",
                script="scripts.dictionary.import_run",
                type=TYPE,
                args={
                    "profile_ids": profile_ids,
                    "file_name": file_name,
                    "data": data,
                }
            )
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="UNHANDLED", message=result["errors"]["message"])

    def export(self, ids):
        """
        Экспортирование шаблонов
        """
        dictionaries = {}

        for dict_id in ids:
            dictionaries[dict_id] = {}

            suite = self.fetch(dict_id)

            dictionaries[dict_id]["name"] = suite["code"] or suite.dictionary_id  # noqa
            dictionaries[dict_id]["content"] = suite["content"]

        result = post_request(
            url=PROCESSOR_HOST,
            headers=None,
            request_data=get_create_request(
                method="task.create",
                script="scripts.dictionaries.export_run",
                type=TYPE,
                args={
                    "dictionaries": dictionaries
                }
            )
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="UNHANDLED", message=result["errors"]["message"])


def _process_dictionary_inplace(dictionary):
    if "content" not in dictionary:
        return dictionary

    dictionary["content"] = transform_template_text(dictionary["content"])
    return dictionary
