import random
from datetime import datetime, timedelta

from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from tables import (access_complect_account_table,
                    access_profile_account_table, access_profile_user_table,
                    access_user_flags_table, complects_table,
                    dictionaries_table, dictionaries_versions_table, metadata,
                    profiles_table, suites_table, templates_table,
                    testcase_table, users_table)

Base = declarative_base(metadata=metadata)


class User(Base):
    __table__ = users_table

    user_id = users_table.c.id
    first_name = users_table.c.first_name
    last_name = users_table.c.last_name


class Profile(Base):
    __table__ = profiles_table

    profile_id = profiles_table.c.id
    created = profiles_table.c.created
    updated = profiles_table.c.updated
    version = profiles_table.c.version
    name = profiles_table.c.name
    code = profiles_table.c.code
    state = profiles_table.c.state
    common = profiles_table.c.common
    is_enabled = profiles_table.c.is_enabled
    engine_id = profiles_table.c.engine_id

    def to_dict(self):
        return {
            "id": self.profile_id,
            "name": self.name,
            "code": self.code,
            "state": self.state,
            "common": self.common,
            "meta": self.meta,
            "is_enabled": self.is_enabled,
            "engine_id": self.engine_id,
        }


class Suite(Base):
    __table__ = suites_table

    suite_id = suites_table.c.id
    profile_id = suites_table.c.profile_id
    created = suites_table.c.created
    updated = suites_table.c.updated
    version = suites_table.c.version
    title = suites_table.c.title
    state = suites_table.c.state
    is_enabled = suites_table.c.is_enabled
    hidden = suites_table.c.hidden

    def to_dict(self):
        return {
            "id": self.suite_id,
            "title": self.title,
            "state": self.state,
            "updated": self.updated or self.created,
            "profile_id": self.profile_id,
            "meta": self.meta,
            "is_enabled": self.is_enabled,
            "hidden": self.hidden,
        }


class Template(Base):
    __table__ = templates_table

    template_id = templates_table.c.id
    suite_id = templates_table.c.suite_id
    created = templates_table.c.created
    updated = templates_table.c.updated
    content = templates_table.c.content
    version = templates_table.c.version
    state = templates_table.c.state
    position = templates_table.c.position
    is_enabled = templates_table.c.is_enabled
    is_compilable = templates_table.c.is_compilable

    suite = relationship("Suite", lazy="joined")

    def to_dict(self):
        res = {
            "id": self.template_id,
            "content": self.content,
            "suite_id": self.suite_id,
            "is_enabled": self.is_enabled,
            "is_compilable": self.is_compilable,
            "position": self.position,
            "updated": self.updated or self.created,
            "created": self.created,
            "state": self.state,
            "profile_id": self.suite.profile_id if self.suite else None,
            "meta": self.meta,
            "stats": self.extract_stats(),
            "suite_title": self.suite.title if self.suite else None,
            "template_title": self.meta.get("title") if self.meta else None,
        }

        return res

    def extract_stats(self):
        # For debug now
        used_7d = random.randint(0, 2)

        last_used = datetime.now() - timedelta(days=random.uniform(1, 60))
        if used_7d:
            last_used = datetime.now() - timedelta(days=random.uniform(1, 7))

        res = {
            "last_used": last_used,
            "used_7d": used_7d,
            "used_30d": random.randint(0, 2) + used_7d,
        }
        return res


class Dictionary(Base):
    __table__ = dictionaries_table

    dictionary_id = dictionaries_table.c.id
    created = dictionaries_table.c.created
    updated = dictionaries_table.c.updated
    version = dictionaries_table.c.version
    state = dictionaries_table.c.state
    kind = dictionaries_table.c.kind
    code = dictionaries_table.c.title
    description = dictionaries_table.c.description
    content = dictionaries_table.c.content
    common = dictionaries_table.c.common
    hidden = dictionaries_table.c.hidden
    meta = dictionaries_table.c.meta
    profile_ids = dictionaries_table.c.profile_ids
    is_enabled = dictionaries_table.c.is_enabled
    parts = dictionaries_table.c.parts

    def to_dict(self):
        res = {
            "id": self.dictionary_id,
            "created": self.created,
            "updated": self.updated or self.created,
            "state": self.state,
            "kind": self.kind,
            "code": self.code,
            "description": self.description,
            "content": self.content,
            "common": self.common,
            "hidden": self.hidden,
            "meta": self.meta,
            "profile_ids": self.profile_ids,
            "is_enabled": self.is_enabled,
            "version": self.version,
            "parts": self.parts,
        }

        return res

    def to_short_dict(self):
        res = {
            "id": self.dictionary_id,
            "created": self.created,
            "updated": self.updated or self.created,
            "state": self.state,
            "kind": self.kind,
            "code": self.code,
            "description": self.description,
            "common": self.common,
            "hidden": self.hidden,
            "meta": self.meta,
            "profile_ids": self.profile_ids,
            "is_enabled": self.is_enabled,
            "version": self.version,
            "parts": self.parts,
        }

        return res


