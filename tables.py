import sqlalchemy
from sqlalchemy import Table, MetaData, Column, Integer, String, Boolean, \
    BigInteger, DateTime, TEXT, func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID, JSONB, ARRAY

metadata = MetaData()

ELEMENT_STATUSES = ("active", "inactive")

element_statuses = ENUM(*ELEMENT_STATUSES, name="status")


users_table = Table(
    "users", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=False),
    Column("first_name", String()),
    Column("last_name", String()),
    Column("version", BigInteger, nullable=False),
    Column("meta", JSONB, server_default="{}", nullable=False),
)


profiles_table = Table(
    "profiles", metadata,
    Column("id", UUID, server_default=func.uuid_generate_v4(),
           primary_key=True),
    Column("created", DateTime(timezone=True), nullable=False,
           server_default=func.now()),
    Column("updated", DateTime(timezone=True), nullable=True,
           onupdate=func.now()),
    Column("version", BigInteger, nullable=False),
    Column("state", element_statuses, default="active", nullable=False),
    Column("name", String, nullable=False),
    Column("code", String, nullable=False),
    Column("common", Boolean, default=False, nullable=False),
    Column("meta", JSONB, server_default="{}", nullable=False),
    Column("is_enabled", Boolean, server_default="t", nullable=False),
    Column("engine_id", Integer, server_default="1", nullable=False),
)


suites_table = Table(
    "suites", metadata,
    Column("id", UUID, server_default=func.uuid_generate_v4(),
           primary_key=True),
    Column("profile_id", UUID, ForeignKey("profiles.id"), nullable=False),
    Column("created", DateTime(timezone=True), nullable=False,
           server_default=func.now()),
    Column("updated", DateTime(timezone=True), nullable=True,
           onupdate=func.now()),
    Column("version", BigInteger, nullable=False),
    Column("state", element_statuses, default="active", nullable=False),
    Column("title", String, default="", nullable=False),
    Column("is_enabled", Boolean, default=True, nullable=False),
    Column("hidden", Boolean, default=False, nullable=False),
    Column("meta", JSONB, server_default="{}", nullable=False),
)


templates_table = Table(
    "templates", metadata,
    Column("id", UUID, server_default=func.uuid_generate_v4(),
           primary_key=True),
    Column("suite_id", UUID, ForeignKey("suites.id"), nullable=False),
    Column("created", DateTime(timezone=True), nullable=False,
           server_default=func.now()),
    Column("updated", DateTime(timezone=True), nullable=True,
           onupdate=func.now()),
    Column("version", BigInteger, nullable=False),
    Column("position", Integer, nullable=False),
    Column("state", element_statuses, default="active", nullable=False),
    Column("content", TEXT, default="", nullable=False),
    Column("is_enabled", Boolean, default=True, nullable=False),
    Column("is_compilable", Boolean, default=True, nullable=False),
    Column("meta", JSONB, server_default="{}", nullable=False),

    UniqueConstraint(
        "suite_id", "position", name="suite_id_positions",
    ),
)


dictionaries_table = Table(
    "dictionaries", metadata,
    Column("id", UUID, server_default=func.uuid_generate_v4(),
           primary_key=True),
    Column("created", DateTime(timezone=True), nullable=False,
           server_default=func.now()),
    Column("updated", DateTime(timezone=True), nullable=True,
           onupdate=func.now()),
    Column("version", BigInteger, nullable=False),
    Column("state", element_statuses, default="active", nullable=False),
    Column("kind", TEXT, server_default="match", nullable=False),
    Column("title", TEXT, default="", nullable=False),
    Column("description", TEXT, default="", nullable=False),
    Column("content", TEXT, default="", nullable=False),
    Column("common", Boolean, default=False, nullable=False),
    Column("hidden", Boolean, default=False, nullable=False),
    Column("meta", JSONB, server_default="{}", nullable=False),
    Column("profile_ids", ARRAY(UUID),
           server_default=sqlalchemy.text("ARRAY[]::UUID[]"), nullable=False),
    Column("is_enabled", Boolean, server_default="t", nullable=False),
    Column("parts", JSONB, server_default="{}", nullable=False),
)


dictionaries_versions_table = Table(
    "dictionaries_versions", metadata,
    Column("version_id", UUID, server_default=func.uuid_generate_v4(),
           primary_key=True),
    Column("id", UUID),
    Column("created", DateTime(timezone=True)),
    Column("updated", DateTime(timezone=True)),
    Column("version", BigInteger),
    Column("state", TEXT),
    Column("kind", TEXT),
    Column("title", TEXT),
    Column("description", TEXT),
    Column("content", TEXT),
    Column("common", Boolean),
    Column("hidden", Boolean),
    Column("meta", JSONB),
    Column("profile_ids", ARRAY(UUID)),
    Column("is_enabled", Boolean),
    Column("parts", JSONB),
)


complects_table = Table(
    "complects", metadata,
    Column("id", UUID, server_default=func.uuid_generate_v4(),
           primary_key=True),
    Column("created", DateTime(timezone=True), nullable=False,
           server_default=func.now()),
    Column("updated", DateTime(timezone=True), nullable=True,
           onupdate=func.now()),
    Column("version", BigInteger, nullable=False),
    Column("state", element_statuses, default="active", nullable=False),
    Column("profile_ids", ARRAY(UUID), nullable=False),
    Column("name", String, nullable=False),
    Column("code", String, nullable=False, unique=True),
    Column("meta", JSONB, server_default="{}", nullable=False),
    Column("is_enabled", Boolean, server_default="t", nullable=False),
    Column("compiler_target", String, server_default="", nullable=False),
    Column("debug_target", String, server_default="", nullable=False),
    Column("deploy_target", String, server_default="", nullable=False),
)


testcase_table = Table(
    "testcase", metadata,
    Column("id", UUID, server_default=func.uuid_generate_v4(),
           primary_key=True),
    Column("created", DateTime(timezone=True), nullable=False,
           server_default=func.now()),
    Column("updated", DateTime(timezone=True), nullable=True,
           onupdate=func.now()),
    Column("profile_id", UUID, ForeignKey("profiles.id"), nullable=True),
    Column("title", TEXT, nullable=False),
    Column("description", TEXT),
    Column("replicas", ARRAY(String), nullable=False),
    Column("is_common", Boolean, default=True, nullable=False),
    Column("author", BigInteger, nullable=False)
)

access_profile_user_table = Table(
    "access_profile_user", metadata,
    Column("user_id", UUID, nullable=False, primary_key=True),
    Column("profile_id", UUID, ForeignKey("profiles.id"), nullable=False,
           primary_key=True),
    Column("permissions", JSONB, server_default="{}", nullable=False)
)


access_user_flags_table = Table(
    "access_user_flags", metadata,
    Column("user_id", UUID, nullable=False, primary_key=True),
    Column("flags", JSONB, server_default="{}", nullable=False),
)


access_profile_account_table = Table(
    "access_profile_account", metadata,
    Column("account_id", UUID, nullable=False, primary_key=True),
    Column("profile_id", UUID, ForeignKey("profiles.id"), nullable=False,
           primary_key=True),
)


access_complect_account_table = Table(
    "access_complect_account", metadata,
    Column("account_id", UUID, nullable=False, primary_key=True),
    Column("complect_id", UUID, ForeignKey("complects.id"), nullable=False,
           primary_key=True),
)
