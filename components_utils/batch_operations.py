from nlab.rpc import ApiError


class BatchUpdateHelper:
    @classmethod
    def update(cls, instance, args, kwargs):
        with instance.create_session() as session:
            kwargs['action'] = 'update'
            kwargs['session'] = session
            result = cls._update(instance, session, args, kwargs)
            session.commit()
            return result

    @classmethod
    def _update(cls, instance, session, args, kwargs):
        if args:
            return [cls._update_one(instance, session, arg) for arg in args]
        else:
            return cls._update_one(instance, session, kwargs)

    @staticmethod
    def _update_one(instance, session, kwargs):
        # TODO: some components have more complex primary_key
        if kwargs.get("id") is None:
            raise ApiError(
                code="ID_REQUIRED",
                message="Must be id in update operation",
            )
        kwargs['action'] = 'update'
        kwargs['session'] = session
        return instance._store(**kwargs)


class BatchCreateHelper:
    @classmethod
    def create(cls, instance, args, kwargs):
        with instance.create_session() as session:
            kwargs['action'] = 'create'
            kwargs['session'] = session
            result = cls._create(instance, args, kwargs)
            session.commit()
            return result

    @staticmethod
    def _create(instance, args, kwargs):
        if args:
            return [instance._store(**arg) for arg in args]
        else:
            return instance._store(**kwargs)


class BatchCreateMixin:
    """
    Adds create method
    """
    def create(self, *args, **kwargs):
        return BatchCreateHelper.create(self, args, kwargs)


class BatchUpdateMixin:
    """
    Adds update method
    """
    def update(self, *args, **kwargs):
        return BatchUpdateHelper.update(self, args, kwargs)
