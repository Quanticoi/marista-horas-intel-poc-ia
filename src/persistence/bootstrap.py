from psycopg import sql
from src.persistence.db import engine
from src.common.settings import required
import os


def bootstrap():
    with engine("admin").connect().execution_options(isolation_level="AUTOCOMMIT") as con:
        db = con.connection.driver_connection
        for name, secret in [("planning_migration", "MIGRATION_PASSWORD"),
                             ("planning_app", "APP_PASSWORD"),
                             ("planning_readonly", "READONLY_PASSWORD"), ("mlflow", "MLFLOW_PASSWORD")]:
            if not db.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (name,)).fetchone():
                db.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(name), sql.Literal(required(secret))))
        app_db = os.getenv("APP_DB_NAME", "planejamento_db")
        mlflow_db = os.getenv("MLFLOW_DB_NAME", "mlflow_db")
        for name, owner in [(app_db, "planning_migration"), (mlflow_db, "mlflow")]:
            if not db.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone():
                db.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(name), sql.Identifier(owner)))
            db.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(name)))
        db.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO planning_app, planning_readonly").format(sql.Identifier(app_db)))


def grants():
    with engine("migration").begin() as con:
        con.exec_driver_sql("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        con.exec_driver_sql("GRANT USAGE ON SCHEMA planning TO planning_app, planning_readonly")
        con.exec_driver_sql("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA planning TO planning_app")
        con.exec_driver_sql("GRANT SELECT ON ALL TABLES IN SCHEMA planning TO planning_readonly")
        con.exec_driver_sql("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA planning TO planning_app")
        con.exec_driver_sql("REVOKE UPDATE, DELETE ON planning.audit_events FROM planning_app")
