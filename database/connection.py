import pymysql
import pymysql.cursors
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_raw_connection(include_db=True):
    """Establishes connection to MySQL server."""
    kw = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True,
        'connect_timeout': 10
    }
    if include_db and Config.DB_NAME:
        kw['database'] = Config.DB_NAME
    return pymysql.connect(**kw)

def get_db_connection():
    """Get connection to insurance_management database."""
    try:
        return get_raw_connection(include_db=True)
    except Exception as e:
        logger.error(f"Operational error connecting to MySQL: {e}")
        # Try initializing db and reconnecting
        try:
            init_db()
            return get_raw_connection(include_db=True)
        except Exception:
            raise e

def init_db():
    """Initializes the database and executes schema.sql"""
    try:
        # Connect directly with or without db
        try:
            conn = get_raw_connection(include_db=True)
        except Exception:
            conn = get_raw_connection(include_db=False)
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()
            conn = get_raw_connection(include_db=True)

        import os
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            statements = sql_script.split(';')
            with conn.cursor() as cursor:
                for statement in statements:
                    stmt = statement.strip()
                    if stmt:
                        try:
                            cursor.execute(stmt)
                        except Exception as ex:
                            logger.error(f"Error executing statement: {stmt[:50]}... Error: {ex}")
        conn.close()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise e
