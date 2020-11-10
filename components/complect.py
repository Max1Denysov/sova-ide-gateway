import copy
from datetime import datetime

from components_utils.batch_operations import BatchUpdateMixin
from models import Complect
from nlab.rpc import ApiError, RpcGroup, rpc_name
from nlab.rpc.object import VersionNoObject, VersionObject


class ComplectRpc(RpcGroup, BatchUpdateMixin):

    def __init__(self, tracer, create_session):

        super().__init__(
            name="complect", tracer=tracer, create_session=create_session
        )
        self.complect = VersionObject(
            name=self.name, primary_key="complect_id", entity=Complect,
            create_session=create_session
        )

    def create(self, **kwargs):
        with self.create_session() as session:
            kwargs['session'] = session
            result = self._store(**kwargs)
            session.commit()

        return result

    @rpc_name("list")
    def list_(self, user=None, account_id=None, offset=None, limit=None,
              search=None, order=None):

        filter_q = {}
        join = None

        items, total_items = self.complect.filter(
            filter_q=filter_q, join=join,
            offset=offset, limit=limit, order=order
        )

        return {
            "items": items,
            "total": total_items,
        }

    def fetch(self, id):

        with self.create_session() as session:
            complect_model = self.complect.get(id, session=session)
            if not complect_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find complect with id=%r" % id
                )

            return complect_model.to_dict()

    def change(self, id, action, profile_id):

        if action not in ("add", "remove"):
            raise ValueError("Invalid action: %s" % action)

        with self.create_session() as session:
            complect_model = self.complect.get(id, session=session)
            if not complect_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find complect with id=%r" % id
                )

            save = False

            in_ = profile_id in complect_model.profile_ids
            if action == "add":
                if not in_:
                    profile_ids = copy.deepcopy(complect_model.profile_ids)
                    profile_ids.append(profile_id)
                    complect_model.profile_ids = profile_ids
                    save = True
            else:
                if in_:
                    profile_ids = copy.deepcopy(complect_model.profile_ids)
                    profile_ids.remove(profile_id)
                    complect_model.profile_ids = profile_ids
                    save = True

            if save:
                session.add(complect_model)
                session.commit()

            return complect_model.to_dict()

    def remove(self, id):

        try:
            return self.complect.remove(id)
        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e

    def _store(self, id=None, name=None, state=None, profile_ids=None,
               meta=None, is_enabled=None, code=None,
               action=None, compiler_target=None, debug_target=None,
               deploy_target=None, session=None):

        if action == 'update':
            complect_model = self.complect.get(id, session=session)
            if not complect_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find complect with id=%r" % id
                )
        else:
            complect_model = Complect(created=datetime.now(), version=0, )

        if name is not None:
            complect_model.name = name

        if state is not None:
            complect_model.state = state

        if profile_ids is not None:
            complect_model.profile_ids = profile_ids

        if meta is not None:
            complect_model.meta = meta

        if is_enabled is not None:
            complect_model.is_enabled = is_enabled

        if code is not None:
            complect_model.code = code

        if compiler_target is not None:
            complect_model.compiler_target = compiler_target

        if debug_target is not None:
            complect_model.debug_target = debug_target

        if deploy_target is not None:
            complect_model.deploy_target = deploy_target

        complect_model.version += 1

        session.add(complect_model)
        session.flush()

        return complect_model.to_dict()
