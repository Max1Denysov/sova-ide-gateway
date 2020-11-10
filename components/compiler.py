from sqlalchemy.orm import load_only

from models import Complect
from nlab.job import get_create_request, get_info_request, post_request
from nlab.rpc import RpcGroup, rpc_name
from nlab.rpc.exceptions import ApiError
from settings import HEADERS, PROCESSOR_HOST


class CompilerRpc(RpcGroup):

    def __init__(self, tracer, create_session):

        super().__init__(
            name="compiler", tracer=tracer, create_session=create_session
        )

    def create(self, complect_id, try_create_revision=False):
        """
        Создание задачи
        """
        if complect_id is None:
            raise ApiError(
                code="INVALID_COMPLECT_ID", message="Complect id can't be null"
            )

        with self.create_session() as session:
            tiny_complect = session.query(Complect).options(
                load_only("compiler_target")
            ).get(complect_id)

        if tiny_complect is None:
            raise ApiError(
                code="NOT_EXISTS",
                message="Can't find complect with id=%r" % complect_id
            )

        response = post_request(
            url=PROCESSOR_HOST,
            headers=HEADERS,
            request_data=get_create_request(
                method="task.create",
                script="scripts.processor.run",
                type="compiler",
                extra={"complect_id": complect_id},
                args={
                    "complect_id": complect_id,
                    "target": tiny_complect.compiler_target,
                    "try_create_revision": try_create_revision,
                }
            )
        )

        result = response["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="UNHANDLED", message=result["errors"]["message"])

    @staticmethod
    def info(task_id):
        """
        Получение информации о задаче
        """
        result = post_request(
            url=PROCESSOR_HOST, headers=HEADERS,
            request_data=get_info_request(method="task.info", task_id=task_id)
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="NOT_EXISTS", message=result["errors"]["message"])

    @staticmethod
    @rpc_name("list")
    def list_(extra=None, offset=None, limit=None, order=None):
        """
        Получение списка задач по типу
        """

        result = post_request(
            url=PROCESSOR_HOST, headers=HEADERS,
            request_data=get_info_request(
                method="task.list", type="compiler",
                extra=extra,
                offset=offset, limit=limit, order=order
            )
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="NOT_EXISTS", message=result["errors"]["message"])
