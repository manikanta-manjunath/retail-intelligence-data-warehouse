"""Database connection manager for Microsoft SQL Server.

Supports both SQLAlchemy engines and direct DBAPI connections (pymssql and pyodbc).
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.engine import Engine
import pymssql

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


class DatabaseConnectionManager:
    """Manages connections to Microsoft SQL Server Data Warehouse."""

    def __init__(self):
        self.server = os.getenv("SQL_SERVER", "localhost,1433")
        self.database = os.getenv("SQL_DATABASE", "RetailIntelligenceDW")
        self.username = os.getenv("SQL_USERNAME", "sa")
        self.password = os.getenv("SQL_PASSWORD", "")
        self.driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
        self.dialect_driver = os.getenv("SQL_DIALECT_DRIVER", "mssql+pymssql")
        self._engine: Engine | None = None

    def get_host_port(self) -> tuple[str, int]:
        """Parse host and port from server string."""
        if "," in self.server:
            host, port_str = self.server.split(",", 1)
            return host.strip(), int(port_str.strip())
        elif ":" in self.server:
            host, port_str = self.server.split(":", 1)
            return host.strip(), int(port_str.strip())
        return self.server.strip(), 1433

    def get_raw_connection(self, database: str | None = None, *, autocommit: bool = False) -> pymssql.Connection:
        """Create a direct DBAPI connection using pymssql."""
        host, port = self.get_host_port()
        db_name = database if database is not None else self.database
        if not self.password:
            raise ValueError("Set SQL_PASSWORD in the local .env or environment.")
        return pymssql.connect(
            server=host,
            port=port,
            user=self.username,
            password=self.password,
            database=db_name,
            autocommit=autocommit,
            login_timeout=8,
            timeout=60,
        )

    def get_engine(self, database: str | None = None) -> Engine:
        """Create and return a SQLAlchemy engine."""
        db_name = database if database is not None else self.database
        host, port = self.get_host_port()
        if not self.password:
            raise ValueError("Set SQL_PASSWORD in the local .env or environment.")
        query = {}
        if self.dialect_driver.startswith("mssql+pyodbc"):
            query = {"driver": self.driver, "TrustServerCertificate": "yes"}
        url = URL.create(self.dialect_driver, username=self.username,
                         password=self.password, host=host, port=port,
                         database=db_name, query=query)
        return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)

    @contextmanager
    def session_scope(self, database: str | None = None) -> Generator[Any, None, None]:
        """Provide a transactional scope around a series of operations."""
        conn = self.get_raw_connection(database)
        cursor = conn.cursor(as_dict=True)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def test_connection(self) -> bool:
        """Verify that SQL Server is reachable and responsive."""
        try:
            host, port = self.get_host_port()
            conn = pymssql.connect(
                server=host,
                port=port,
                user=self.username,
                password=self.password,
                database="master",
                timeout=5,
                login_timeout=8,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            conn.close()
            return row is not None
        except Exception as ex:
            print(f"Connection test failed: {ex}")
            return False


db_manager = DatabaseConnectionManager()
