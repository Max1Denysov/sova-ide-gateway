from datetime import datetime

from sqlalchemy import func

from components_utils.batch_operations import BatchUpdateMixin
from models import Suite, Template
from nlab.job import get_create_request, post_request
from nlab.rpc import RpcGroup
from nlab.rpc.exceptions import ApiError
from nlab.rpc.object import VersionNoObject, VersionObject
from settings import PROCESSOR_HOST

from .template import TemplateRpc

TYPE = "suite"


class SuiteRpc(RpcGroup, BatchUpdateMixin):
    def __init__(self, tracer, create_session):

        super().__init__(
            name="suite", tracer=tracer, create_session=create_session
        )
        self.suite = VersionObject(
            name=self.name, primary_key="suite_id", entity=Suite,
            create_session=create_session
        )

    def create(self, **kwargs):
        with self.create_session() as session:
            kwargs['session'] = session
            result = self._store(**kwargs)
            session.commit()

        return result

    def remove(self, id):

        try:
            with self.create_session() as session:
                query_result = session.query(Template).filter(
                    Template.suite_id.in_(
                        [id] if not isinstance(id, list) else id
                    )
                )

                query_result.delete(synchronize_session=False)
                session.commit()

                return self.suite.remove(id=id, session=session)

        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e

    def list(self, profile_ids, offset=None, limit=None, search=None,
             order=None, is_enabled=None):

        if not isinstance(profile_ids, list):
            profile_ids = [profile_ids]

        filter_q = [
            Suite.profile_id.in_(profile_ids),
        ]
        return self._stat_filter(
            filter_q=filter_q, offset=offset, limit=limit,
            order=order, is_enabled=is_enabled
        )

    def _stat_filter(self, filter_q, offset, limit, order, is_enabled):

        with self.create_session() as session:
            fetch_args = [
                func.count(Template.template_id).label("templates")
            ]

            if is_enabled is not None:
                filter_q.append(Suite.is_enabled.is_(is_enabled))

            q = self.suite.prepare_filter_q(
                session=session,
                filter_q=filter_q,
                offset=offset,
                limit=limit,
                fetch_args=fetch_args,
                outerjoin=[Template],
                group_by=[Suite.suite_id],
                order=order,
            )

            items = q.all()
            total_items = 0
            if items:
                total_items = items[0][1]

            result_items = []
            for item, total_count, templates_count in items:
                res = item.to_dict()
                res["stat"] = {
                    "templates": templates_count,
                }
                result_items.append(res)

            return {
                "items": result_items,
                "total": total_items,
            }

    def store(self, **kwargs):

        with self.create_session() as session:
            kwargs['session'] = session
            result = self._store(**kwargs)
            session.commit()

            return result

    def _store(self, title=None, state=None, profile_id=None, id=None,
               meta=None, is_enabled=None, action=None, session=None):

        if action == "update":
            suite_model = self.suite.get(id, session=session)
            if not suite_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find suite with id=%r" % id
                )
        else:
            if not profile_id:
                raise ApiError(
                    code="MISSING_PROFILE_ID",
                    message="profile_id must be given for creating suite"
                )

            suite_model = Suite(
                profile_id=profile_id,
                created=datetime.now(),
                version=0,
            )

        if title is not None:
            suite_model.title = title

        if state is not None:
            suite_model.state = state

        if meta is not None:
            suite_model.meta = meta

        if is_enabled is not None:
            suite_model.is_enabled = is_enabled

        suite_model.version += 1

        session.add(suite_model)
        session.flush()

        return suite_model.to_dict()

    def fetch(self, id):

        with self.create_session() as session:
            suite_model = self.suite.get(id, session=session)
            if not suite_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find suite with id=%r" % id
                )
            return suite_model.to_dict()

    @staticmethod
    def import_file(profile_id, file_name, data):
        """
        Импортирование шаблонов из файла
        """
        result = post_request(
            url=PROCESSOR_HOST, headers=None,
            request_data=get_create_request(
                method="task.create",
                script="scripts.suite.import_run",
                type=TYPE,
                args={
                    "profile_id": profile_id, "file_name": file_name,
                    "data": data
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
        suites = {}
        template_rpc = TemplateRpc(
            tracer=self.tracer, create_session=self.create_session
        )

        for suite_id in ids:
            suites[suite_id] = {}

            suite = self.fetch(suite_id)

            suites[suite_id]["name"] = suite["title"] or suite_id

            suites[suite_id]["templates"] = []
            templates = template_rpc.list(suite_id=suite_id)

            for template in templates["items"]:
                suites[suite_id]["templates"].append(template["content"])

        result = post_request(
            url=PROCESSOR_HOST, headers=None,
            request_data=get_create_request(
                method="task.create",
                script="scripts.suite.export_run",
                type=TYPE,
                args={"suites": suites}
            )
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="UNHANDLED", message=result["errors"]["message"])
