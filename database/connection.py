import pymysql
import pymysql.cursors
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_raw_connection(include_db=True):
    """Establishes connection to MySQL server."""
    kw = {
        'host': Config.DB_HOST,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True
    }
    if include_db:
        kw['database'] = Config.DB_NAME
    return pymysql.connect(**kw)

def get_db_connection():
    """Get connection to insurance_management database."""
    try:
        return get_raw_connection(include_db=True)
    except pymysql.err.OperationalError as e:
        # If database does not exist (error 1049), auto create
        if e.args[0] == 1049:
            init_db()
            return get_raw_connection(include_db=True)
        raise e

def init_db():
    """Initializes the database and executes schema.sql"""
    try:
        # Connect without db selected to create database
        conn = get_raw_connection(include_db=False)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()

        # Connect with db selected to execute schema
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
