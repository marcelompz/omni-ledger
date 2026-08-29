# AGENTS.md — OmniLedger Harness Engineering Protocol

> **Protocolo Operativo de Actuación y Barrera de Calidad para Inteligencia Artificial**  
> **Servicio:** `omniledger-standalone` (Microservicio Standalone de Contabilidad & Libro Mayor Canónico)  
> **Versión:** 1.0.0 (Harness Engineering & E2E QA Standard)  
> **Fecha:** 27 de Agosto de 2026  

---

## 🚦 1. Primer Paso Obligatorio: Carga de Contexto
Antes de examinar código o ejecutar cualquier acción en la base del proyecto, debes consultar la especificación técnica maestra:
👉 [docs/planes/PLAN_CONSTRUCCION_OMNILEDGER.md](docs/planes/PLAN_CONSTRUCCION_OMNILEDGER.md)

---

## 🛡️ 2. Reglas Inviolables de Arquitectura & Código

1. **`tenant_id` es Sagrado & Policy RLS Obligatoria:** NO eliminar `tenant_id` de ninguna query, filtro o entidad. Toda tabla en PostgreSQL NACE obligatoriamente con la columna `tenant_id` y con su correspondiente política **Row-Level Security (RLS)** activa desde la primera migración de Alembic.
2. **Inmutabilidad de Asientos & Partida Doble Estricta:**
   - **Validación Atómica:** Se exige estricta igualdad $\sum \text{Débitos} = \sum \text{Créditos}$ antes de procesar cualquier asiento. Las peticiones desbalanceadas DEBEN ser rechazadas con `HTTP 422 Unprocessable Entity`.
   - **Transición de Estado:** Estado inicial `draft` $\rightarrow$ `posted`. Todo asiento en estado `posted` es **estrictamente inmutable**. Correcciones o anulaciones DEBEN realizarse exclusivamente generando un asiento de reversión (*reversal move*).
3. **Cero Redondeo Flotante (`Decimal` Obligatorio):** Queda estrictamente prohibido usar tipos `float` para importes monetarios o IVA. Todas las operaciones aritméticas de impuestos y saldos DEBEN utilizar `Decimal` de Python (`pydantic.condecimal` / `sqlalchemy.Numeric`) para evitar discrepancias centesimales.
4. **Infraestructura Proxy Exclusive Traefik v3.4 (Puerto `:3027`):** Prohibido configurar Nginx. Traefik administra SSL y subdominios dinámicos (`ledger.<tenant.subdomain>.<ROOT_DOMAIN>`).
5. **Stack Técnico Homologado:** FastAPI + Pydantic v2, SQLAlchemy 2.0 Async + SQLModel, AsyncPG, Alembic con baseline `v18-compat` y gestor de paquetes `uv`.
6. **Formato y Convención `kebab-case`:** Uso estricto de `kebab-case` para nombres de archivos (`.py`, `.sh`, `.md`).
7. **Sincronización de Documentación con Wiki & Monorepo Core:** Toda actualización de documentación en `docs/` o `README.md` debe sincronizarse con la Wiki oficial (`/opt/wiki/orderflow/`) y registrarse en `ROADMAP.md`, `CHANGELOG.md` y `VERSION` del ecosistema.
8. **Autorización Previa Obligatoria para Despliegues:** Queda estrictamente PROHIBIDO que la IA ejecute despliegues, builds de producción, reinicios de contenedores o comandos/scripts de deploy (tales como `docker compose up`, `deploy-production.sh`, etc.) sin solicitar y obtener autorización previa y explícita del usuario.

---

## 🔍 2.1 Troubleshooting First (Obligatorio)

Antes de investigar un bug o error de despliegue, consultar el índice de troubleshooting del microservicio:

👉 [docs/troubleshooting/README.md](docs/troubleshooting/README.md)

---

## ⚙️ 3. Barrera de Validación Automatizada

La IA debe verificar el proyecto ejecutando la suite de validación:

```bash
uv run pytest
```

### El entorno verifica automáticamente:
1. Migraciones limpias de Alembic (`uv run alembic upgrade head`).
2. Validación de paridad de partida doble ($\sum \text{Débitos} = \sum \text{Créditos}$).
3. Aislamiento RLS multi-tenant a nivel de base de datos.
4. Cobertura de tests unitarios y de propiedad (`hypothesis`).
