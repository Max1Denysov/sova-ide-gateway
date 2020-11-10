from datetime import datetime

from sqlalchemy import desc, func

from models import Suite, Template
from nlab.rpc import ApiError, RpcGroup
from nlab.rpc.object import VersionNoObject, VersionObject
from processor import transform_template_text


class TemplateRpc(RpcGroup):
    def __init__(self, tracer, create_session):
        super().__init__(
            name="template", tracer=tracer, create_session=create_session
        )
        self.template = VersionObject(
            name=self.name, primary_key="template_id", entity=Template,
            create_session=create_session
        )

    def create(self, suite_id, content=None, is_enabled=None,
               is_compilable=None, meta=None, position=None,
               position_before=None, position_after=None):

        return self._store(
            content=content, suite_id=suite_id, id=None,
            is_enabled=is_enabled, is_compilable=is_compilable,
            meta=meta, position=position,
            position_before=position_before, position_after=position_after,
        )

    def update(self, *args, **kwargs):

        if args:  # Получили список словарей
            result = []  # Возвращать, так же, будем список
            for item in args:
                item['action'] = 'update'
                result.append(self._store(**item))
            return result
        else:  # Получили словарь
            kwargs['action'] = 'update'
            return self._store(**kwargs)

    def list(self, offset=None, limit=None, profile_ids=None, suite_id=None,
             search=None, order=None, is_enabled=None, id=None, _process=None):

        filter_q = []

        if id is not None:
            filter_q.append(Template.template_id.in_(id))

        filter_by_q = {}
        if suite_id:
            filter_by_q["suite_id"] = suite_id

        join = []

        if profile_ids:
            join.append(Template.suite)
            filter_q.append(Suite.profile_id.in_(profile_ids))

        if is_enabled is not None:
            filter_q.append(Template.is_enabled.is_(is_enabled))

        items, total_items = self.template.filter(
            filter_q=filter_q, filter_by_q=filter_by_q,
            offset=offset, limit=limit, join=join, order=order
        )

        if _process:
            items = [_process_template_inplace(item) for item in items]

        return {
            "items": items,
            "total": total_items,
        }

    def fetch(self, id, _process=None):

        with self.create_session() as session:
            template_model = self.template.get(id, session=session)
            if not template_model:
                raise ApiError(
                    code="NOT_EXISTS",
                    message="Can't find template with id=%r" % id
                )

            item = template_model.to_dict()

            if _process:
                item = _process_template_inplace(item)

            return item

    def remove(self, id):

        try:
            with self.create_session() as session:
                if not isinstance(id, list):
                    id = [id]

                for iid in id:
                    template_model = self.template.get(iid, session=session)
                    self._update_parent(template_model, session=session)

                return self.template.remove(id, session)

        except VersionNoObject as e:
            raise ApiError(code="NOT_EXISTS", message=e.args[0]) from e

    def store(self, content=None, suite_id=None, id=None, is_enabled=None,
              is_compilable=None, meta=None, position=None):

        return self._store(
            content=content, suite_id=suite_id, id=id, is_enabled=is_enabled,
            is_compilable=is_compilable, meta=meta,
            position=position,
            position_before=None, position_after=None,
        )

    def _store(self, *, content=None, suite_id=None, id=None, is_enabled=None,
               is_compilable=None, meta=None, position=None,
               position_before=None, position_after=None, action=None):

        with self.create_session() as session:
            set_position = self._calculate_template_position(
                position=position,
                position_before=position_before,
                position_after=position_after,
                suite_id=suite_id,
                do_insert=not id,
                session=session
            )

            if action == "update":
                template_model = self.template.get(id, session=session)
                if not template_model:
                    raise ApiError(
                        code="NOT_EXISTS",
                        message="Can't find template with id=%r" % id
                    )
            else:
                if suite_id is None:
                    raise ApiError(
                        code="MISSING_SUITE_ID",
                        message="suite_id must be given for creating template"
                    )

                if set_position is None:
                    # Если позиция не указана, ставим в конец.
                    max_position = session.query(
                        func.max(Template.position)
                    ).filter_by(suite_id=suite_id).scalar()
                    set_position = (max_position or 0) + 1

                template_model = Template(
                    template_id=id,
                    suite_id=suite_id,
                    created=datetime.now(),
                    version=0,
                )

            if content is not None:
                template_model.content = content

            if is_enabled is not None:
                template_model.is_enabled = is_enabled

            if is_compilable is not None:
                template_model.is_compilable = is_compilable

            if meta is not None:
                template_model.meta = meta

            if set_position is not None:
                self._move_positions_slow_method(
                    template_model, set_position, session=session
                )

            # template_model.updated = datetime.now()
            template_model.version += 1

            session.add(template_model)

            self._update_parent(template_model, session)

            template = template_model.to_dict()
            del template["stats"]

            session.commit()

            return template_model.to_dict()

    @staticmethod
    def _update_parent(template_model: Template, session):
        suite_model = session.query(Suite).get(template_model.suite_id)
        suite_model.updated = datetime.now()
        session.add(suite_model)

    def _calculate_template_position(
            self, *, position: int,
            position_before: str, position_after: str, suite_id: str,
            do_insert: bool, session
            ):
        """
        Calculates position for template in insert or update operation.

        :param position: Set position
        :param position_before: Position before template uuid or "last"
        :param position_after: Position after template uuid or "first"
        :param suite_id: Suite id
        :param do_insert: Do insert or update
        :param session: Database session
        :return: new position or None if not changes
        """
        position_arguments_exist = sum(
            int(arg is not None)
            for arg in (position, position_before, position_after)
        )
        if position_arguments_exist > 1:
            raise ApiError(
                code="INVALID_POSITION",
                message="Only one of `position`, `position_before` "
                        "and `position_after` arguments must be given!"
            )

        fetch_position = position_before or position_after or None

        if fetch_position not in ("first", "last", None):
            # fetch_position is Template uuid
            fetch_template = (session
                              .query(Template)
                              .filter_by(template_id=fetch_position)
                              .scalar())

            set_position = fetch_template.position
            if position_after:
                set_position += 1

        elif fetch_position == "first":
            set_position = 1
        elif position is not None:
            set_position = position
        elif do_insert or fetch_position == "last":
            # Get max template position in suite
            max_position = (session
                            .query(func.max(Template.position))
                            .filter_by(suite_id=suite_id)
                            .scalar())
            set_position = (max_position or 0) + 1
        else:
            # Do nothing
            set_position = None

        return set_position

    def _move_positions_slow_method(
            self, template_model: Template, position: int, *, session):
        """
        FIXME: Need correct batch solution for updating with constraint
        There was constraint uniquenness problem in updating positions.
        And something goes wrong with other correct methods.
        Slow but working method

        :param template_model: Model which position updates
        :param position: Set position
        :param session:
        :return:
        """
        templates = (
            session.query(Template.template_id)
            .filter(
                # Move all templates in suite
                Template.suite_id == template_model.suite_id,
                # Which positions next to set position
                Template.position >= position,
            )
            .order_by(desc(Template.position))
            .all()
        )

        for move_template in templates:
            session.query(Template).filter(
                Template.template_id == move_template.template_id
            ).update(
                    {Template.position: Template.position + 1},
                    synchronize_session=False,
            )

        template_model.position = position


def _process_template_inplace(template):
    template["content"] = transform_template_text(template["content"])
    return template
