import os
import sys


if os.getenv("NLAB_ARM_DEV") == "1":
    from dotenv import load_dotenv
    sys.path.append(".")
    sys.path.append("nlab-armbe-common")
    load_dotenv("env/develop.env", override=True, verbose=True)

POSTGRES_ENV_PREFIX = "NLAB_ARM_POSTGRES_"
PROCESSOR_HOST = os.getenv("NLAB_ARM_PROCESSOR_HOST")

HEADERS = {"Content-type": "application/json"}

GATEWAY_PORT = os.getenv("NLAB_ARM_GATEWAY_PORT", "5000")

MAIN_COMPLECT_ID = os.getenv("NLAB_ARM_MAIN_COMPLECT_ID",
                             "3eaef2ac-c041-44ff-b022-377e8b5f8325")

POSTGRES_USER = os.getenv("NLAB_ARM_POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("NLAB_ARM_POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("NLAB_ARM_POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("NLAB_ARM_POSTGRES_DB")
POSTGRES_PORT = os.getenv("NLAB_ARM_POSTGRES_PORT", "5432")

COMPILER_TARGET = os.getenv("NLAB_ARM_COMPILER_TARGET", "sova-engine")
