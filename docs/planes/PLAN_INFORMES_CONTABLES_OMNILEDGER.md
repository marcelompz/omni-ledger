# **📊 PLAN: INFORMES CONTABLES DINÁMICOS EN OMNILEDGER**

> **Documento:** `docs/planes/PLAN_INFORMES_CONTABLES_OMNILEDGER.md`
> **Versión:** 1.0
> **Fecha:** 31 de agosto de 2026
> **Extiende:** `ROADMAP_OMNILEDGER_MAESTRO.md` (v4.0), Fase 4 — "Motor de impuestos + libros fiscales"
> **Depende de:** `PLAN_IMPLEMENTACION_OMNILEDGER.md` (v2.0), Sección 3 (modelo de datos) y Sección 5 (API REST)

---

## **1. CONTEXTO Y ALCANCE**

Este plan traduce el addon Odoo `account_books_reports_cross` (Crossnexion) a endpoints nativos de OmniLedger, manteniendo la salida fiscal paraguaya pero **sin depender de Odoo** para generarla.

### Fuente de verdad
- `/opt/omniledger/docs/planes/account_books_reports_cross/` — Addon Odoo de referencia (solo lectura)
- Wizards: `account_books_report_wizard.py`, `financial_report_collectpay_wizard.py`, `rg90_report_wizard.py`
- Reportes QWeb: `account_books_report.xml`, `financial_report_collectpay.xml`, `partner_financial_report.xml`

### Informes a implementar

| # | Informe | Formatos | Endpoint propuesto |
|---|---|---|---|
| 1 | **Libro IVA Ventas** (Ley 125/91) | PDF, XLSX, CSV, TXT | `GET /api/v1/reports/libro-ventas` |
| 2 | **Libro IVA Compras** (Ley 125/91) | PDF, XLSX, CSV, TXT | `GET /api/v1/reports/libro-compras` |
| 3 | **Reporte Financiero** (Cobros/Pagos) | XLSX | `GET /api/v1/reports/financial-collect-pay` |
| 4 | **RG90 SET** (Registro electrónico) | TXT/CSV en ZIP | `GET /api/v1/reports/rg90` |

---

## **2. DATOS REQUERIDOS POR INFORME**

### 2.1 Libro IVA Ventas/Compras

Campos que el addon Odoo extrae de `account.move` y campos relacionados:

| Campo OmniLedger | Origen Odoo | Tipo |
|---|---|---|
| `invoice_date` | `account.move.invoice_date` | date |
| `invoice_number` | `account.move.name` | str |
| `serie` | `account.move.serie` | str |
| `cdc` | `account.move.cdc_l10n_py` | str |
| `authorization_id.stamped` | `account.move.authorization_id.stamped` | str |
| `authorization_id.date_to` | vencimiento timbrado | date |
| `partner_id.name` | `res.partner.name` | str |
| `partner_id.vat` | `res.partner.vat` | str |
| `partner_vat_dv` | split `vat` por `-` | str |
| `amount_iva10_tax_included` | cálculo por líneas | Decimal |
| `amount_iva5_tax_included` | cálculo por líneas | Decimal |
| `amount_iva10` | base imponible 10% | Decimal |
| `amount_iva5` | base imponible 5% | Decimal |
| `amount_iva0` | exentas | Decimal |
| `amount_total` | total factura | Decimal |
| `currency_id.symbol` | moneda | str |
| `invoice_condition` | compute: CON/CRE/DES/DEV/ANL/SIN | str |
| `installment_qty` | si término de pago es cuotas | int |
| `accounts` | concatenación `account_move_line.account_id.name` | str |
| `product_categ` | concatenación `product_id.categ_id.name` | str |
| `form145_id.name` | `account.move.form145_id` | str |
| `reasons_inclusion_id.name` | `account.move.form145_reasons_inclusion_id` | str |
| `details_inclusion` | `account.move.details_inclusion` | str |
| `reasons_cancelled` | `account.move.books_reports_cancel_reason` | str |
| `form120_id.name` | `account.move.form120_id` | str |
| `in_invoice_latam_doc_type_id.name` | compras | str |
| `in_invoice_stamped` | compras | str |
| `in_invoice_stamped_date_due` | compras | date |

### 2.2 Reporte Financiero (Collect/Pay)

Campos más simples, centrados en saldos:

