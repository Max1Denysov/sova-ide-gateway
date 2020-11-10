from nlab.rpc import RpcGroup


class SystemRpc(RpcGroup):
    def __init__(self, tracer, create_session):
        super().__init__(
            name="system", tracer=tracer, create_session=create_session
        )

    def version(self):
        return {
            "version": "1.0.3",
            "components": {
                "gateway": "1.0.3",
            },
        }
