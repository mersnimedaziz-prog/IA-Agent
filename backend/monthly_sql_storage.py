import os
import sqlite3
from datetime import datetime


DB_DIR = "data/monthly"
DB_PATH = os.path.join(DB_DIR, "monthly_kpi.db")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_monthly_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            compilation_date TEXT NOT NULL,
            kpi_name TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            total_md REAL,
            type TEXT DEFAULT 'Result',
            created_at TEXT,
            UNIQUE(month, kpi_name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            compilation_date TEXT NOT NULL,
            kpi_name TEXT NOT NULL,
            target_value REAL NOT NULL,
            unit TEXT,
            comparison TEXT DEFAULT '>=',
            type TEXT DEFAULT 'Target',
            created_at TEXT,
            UNIQUE(month, kpi_name)
        )
    """)

    conn.commit()
    conn.close()


def save_result_sql(month: str, kpi_name: str, value: float, unit: str, total_md=None):
    init_monthly_database()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO monthly_results (
            month,
            compilation_date,
            kpi_name,
            value,
            unit,
            total_md,
            type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(month, kpi_name)
        DO UPDATE SET
            value = excluded.value,
            unit = excluded.unit,
            total_md = excluded.total_md,
            type = excluded.type,
            created_at = excluded.created_at
    """, (
        month,
        f"{month}-01",
        kpi_name,
        value,
        unit,
        total_md,
        "Result",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def save_target_sql(
    month: str,
    kpi_name: str,
    target_value: float,
    unit: str,
    comparison: str = ">="
):
    init_monthly_database()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO monthly_targets (
            month,
            compilation_date,
            kpi_name,
            target_value,
            unit,
            comparison,
            type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(month, kpi_name)
        DO UPDATE SET
            target_value = excluded.target_value,
            unit = excluded.unit,
            comparison = excluded.comparison,
            type = excluded.type,
            created_at = excluded.created_at
    """, (
        month,
        f"{month}-01",
        kpi_name,
        target_value,
        unit,
        comparison,
        "Target",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_results_sql():
    init_monthly_database()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            month,
            compilation_date,
            kpi_name,
            value,
            unit,
            total_md,
            type,
            created_at
        FROM monthly_results
        ORDER BY compilation_date ASC
    """)

    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return rows


def get_targets_sql():
    init_monthly_database()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            month,
            compilation_date,
            kpi_name,
            target_value,
            unit,
            comparison,
            type,
            created_at
        FROM monthly_targets
        ORDER BY compilation_date ASC
    """)

    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return rows