| Campo | Origen | Tipo |
|---|---|---|
| `invoice_number` | `account.move.name` | str |
| `invoice_date` | `account.move.invoice_date` | date |
| `partner_id.vat` | `res.partner.vat` | str |
| `partner_id.name` | `res.partner.name` | str |
| `currency_id.name` | moneda | str |
| `amount_total_in_currency_signed` | total en moneda del reporte | Decimal |
| `amount_residual` | saldo pendiente | Decimal |
| `amount_residual_signed` | saldo pendiente firmado | Decimal |

### 2.3 RG90 SET

Formato fiscal electrónico con columnas fijas:

| Campo | Posición | Tipo | Observación |
|---|---|---|---|
| `code` | 1 | int | 1=ventas, 2=compras, 3=ingresos, 4=egresos |
| `identification_type` | 2 | int | Mapeo Odoo → SET (11=RUC, 12=CI, etc.) |
| `partner_vat` | 3 | str | RUC sin DV, o `X`/`1` para casos especiales |
| `partner_name` | 4 | str | Razón social |
| `receipt_type` | 5 | str | Código tipo comprobante |
| `date` | 6 | date | DD/MM/YYYY |
| `stamped` | 7 | str | Número timbrado |
| `receipt_number` | 8 | str | Número comprobante |
| `amount_iva10_tax_included` | 9 | Decimal | Gravado 10% (IVA incluido) |
| `amount_iva5_tax_included` | 10 | Decimal | Gravado 5% (IVA incluido) |
| `amount_iva0` | 11 | Decimal | Exento |
| `amount_total` | 12 | Decimal | Total comprobante |
| `receipt_condition` | 13 | int | 1=contado, 2=crédito |
| `foreign_currency` | 14 | str | N=PYG, S=extranjera |
| `impute_iva` | 15 | str | S/N |
| `impute_ire` | 16 | str | S/N |
| `impute_irp` | 17 | str | S/N |
| `associated_receipt` | 18 | str | Comprobante asociado (nota crédito) |
| `stamped_associated_receipt` | 19 | str | Timbrado asociado |
| `receipt_period` | 20 | str | DD/MM/YYYY (solo código 208) |
| `specify_document_type` | 21 | str | Especificar tipo |
| `no_impute` | 22 | str | No imputa (solo egresos) |
| `account_number` | 23 | str | Número cuenta (solo egresos) |
| `bank` | 24 | str | Banco/financiera (solo egresos) |
| `employer_vat` | 25 | str | RUC empleador IPS (solo egresos) |
| `receipt_type_specific` | 26 | str | Especificar tipo (solo egresos) |

---

## **3. MODELOS DE DATOS NECESARIOS**

### 3.1 Nuevas tablas en OmniLedger

El addon Odoo agrega campos a `account.move` y crea modelos auxiliares. En OmniLedger, estos campos deben agregarse como **columnas adicionales** en las tablas existentes o como tablas auxiliares:

#### Opción A: Columnas adicionales en `account_moves` (preferida)
```sql
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS serie VARCHAR(50);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS cdc VARCHAR(100);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS invoice_condition VARCHAR(10);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS installment_qty INTEGER;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS out_invoice_stamped VARCHAR(50);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS out_invoice_stamped_date_due DATE;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS in_invoice_stamped VARCHAR(50);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS in_invoice_stamped_date_due DATE;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS details_inclusion TEXT;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS reasons_cancelled TEXT;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS receipt_period VARCHAR(50);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS specify_document_type VARCHAR(100);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS receipt_type_code VARCHAR(20);
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS receipt_type_id INTEGER;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS authorization_id INTEGER;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS form145_id INTEGER;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS form120_id INTEGER;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS reasons_inclusion_id INTEGER;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS is_fiscal_document BOOLEAN DEFAULT FALSE;
ALTER TABLE account_moves ADD COLUMN IF NOT EXISTS is_electronic_invoice BOOLEAN DEFAULT FALSE;
```

