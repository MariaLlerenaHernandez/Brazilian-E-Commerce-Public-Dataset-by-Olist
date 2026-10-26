"""
run_pipeline.py
Ejecuta el ETL completo en orden: perfilado -> limpieza -> carga a PostgreSQL.

Uso:  python etl/run_pipeline.py
"""
import runpy
import sys
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ETL_DIR))

for paso in ["01_perfilado.py", "02_limpieza.py", "03_carga.py"]:
    print(f"\n===== {paso} =====")
    runpy.run_path(str(ETL_DIR / paso), run_name="__main__")
