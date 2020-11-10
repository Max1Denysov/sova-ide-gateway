import logging

from models import Complect
from nlab.job.job import post_request, get_info_request
from nlab.rpc import RpcGroup
from nlab.rpc.exceptions import ApiError
from settings import PROCESSOR_HOST, HEADERS

logger = logging.getLogger(__name__)


class ClusterRpc(RpcGroup):
    """Кластер"""
    def __init__(self, tracer, create_session):

        super().__init__(
            name="cluster", tracer=tracer, create_session=create_session
        )

    def complect_info(self, complect_id):
        """Информация о комплекте"""
        return self._get_complect_info(complect_id)

    def _get_compilers(self):
        response = post_request(
            url=PROCESSOR_HOST,
            headers=HEADERS,
            request_data=get_info_request(
                method="cluster.list_compilers",
            )
        )

        try:
            compilers_list = response["result"]["response"]["items"]
        except KeyError:
            logger.exception("Error in gettings compilers")
            raise ApiError(
                code="ERROR",
                message="Error in gettings compilers",
            )

        compilers = {v["code"]: v for v in compilers_list}
        return compilers

    def _get_complect_info(self, complect_id):
        compilers = self._get_compilers()

        with self.create_session() as session:
            complect = session.query(Complect).get(complect_id)
            if complect is None:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Complect with id=%r not exists!" % complect_id,
                )

            compiler_info = compilers.get(complect.compiler_target)
            if compiler_info is None:
                raise ApiError(
                    code="TARGET_NOT_EXISTS",
                    message="Compiler with id=%r not exists!" %
                            complect.compiler_target,
                )

            return {
                "debug_target_url": compiler_info["infengine_url"],
            }
