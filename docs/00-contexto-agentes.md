# AGENTS.md — OmniLedger Contexto Técnico Vivo

> Guía de contexto técnico vivo del microservicio **OmniLedger** (`omniledger-standalone`).

---

## 1. Qué es OmniLedger

**OmniLedger** es el microservicio desacoplado de Contabilidad Canónica y Libro Mayor General de **OmniFlow SaaS**.

- **Repositorio:** `https://github.com/marcelompz/omni-ledger.git`
- **Ruta local:** `/opt/omniledger`
- **Puerto:** `:3027`
- **Subdominio Traefik:** `ledger.*`
- **Lenguaje / Stack:** Python 3.11+ / 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 Async, PostgreSQL RLS.

---

## 2. Reglas Clave
1. `tenant_id` obligatorio y políticas Row-Level Security (RLS) en Postgres.
2. Inmutabilidad estricta de asientos en estado `posted`.
3. Operaciones de moneda exclusivamente con `Decimal`.
