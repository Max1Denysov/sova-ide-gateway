from datetime import datetime

from components_utils.batch_operations import BatchUpdateMixin
from models import Testcase
from nlab.job import get_create_request, get_info_request, post_request
from nlab.rpc import ApiError, RpcGroup
from nlab.rpc.object import VersionNoObject, VersionObject
from settings import PROCESSOR_HOST

from .profile import ProfileRpc

MAX_COUNT_TESTCASE_TO_RUN = 100000

TYPE = "testcase"


class TestcaseRpc(RpcGroup, BatchUpdateMixin):
    __test__ = False

    """Тесткейс"""

    def __init__(self, tracer, create_session):

        super().__init__(
            name="testcase", tracer=tracer, create_session=create_session
        )
        self.testcase = VersionObject(
            name=self.name, primary_key="testcase_id", entity=Testcase,
            create_session=create_session
        )

    def create(self, **kwargs):
        with self.create_session() as session:
            kwargs['session'] = session
            result = self._store(**kwargs)
            session.commit()

        return result

    def _fetch(self, id):
        """Получение"""
        with self.create_session() as session:
            testcase_model = self.testcase.get(id, session=session)
            if not testcase_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find testcase with id=%r" % id
                )
            return testcase_model.to_dict()

    def list(self, offset=None, limit=None, profile_ids=None, is_common=None,
             order=None):
        """Получение списка"""
        filter_q = []

        if profile_ids:
            if isinstance(profile_ids, str):
                profile_ids = [profile_ids]
            filter_q.append(Testcase.profile_id.in_(profile_ids))

        if is_common:
            filter_q.append(Testcase.is_common == is_common)

        items, total_items = self.testcase.filter(
            filter_q=filter_q, offset=offset, limit=limit, order=order
        )

        return {"items": items, "total": total_items, }

    def remove(self, id):
        """Удаление"""
        try:
            return self.testcase.remove(id)
        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e

    @staticmethod
    def result_list(offset=None, limit=None):
        """
        Получение списка задача/статус
        """
        result = post_request(
            url=PROCESSOR_HOST, headers=None,
            request_data=get_info_request(
                method="task.list", type=TYPE, offset=offset, limit=limit
            )
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="NOT_EXISTS", message=result["errors"]["message"])

    @staticmethod
    def result(task_id):
        """
        Получение результата по задаче
        """
        result = post_request(
            url=PROCESSOR_HOST, headers=None,
            request_data=get_info_request(method="task.info", task_id=task_id)
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(
            code="PROCESSOR_SERVICE", message=result["errors"]["message"]
        )

    def run(self, profile_id, ids):
        """
        Запуск
        """
        if len(ids) > MAX_COUNT_TESTCASE_TO_RUN:
            raise ApiError(
                code="COUNT_TESTCASES",
                message="Количество тесткейсов превышает допустимое количество"
                        " {} для одного запуска".format(
                            MAX_COUNT_TESTCASE_TO_RUN
                        )
            )

        def form_items(items):
            res = []
            for item, _ in items:
                res.append(item.to_short_dict())

            return res

        filter_q = [
            Testcase.profile_id == profile_id, Testcase.testcase_id.in_(ids)
        ]
        testcases, _ = self.testcase.filter(
            filter_q=filter_q, limit=len(ids),
            form_items=form_items  # TODO: ? Так оно точно работает?
        )

        profile = ProfileRpc(
            tracer=self.tracer, create_session=self.create_session
        )
        profile_info = profile.fetch(profile_id)

        result = post_request(
            url=PROCESSOR_HOST, headers=None,
            request_data=get_create_request(
                method="task.create", script="scripts.testcase.run",
                type=TYPE, args={
                    "ids": ids, "testcases": testcases,
                    "profile_info": profile_info
                }
            )
        )

        return result["result"]["response"]

    def _store(self, id=None, profile_id=False, title=None, description=None,
               replicas=None, is_common=None, author=None,
               action=None, session=None):

        if action == "update":
            testcase_model = self.testcase.get(id, session=session)
            if not testcase_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find testcase with id=%r" % id
                )
        else:
            testcase_model = Testcase(created=datetime.now(), )

        if profile_id is not False:
            # False, потому что клиент может отправлять None
            # для очистки profile_id
            testcase_model.profile_id = profile_id

        if title is not None:
            testcase_model.title = title

        if description is not None:
            testcase_model.description = description

        if replicas is not None:
            testcase_model.replicas = replicas

        if is_common is not None:
            testcase_model.is_common = is_common

        if author is not None:
            testcase_model.author = author

        session.add(testcase_model)
        session.flush()

        return testcase_model.to_dict()
