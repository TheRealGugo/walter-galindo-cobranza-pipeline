"""
generar_datos.py
----------------
Genera archivos Excel simulados de gestiones de cobranza telefónica
para alimentar el pipeline de automatización.

Cada archivo representa la gestión diaria de un asesor de cobranza.
Se simulan 30 archivos (1 mes operativo) con datos realistas de
contactabilidad, promesas de pago y recuperación efectiva.

Autor: Walter Galindo Parra
Contexto: Portafolio para Analista Jr. de Automatización de Procesos
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Semilla fija para reproducibilidad: cualquiera que ejecute obtiene
# exactamente los mismos datos. Importante para demos y entrevistas.
random.seed(42)

# ---------------------------------------------------------------------------
# Configuración del dataset sintético
# ---------------------------------------------------------------------------
ASESORES = [
    "A001 - Ana Quispe",
    "A002 - Carlos Mendoza",
    "A003 - Lucía Ramos",
    "A004 - Jorge Vargas",
    "A005 - María Salas",
]

TIPIFICACIONES = [
    "CONTACTO EFECTIVO - PROMESA DE PAGO",
    "CONTACTO EFECTIVO - SE NIEGA A PAGAR",
    "CONTACTO EFECTIVO - YA PAGÓ",
    "NO CONTESTA",
    "NÚMERO ERRADO",
    "BUZÓN DE VOZ",
    "TERCERO INFORMADO",
    "FUERA DE SERVICIO",
]

# Distribución realista de outcomes en una cartera de cobranza promedio
PESOS_TIPIFICACION = [0.22, 0.08, 0.05, 0.30, 0.10, 0.15, 0.07, 0.03]

PRODUCTOS = ["Tarjeta de Crédito", "Préstamo Personal", "Préstamo Vehicular"]

# Tramos de mora habituales en cobranza B2C peruana
TRAMOS_MORA = ["1-30 días", "31-60 días", "61-90 días", "91-180 días", "180+ días"]


def _generar_dni() -> str:
    """DNI peruano de 8 dígitos."""
    return str(random.randint(10_000_000, 99_999_999))


def _generar_telefono() -> str:
    """Móvil peruano. Formato 9XXXXXXXX."""
    return "9" + "".join(str(random.randint(0, 9)) for _ in range(8))


def _generar_registro(fecha: datetime, asesor: str) -> dict:
    """Genera una fila de gestión de cobranza."""
    tipificacion = random.choices(TIPIFICACIONES, weights=PESOS_TIPIFICACION, k=1)[0]

    monto_deuda = round(random.uniform(150, 18_500), 2)

    # Sólo hay monto prometido si la tipificación es promesa de pago
    if tipificacion == "CONTACTO EFECTIVO - PROMESA DE PAGO":
        monto_prometido = round(monto_deuda * random.uniform(0.3, 1.0), 2)
        fecha_promesa = fecha + timedelta(days=random.randint(1, 15))
    else:
        monto_prometido = 0.0
        fecha_promesa = None

    # Sólo hay pago confirmado si ya pagó (~5% de las gestiones)
    monto_pagado = monto_deuda if tipificacion == "CONTACTO EFECTIVO - YA PAGÓ" else 0.0

    return {
        "fecha_gestion": fecha.strftime("%Y-%m-%d"),
        "asesor": asesor,
        "dni": _generar_dni(),
        "telefono": _generar_telefono(),
        "producto": random.choice(PRODUCTOS),
        "tramo_mora": random.choice(TRAMOS_MORA),
        "monto_deuda": monto_deuda,
        "tipificacion": tipificacion,
        "monto_prometido": monto_prometido,
        "fecha_promesa": fecha_promesa.strftime("%Y-%m-%d") if fecha_promesa else "",
        "monto_pagado": monto_pagado,
        "duracion_llamada_seg": random.randint(15, 480),
    }


def _inyectar_problemas_de_calidad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Inyecta intencionalmente problemas típicos de datos sucios
    para que el pipeline de limpieza tenga sentido.
    """
    n = len(df)

    # 3% de duplicados exactos (mismo DNI mismo día -> error humano)
    n_dup = max(1, int(n * 0.03))
    duplicados = df.sample(n=n_dup, random_state=1).copy()
    df = pd.concat([df, duplicados], ignore_index=True)

    # 2% de DNIs con formato sucio (espacios, guiones)
    indices_sucios = df.sample(frac=0.02, random_state=2).index
    df.loc[indices_sucios, "dni"] = df.loc[indices_sucios, "dni"].apply(
        lambda x: f"  {x[:4]}-{x[4:]} "
    )

    # 1% de teléfonos en formato distinto (+51, espacios)
    indices_tel = df.sample(frac=0.01, random_state=3).index
    df.loc[indices_tel, "telefono"] = df.loc[indices_tel, "telefono"].apply(
        lambda x: f"+51 {x[:3]} {x[3:6]} {x[6:]}"
    )

    return df


def generar_archivos(carpeta_destino: Path, n_dias: int = 30) -> None:
    """Genera n_dias archivos Excel, uno por día operativo."""
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    fecha_inicio = datetime(2026, 4, 1)

    for i in range(n_dias):
        fecha = fecha_inicio + timedelta(days=i)
        registros = []

        for asesor in ASESORES:
            # Cada asesor gestiona entre 40 y 80 cuentas por día
            n_gestiones = random.randint(40, 80)
            for _ in range(n_gestiones):
                registros.append(_generar_registro(fecha, asesor))

        df = pd.DataFrame(registros)
        df = _inyectar_problemas_de_calidad(df)

        nombre = f"gestiones_{fecha.strftime('%Y%m%d')}.xlsx"
        ruta = carpeta_destino / nombre
        df.to_excel(ruta, index=False, sheet_name="Gestiones")
        print(f"  Generado: {nombre} ({len(df)} filas)")


if __name__ == "__main__":
    destino = Path(__file__).resolve().parents[1] / "data" / "input"
    print(f"Generando archivos simulados en: {destino}")
    generar_archivos(destino, n_dias=30)
    print("Listo. Ejecuta ahora: python src/pipeline.py")
