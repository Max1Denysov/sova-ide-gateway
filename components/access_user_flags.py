from models import AccessUserFlags
from nlab.rpc import RpcGroup
from nlab.rpc.exceptions import ApiError
from nlab.rpc.object import VersionObject


class AccessUserFlagsRpc(RpcGroup):

    def __init__(self, tracer, create_session):

        super().__init__(
            name="access.user.flags", tracer=tracer,
            create_session=create_session
        )
        self.access_user_flags = VersionObject(
            name=self.name, primary_key="user_id", entity=AccessUserFlags,
            create_session=create_session
        )

    def fetch(self, user_id):
        """
        Получение флагов
        """
        with self.create_session() as session:
            access_user_flags_model = self.access_user_flags.get(
                user_id, session=session
            )
            if not access_user_flags_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find access user flags with "
                            "user_id={}".format(user_id)
                )

            return access_user_flags_model.to_dict()

    def set(self, user_id, flags):
        """
         Установка флагов
        """
        return self._store(user_id=user_id, flags=flags)

    def _store(self, user_id, flags):

        with self.create_session() as session:
            access_user_flags_model = self.access_user_flags.get(
                user_id, session=session
            )
            if access_user_flags_model:
                access_user_flags_model.flags = flags
            else:
                access_user_flags_model = AccessUserFlags(
                    user_id=user_id,
                    flags=flags
                )

            session.add(access_user_flags_model)
            session.commit()

            return access_user_flags_model.to_dict()
