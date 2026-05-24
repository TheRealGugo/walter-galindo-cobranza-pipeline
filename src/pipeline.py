"""
pipeline.py
-----------
Pipeline ETL de consolidación de gestiones diarias de cobranza.

Flujo:
    1. EXTRACT  -> Lee todos los Excel de data/input/
    2. TRANSFORM -> Limpia, valida y normaliza
    3. LOAD     -> Genera consolidado + KPIs + reporte ejecutivo
    4. LOG      -> Registra ejecución en bitácora

Ejecuta:
    python src/pipeline.py

Autor: Walter Galindo Parra
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuración de paths y logging
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
INPUT_DIR = RAIZ / "data" / "input"
OUTPUT_DIR = RAIZ / "data" / "output"
LOG_DIR = RAIZ / "data" / "output" / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------
def leer_archivos_excel(carpeta: Path) -> pd.DataFrame:
    """Lee todos los .xlsx de la carpeta y los concatena en un solo DataFrame."""
    archivos = sorted(carpeta.glob("*.xlsx"))
    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron archivos .xlsx en {carpeta}. "
            "Ejecuta primero: python src/generar_datos.py"
        )

    log.info("Iniciando lectura de %d archivos desde %s", len(archivos), carpeta)
    dfs = []
    for archivo in archivos:
        df = pd.read_excel(archivo, sheet_name="Gestiones")
        df["_archivo_origen"] = archivo.name
        dfs.append(df)
        log.debug("  Leído: %s (%d filas)", archivo.name, len(df))

    consolidado = pd.concat(dfs, ignore_index=True)
    log.info("Lectura completa: %d filas en total", len(consolidado))
    return consolidado


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------
def normalizar_dni(dni: str) -> str:
    """Quita espacios, guiones y rellena con ceros a 8 dígitos."""
    if pd.isna(dni):
        return ""
    solo_digitos = re.sub(r"\D", "", str(dni))
    return solo_digitos.zfill(8) if solo_digitos else ""


def normalizar_telefono(tel: str) -> str:
    """Deja sólo los 9 dígitos del móvil peruano, sin prefijo país."""
    if pd.isna(tel):
        return ""
    solo_digitos = re.sub(r"\D", "", str(tel))
    # Si vino con prefijo país +51, se lo quitamos
    if solo_digitos.startswith("51") and len(solo_digitos) == 11:
        solo_digitos = solo_digitos[2:]
    return solo_digitos


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las reglas de limpieza y normalización."""
    log.info("Iniciando limpieza de datos")
    n_inicial = len(df)

    # Normalización de identificadores
    df["dni"] = df["dni"].apply(normalizar_dni)
    df["telefono"] = df["telefono"].apply(normalizar_telefono)

    # Tipos correctos
    df["fecha_gestion"] = pd.to_datetime(df["fecha_gestion"], errors="coerce")
    df["fecha_promesa"] = pd.to_datetime(df["fecha_promesa"], errors="coerce")

    # Quitar registros inválidos (DNI vacío o fecha mal)
    invalidos = df["dni"].eq("") | df["fecha_gestion"].isna()
    if invalidos.any():
        log.warning("Removiendo %d filas inválidas", invalidos.sum())
        df = df[~invalidos].copy()

    # Deduplicar por DNI + fecha + asesor (gestión duplicada accidental)
    antes = len(df)
    df = df.drop_duplicates(subset=["dni", "fecha_gestion", "asesor"])
    log.info("Deduplicados: %d filas removidas", antes - len(df))

    # Columnas derivadas útiles para análisis
    df["semana"] = df["fecha_gestion"].dt.isocalendar().week
    df["dia_semana"] = df["fecha_gestion"].dt.day_name()
    df["es_contacto_efectivo"] = df["tipificacion"].str.startswith("CONTACTO EFECTIVO")
    df["es_promesa"] = df["tipificacion"].eq("CONTACTO EFECTIVO - PROMESA DE PAGO")
    df["es_pago"] = df["tipificacion"].eq("CONTACTO EFECTIVO - YA PAGÓ")

    log.info("Limpieza completa: %d -> %d filas (%.1f%% retenido)",
             n_inicial, len(df), 100 * len(df) / n_inicial)
    return df