#### Opción B: Tabla auxiliar `fiscal_document_metadata`
```sql
CREATE TABLE IF NOT EXISTS fiscal_document_metadata (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  move_id INTEGER NOT NULL,
  cdc VARCHAR(100),
  stamped VARCHAR(50),
  stamped_date_due DATE,
  serie VARCHAR(50),
  invoice_condition VARCHAR(10),
  installment_qty INTEGER,
  details_inclusion TEXT,
  reasons_cancelled TEXT,
  receipt_period VARCHAR(50),
  specify_document_type VARCHAR(100),
  form145_id INTEGER,
  form120_id INTEGER,
  reasons_inclusion_id INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 3.2 Criterio de selección
- **Usar Opción A** si los campos son específicos de facturación fiscal y se consultan frecuentemente en reportes.
- **Usar Opción B** si se quiere mantener el schema contable limpio y separar metadata fiscal de la contabilidad core.

**Recomendación:** Opción A para `is_fiscal_document`, `cdc`, `stamped`, `receipt_type_code`. Opción B para metadata menos frecuente como `details_inclusion`, `reasons_cancelled`.

---

## **4. LÓGICA DE CÁLCULO**

### 4.1 Desglose de impuestos por línea

El addon Odoo calcula:
```python
# IVA 10% incluido = suma de price_total de líneas con tasa 10%
tax10_included = sum(line.price_total for line in invoice.invoice_line_ids if line.tax_ids.amount == 10)

# IVA 5% incluido = suma de price_total de líneas con tasa 5%
tax5_included = sum(line.price_total for line in invoice.invoice_line_ids if line.tax_ids.amount == 5)

# Exentas = suma de price_total de líneas sin impuestos
tax0 = sum(line.price_total for line in invoice.invoice_line_ids if not line.tax_ids)

# Base imponible 10% = tax10_included / 1.10
tax10_base = tax10_included / 1.10

# Base imponible 5% = tax5_included / 1.05
tax5_base = tax5_included / 1.05
```

**En OmniLedger:** Este cálculo debe realizarse en el **motor de partida doble** (Fase 2) al crear las líneas de asiento, almacenando los campos desglosados en `account_move_lines`:
```python
class AccountMoveLine(Base):
    tax_code = String(20)  # IVA_10, IVA_5, EXENTO
    tax_amount = Numeric(19, 2)  # impuesto desglosado
    tax_base = Numeric(19, 2)  # base imponible
    amount_tax_included = Numeric(19, 2)  # total con IVA
```

### 4.2 Formato RG90

El addon genera archivos de texto fijo/CSV con 19-26 columnas según el tipo. La lógica de formateo debe implementarse en un **report engine** dedicado:

```
1,11,80012345-6,EMPRESA SA,001,01/01/2024,TIMB123,FAC-001,1000000,50000,0,1050000,1,N,S,S,N,,,,,
```

---

## **5. ENDPOINTS PROPUESTOS**

### 5.1 Libro IVA Ventas/Compras

```
GET /api/v1/reports/libro-ventas?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&format=pdf|xlsx|csv|txt
GET /api/v1/reports/libro-compras?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&format=pdf|xlsx|csv|txt
```

**Lógica:**
1. Validar `date_from` <= `date_to`
2. Consultar `account_moves` donde:
   - `tenant_id` = current_tenant
   - `state` = `posted`
   - `date` entre `date_from` y `date_to`
   - `move_type` = `out_invoice` + `out_refund` (ventas) o `in_invoice` + `in_refund` (compras)
   - `is_fiscal_document` = true
3. Calcular desglose de impuestos por línea
4. Generar reporte en formato solicitado
5. Retornar `application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/csv` o `text/plain`

### 5.2 Reporte Financiero

```
GET /api/v1/reports/financial-collect-pay?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
```

**Lógica:**
1. Consultar `account_moves` donde `state` = `posted` y `date` en rango
2. Para cada factura, calcular:
   - `amount_total_in_currency_signed` = total en moneda del reporte
   - `amount_residual` = saldo pendiente
   - `amount_residual_signed` = saldo pendiente firmado
3. Agrupar por partner
4. Generar XLSX con totales

### 5.3 RG90 SET

```
GET /api/v1/reports/rg90?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&type=out_invoice|in_invoice|income|revenue&format=txt|csv
```

**Lógica:**
1. Mapear `type` a código de registro (1-4)
2. Filtrar facturas fiscales en rango
3. Mapear `identification_type` según país y documento
4. Calcular montos por tipo de impuesto
5. Generar TXT/CSV con delimitador fijo
6. Empaquetar en ZIP con nombre `{RUC}_REG_{PERIODO}_{VERSION}.zip`

---

## **6. FORMATOS DE SALIDA**

### 6.1 PDF (Libro IVA)
- Usar `ReportLab` o `WeasyPrint` para generar PDF desde HTML
- Formato: A4 landscape, fuente Arial 8-10px
- Encabezado: CONTRIBUYENTE, PERIODO, ACTIVIDAD
- Tabla con 27 columnas (ver XML del addon)

### 6.2 XLSX (Libro IVA + Financiero)
- Usar `openpyxl` o `xlsxwriter`
- Formatos: título, subtítulo, encabezado, datos, números
- Anchos de columna predefinidos
- Números con formato `#,##0.00` según moneda

