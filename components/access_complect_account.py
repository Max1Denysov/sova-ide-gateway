from models import AccessComplectAccount
from nlab.rpc import RpcGroup, rpc_name
from nlab.rpc.exceptions import ApiError
from nlab.rpc.object import VersionNoObject, VersionObject


class AccessComplectAccountRpc(RpcGroup):

    def __init__(self, tracer, create_session) -> None:

        super().__init__(
            name="access.complect_account", tracer=tracer,
            create_session=create_session
        )
        self.access_complect_account = VersionObject(
            name=self.name, primary_key=("account_id", "complect_id"),
            entity=AccessComplectAccount, create_session=create_session
        )

    def create(self, account_id, complect_ids) -> dict:

        return self._store(account_id=account_id, complect_ids=complect_ids)

    def _store(self, account_id, complect_ids) -> dict:

        with self.create_session() as session:
            for complect_id in complect_ids:
                access_complect_account = self.access_complect_account.get(
                    (account_id, complect_id), session=session
                )
                if not access_complect_account:

                    access_complect_account = AccessComplectAccount(
                        account_id=account_id,
                        complect_id=complect_id
                    )

                    session.add(access_complect_account)

            session.commit()

            return {
                "account_id": account_id,
                "complect_ids": complect_ids
            }

    @staticmethod
    def _form_items(items) -> list:

        res = []
        for item in items:
            item_dict = item[0].to_dict()
            res.append(item_dict["complect_id"])

        return res

    @rpc_name("list")
    def list_(self, account_id, offset=None, limit=None, search=None,
              order=None) -> dict:
        """
        Получение списка
        """
        items, total_items = self.access_complect_account.filter(
            filter_q=[AccessComplectAccount.account_id == account_id],
            offset=offset, limit=limit, form_items=self._form_items,
            order=order
        )

        return {
            "items": items,
            "total": total_items,
        }

    def fetch(self, account_id, complect_id) -> dict:
        """
        Получение записи
        :param account_id: идентификатор аккаунта
        :param complect_id: идентификатор комплекта
        """
        with self.create_session() as session:
            access_complect_account = self.access_complect_account.get(
                (account_id, complect_id), session=session
            )
            if not access_complect_account:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find access complect account with "
                            "account_id={} and complect_id={}".format(
                                account_id, complect_id
                            )
                )

            return access_complect_account.to_dict()

    def remove(self, account_id, complect_ids) -> bool:
        """
        Удаление
        :param account_id: идентификатор аккаунта
        :param complect_ids: список идентификаторов профиля
        """
        try:
            ids = []
            for complect_id in complect_ids:
                ids.append((account_id, complect_id))

            return self.access_complect_account.remove(ids)

        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e
