# **🗺️ PLAN DE CONSTRUCCIÓN: OMNILEDGER (FEAT-088)**

> **Documento:** `docs/planes/PLAN_CONSTRUCCION_OMNILEDGER.md`
> **Feature ID:** `FEAT-088` (tentativo — próximo ID libre según el último estado conocido del repo: last_id `FEAT-087` "OmniCatalog UX Mejoras" completed. **Verificar contra `featurelist.json` actual antes de reservarlo formalmente**, puede haber avanzado desde la última sincronización.)
> **Depende de:** `ROADMAP_ODOO_TO_FASTAPI_TRANSITION.md` (v3.5) y `ROADMAP_LEGACY_ADAPTERS.md` (v1.0)
> **Versión:** 1.0
> **Fecha:** 26 de agosto de 2026
> **Servicio:** `omniledger-standalone` — sigue el patrón `*-standalone` ya productivo (`biolinks-standalone` :3022, `bookings-standalone` :3023, etc.)

---

## **0. DECISIONES DE ARQUITECTURA (cerradas para este plan)**

| Decisión | Resolución | Razón |
|---|---|---|
| Multi-tenancy | **Row-Level Security (RLS)** sobre schema único | Consistente con la regla AGENTS.md de "tenantId nunca se elimina de queries"; una sola migración Alembic corre para todos los tenants en vez de N schemas |
| Puente BullMQ ↔ FastAPI | **El Integration Worker (Node) sigue siendo el consumidor de BullMQ** y llama a OmniLedger vía `POST` HTTP | Mantiene la separación de responsabilidades; evita acoplar el stack Python a la semántica de colas de Node |
| Puerto / subdominio | `:3027`, `ledger.*` | Sigue la numeración secuencial de los standalones existentes |

Si en algún momento estas decisiones necesitan revisarse, deben quedar registradas como un cambio explícito de versión de este documento, no como un ajuste silencioso.

---

## **1. SPRINT 0 — SCAFFOLDING**

- Estructura de proyecto: FastAPI + Pydantic v2, SQLAlchemy 2.0 Async + SQLModel, AsyncPG, Alembic con baseline `v18-compat`.
- Gestor de dependencias: `uv` (o Poetry si el resto del ecosistema Python de OmniFlow ya usa Poetry — verificar consistencia).
- Dockerfile multi-stage + healthcheck (`GET /health`) para que Traefik pueda hacer liveness checks.
- Entrada en `docker-compose.standalone.yml` + ruta en `traefik-orderflow`.
- Política RLS base en Postgres: toda tabla nueva nace con `tenant_id` obligatorio + policy de aislamiento desde el primer `CREATE TABLE`, no como parche posterior.

**Entregable de sprint:** servicio vacío mono-endpoint (`/health`) desplegado y ruteado, con CI corriendo Alembic contra una base de test.

---

## **2. FASE 1 — MODELO DE DATOS**

Las 6 entidades del mapeo canónico Odoo→FastAPI:

| Tabla | Contenido |
|---|---|
| `account_accounts` | Plan de cuentas jerárquico |
| `account_journals` | Diarios (Ventas, Compras, Banco, Efectivo POS, Varios) |
| `account_moves` | Cabecera de asiento/factura (fecha, estado `draft`/`posted`, ref. fiscal) |
| `account_move_lines` | Apuntes individuales (débito, crédito, partner) |
| `account_taxes` | Reglas de impuestos (IVA 10%, IVA 5%, Exentas) |
| `partner_ledgers` | Estado de cuenta, límite de crédito, saldo por partner |

**Agregados no cubiertos por el mapeo original**, incorporados en este plan:

- `account_mapping_rules`: tabla de mapeo cuenta-externa → cuenta-canónica, por tenant, versionada por fecha de vigencia (necesaria desde el día uno para que el adaptador Odoo pueda alimentar OmniLedger en modo `hybrid_shadow`).
- `tenant_schema_version`: metadata de compatibilidad (`v18-compat`/`v19-compat`) por tenant, para no forzar upgrades simultáneos.

