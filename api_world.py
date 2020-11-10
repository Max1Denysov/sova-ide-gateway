from typing import Dict

from jsonrpcserver.methods import Methods

from components.cluster import ClusterRpc
from nlab.rpc import RpcGroup
from nlab.service import Tracer

from components.access_complect_account import AccessComplectAccountRpc
from components.access_profile_account import AccessProfileAccountRpc
from components.access_profile_user import AccessProfileUserRpc
from components.access_user_flags import AccessUserFlagsRpc
from components.complect import ComplectRpc
from components.complect_revision import ComplectRevisionRpc
from components.deploy import DeployRpc
from components.dictionary import DictionaryRpc
from components.compiler import CompilerRpc
from components.profile import ProfileRpc
from components.suite import SuiteRpc
from components.system import SystemRpc
from components.template import TemplateRpc
from components.testcase import TestcaseRpc


# add all imported "rpc" classes here
RPC_CLASSES = (
    ComplectRpc, DictionaryRpc, ProfileRpc, SuiteRpc, TemplateRpc,
    TestcaseRpc, AccessProfileUserRpc,
    AccessUserFlagsRpc, AccessProfileAccountRpc, CompilerRpc,
    ComplectRevisionRpc, DeployRpc, AccessComplectAccountRpc,
    SystemRpc, ClusterRpc
)


class ApiWorld:
    def __init__(self, create_session):
        self.create_session = create_session
        self.tracer = Tracer("proxy")
        self.tracer.configure({})

        params = {
            'tracer': self.tracer, 'create_session': self.create_session
        }

        self.rpcs: Dict[type, RpcGroup] = {
            rpc_class: rpc_class(**params) for rpc_class in RPC_CLASSES
        }

    def install(self, methods: Methods):
        for rpc in self.rpcs.values():
            rpc.install(self, methods)
