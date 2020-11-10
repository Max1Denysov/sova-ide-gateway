from nlab.job import get_info_request, post_request
from nlab.rpc import RpcGroup, rpc_name
from nlab.rpc.exceptions import ApiError
from settings import HEADERS, PROCESSOR_HOST


class ComplectRevisionRpc(RpcGroup):

    def __init__(self, tracer, create_session):

        super().__init__(
            name="complect_revision", tracer=tracer,
            create_session=create_session
        )

    @rpc_name("list")
    def list_of_complect_revisions(self, complect_id=None,
                                   offset=None, limit=None, order=None):

        result = self._get_complect_revision_list(
            complect_id=complect_id,
            offset=offset,
            limit=limit,
            order=order,
        )

        result = result["result"]
        if result["status"]:
            return result["response"]

        raise ApiError(code="NOT_EXISTS", message=result["errors"]["message"])

    def _get_complect_revision_list(self, *, complect_id, offset, limit,
                                    order):
        result = post_request(
            url=PROCESSOR_HOST, headers=HEADERS,
            request_data=get_info_request(
                method="complect_revision.list",
                complect_id=complect_id,
                offset=offset, limit=limit, order=order
            )
        )

        return result
