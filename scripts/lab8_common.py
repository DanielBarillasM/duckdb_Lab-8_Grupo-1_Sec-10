"""Rutas y vista normalizada para analizar los Parquet originales con DuckDB."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = PROCESSED / "results"
PATTERN = re.compile(r"^(yellow|green)_tripdata_(202[456])-(\d{2})\.parquet$")


def parquet_files(years: tuple[int, ...] | None = None) -> list[Path]:
    """Devuelve solo archivos esperados, ordenados y existentes."""
    paths = []
    for path in RAW.glob("*/*/*_tripdata_*.parquet"):
        match = PATTERN.fullmatch(path.name)
        if not match:
            continue
        taxi, year, month = match.groups()
        if path.parent.name != year or path.parent.parent.name != taxi:
            continue
        if years is not None and int(year) not in years:
            continue
        if 1 <= int(month) <= 12:
            paths.append(path)
    return sorted(paths)


def sql_path_list(paths: list[Path]) -> str:
    if not paths:
        raise FileNotFoundError("No se encontraron Parquet en data/raw; ejecute download_data.py")
    escaped = ["'" + path.as_posix().replace("'", "''") + "'" for path in paths]
    return "[" + ", ".join(escaped) + "]"


def replace_view(connection, years: tuple[int, ...] | None = None) -> None:
    """Actualiza la vista con exactamente los años/archivos del escenario."""
    paths = parquet_files(years)
    source = sql_path_list(paths)
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW trips AS
        SELECT
            regexp_extract(filename, '(yellow|green)_tripdata_', 1) AS taxi_type,
            try_cast(regexp_extract(filename, 'tripdata_([0-9]{{4}})-', 1) AS INTEGER) AS file_year,
            try_cast(regexp_extract(filename, 'tripdata_[0-9]{{4}}-([0-9]{{2}})', 1) AS INTEGER) AS file_month,
            filename AS source_file,
            coalesce(try_cast(tpep_pickup_datetime AS TIMESTAMP),
                     try_cast(lpep_pickup_datetime AS TIMESTAMP)) AS pickup_datetime,
            coalesce(try_cast(tpep_dropoff_datetime AS TIMESTAMP),
                     try_cast(lpep_dropoff_datetime AS TIMESTAMP)) AS dropoff_datetime,
            try_cast(passenger_count AS DOUBLE) AS passenger_count,
            try_cast(trip_distance AS DOUBLE) AS trip_distance,
            try_cast(PULocationID AS INTEGER) AS pickup_zone_id,
            try_cast(DOLocationID AS INTEGER) AS dropoff_zone_id,
            try_cast(payment_type AS INTEGER) AS payment_type,
            try_cast(fare_amount AS DOUBLE) AS fare_amount,
            try_cast(tip_amount AS DOUBLE) AS tip_amount,
            try_cast(total_amount AS DOUBLE) AS total_amount
        FROM read_parquet({source}, union_by_name=true, filename=true)
        """
    )


def connect_with_view(years: tuple[int, ...] | None = None,
                      database: Path | None = None):
    """Crea una conexión y una vista sobre Parquet sin importarlos a una tabla."""
    import duckdb

    connection = duckdb.connect(str(database) if database else ":memory:")
    connection.execute("SET threads TO 4")
    replace_view(connection, years)
    return connection
