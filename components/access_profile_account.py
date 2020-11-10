from models import AccessProfileAccount
from nlab.rpc import RpcGroup
from nlab.rpc.exceptions import ApiError
from nlab.rpc.object import VersionNoObject, VersionObject


class AccessProfileAccountRpc(RpcGroup):

    def __init__(self, tracer, create_session):

        super().__init__(
            name="access.account", tracer=tracer, create_session=create_session
        )
        self.access_account = VersionObject(
            name=self.name, primary_key=("account_id", "profile_id"),
            entity=AccessProfileAccount, create_session=create_session
        )

    def create(self, account_id, profile_ids):
        """
        Создание записи
        """
        return self._store(account_id=account_id, profile_ids=profile_ids)

    @staticmethod
    def _form_items(items):

        res = []
        for item in items:
            item_dict = item[0].to_dict()
            res.append(item_dict["profile_id"])

        return res

    def list(self, account_id, offset=None, limit=None, search=None,
             order=None):
        """
        Получение списка
        """
        items, total_items = self.access_account.filter(
            filter_q=[AccessProfileAccount.account_id == account_id],
            offset=offset, limit=limit, form_items=self._form_items,
            order=order
        )

        return {
            "items": items,
            "total": total_items,
        }

    def fetch(self, account_id, profile_id):
        """
        Получение записи
        :param account_id: идентификатор аккаунта
        :param profile_id: идентификатор профиля
        """
        with self.create_session() as session:
            access_profile_account_model = self.access_account.get(
                (account_id, profile_id), session=session
            )
            if not access_profile_account_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find access profile account with "
                            "account_id={} and profile_id={}".format(
                                account_id, profile_id
                            )
                )

            return access_profile_account_model.to_dict()

    def remove(self, account_id, profile_ids):
        """
        Удаление
        :param account_id: идентификатор аккаунта
        :param profile_ids: список идентификаторов профиля
        """
        try:
            ids = []
            for profile_id in profile_ids:
                ids.append((account_id, profile_id))

            return self.access_account.remove(ids)

        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e

    def _store(self, account_id, profile_ids):

        with self.create_session() as session:
            for profile_id in profile_ids:
                access_profile_account_model = self.access_account.get(
                    (account_id, profile_id), session=session
                )
                if access_profile_account_model:
                    continue

                access_profile_account_model = AccessProfileAccount(
                    account_id=account_id,
                    profile_id=profile_id
                )

                session.add(access_profile_account_model)

            session.commit()

            return {
                "account_id": account_id,
                "profile_ids": profile_ids
            }
