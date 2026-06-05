from __future__ import annotations

from sqlalchemy import inspect

from database.connection import check_db_connection, engine, init_db


def main() -> None:
    check_db_connection()
    init_db()

    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    print("Conexion a PostgreSQL OK.")
    print("Tablas disponibles:")
    for table in tables:
        print(f"- {table}")


if __name__ == "__main__":
    main()
