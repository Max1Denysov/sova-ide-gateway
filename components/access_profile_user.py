import copy

from models import AccessProfileUser
from nlab.rpc import RpcGroup
from nlab.rpc.exceptions import ApiError
from nlab.rpc.object import VersionNoObject, VersionObject


class AccessProfileUserRpc(RpcGroup):

    def __init__(self, tracer, create_session):

        super().__init__(
            name="access.user", tracer=tracer, create_session=create_session
        )
        self.access_profile_user = VersionObject(
            name=self.name, primary_key=("user_id", "profile_id"),
            entity=AccessProfileUser, create_session=create_session
        )

    def create(self, **kwargs):

        with self.create_session() as session:
            kwargs['session'] = session
            result = self._store(**kwargs)
            session.commit()

            return result

    def update(self, **kwargs):

        with self.create_session() as session:
            kwargs['session'] = session
            kwargs['action'] = 'update'
            result = self._store(**kwargs)
            session.commit()

            return result

    def fetch(self, user_id, profile_ids):

        with self.create_session() as session:
            result = []
            for profile_id in profile_ids:

                permission_model = self.access_profile_user.get(
                    (user_id, profile_id), session=session
                )
                if not permission_model:
                    raise ApiError(
                        code="NOT_EXISTS",
                        message="Can't find permission with user_id={} "
                                "and profile_id={}".format(user_id, profile_id)
                    )
                result.append(permission_model.to_dict())

            return result

    def remove(self, user_id, profile_ids):

        try:
            ids = []
            for profile_id in profile_ids:
                ids.append((user_id, profile_id))

            return self.access_profile_user.remove(ids)

        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e

    @staticmethod
    def _form_items(items):

        res = []
        for item in items:
            item_dict = item[0].to_dict()
            res.append(item_dict["profile_id"])
        return res

    def list(self, user_id, offset=None, limit=None, search=None, order=None):
        """
        Получение списка
        """
        items, total_items = self.access_profile_user.filter(
            filter_q=[AccessProfileUser.user_id == user_id], offset=offset,
            limit=limit, form_items=self._form_items, order=order
        )

        return {"items": items, "total": total_items, }

    @staticmethod
    def _form_permissions(permissions, new_permissions):

        for perm, value in new_permissions.items():
            permissions[perm] = value

        return permissions

    def _store(self, user_id=None, profile_ids=None,
               action=None, session=None):

        for item in profile_ids:
            if action == "update":
                permission_model = self.access_profile_user.get(
                    (user_id, item["profile_id"]), session=session
                )

                if not permission_model:
                    raise ApiError(
                        code="NOT_EXISTS",
                        message="Can't find permission with user_id={} "
                                "and profile_id={}".format(
                                    user_id, item["profile_id"]
                                )
                    )

                permission_model.permissions = self._form_permissions(
                    copy.deepcopy(permission_model.permissions),
                    item["permissions"]
                )

            else:
                permission_model = self.access_profile_user.get(
                    (user_id, item["profile_id"]), session=session
                )

                if permission_model:
                    permission_model.permissions = item["permissions"]
                else:
                    permission_model = AccessProfileUser(
                        user_id=user_id,
                        profile_id=item["profile_id"],
                        permissions=item["permissions"]
                    )

            session.add(permission_model)

            return {"user_id": user_id, "profile_ids": profile_ids, }
