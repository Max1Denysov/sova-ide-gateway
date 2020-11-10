#!/bin/bash

until alembic upgrade head 2>/dev/null; do
  echo "Database is unavailable - sleeping (10s)"
  sleep 10
done &&
echo "Done: alembic upgrade head" &&

python db_init.py &&

python gateway_server.py
