# 🏛️ OmniLedger — Standalone Accounting & General Ledger Service (`FEAT-088`)

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-green)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL%20RLS-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)

**OmniLedger** es el microservicio standalone desacoplado para la gestión contable de partida doble, libros diarios, estado de cuentas de partners y generación de reportes fiscales para la plataforma **OmniFlow SaaS**.

Forma parte de la suite de microservicios independientes (`:3027`, subdominio `ledger.*`), operando de manera aislada con **Row-Level Security (RLS)** y conectándose con los adaptadores de ERP (Odoo v14/v18/v19) y el Integration Worker mediante eventos asíncronos y contratos REST OpenAPI.

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                 FRONT-OFFICE / INTEGRATION ENGINE           │
│  - Integration Worker (BullMQ + Node.js)                    │
│  - Adaptadores ERP (Odoo CE / Tango / Custom)               │
└──────────────────────────────┬──────────────────────────────┘
                               │ (REST Async / JSON DTOs)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              OMNILEDGER STANDALONE (:3027)                  │
│  - FastAPI + Pydantic v2 Engine                             │
│  - Motor de Partida Doble (Strict ∑Débitos = ∑Créditos)     │
│  - Asientos Inmutables (`posted`) + Reversal Moves          │
│  - Reportes Fiscales DNIT (Libro Ventas / Libro Compras)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ (SQLAlchemy 2.0 Async + AsyncPG)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 POSTGRESQL (Row-Level Security)             │
│  - Aislamiento Lógico Multi-Tenant por RLS (`tenant_id`)    │
│  - Schema Canónico de Contabilidad (v18-compat / v19-compat)│
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Entidades Principales del Schema Canónico

| Tabla | Descripción |
| :--- | :--- |
| `account_accounts` | Plan de cuentas jerárquico por tenant. |
| `account_journals` | Diarios contables (Ventas, Compras, Banco, Efectivo POS, Varios). |
| `account_moves` | Cabecera del asiento/factura (fecha, estado `draft`/`posted`, referencia fiscal). |
| `account_move_lines` | Apuntes individuales (débito, crédito, partner, cuenta). |
| `account_taxes` | Reglas de impuestos (IVA 10%, IVA 5%, Exentas). |
| `partner_ledgers` | Estado de cuenta del cliente/proveedor, límite de crédito y saldo. |
| `account_mapping_rules` | Reglas de mapeo entre cuentas externas (Odoo) y cuentas canónicas OmniLedger. |
| `tenant_schema_version` | Metadata de compatibilidad de esquema (`v18-compat` / `v19-compat`). |

---

## 🔌 API REST Contracts (OpenAPI)

### 📌 Asientos & Partida Doble
- **`POST /api/v1/moves`:** Registra un nuevo asiento contable. Valida atómicamente que $\sum \text{Débitos} = \sum \text{Créditos}$ (Rechazo `HTTP 422` si está desbalanceado).
- **`POST /api/v1/moves/{id}/reverse`:** Genera un *reversal move* inmutable para anular o corregir un asiento `posted`.

### 📌 Consultas de Cuentas & Partners
- **`GET /api/v1/partners/{id}/ledger`:** Consulta el saldo consolidado y extracto de cuenta del partner.
- **`GET /api/v1/accounts/{code}/balance`:** Obtiene el saldo de una cuenta contable en un rango de fechas.

### 📌 Reportes Fiscales DNIT
- **`GET /api/v1/reports/libro-ventas?periodo=YYYY-MM`:** Genera el Libro de Ventas acumulado para el periodo.
- **`GET /api/v1/reports/libro-compras?periodo=YYYY-MM`:** Genera el Libro de Compras acumulado para el periodo.

---

## 🛠️ Desarrollo & Puesta en Marcha

### Prerrequisitos
- Python 3.11+ / 3.12+
- `uv` (Gestor rápido de paquetes de Python)
- PostgreSQL 15+ con extensión `pgcrypto`

### Instalación Local
```bash
# Clonar el repositorio
git clone https://github.com/marcelompz/omni-ledger.git /opt/omniledger
cd /opt/omniledger

# Crear entorno virtual e instalar dependencias con uv
uv sync

# Ejecutar migraciones de base de datos Alembic
uv run alembic upgrade head

# Iniciar servidor de desarrollo FastAPI
uv run uvicorn app.main:app --host 0.0.0.0 --port 3027 --reload
```

---

## 🧪 Suite de Pruebas & Calidad

```bash
# Ejecutar tests unitarios y de partida doble
uv run pytest

# Ejecutar tests de propiedad para redondeo con hypothesis
uv run pytest tests/test_rounding_hypothesis.py

# Verificar aislamiento RLS multi-tenant
uv run pytest tests/test_rls_isolation.py
```

---

## 📚 Documentación Vinculada
- **Plan Maestro de Construcción:** [`docs/planes/PLAN_CONSTRUCCION_OMNILEDGER.md`](docs/planes/PLAN_CONSTRUCCION_OMNILEDGER.md)
- **Protocolo de Actuación:** [`AGENTS.md`](AGENTS.md)
- **Índice de Troubleshooting:** [`docs/troubleshooting/README.md`](docs/troubleshooting/README.md)
