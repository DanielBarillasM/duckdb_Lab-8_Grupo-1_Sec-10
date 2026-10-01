"""Compara consultas equivalentes sobre Parquet y tabla DuckDB materializada."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import time

from lab8_common import PROCESSED, ROOT, connect_with_view, parquet_files, replace_view

DB_PATH = PROCESSED / "taxis.duckdb"

QUERIES = {
    "conteo_tipo": """
        SELECT file_year, taxi_type, count(*) AS viajes
        FROM {source} WHERE file_year IN ({years})
        GROUP BY 1, 2 ORDER BY 1, 2
    """,
    "importe_mensual": """
        SELECT file_year, file_month, taxi_type,
               count(*) AS viajes,
               round(avg(total_amount) FILTER (WHERE total_amount >= 0), 2) AS media_usd
        FROM {source}
        WHERE file_year IN ({years}) AND year(pickup_datetime) = file_year
        GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
    """,
    "pagos": """
        SELECT file_year, taxi_type, payment_type, count(*) AS viajes
        FROM {source}
        WHERE file_year IN ({years}) AND year(pickup_datetime) = file_year
        GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
    """,
}


def equivalent(left: list[tuple], right: list[tuple]) -> bool:
    if len(left) != len(right):
        return False
    for row_a, row_b in zip(left, right):
        if len(row_a) != len(row_b):
            return False
        for a, b in zip(row_a, row_b):
            if isinstance(a, (float, int)) and isinstance(b, (float, int)):
                if not math.isclose(float(a), float(b), rel_tol=1e-5, abs_tol=0.01):
                    return False
            elif a != b:
                return False
    return True


def benchmark(repetitions: int = 4, reuse_table: bool = False) -> list[dict]:
    years = (2024, 2025, 2026)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    con = connect_with_view(years, DB_PATH)
    table_exists = bool(con.execute("""SELECT count(*) FROM information_schema.tables
                                       WHERE table_name = 'trips_materialized'""").fetchone()[0])
    if reuse_table and table_exists:
        build_seconds = None
        print("Reutilizando tabla materializada ya verificada.", flush=True)
    else:
        print("Materializando tabla analítica en DuckDB...", flush=True)
        start = time.perf_counter()
        # Proyección analítica: columnas exactas que usan las consultas equivalentes.
        # Evita duplicar en disco las columnas irrelevantes de 121 M de viajes.
        con.execute("""CREATE OR REPLACE TABLE trips_materialized AS
                       SELECT taxi_type, file_year, file_month, pickup_datetime,
                              total_amount, payment_type FROM trips""")
        build_seconds = time.perf_counter() - start
        print(f"Tabla lista en {build_seconds:.1f} s; {DB_PATH.stat().st_size / 1e9:.2f} GB", flush=True)

    scenarios = {
        "2026": (2026,),
        "2024+2026": (2024, 2026),
        "2024+2025+2026": years,
    }
    rows = []
    detail = []
    for scenario, included in scenarios.items():
        replace_view(con, included)
        year_sql = ", ".join(map(str, included))
        nfiles = len(parquet_files(included))
        for query_name, template in QUERIES.items():
            direct = template.format(source="trips", years=year_sql)
            table = template.format(source="trips_materialized", years=year_sql)
            # Ejecutar ambas fuentes antes del cronómetro comprueba equivalencia
            # y evita incluir compilación inicial en las mediciones.
            expected = con.execute(direct).fetchall()
            actual = con.execute(table).fetchall()
            if not equivalent(expected, actual):
                raise AssertionError(f"Resultados no equivalentes: {scenario}/{query_name}")
            samples_by_source = {"Parquet": [], "DuckDB": []}
            for repeat in range(1, repetitions + 1):
                # Alternar el orden reduce la ventaja sistemática de caché.
                pair = (("Parquet", direct), ("DuckDB", table))
                if repeat % 2 == 0:
                    pair = tuple(reversed(pair))
                for order, (source_name, query) in enumerate(pair, start=1):
                    start = time.perf_counter()
                    con.execute(query).fetchall()
                    elapsed = time.perf_counter() - start
                    samples_by_source[source_name].append(elapsed)
                    detail.append({"escenario": scenario, "archivos": nfiles,
                                   "consulta": query_name, "fuente": source_name,
                                   "repeticion": repeat, "orden": order,
                                   "segundos": round(elapsed, 4)})
            for source_name, samples in samples_by_source.items():
                rows.append({"escenario": scenario, "archivos": nfiles,
                             "consulta": query_name, "fuente": source_name,
                             "repeticiones": repetitions,
                             "mediana_segundos": round(statistics.median(samples), 4),
                             "min_segundos": round(min(samples), 4),
                             "max_segundos": round(max(samples), 4),
                             "filas_resultado": len(expected),
                             "materializacion_segundos":
                                 round(build_seconds, 2) if build_seconds is not None else "reutilizada"})
                print(f"{scenario} / {query_name} / {source_name}: "
                      f"{statistics.median(samples):.3f} s", flush=True)
    for name, data in (("benchmark_resultados.csv", rows),
                       ("benchmark_detalle.csv", detail)):
        path = ROOT / "docs" / name
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    con.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=4)
    parser.add_argument("--reuse-table", action="store_true",
                        help="reutiliza la tabla existente; apropiado solo si los Parquet no cambiaron")
    args = parser.parse_args()
    if args.repetitions < 2 or args.repetitions % 2:
        parser.error("use un número par de al menos dos repeticiones para balancear el orden")
    benchmark(args.repetitions, reuse_table=args.reuse_table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