# ---------------------------------------------------------------------------
# KPIs DE NEGOCIO
# ---------------------------------------------------------------------------
def calcular_kpis_globales(df: pd.DataFrame) -> dict:
    """KPIs agregados del periodo completo."""
    total = len(df)
    contactos = df["es_contacto_efectivo"].sum()
    promesas = df["es_promesa"].sum()
    pagos = df["es_pago"].sum()

    kpis = {
        "total_gestiones": total,
        "total_contactos_efectivos": int(contactos),
        "total_promesas": int(promesas),
        "total_pagos_confirmados": int(pagos),
        "tasa_contactabilidad_pct": round(100 * contactos / total, 2) if total else 0,
        "tasa_promesa_pct": round(100 * promesas / contactos, 2) if contactos else 0,
        "tasa_pago_pct": round(100 * pagos / total, 2) if total else 0,
        "monto_total_gestionado": round(df["monto_deuda"].sum(), 2),
        "monto_total_prometido": round(df["monto_prometido"].sum(), 2),
        "monto_total_recuperado": round(df["monto_pagado"].sum(), 2),
        "duracion_promedio_llamada_seg": round(df["duracion_llamada_seg"].mean(), 1),
    }
    return kpis


def kpis_por_asesor(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de desempeño por asesor."""
    grp = df.groupby("asesor").agg(
        gestiones=("dni", "count"),
        contactos=("es_contacto_efectivo", "sum"),
        promesas=("es_promesa", "sum"),
        monto_prometido=("monto_prometido", "sum"),
        monto_recuperado=("monto_pagado", "sum"),
        duracion_promedio=("duracion_llamada_seg", "mean"),
    ).reset_index()

    grp["tasa_contactabilidad_%"] = (100 * grp["contactos"] / grp["gestiones"]).round(2)
    grp["tasa_promesa_%"] = (100 * grp["promesas"] / grp["contactos"].replace(0, 1)).round(2)
    grp = grp.sort_values("monto_recuperado", ascending=False)
    return grp


def kpis_por_producto(df: pd.DataFrame) -> pd.DataFrame:
    """Análisis por línea de producto."""
    return df.groupby("producto").agg(
        gestiones=("dni", "count"),
        monto_deuda_total=("monto_deuda", "sum"),
        monto_recuperado=("monto_pagado", "sum"),
        tasa_recuperacion_pct=("monto_pagado", lambda s: round(100 * s.sum() / df.loc[s.index, "monto_deuda"].sum(), 2)),
    ).reset_index().sort_values("monto_recuperado", ascending=False)


# ---------------------------------------------------------------------------
# LOAD: escritura del reporte Excel con formato
# ---------------------------------------------------------------------------
def exportar_reporte(
    consolidado: pd.DataFrame,
    kpis_globales: dict,
    df_asesores: pd.DataFrame,
    df_productos: pd.DataFrame,
    destino: Path,
) -> Path:
    """Escribe un Excel multi-hoja con formato condicional."""
    ruta = destino / f"reporte_cobranza_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
        # Hoja 1: Resumen ejecutivo
        df_resumen = pd.DataFrame(
            list(kpis_globales.items()), columns=["KPI", "Valor"]
        )
        df_resumen.to_excel(writer, sheet_name="Resumen Ejecutivo", index=False)

        # Hoja 2: Ranking de asesores
        df_asesores.to_excel(writer, sheet_name="Asesores", index=False)

        # Hoja 3: Análisis por producto
        df_productos.to_excel(writer, sheet_name="Productos", index=False)

        # Hoja 4: Dataset consolidado completo
        consolidado.to_excel(writer, sheet_name="Consolidado", index=False)

    log.info("Reporte exportado: %s", ruta.name)
    return ruta


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("=" * 60)
    log.info("PIPELINE DE CONSOLIDACIÓN DE GESTIONES DE COBRANZA")
    log.info("=" * 60)

    # 1. Extract
    df_crudo = leer_archivos_excel(INPUT_DIR)

    # 2. Transform
    df_limpio = limpiar_datos(df_crudo)

    # 3. Calcular KPIs
    kpis = calcular_kpis_globales(df_limpio)
    rk_asesores = kpis_por_asesor(df_limpio)
    rk_productos = kpis_por_producto(df_limpio)

    log.info("KPIs globales calculados:")
    for k, v in kpis.items():
        log.info("  %-35s %s", k, v)

    # 4. Load
    ruta = exportar_reporte(df_limpio, kpis, rk_asesores, rk_productos, OUTPUT_DIR)
    log.info("Pipeline finalizado correctamente -> %s", ruta)


if __name__ == "__main__":
    main()