class DictionaryVersion(Base):
    __table__ = dictionaries_versions_table
    dictionary_id = dictionaries_versions_table.c.id
    created = dictionaries_versions_table.c.created
    updated = dictionaries_versions_table.c.updated
    version = dictionaries_versions_table.c.version
    state = dictionaries_versions_table.c.state
    kind = dictionaries_versions_table.c.kind
    code = dictionaries_versions_table.c.title
    description = dictionaries_versions_table.c.description
    content = dictionaries_versions_table.c.content
    common = dictionaries_versions_table.c.common
    hidden = dictionaries_versions_table.c.hidden
    meta = dictionaries_versions_table.c.meta
    profile_ids = dictionaries_versions_table.c.profile_ids
    is_enabled = dictionaries_versions_table.c.is_enabled
    parts = dictionaries_versions_table.c.parts

    def to_dict(self):
        return {
            "version_id": self.version_id,
            "id": self.dictionary_id,
            "created": self.created,
            "updated": self.updated or self.created,
            "state": self.state,
            "kind": self.kind,
            "code": self.code,
            "description": self.description,
            "content": self.content,
            "common": self.common,
            "hidden": self.hidden,
            "meta": self.meta,
            "profile_ids": self.profile_ids,
            "is_enabled": self.is_enabled,
            "version": self.version,
            "parts": self.parts,
        }


@listens_for(Dictionary, 'after_insert')
@listens_for(Dictionary, 'after_update')
def task_after_update_function(mapper, connection, target):

    table = DictionaryVersion.__table__
    connection.execute(
        table.insert().values(
            id=target.dictionary_id,
            created=target.created,
            updated=target.updated,
            version=target.version,
            state=target.state,
            kind=target.kind,
            title=target.code,
            description=target.description,
            content=target.content,
            common=target.common,
            hidden=target.hidden,
            meta=target.meta,
            profile_ids=target.profile_ids,
            is_enabled=target.is_enabled,
            parts=target.parts,
        )
    )


class Complect(Base):
    __table__ = complects_table

    complect_id = complects_table.c.id
    created = complects_table.c.created
    updated = complects_table.c.updated
    name = complects_table.c.name
    code = complects_table.c.code
    version = complects_table.c.version
    state = complects_table.c.state
    profile_ids = complects_table.c.profile_ids
    is_enabled = complects_table.c.is_enabled
    compiler_target = complects_table.c.compiler_target
    debug_target = complects_table.c.debug_target
    deploy_target = complects_table.c.deploy_target

    def to_dict(self):
        res = {
            "id": self.complect_id,
            "name": self.name,
            "code": self.code,
            "state": self.state,
            "profile_ids": self.profile_ids,
            "created": self.created,
            "updated": self.updated or self.created,
            "meta": self.meta,
            "is_enabled": self.is_enabled,
            "compiler_target": self.compiler_target,
            "debug_target": self.debug_target,
            "deploy_target": self.deploy_target,
        }

        return res


class Testcase(Base):
    __test__ = False

    __table__ = testcase_table

    testcase_id = testcase_table.c.id
    created = testcase_table.c.created
    updated = testcase_table.c.updated
    profile_id = testcase_table.c.profile_id
    title = testcase_table.c.title
    description = testcase_table.c.description
    replicas = testcase_table.c.replicas
    is_common = testcase_table.c.is_common
    author = testcase_table.c.author

    def to_dict(self):
        res = {
            "id": self.testcase_id,
            "profile_id": self.profile_id,
            "title": self.title,
            "description": self.description,
            "replicas": self.replicas,
            "is_common": self.is_common,
            "created": self.created,
            "author": self.author
        }

        return res

    def to_short_dict(self):
        res = {
            "id": self.testcase_id,
            "replicas": self.replicas,
        }

        return res


class AccessProfileUser(Base):
    __table__ = access_profile_user_table

    user_id = access_profile_user_table.c.user_id
    profile_id = access_profile_user_table.c.profile_id
    permissions = access_profile_user_table.c.permissions

    def to_dict(self):
        res = {
            "user_id": self.user_id,
            "profile_id": self.profile_id,
            "permissions": self.permissions
            }

        return res


class AccessUserFlags(Base):
    __table__ = access_user_flags_table

    user_id = access_user_flags_table.c.user_id
    flags = access_user_flags_table.c.flags

    def to_dict(self):
        res = {
            "user_id": self.user_id,
            "flags": self.flags,
            }

        return res


class AccessProfileAccount(Base):
    __table__ = access_profile_account_table

    account_id = access_profile_account_table.c.account_id
    profile_id = access_profile_account_table.c.profile_id

    def to_dict(self):
        res = {
            "account_id": self.account_id,
            "profile_id": self.profile_id,
            }

        return res


class AccessComplectAccount(Base):

    __table__ = access_complect_account_table

    account_id = access_complect_account_table.c.account_id
    complect_id = access_complect_account_table.c.complect_id

    def to_dict(self):

        res = {
            "account_id": self.account_id,
            "complect_id": self.complect_id,
        }

        return res
