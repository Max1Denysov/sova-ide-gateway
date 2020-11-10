"""
    Новая версия модуля запуска API RPC Flask сервера gateway
"""
from typing import Tuple

from flask import Flask
from flask import Response as FlaskResponse
from flask import request as flask_request
from jsonrpcserver import dispatch
from jsonrpcserver.methods import global_methods as methods
from sqlalchemy.engine.base import Engine

import settings
from api_world import ApiWorld
from nlab.db import create_sessionmaker

HOST = '0.0.0.0'
PORT = settings.GATEWAY_PORT
POSTGRES_PREFIX = settings.POSTGRES_ENV_PREFIX

app = Flask(__name__)


@app.route("/", methods=["POST"])
def index():
    """
        Обработка всех запросов к api gateway
    """
    request = flask_request.get_data().decode()

    response = dispatch(
        request=request, methods=methods, debug=True, basic_logging=True
    )
    return FlaskResponse(
        str(response), response.http_status, mimetype="application/json"
    )


def get_server_params(app=app, pg_prefix=POSTGRES_PREFIX,
                      methods=methods) -> Tuple[Flask, ApiWorld, Engine]:
    """
        Функция создает rpc-сервер и отдает его реквизиты.
    """
    sessionmaker = create_sessionmaker(env_prefix=pg_prefix)
    api = ApiWorld(sessionmaker)
    api.install(methods)

    database_engine = sessionmaker().session.bind

    return app, api, database_engine


if __name__ == "__main__":
    app, _, _ = get_server_params()
    app.run(host=HOST, port=PORT,)
