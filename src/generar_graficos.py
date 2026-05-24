"""
generar_graficos.py
-------------------
Genera visualizaciones PNG para el informe ejecutivo.
Lee el último reporte consolidado y produce 4 gráficos clave.

Ejecuta:
    python src/generar_graficos.py

Autor: Walter Galindo Parra
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
OUTPUT_DIR = RAIZ / "data" / "output"
ASSETS_DIR = RAIZ / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Paleta corporativa sobria (evitamos colores brillantes tipo default)
PALETA = ["#1F4E79", "#2E75B6", "#9DC3E6", "#BDD7EE", "#DEEBF7"]
COLOR_ACENTO = "#C00000"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
})


def _ultimo_reporte() -> Path:
    archivos = sorted(OUTPUT_DIR.glob("reporte_cobranza_*.xlsx"))
    if not archivos:
        raise FileNotFoundError("Ejecuta primero: python src/pipeline.py")
    return archivos[-1]


def grafico_tasa_contactabilidad_diaria(df: pd.DataFrame, destino: Path) -> None:
    """Evolución diaria de la tasa de contactabilidad."""
    df["fecha_gestion"] = pd.to_datetime(df["fecha_gestion"])
    serie = df.groupby(df["fecha_gestion"].dt.date).agg(
        gestiones=("dni", "count"),
        contactos=("es_contacto_efectivo", "sum"),
    )
    serie["tasa"] = 100 * serie["contactos"] / serie["gestiones"]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(serie.index, serie["tasa"], marker="o", color=PALETA[0], linewidth=2)
    ax.axhline(serie["tasa"].mean(), color=COLOR_ACENTO, linestyle="--",
               label=f"Promedio: {serie['tasa'].mean():.1f}%")
    ax.set_title("Evolución diaria de la tasa de contactabilidad", fontsize=13, weight="bold")
    ax.set_ylabel("Tasa de contactabilidad (%)")
    ax.set_xlabel("Fecha")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(destino, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Generado: {destino.name}")


def grafico_ranking_asesores(df_asesores: pd.DataFrame, destino: Path) -> None:
    """Barras horizontales de monto recuperado por asesor."""
    df = df_asesores.sort_values("monto_recuperado")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.barh(df["asesor"], df["monto_recuperado"], color=PALETA[1])
    ax.set_title("Monto recuperado por asesor (período completo)",
                 fontsize=13, weight="bold")
    ax.set_xlabel("Monto recuperado (S/)")

    # Etiquetas al final de cada barra
    for i, v in enumerate(df["monto_recuperado"]):
        ax.text(v, i, f"  S/ {v:,.0f}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(destino, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Generado: {destino.name}")


def grafico_distribucion_tipificaciones(df: pd.DataFrame, destino: Path) -> None:
    """Top tipificaciones con porcentaje."""
    serie = df["tipificacion"].value_counts(normalize=True).mul(100).round(1)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(serie.index[::-1], serie.values[::-1], color=PALETA[2])
    ax.set_title("Distribución de tipificaciones", fontsize=13, weight="bold")
    ax.set_xlabel("Porcentaje del total (%)")

    for i, v in enumerate(serie.values[::-1]):
        ax.text(v, i, f"  {v}%", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(destino, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Generado: {destino.name}")


def grafico_recuperacion_por_producto(df_productos: pd.DataFrame, destino: Path) -> None:
    """Comparativa de tasa de recuperación por producto."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(df_productos["producto"], df_productos["tasa_recuperacion_pct"],
                  color=[PALETA[0], PALETA[1], PALETA[2]])
    ax.set_title("Tasa de recuperación por producto", fontsize=13, weight="bold")
    ax.set_ylabel("Tasa de recuperación (%)")

    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h, f"{h:.1f}%",
                ha="center", va="bottom", fontsize=10, weight="bold")

    plt.tight_layout()
    plt.savefig(destino, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Generado: {destino.name}")


def main() -> None:
    ruta = _ultimo_reporte()
    print(f"Leyendo: {ruta.name}")

    df_consol = pd.read_excel(ruta, sheet_name="Consolidado")
    df_asesores = pd.read_excel(ruta, sheet_name="Asesores")
    df_productos = pd.read_excel(ruta, sheet_name="Productos")

    print("Generando gráficos...")
    grafico_tasa_contactabilidad_diaria(df_consol, ASSETS_DIR / "01_contactabilidad_diaria.png")
    grafico_ranking_asesores(df_asesores, ASSETS_DIR / "02_ranking_asesores.png")
    grafico_distribucion_tipificaciones(df_consol, ASSETS_DIR / "03_tipificaciones.png")
    grafico_recuperacion_por_producto(df_productos, ASSETS_DIR / "04_recuperacion_producto.png")

    print(f"\nGráficos guardados en: {ASSETS_DIR}")


if __name__ == "__main__":
    main()