**Entregable de fase:** migraciones Alembic completas + policies RLS por tabla + fixtures de test.

---

## **3. FASE 2 — MOTOR DE PARTIDA DOBLE**

- Validación atómica ∑Débitos = ∑Créditos antes de cualquier escritura; rechazo `HTTP 422` explícito (Regla de Oro #2 del roadmap original).
- Transición de estado `draft` → `posted`; inmutabilidad estricta post-`posted`; correcciones únicamente vía *reversal move* (Regla de Oro #3).
- Toda operación monetaria con `Decimal` (nunca `float`) para eliminar el riesgo de redondeo de IVA ya identificado en la matriz de riesgos del roadmap original.

**Entregable de fase:** servicio de dominio (no HTTP todavía) con cobertura de tests unitarios ≥ casos límite de redondeo e inconsistencia de partida.

---

## **4. FASE 3 — ENDPOINTS Y CONTRATO CON EL ADAPTADOR**

| Endpoint | Función |
|---|---|
| `POST /api/v1/moves` | Recibe el DTO canónico ya traducido, crea/valida un asiento |
| `GET /api/v1/partners/{id}/ledger` | Estado de cuenta del partner |
| `GET /api/v1/accounts/{code}/balance` | Saldo de una cuenta en un rango de fechas |
| `POST /api/v1/moves/{id}/reverse` | Genera el *reversal move* de un asiento `posted` |

El contrato debe ser indistinguible entre lo que hoy recibe el adaptador Odoo y lo que va a recibir OmniLedger — el Integration Worker no debería requerir cambios más allá de la URL de destino por tenant.

**Entregable de fase:** API documentada (OpenAPI autogenerado por FastAPI), colección de requests de ejemplo para el equipo de integración.

---

## **5. FASE 4 — REPORTES FISCALES DERIVADOS**

Gap identificado en la revisión del roadmap original: FacturaSend resuelve el timbrado/CDC, pero los libros formales (Libro Ventas, Libro Compras) para DNIT deben generarse a partir de `account_moves`/`account_move_lines`.

- `GET /api/v1/reports/libro-ventas?periodo=YYYY-MM`
- `GET /api/v1/reports/libro-compras?periodo=YYYY-MM`
- Exportación en el formato que DNIT/contador del cliente requiera (CSV/XLSX como mínimo).

**Entregable de fase:** reportes verificados contra un cierre mensual real de un tenant piloto.

---

## **6. FASE 5 — SUITE DE TESTS**

- Portar `test_account_move.py` de Odoo a Pytest (mitigación ya definida en la matriz de riesgos del roadmap original).
- Tests de propiedad (`hypothesis`) para redondeo de IVA sobre montos aleatorios, además de los casos fijos heredados de Odoo.
- Tests de policies RLS: confirmar que ningún query cross-tenant es posible ni siquiera con un bug de aplicación (test a nivel de base de datos, no solo de API).

**Entregable de fase:** suite corriendo en CI con cobertura reportada; bloqueante para pasar a Fase 6.

---

## **7. FASE 6 — INTEGRACIÓN CON DUAL-WRITE**

Punto de encuentro con la Fase 3 del roadmap general (`ROADMAP_ODOO_TO_FASTAPI_TRANSITION.md`): no hay trabajo nuevo de OmniLedger en sí, es la activación del modo `hybrid_shadow` por tenant (definido en `ROADMAP_LEGACY_ADAPTERS.md`), con los scripts de verificación de paridad de balances corriendo contra datos reales.

**Entregable de fase:** primer tenant piloto en `hybrid_shadow` con paridad 100% sostenida durante el período de prueba definido.

---

## **8. SINCRONIZACIÓN CON EL PROTOCOLO DE AGENTS.md**

Al reservar formalmente `FEAT-088` (o el ID que corresponda tras verificar `featurelist.json`), este plan requiere actualizar en el mismo paso: `VERSION`, `ROADMAP.md`, `CHANGELOG.md`, `docs/02-architecture.md`, el manifiesto correspondiente, y la Wiki en `/opt/wiki/orderflow/` — según la regla ya vigente del proyecto.
