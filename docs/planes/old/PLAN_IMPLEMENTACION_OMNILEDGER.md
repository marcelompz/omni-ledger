# **🏗️ PLAN DE IMPLEMENTACIÓN: OMNILEDGER**

> **Documento:** `docs/planes/PLAN_IMPLEMENTACION_OMNILEDGER.md`
> **Versión:** 2.0 — **documento único y canónico**
> **Fecha:** 27 de agosto de 2026
> **Depende de:** `ROADMAP_OMNILEDGER_MAESTRO.md` (v4.0)
> **Estado:** ✅ Reemplaza y deja obsoletos a `PLAN_CONSTRUCCION_OMNILEDGER.md` y al borrador anterior `PLAN_IMPLEMENTACION_OMNI_LEDGER.md` (archivar, no borrar).
> **Feature ID:** pendiente de reconfirmar contra `featurelist.json` real antes de reservar (última verificación: próximo libre `FEAT-105`).

---

## **1. DECISIONES DE ARQUITECTURA (cerradas — cambiarlas exige nueva versión de este documento)**

| Decisión | Resolución | Razón |
|---|---|---|
| Multi-tenancy | **Row-Level Security (RLS)** sobre schema único | Consistente con la regla AGENTS.md de "tenantId nunca se elimina de queries"; una sola migración Alembic corre para todos los tenants |
| Puente BullMQ ↔ FastAPI | El **Integration Worker (Node) sigue siendo el consumidor** de BullMQ y llama a OmniLedger vía `POST` HTTP | Mantiene la separación de responsabilidades; evita acoplar el stack Python a la semántica de colas de Node |
| Servicio / puerto / subdominio | `omniledger-standalone`, `:3027`, `ledger.*` | Sigue el patrón `*-standalone` ya productivo |
| Precisión monetaria | `Decimal(19, 2)` en todas las columnas de monto, redondeo **half-even** | Resuelve la inconsistencia entre el código actual (`Numeric(19,2)`) y el borrador anterior (`Decimal(16,2)`); 19,2 da margen para montos altos en guaraníes sin decimales fraccionarios reales |
| Gestor de dependencias | `uv` | Confirmar consistencia con el resto del ecosistema Python de OmniFlow antes de Sprint 0 |
| Fuente de especificación contable | `../odoo-addons` y `../odoo-l10n-py` (repos hermanos, **solo lectura**, nunca en ejecución) | Extraer lógica de partida doble y fixtures del plan de cuentas de Paraguay sin acoplarse a Odoo en producción |

---

## **2. ESTRUCTURA DEL PROYECTO (única — reemplaza la estructura plana actual del repo)**

El código actual en `omniledger_tar.zx` (`src/app/main.py`, `src/db/models.py`) es un scaffold incompleto que debe reorganizarse a esta estructura antes de continuar, para no tener dos convenciones conviviendo:

```
omniledger/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   ├── main.py                 # Inicialización FastAPI, middlewares, CORS
│   ├── core/
│   │   ├── config.py           # Settings vía Pydantic (DB URL, Redis, etc.)
│   │   ├── database.py         # Async engine & sessionmaker (asyncpg)
│   │   └── security.py         # API keys / JWT multi-tenant
│   ├── models/                 # SQLAlchemy 2.0 / SQLModel
│   │   ├── account.py
│   │   ├── journal.py
│   │   ├── move.py
│   │   ├── move_line.py
│   │   ├── tax.py
│   │   ├── partner.py
│   │   └── mapping.py          # account_mapping_rules, tenant_schema_version
│   ├── schemas/                # DTOs Pydantic v2
│   │   ├── move_dto.py
│   │   ├── partner_dto.py
│   │   └── report_dto.py
│   ├── services/                # Lógica de negocio pura
│   │   ├── ledger_service.py    # Balanceo, validación, posting
│   │   ├── reconciliation.py    # Conciliación de pagos
│   │   └── report_engine.py     # Agregaciones para balances/libros
│   └── api/v1/
│       ├── moves.py
│       ├── accounts.py
│       ├── partners.py
│       └── reports.py
└── tests/
    ├── conftest.py               # Fixtures de DB (testcontainers Postgres)
    ├── test_double_entry.py
    ├── test_credit_sales.py
    ├── test_tax_computation.py
    ├── test_rls_isolation.py
    └── test_odoo_parity.py       # Portados de test_account_move.py de Odoo
```

**Nota de migración de código:** al reorganizar, corregir también el bug ya detectado en `models.py` — `AccountAccount` y `AccountMove` usan `__mapper_args__` con `polymorphic_identity`/`with_polymorphic="*"` sin estructura de herencia real; eliminar esas líneas, no tienen función en este esquema.

---

## **3. MODELO DE DATOS**

8 tablas, sin excepción — cualquier tabla adicional requiere justificarse contra la Sección 2 del roadmap maestro (alcance explícito):

