from models import Complect
from nlab.rpc import RpcGroup, rpc_name
from nlab.rpc.exceptions import ApiError
from nlab.job import get_create_request, post_request, get_info_request
from settings import HEADERS, PROCESSOR_HOST


class DeployRpc(RpcGroup):
    TASK_TYPE = "deploy"

    def __init__(self, tracer, create_session):

        super().__init__(
            name="deploy", tracer=tracer, create_session=create_session
        )

    def run(self, complect_revision_id):
        """
        Run deploy process
        :param complect_revision_id:
        :return:
        """

        # Check complect_revision_id exists
        if complect_revision_id is None:
            raise ApiError(
                code="COMPLECT_REVISION_ID",
                message="Complect revision id can't be null"
            )

        # Query complect revision information, we need Complect deploy_target
        complect_revision_response = post_request(
            url=PROCESSOR_HOST,
            headers=HEADERS,
            request_data=get_info_request(
                method="complect_revision.fetch",
                id=complect_revision_id,
            )
        )

        complect_revision_result = complect_revision_response["result"]
        if complect_revision_result.get("errors", {}).get("code") \
                is not None:
            raise ApiError(
                code=complect_revision_result["errors"]["code"],
                message=complect_revision_result["errors"]["message"],
            )

        # Query complect by complect_id
        complect_id = complect_revision_result["response"]["complect_id"]
        with self.create_session() as session:
            complect_model = session.query(Complect).get(complect_id)
            deploy_target = complect_model.deploy_target

        response = post_request(
            url=PROCESSOR_HOST,
            headers=HEADERS,
            request_data=get_create_request(
                method="task.create",
                script="scripts.deploy.run",
                type=self.TASK_TYPE,
                extra={"complect_revision_id": complect_revision_id},
                args={
                    "complect_revision_id": complect_revision_id,
                    "target": deploy_target,
                }
            )
        )
        result = response["result"]

        if not result["status"]:
            raise ApiError(
                code="UNHANDLED", message=result["errors"]["message"]
            )

        return result["response"]

    @staticmethod
    def info(task_id):
        """
        Get task info
        """
        result = post_request(
            url=PROCESSOR_HOST, headers=HEADERS,
            request_data=get_info_request(method="task.info", task_id=task_id)
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="NOT_EXISTS", message=result["errors"]["message"])

    @classmethod
    @rpc_name("list")
    def list_(cls, extra=None, offset=None, limit=None, order=None):
        """
        Get deploy task's list
        """
        result = post_request(
            url=PROCESSOR_HOST, headers=HEADERS,
            request_data=get_info_request(
                method="task.list", type=cls.TASK_TYPE,
                extra=extra,
                offset=offset, limit=limit, order=order
            )
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="NOT_EXISTS", message=result["errors"]["message"])
