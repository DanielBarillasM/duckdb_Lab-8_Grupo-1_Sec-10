"""Ejecuta el catálogo SQL directamente sobre Parquet y guarda resultados CSV."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone

import duckdb

from lab8_common import RESULTS, ROOT, connect_with_view, parquet_files


def git_revision() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None  # La imagen de análisis no instala Git ni monta .git.
    return result.stdout.strip() if result.returncode == 0 else None


def run(years: tuple[int, ...]) -> dict:
    connection = connect_with_view(years)
    RESULTS.mkdir(parents=True, exist_ok=True)
    schema = connection.execute("DESCRIBE SELECT * FROM trips").df()
    schema.to_csv(RESULTS / "00_esquema_normalizado.csv", index=False)
    output = {}
    for path in sorted((ROOT / "sql").glob("[0-9][0-9]_*.sql")):
        query = path.read_text(encoding="utf-8")
        frame = connection.execute(query).df()
        frame.to_csv(RESULTS / f"{path.stem}.csv", index=False)
        output[path.stem] = {"filas_resultado": len(frame), "columnas": list(frame.columns)}
        print(f"{path.name}: {len(frame)} filas", flush=True)
    manifest = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "revision_git": git_revision(),
        "duckdb": duckdb.__version__,
        "anios": list(years),
        "archivos": len(parquet_files(years)),
        "resultados": output,
        "filtros": "año de recogida igual al año del archivo; otros filtros documentados por consulta",
    }
    (RESULTS / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    connection.close()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", type=int, choices=(2024, 2025, 2026),
                        default=[2024, 2025, 2026])
    args = parser.parse_args()
    run(tuple(dict.fromkeys(args.years)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
