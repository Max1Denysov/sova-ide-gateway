""" Скрипт инициализации БД сервиса gateway.

    Cоздает запись в таблице complect c complect_id=settings.MAIN_COMPLECT_ID
"""
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from models import Complect
from settings import (COMPILER_TARGET, MAIN_COMPLECT_ID, POSTGRES_DB,
                      POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT,
                      POSTGRES_USER)

connect_str = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
connect_str += f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(connect_str)
Session = sessionmaker(bind=engine)
session = Session()

q = insert(Complect).values(
    id=MAIN_COMPLECT_ID,
    version=1,
    profile_ids=[],
    name="main",
    code=MAIN_COMPLECT_ID,
    compiler_target=COMPILER_TARGET,
    debug_target=COMPILER_TARGET,
    deploy_target=COMPILER_TARGET,
)

try:
    session.execute(q)
    session.commit()

    message = f"Table 'complect': row with complect_id={MAIN_COMPLECT_ID} "
    message += f"and compiler_target='{COMPILER_TARGET}' "
    message += "was created!"
    print(message)

except Exception:
    pass
