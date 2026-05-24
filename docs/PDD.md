# Process Design Document (PDD)
## Consolidación de Gestiones de Cobranza Telefónica

| Campo | Detalle |
|---|---|
| **Proceso** | Consolidación mensual de gestiones de cobranza |
| **Autor** | Walter Galindo Parra |
| **Versión** | 1.0 |
| **Fecha** | Mayo 2026 |
| **Estado** | Implementado y validado con UAT |

---

## 1. Objetivo del proceso

Consolidar diariamente los registros de gestión telefónica de los asesores de cobranza, normalizar los datos, calcular KPIs operativos y generar un reporte ejecutivo para el supervisor de operaciones.

## 2. Stakeholders

| Rol | Responsabilidad |
|---|---|
| Supervisor de Cobranza | Owner del proceso. Define KPIs y aprueba el reporte. |
| Asesores de cobranza | Generadores del dato (Excel diario). |
| Analista de procesos (este puesto) | Diseña, implementa y mantiene la automatización. |
| Gerencia comercial | Consumidor final del reporte. |

---

## 3. Proceso AS-IS (estado actual manual)

| # | Actividad | Responsable | Tiempo (min) | Tipo |
|---|---|---|---|---|
| 1 | Asesor guarda su Excel del día en carpeta compartida | Asesor | 5 | VA |
| 2 | Analista descarga 5 archivos × 30 días = 150 archivos | Analista | 30 | NVA |
| 3 | Abre cada archivo y copia los datos a una hoja maestra | Analista | 180 | NVA |
| 4 | Limpia DNIs con espacios/guiones manualmente | Analista | 45 | NVA |
| 5 | Detecta y borra duplicados visualmente | Analista | 30 | NVA |
| 6 | Construye tablas dinámicas para KPIs | Analista | 60 | NVA-N |
| 7 | Crea gráficos y los pega en PowerPoint | Analista | 45 | NVA-N |
| 8 | Envía reporte por correo | Analista | 5 | VA |
| **TOTAL** | | | **~400 min (6.7h)** | |

VA = Valor Agregado · NVA = No Valor Agregado · NVA-N = NVA Necesario

**Pain points identificados:**
1. **Error humano** en consolidación: pérdida de filas por copy-paste mal hecho
2. **Inconsistencia de formato**: cada asesor escribe DNIs distintos
3. **Retrabajo** cuando aparecen duplicados detectados tarde
4. **No trazabilidad**: si el reporte sale mal, nadie sabe en qué paso falló

---

## 4. Proceso TO-BE (con automatización)

| # | Actividad | Responsable | Tiempo (min) | Tipo |
|---|---|---|---|---|
| 1 | Asesor guarda su Excel del día en carpeta compartida | Asesor | 5 | VA |
| 2 | Pipeline lee automáticamente todos los archivos | Bot Python | 0.5 | Auto |
| 3 | Limpia, normaliza y deduplica | Bot Python | 0.5 | Auto |
| 4 | Calcula KPIs y genera reporte Excel multi-hoja | Bot Python | 1 | Auto |
| 5 | Genera 4 gráficos PNG | Bot Python | 1 | Auto |
| 6 | Analista revisa y envía | Analista | 10 | VA |
| **TOTAL** | | | **~18 min** | |

**Ahorro: 95.5% del tiempo operativo. Ahorro mensual: ~6.4 horas → ~75 horas/año.**

---

## 5. Reglas de negocio

| ID | Regla |
|---|---|
| BR-01 | Un DNI peruano válido tiene 8 dígitos numéricos. Se rellena con ceros a la izquierda si tiene menos. |
| BR-02 | Un móvil peruano tiene 9 dígitos. Si trae prefijo `+51` o `51`, se remueve. |
| BR-03 | Una gestión es duplicada si coincide DNI + fecha + asesor. Se conserva la primera ocurrencia. |
| BR-04 | "Contacto efectivo" incluye: promesa de pago, negación a pagar, ya pagó. |
| BR-05 | La tasa de contactabilidad = contactos efectivos / total gestiones. |
| BR-06 | La tasa de promesa = promesas / contactos efectivos. |
| BR-07 | Registros sin DNI o sin fecha válida se descartan y se loggean. |

---

## 6. Inputs y outputs

### Inputs
- **Fuente**: carpeta `data/input/`
- **Formato**: archivos `.xlsx` con hoja `Gestiones`
- **Volumen esperado**: ~150 archivos/mes, ~9 000 filas
- **Frecuencia**: ejecución diaria al cierre operativo (18:00)

### Outputs
- **Reporte Excel multi-hoja**: `reporte_cobranza_YYYYMMDD_HHMMSS.xlsx`
  - Hoja 1: Resumen ejecutivo (KPIs)
  - Hoja 2: Ranking de asesores
  - Hoja 3: Análisis por producto
  - Hoja 4: Dataset consolidado
- **4 gráficos PNG** para informe ejecutivo
- **Log de ejecución**: `logs/pipeline_YYYYMMDD_HHMMSS.log`

---

## 7. Manejo de excepciones

| Excepción | Manejo |
|---|---|
| No hay archivos en `input/` | `FileNotFoundError` con mensaje claro al usuario |
| Archivo Excel corrupto | Se loggea y se omite, continúa con los demás |
| DNI inválido (vacío o no numérico) | Se descarta la fila y se loggea con conteo |
| Fecha en formato no reconocido | `pd.to_datetime(..., errors="coerce")` → NaT, se descarta |

---

## 8. KPIs de éxito de la automatización

| KPI | Baseline (manual) | Target | Medido |
|---|---|---|---|
| Tiempo de procesamiento | 6.7 h | < 30 min | **< 5 segundos** ✓ |
| Tasa de error | ~3% (humano) | < 0.1% | **0%** ✓ |
| Disponibilidad del reporte | D+1 (día siguiente) | D+0 17:00 | **D+0 inmediato** ✓ |
| Trazabilidad | No existe | Log completo | **Implementado** ✓ |

---

## 9. Plan de UAT

Casos de prueba ejecutados con éxito (12/12 unitarios + validación end-to-end). Ver `tests/test_limpieza.py`.

---

## 10. Roadmap de escalamiento

**Fase 1 (actual)**: Python en máquina local, ejecución manual.
**Fase 2**: Trigger automático con Power Automate Desktop al detectar archivo nuevo en SharePoint.
**Fase 3**: Migración a Azure Functions con schedule + notificación Teams.
**Fase 4**: Bot RPA en UiPath que descargue archivos del CRM directamente.
