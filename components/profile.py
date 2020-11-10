import random
import string
from datetime import datetime

from sqlalchemy import and_

import settings
from components_utils.batch_operations import BatchUpdateMixin
from models import (AccessProfileAccount, AccessProfileUser, AccessUserFlags,
                    Complect, Profile, Suite)
from nlab.db import next_seq_id
from nlab.rpc import RpcGroup
from nlab.rpc.exceptions import ApiError
from nlab.rpc.object import VersionObject


class ProfileRpc(RpcGroup, BatchUpdateMixin):
    def __init__(self, tracer, create_session):

        super().__init__(
            name="profile", tracer=tracer, create_session=create_session
        )
        self.profile = VersionObject(
            name=self.name, primary_key="profile_id", entity=Profile,
            create_session=create_session
        )

    def create(self, **kwargs):

        with self.create_session() as session:
            kwargs['session'] = session
            result = self._store(**kwargs)
            session.commit()

            return result

    @staticmethod
    def _form_items(default_perm_value):

        def inner(items, value=default_perm_value):

            res = []

            for item, _, *permissions in items:
                d = item.to_dict()
                if permissions != [None] and permissions != []:
                    d["permissions"] = permissions[0]
                    if "dl_read" not in d["permissions"] or not d["permissions"]["dl_read"]:  # noqa
                        d["permissions"]["dl_read"] = value

                    if "dl_write" not in d["permissions"] or not d["permissions"]["dl_write"]:  # noqa
                        d["permissions"]["dl_write"] = value

                    if "dict_read" not in d["permissions"] or not d["permissions"]["dict_read"]:  # noqa
                        d["permissions"]["dict_read"] = value

                    if "dict_write" not in d["permissions"] or not d["permissions"]["dict_write"]:  # noqa
                        d["permissions"]["dict_write"] = value

                else:
                    d["permissions"] = {}
                    d["permissions"]["dl_read"] = value
                    d["permissions"]["dl_write"] = value
                    d["permissions"]["dict_read"] = value
                    d["permissions"]["dict_write"] = value

                res.append(d)

            return res
        return inner

    def list(self, offset=None, limit=None, search=None, user=None,
             account_id=None, group_ids=None, role_id=None,
             full_list=None, order=None):

        filter_q = []
        outerjoin = None
        fetch_args = None

        default_perm_value = True

        def get_profile_ids_by_account():

            accesses = session.query(
                AccessProfileAccount
            ).filter(AccessProfileAccount.account_id == account_id)

            return [acc.profile_id for acc in accesses]

        if user and user.get("user_id"):
            with self.create_session() as session:
                user_flags = session.query(AccessUserFlags).filter(
                    AccessUserFlags.user_id == user["user_id"]
                ).first()

                sys_admin, acc_admin = (
                    user_flags.flags["sys_admin"],
                    user_flags.flags["acc_admin"]
                ) if user_flags else (False, False)

                if not sys_admin:
                    # если пользователь имеет флаг sys_admin, то ограничения
                    # не применяются
                    if acc_admin and account_id:  # аккаунт
                        profile_ids = get_profile_ids_by_account()
                    else:
                        default_perm_value = False

                        if full_list and account_id:
                            profile_ids = get_profile_ids_by_account()

                            outerjoin = [
                                AccessProfileUser,
                                and_(
                                    Profile.profile_id == AccessProfileUser.profile_id,  # noqa
                                    AccessProfileUser.user_id == user[
                                        "user_id"
                                    ]
                                )
                            ]
                        else:
                            accesses = session.query(  # пользователь + профиль
                                AccessProfileUser
                            ).filter(
                                AccessProfileUser.user_id == user["user_id"]
                            )

                            profile_ids = [acc.profile_id for acc in accesses]

                            outerjoin = [
                                AccessProfileUser,
                                Profile.profile_id == AccessProfileUser.profile_id  # noqa
                            ]

                            filter_q.append(
                                AccessProfileUser.user_id == user["user_id"]
                            )

                        fetch_args = [AccessProfileUser.permissions]

                    if not profile_ids:
                        return {"items": [], "total": 0}

                    filter_q.append(Profile.profile_id.in_(profile_ids))

        items, total_items = self.profile.filter(
            filter_q=filter_q,
            offset=offset,
            limit=limit,
            outerjoin=outerjoin,
            fetch_args=fetch_args,
            form_items=self._form_items(default_perm_value),
            order=order
        )

        return {
            "items": items,
            "total": total_items,
        }

    def fetch(self, id):

        with self.create_session() as session:
            profile_model = self.profile.get(id, session=session)
            if not profile_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find profile with id=%r" % id
                )
            return profile_model.to_dict()

    def remove(self, id):

        from components.suite import SuiteRpc

        with self.create_session() as session:
            query_id = id if isinstance(id, list) else [id]
            profile_suites = session.query(Suite).filter(
                Suite.profile_id.in_(query_id)
            )
            remove_suite_ids = [suite.suite_id for suite in profile_suites]
            if remove_suite_ids:
                self._parent_world.rpcs[SuiteRpc].remove(remove_suite_ids)

            session.query(AccessProfileUser).filter(
                AccessProfileUser.profile_id.in_(query_id)
            ).delete(synchronize_session=False)

            session.query(AccessProfileAccount).filter(
                AccessProfileAccount.profile_id.in_(query_id)
            ).delete(synchronize_session=False)

            return self.profile.remove(id, session=session)

    def store(self, **kwargs):

        with self.create_session() as session:
            kwargs['session'] = session
            result = self._store(**kwargs)
            session.commit()

            return result

    def _store(self, id=None, name=None, code=None, common=None, state=None,
               meta=None, is_enabled=None, action=None, session=None):

        if action == "update":
            profile_model = self.profile.get(id, session=session)
            if not profile_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find profile with id=%r" % id
                )
        else:
            profile_model = Profile(
                created=datetime.now(),
                version=0,
            )
            profile_model.engine_id = next_seq_id(
                "profile_engine_id_seq", session
            )

            if not code:

                def generate_inf_name():

                    return ''.join(
                        random.choice(string.ascii_lowercase)
                        for _ in range(6)
                    )

                profile_model.code = generate_inf_name()

        if name is not None:
            profile_model.name = name

        code = name  # Для совы

        if code:  # Don't change code if None or empty.
            profile_model.code = code

        if common is not None:
            profile_model.common = common

        if state is not None:
            profile_model.state = state

        if meta is not None:
            profile_model.meta = meta

        if is_enabled is not None:
            profile_model.is_enabled = is_enabled

        profile_model.version += 1

        session.add(profile_model)

        complect_model = session.query(Complect).get(
            settings.MAIN_COMPLECT_ID
        )
        if complect_model:
            complect_model.profile_ids = (
                complect_model.profile_ids or []
            ) + [profile_model.profile_id]

            session.add(complect_model)

        return profile_model.to_dict()
