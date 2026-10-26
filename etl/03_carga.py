"""
03_carga.py
Paso 3 del ETL: carga a PostgreSQL y construcción del Data Mart.

  1. Ejecuta sql/01_staging.sql (crea el esquema staging).
  2. Carga cada CSV limpio de data/clean/ con COPY (rápido y transaccional).
  3. Registra la bitácora de limpieza en staging.etl_log.
  4. Ejecuta los scripts del modelo dimensional en orden:
     02_dw_tablas -> 03_dimensiones -> 04_fact_ventas -> 07_restricciones -> 06_funciones
  5. Ejecuta sql/05_validaciones.sql y guarda el resultado en reports/validaciones.md

Todo se ejecuta en UNA transacción: si un paso falla, la base queda como estaba.

Uso:  python etl/03_carga.py
"""
import csv
import time

import psycopg2

from config import CLEAN_DIR, DB, REPORTS_DIR, SQL_DIR

# Tabla de staging -> archivo limpio (mismo orden de columnas que el CSV)
TABLAS_STAGING = [
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "customers",
    "sellers",
    "products",
    "category_translation",
]

SCRIPTS_DW = [
    "02_dw_tablas.sql",
    "03_dimensiones.sql",
    "04_fact_ventas.sql",
    "07_restricciones.sql",
    "06_funciones.sql",
]


def ejecutar_script(cur, nombre: str) -> None:
    t0 = time.time()
    cur.execute((SQL_DIR / nombre).read_text(encoding="utf-8"))
    print(f"  {nombre:<22} OK ({time.time() - t0:.1f} s)")


def copiar_csv(cur, tabla: str) -> int:
    ruta = CLEAN_DIR / f"{tabla}.csv"
    with open(ruta, encoding="utf-8") as f:
        columnas = next(csv.reader(f))
        f.seek(0)
        cur.copy_expert(
            f"COPY staging.{tabla} ({', '.join(columnas)}) FROM STDIN WITH (FORMAT csv, HEADER true)",
            f,
        )
    cur.execute(f"SELECT count(*) FROM staging.{tabla}")
    return cur.fetchone()[0]


def cargar_bitacora(cur) -> None:
    with open(REPORTS_DIR / "bitacora_limpieza.csv", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            cur.execute(
                "INSERT INTO staging.etl_log (tabla, filas_origen, filas_limpias, filas_descartadas, acciones)"
                " VALUES (%s, %s, %s, %s, %s)",
                (fila["tabla"], fila["filas_origen"], fila["filas_limpias"], fila["filas_descartadas"], fila["acciones"]),
            )


def tabla_markdown(columnas: list[str], filas: list[tuple]) -> str:
    def fmt(v):
        return "" if v is None else str(v)

    lineas = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    lineas += ["| " + " | ".join(fmt(v) for v in fila) + " |" for fila in filas]
    return "\n".join(lineas)


def ejecutar_validaciones(cur) -> None:
    """Ejecuta cada consulta de 05_validaciones.sql y guarda los resultados."""
    texto = (SQL_DIR / "05_validaciones.sql").read_text(encoding="utf-8")
    # Se quitan los comentarios antes de separar por ';' (un comentario puede contener ';')
    sin_comentarios = "\n".join(l for l in texto.splitlines() if not l.strip().startswith("--"))
    salida = ["# Resultados de las consultas de validación", ""]
    for bloque in sin_comentarios.split(";"):
        sentencia = bloque.strip()
        if not sentencia:
            continue
        cur.execute(sentencia)
        columnas = [d[0] for d in cur.description]
        filas = cur.fetchall()
        titulo = filas[0][0] if filas else sentencia.split("'")[1]
        salida += [f"## {titulo}", "", tabla_markdown(columnas[1:], [f[1:] for f in filas]), ""]
    (REPORTS_DIR / "validaciones.md").write_text("\n".join(salida), encoding="utf-8")
    print(f"  Resultados de validación en {REPORTS_DIR / 'validaciones.md'}")


def main() -> None:
    print(f"Conectando a PostgreSQL {DB['host']}:{DB['port']}/{DB['dbname']} como {DB['user']}")
    conn = psycopg2.connect(**DB)
    try:
        with conn:  # una sola transacción: commit al final o rollback si algo falla
            with conn.cursor() as cur:
                print("1) Staging")
                ejecutar_script(cur, "01_staging.sql")
                for tabla in TABLAS_STAGING:
                    n = copiar_csv(cur, tabla)
                    print(f"  COPY staging.{tabla:<20} {n:>9,} filas")
                cargar_bitacora(cur)
                print("2) Modelo dimensional (esquema dw)")
                for script in SCRIPTS_DW:
                    ejecutar_script(cur, script)
                print("3) Validaciones")
                ejecutar_validaciones(cur)
        print("Carga finalizada correctamente.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