| Tabla | Contenido | Origen |
|---|---|---|
| `account_accounts` | Plan de cuentas jerárquico | Mapeo canónico original |
| `account_journals` | Diarios (Ventas, Compras, Banco, Efectivo POS, Varios) | Mapeo canónico original |
| `account_moves` | Cabecera de asiento/factura (`draft`/`posted`, ref. fiscal, CDC) | Mapeo canónico original |
| `account_move_lines` | Apuntes individuales (débito, crédito, partner, cuenta, impuesto) | Mapeo canónico original |
| `account_taxes` | Reglas de impuestos (IVA 10%, 5%, Exentas) | Mapeo canónico original |
| `partner_ledgers` | Estado de cuenta, límite de crédito, saldo por partner | Mapeo canónico original |
| `account_mapping_rules` | Mapeo cuenta-externa → cuenta-canónica, por tenant, versionado por fecha de vigencia | Gap identificado en revisión anterior |
| `tenant_schema_version` | Metadata de compatibilidad `v18-compat`/`v19-compat` por tenant | Gap identificado en revisión anterior |

Toda tabla nace con `tenant_id NOT NULL` + policy RLS desde el primer `CREATE TABLE`, nunca como parche posterior.

---

## **4. MOTOR DE PARTIDA DOBLE**

- Validación atómica ∑Débitos = ∑Créditos antes de cualquier escritura; rechazo `HTTP 422` explícito.
- Transición `draft` → `posted`; inmutabilidad estricta post-`posted`; correcciones solo vía *reversal move* con motivo documentado.
- Toda operación monetaria con `Decimal(19,2)`, redondeo half-even — nunca `float`.
- Cada línea contable almacena `origin_document_id`, `sifen_cdc` y `fiscal_number` para trazabilidad integral.

---

## **5. API REST — CONTRATO ÚNICO**

| Endpoint | Función |
|---|---|
| `POST /api/v1/moves` | Crea un asiento en `draft` |
| `POST /api/v1/moves/{id}/post` | Valida ∑D=∑C y publica (`posted`) |
| `POST /api/v1/moves/{id}/reverse` | Genera *reversal move* con trazabilidad cruzada |
| `GET /api/v1/moves` | Consulta paginada por fecha, diario, partner, estado |
| `GET /api/v1/partners/{id}/statement` | Estado de cuenta, saldo pendiente, facturas vencidas, límite de crédito |
| `POST /api/v1/partners/{id}/reconcile` | Concilia cobros/pagos contra facturas pendientes (manual o FIFO) |
| `GET /api/v1/accounts/{code}/balance` | Saldo de una cuenta en un rango de fechas |
| `GET /api/v1/reports/libro-ventas?periodo=YYYY-MM` | Libro de Ventas fiscal |
| `GET /api/v1/reports/libro-compras?periodo=YYYY-MM` | Libro de Compras con desglose de IVA |
| `GET /api/v1/reports/general-ledger` | Libro Mayor por cuenta y partner |
| `GET /api/v1/reports/trial-balance` | Balance de comprobación (8 columnas) |

El contrato debe ser indistinguible entre lo que hoy recibe el adaptador Odoo y lo que recibe OmniLedger — el Integration Worker no requiere cambios más allá de la URL de destino por tenant.

---

## **6. FASES DE CONSTRUCCIÓN (calendario en `ROADMAP_OMNILEDGER_MAESTRO.md` Sección 7)**

1. **Sprint 0** — Scaffolding real: `pyproject.toml`, Dockerfile, Alembic inicial, política RLS base, entrada en `docker-compose.standalone.yml` + Traefik. Entregable: `/health` desplegado y ruteado, CI corriendo Alembic contra base de test.
2. **Fase 1** — Las 8 tablas completas + migraciones + fixtures de test.
3. **Fase 2** — Motor de partida doble como servicio de dominio, sin HTTP todavía. Cobertura de tests en casos límite de redondeo.
4. **Fase 3** — Endpoints REST completos + módulo de cuentas por cobrar/crédito POS.
5. **Fase 4** — Motor de impuestos + libros fiscales, verificados contra un cierre mensual real de un tenant piloto.
6. **Fase 5** — Suite de tests de paridad con Odoo (`test_odoo_parity.py`), tests de propiedad (`hypothesis`) para redondeo, tests de aislamiento RLS a nivel de base de datos (no solo de API). Bloqueante para pasar a Fase 6.
7. **Fase 6** — Activación de `hybrid_shadow` en tenant piloto, scripts de verificación de paridad de balances.
8. **Fase 7** — `hybrid_active`, paridad sostenida durante el período de prueba definido antes de considerar `omniledger_only` para ese tenant.

---

## **7. REGLAS DE AUDITORÍA Y CALIDAD**

1. **Inalterabilidad de registros** — toda corrección a un balance publicado es un asiento de reversión explícito con motivo documentado.
2. **Trazabilidad integral** — cada línea contable almacena su identificador de origen.
3. **Control de redondeo** — `Decimal(19,2)`, método half-even, sin excepciones.
4. **La documentación de este servicio (README, AGENTS.md del servicio) solo describe lo que está implementado y verificado, no lo planeado** — lo planeado vive exclusivamente en este documento y en el roadmap maestro, para no repetir la desincronización ya detectada entre el README actual del servicio y su código real.