### 6.3 CSV/TXT (Libro IVA + RG90)
- Usar módulo `csv` de Python
- Delimitador: `,` para CSV, `\t` para TXT
- Encoding: UTF-8 con BOM para Excel
- Quotechar: `"`, quoting: `QUOTE_MINIMAL`

### 6.4 ZIP (RG90)
- Usar módulo `zipfile`
- Contenido: 1 archivo TXT/CSV
- Nombre: `{RUC}_REG_{PERIODO}_{VERSION}.{ext}`
- Nombre ZIP: `{RUC}_REG_{PERIODO}_{VERSION}.zip`

---

## **7. DEPENDENCIAS NUEVAS**

```toml
dependencies = [
    # ... existentes ...
    "openpyxl>=3.1.0",        # XLSX
    "xlsxwriter>=3.2.0",      # XLSX alternativo
    "reportlab>=4.0.0",       # PDF
    "weasyprint>=61.0",       # PDF desde HTML (alternativa)
    "pypdf2>=3.0.0",          # Manipulación PDF
]
```

---

## **8. FASES DE IMPLEMENTACIÓN**

### Fase 4.1 — Modelo de datos (Sem. 9)
- Agregar columnas fiscales a `account_moves` (Opción A) o crear `fiscal_document_metadata` (Opción B)
- Migración Alembic `002_add_fiscal_metadata.py`
- Actualizar `src/models/accounting.py`

### Fase 4.2 — Motor de impuestos (Sem. 9-10)
- Implementar cálculo de desglose de impuestos por línea en `ledger_service.py`
- Métodos: `calculate_tax_breakdown(invoice_lines) -> dict`
- Redondeo half-even, validación de suma

### Fase 4.3 — Report engine base (Sem. 10)
- Crear `src/services/report_engine.py`
- Clases base: `BaseReport`, `XlsxReport`, `CsvReport`, `PdfReport`, `ZipReport`
- Formateo de números, fechas, encabezados

### Fase 4.4 — Endpoints Libro IVA (Sem. 10-11)
- `GET /api/v1/reports/libro-ventas`
- `GET /api/v1/reports/libro-compras`
- Formatos: PDF, XLSX, CSV, TXT
- Tests de salida contra fixture Odoo

### Fase 4.5 — Endpoint Reporte Financiero (Sem. 11)
- `GET /api/v1/reports/financial-collect-pay`
- Formato XLSX
- Agrupación por partner, totales

### Fase 4.6 — Endpoint RG90 SET (Sem. 12)
- `GET /api/v1/reports/rg90`
- Formatos TXT/CSV en ZIP
- Mapeo de tipos de identificación
- Nomenclatura SET validada

### Fase 4.7 — Validación fiscal (Sem. 12)
- Tests de paridad contra addon Odoo
- Validación de sumas por columna
- Prueba de redondeo half-even
- Verificación de formato RG90 contra especificación SET

---

## **9. CHECKLIST DE CUMPLIMIENTO FISCAL**

| Requisito | Estado | Verificación |
|---|---|---|
| Formato RG90 SET | ⏳ Pendiente | Validar contra especificación oficial SET |
| Sumas de IVA 10%/5% | ⏳ Pendiente | Probar con casos de redondeo |
| Identificación de partners | ⏳ Pendiente | Mapeo RUC/CI/Pasaporte |
| Moneda y decimales | ⏳ Pendiente | Usar `Decimal` con contexto adecuado |
| Inmutabilidad de reportes | ✅ | Los reportes son de solo lectura, no modifican datos |
| Aislamiento multi-tenant | ✅ | RLS por `tenant_id` |

---

## **10. SINCRONIZACIÓN CON PROTOCOLO AGENTS.md**

Al completar cada fase, actualizar:
- `VERSION` (incrementar parche)
- `ROADMAP.md` (estado Fase 4)
- `CHANGELOG.md` (nuevos endpoints de reportes)
- `docs/02-architecture.md` (si aplica)
- Wiki `/opt/wiki/orderflow/OmniLedger.md`

El Feature ID para este plan será **FEAT-105** (OmniLedger), a confirmar contra `featurelist.json` actual antes de reservar.

---