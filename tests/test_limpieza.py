"""
test_limpieza.py
----------------
Tests unitarios de las funciones de normalización.

Ejecuta:
    pytest tests/ -v

Autor: Walter Galindo Parra
"""

import sys
from pathlib import Path

# Permite importar desde src/ sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pytest
from pipeline import (
    calcular_kpis_globales,
    limpiar_datos,
    normalizar_dni,
    normalizar_telefono,
)


# ---------------------------------------------------------------------------
# normalizar_dni
# ---------------------------------------------------------------------------
class TestNormalizarDNI:
    def test_dni_limpio_se_mantiene(self):
        assert normalizar_dni("12345678") == "12345678"

    def test_quita_espacios_y_guiones(self):
        assert normalizar_dni("  1234-5678 ") == "12345678"

    def test_rellena_con_ceros_a_la_izquierda(self):
        assert normalizar_dni("123456") == "00123456"

    def test_dni_vacio_devuelve_string_vacio(self):
        assert normalizar_dni("") == ""

    def test_dni_nan_devuelve_string_vacio(self):
        import numpy as np
        assert normalizar_dni(np.nan) == ""


# ---------------------------------------------------------------------------
# normalizar_telefono
# ---------------------------------------------------------------------------
class TestNormalizarTelefono:
    def test_telefono_limpio_se_mantiene(self):
        assert normalizar_telefono("987654321") == "987654321"

    def test_quita_prefijo_pais(self):
        assert normalizar_telefono("+51 987 654 321") == "987654321"

    def test_quita_caracteres_no_numericos(self):
        assert normalizar_telefono("987-654-321") == "987654321"


# ---------------------------------------------------------------------------
# limpiar_datos (integración mínima)
# ---------------------------------------------------------------------------
class TestLimpiarDatos:
    def _df_minimo(self) -> pd.DataFrame:
        return pd.DataFrame({
            "fecha_gestion": ["2026-04-01", "2026-04-01", "2026-04-02"],
            "asesor": ["A001", "A001", "A002"],
            "dni": ["12345678", "12345678", "  8765-4321 "],  # 1er duplicado
            "telefono": ["987654321", "987654321", "+51 912 345 678"],
            "producto": ["TC"] * 3,
            "tramo_mora": ["1-30"] * 3,
            "monto_deuda": [1000, 1000, 500],
            "tipificacion": [
                "CONTACTO EFECTIVO - PROMESA DE PAGO",
                "CONTACTO EFECTIVO - PROMESA DE PAGO",
                "NO CONTESTA",
            ],
            "monto_prometido": [800, 800, 0],
            "fecha_promesa": ["2026-04-10", "2026-04-10", ""],
            "monto_pagado": [0, 0, 0],
            "duracion_llamada_seg": [120, 120, 30],
        })

    def test_elimina_duplicados(self):
        df_in = self._df_minimo()
        df_out = limpiar_datos(df_in)
        # 3 filas con 1 duplicada -> debe quedar 2
        assert len(df_out) == 2

    def test_normaliza_dni_y_telefono(self):
        df_in = self._df_minimo()
        df_out = limpiar_datos(df_in)
        assert "87654321" in df_out["dni"].values
        assert "912345678" in df_out["telefono"].values

    def test_agrega_columnas_derivadas(self):
        df_in = self._df_minimo()
        df_out = limpiar_datos(df_in)
        assert "es_contacto_efectivo" in df_out.columns
        assert "es_promesa" in df_out.columns


# ---------------------------------------------------------------------------
# calcular_kpis_globales
# ---------------------------------------------------------------------------
class TestKPIs:
    def test_estructura_kpis(self):
        df = pd.DataFrame({
            "dni": ["1"] * 10,
            "es_contacto_efectivo": [True] * 4 + [False] * 6,
            "es_promesa": [True] * 2 + [False] * 8,
            "es_pago": [True] * 1 + [False] * 9,
            "monto_deuda": [1000] * 10,
            "monto_prometido": [500] * 2 + [0] * 8,
            "monto_pagado": [1000] + [0] * 9,
            "duracion_llamada_seg": [60] * 10,
        })
        kpis = calcular_kpis_globales(df)

        assert kpis["total_gestiones"] == 10
        assert kpis["total_contactos_efectivos"] == 4
        assert kpis["tasa_contactabilidad_pct"] == 40.0
        assert kpis["tasa_promesa_pct"] == 50.0  # 2 promesas / 4 contactos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
