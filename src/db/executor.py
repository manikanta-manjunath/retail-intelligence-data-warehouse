"""Explicit, non-destructive SQL Server setup and read-only verification."""
import re
from pathlib import Path
from src.db.connection import db_manager
from src.utils.config import PROJECT_ROOT


def split_batches(content: str) -> list[str]:
    """Split the project's T-SQL scripts at standalone GO delimiters."""
    return [part.strip() for part in re.split(
        r"^\s*GO\s*(?:--[^\n]*)?$", content, flags=re.MULTILINE | re.IGNORECASE
    ) if part.strip()]


class SQLExecutor:
    def __init__(self, manager=None):
        self.manager = manager or db_manager

    def execute_script(self, script_path, database=None) -> bool:
        path = Path(script_path)
        if self.manager.database != "RetailIntelligenceDW":
            raise ValueError("The preserved SQL scripts target RetailIntelligenceDW.")
        target = database or ("master" if path.name.startswith("00_") else self.manager.database)
        conn = self.manager.get_raw_connection(target, autocommit=True)
        cursor = conn.cursor()
        try:
            for batch in split_batches(path.read_text(encoding="utf-8")):
                cursor.execute(batch)
                while cursor.nextset():
                    pass
            print(f"Executed {path.name}")
            return True
        finally:
            cursor.close()
            conn.close()

    def run_all_setup_scripts(self, sql_dir=None) -> bool:
        path = Path(sql_dir) if sql_dir else PROJECT_ROOT / "sql"
        names = ["00_create_database.sql", "01_create_schemas.sql", "02_create_source_tables.sql",
                 "03_create_dimensions.sql", "04_create_fact_tables.sql", "05_create_constraints_indexes.sql",
                 "14_etl_reliability.sql", "06_create_etl_procedures.sql",
                 "07_create_warehouse_views.sql", "08_create_data_marts.sql"]
        for name in names:
            self.execute_script(path / name)
        return True


sql_executor = SQLExecutor()
