# Checklist de verificación y cierre de entrega

Procedimiento para comprobar que una instalación nueva reproduce el laboratorio usando solo el `README.md`. Los comandos asumen PowerShell en la raíz del repositorio. Marque cada casilla solo después de ejecutar el paso; este documento no registra resultados.

## A. Auditoría técnica y reproducibilidad

### 1. Sincronizar el repositorio

```powershell
git checkout main
git pull origin main
git status
```

- [ ] Árbol de trabajo limpio antes de comenzar.

### 2. Probar el ambiente Docker

```powershell
docker compose up -d --build
docker compose ps
docker compose logs --tail 50
```

- [ ] JupyterLab responde en <http://127.0.0.1:8888/lab>.
- [ ] Metabase responde en <http://127.0.0.1:3000>.
- [ ] Contenedores `lab8-lab` y `lab8-metabase` activos.
- [ ] Driver de DuckDB disponible en Metabase.
- [ ] Sin errores relevantes en los logs.

### 3. Validar la descarga incremental

```powershell
docker exec lab8-lab python scripts/download_data.py --years 2024 2025 2026
docker exec lab8-lab python scripts/verify_data.py --online
```

Resultado esperado según el corte del 1 de octubre de 2026:

- [ ] 64 archivos Parquet válidos y 121,184,384 registros.
- [ ] Cero archivos históricos faltantes y cero publicados faltantes.
- [ ] Los archivos existentes no se descargan de nuevo (ejecutar el comando una segunda vez).
- [ ] Los meses no publicados de 2026 se informan sin tratarse como fallos.

Si la TLC publicó nuevos meses, se descargan y se repite **todo** el análisis; hay que actualizar resultados, texto, figuras y cobertura en `README.md`, `docs/metodologia.md`, `docs/consultas.md` y el notebook.

### 4. Reproducir el análisis

```powershell
docker exec lab8-lab python scripts/run_analysis.py
docker exec lab8-lab python scripts/build_dashboard.py
```

- [ ] Las 12 consultas SQL terminan correctamente.
- [ ] Se regeneran los CSV en `data/processed/results/`.
- [ ] Se producen siete figuras SVG en `docs/figures/` y se actualiza `docs/tablero.html`.
- [ ] Las comparaciones entre años usan la misma ventana (enero–agosto).
- [ ] Los resultados coinciden con lo explicado en `docs/consultas.md`.

### 5. Reproducir el benchmark

```powershell
docker exec lab8-lab python scripts/benchmark.py --repetitions 4
```

- [ ] Se construye la tabla materializada.
- [ ] El programa confirma equivalencia de resultados entre Parquet y DuckDB.
- [ ] Tres volúmenes de datos y cuatro repeticiones con orden alternado.
- [ ] Se actualizan `docs/benchmark_resultados.csv` y `docs/benchmark_detalle.csv`.
- [ ] Si los tiempos cambian de forma considerable, se actualiza la tabla de `docs/metodologia.md` §4 y la lectura en el notebook.

### 6. Ejecutar el notebook completo

```powershell
docker exec lab8-lab jupyter nbconvert --to notebook --execute --inplace notebooks/lab8_analisis.ipynb --ExecutePreprocessor.timeout=600
```

- [ ] Todas las celdas de código tienen número de ejecución.
- [ ] No hay salidas `Error`.
- [ ] Tablas y visualizaciones visibles.
- [ ] Los resultados narrados coinciden con las salidas.
- [ ] Sin rutas absolutas personales.

### 7. Regenerar Metabase

```powershell
docker exec -e LAB8_METABASE_URL=http://metabase:3000 lab8-lab python scripts/setup_metabase.py
docker exec -e LAB8_METABASE_URL=http://metabase:3000 lab8-lab python scripts/create_metabase_dashboard.py
```

- [ ] Existen siete tarjetas y el tablero las reúne.
- [ ] Las consultas terminan sin error.
- [ ] Los colores distinguen Yellow y Green Taxi.
- [ ] `docs/evidencia_metabase.png` representa la versión actual (reemplazarla si cambiaron resultados o diseño).

### 8. Seguridad y exclusiones de Git

```powershell
git status --short
git ls-files data
git grep -n -I -E "password|token|github_pat"
```

- [ ] En `data/` solo aparecen los `.gitkeep`.
- [ ] No se versionan Parquet, `taxis.duckdb`, CSV generados, archivos `.part`, credenciales de Metabase, sesiones de Playwright, tokens, contraseñas ni cachés de Python o Jupyter.
- [ ] Las coincidencias de `git grep` son solo código legítimo (por ejemplo, `setup_metabase.py` genera la contraseña local; el `Dockerfile` desactiva el token de Jupyter local).

## B. Auditoría contra el enunciado y cierre

### 9. Coherencia narrativa

- [ ] Número de archivos y filas idéntico en README, notebook y documentación.
- [ ] Fechas disponibles de 2026 consistentes.
- [ ] 2026 parcial no se compara contra años completos sin aclaración.
- [ ] Los tres hallazgos están respaldados por resultados y no hacen afirmaciones causales.
- [ ] Importes identificados como USD nominales; los códigos de pago ambiguos no se interpretan como conducta.
- [ ] Tiempos del benchmark en `docs/metodologia.md` iguales a los CSV vigentes.
- [ ] Nombres y carnés correctos (README y notebook).

### 10. Calidad de presentación

```powershell
rg -n "TODO|FIXME|pendiente|C:\\Users|contraseña|password|token" .
git diff --check
```

- [ ] README legible, con comandos copiables y enlaces internos funcionales.
- [ ] Gráficas con títulos, unidades, leyendas y colores coherentes.
- [ ] Tablero sin tarjetas vacías ni errores.
- [ ] Sin textos pendientes ni referencias temporales.

### 11. Materiales exigidos

- [ ] Código fuente modificado, script de descarga y verificador de integridad.
- [ ] Consultas SQL y su documentación.
- [ ] Notebook ejecutado.
- [ ] Scripts y resultados del benchmark.
- [ ] Código de indicadores y tablero (o evidencia del tablero).
- [ ] README reproducible.
- [ ] Sin datasets ni base materializada en Git.

La trazabilidad ejercicio por ejercicio está en [auditoria_rubrica.md](auditoria_rubrica.md).

### 12. Commit y verificación final

```powershell
git add .
git commit -m "docs: cerrar auditoria final y entrega del laboratorio 8"
git push origin main
git status -sb
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

- [ ] El hash local y el remoto coinciden y `main` está limpio y sincronizado.

### 13. Preparar la entrega

Entrega principal: el enlace del fork, <https://github.com/DanielBarillasM/duckdb_Lab-8_Grupo-1_Sec-10>. Abrirlo en una ventana privada y comprobar:

- [ ] Repositorio accesible para el docente.
- [ ] `main` muestra el último commit.
- [ ] El README carga correctamente.
- [ ] La libreta se abre desde GitHub.
- [ ] La imagen del tablero es visible.
- [ ] No aparecen archivos de datos ni secretos.
