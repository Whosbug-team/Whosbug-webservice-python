# -*- coding: utf-8 -*-
import os
import logging
from time import time
from time import sleep
import psycopg2

check_timeout = os.getenv("WHOSBUG_POSTGRES_CHECK_TIMEOUT")
check_interval = os.getenv("WHOSBUG_POSTGRES_CHECK_INTERVAL")
interval_unit = "second" if check_interval == 1 else "seconds"

config = {
    'DB_CONN': os.getenv('DB_CONN', None)
}

start_time = time()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def pg_isready(DB_CONN):
    while time() - start_time < int(check_timeout):
        try:
            conn = psycopg2.connect(DB_CONN)
            logger.info("Postgres is ready! ✨ 💅")
            conn.close()
            return True
        except psycopg2.OperationalError:
            logger.info(f"Postgres isn't ready. Waiting for {check_interval} {interval_unit}...")
            sleep(int(check_interval))

    logger.error(f"We could not connect to Postgres within {check_timeout} seconds.")
    return False


if __name__ == '__main__':
    print(f'DB_CONN: {config["DB_CONN"]}')
    pg_isready(config['DB_CONN'])
