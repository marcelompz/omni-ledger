# 📖 Guía de Usuario — OmniLedger Standalone

## Bienvenido a OmniLedger

**OmniLedger** es el microservicio standalone de contabilidad de partida doble para la plataforma **OmniFlow SaaS**. Gestiona libros mayores, asientos contables, partners y reportes fiscales DNIT.

---

## 🚀 Primeros pasos

### Instalación local

```bash
# 1. Clonar repositorio
git clone https://github.com/marcelompz/omni-ledger.git /opt/omniledger
cd /opt/omniledger

# 2. Instalar dependencias
uv sync

# 3. Ejecutar migraciones
uv run alembic upgrade head

# 4. Iniciar servidor
uv run uvicorn app.main:app --host 0.0.0.0 --port 3027 --reload
```

### Verificar que está corriendo

```bash
curl http://localhost:3027/health
# Expected: {"status":"ok","service":"omniledger-standalone"}
```

---

## 🔌 API REST Contracts

### Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/health` | Health check del servicio |
| `POST` | `/api/v1/moves` | Registrar un nuevo asiento contable |
| `POST` | `/api/v1/moves/{id}/reverse` | Generar reversión de un asiento posted |
| `GET` | `/api/v1/partners/{id}/ledger` | Consulta estado de cuenta del partner |
| `GET` | `/api/v1/accounts/{code}/balance` | Obtener saldo de una cuenta en rango de fechas |
| `GET` | `/api/v1/reports/libro-ventas?periodo=YYYY-MM` | Libro de ventas acumulado |
| `GET` | `/api/v1/reports/libro-compras?periodo=YYYY-MM` | Libro de compras acumulado |

### Ejemplo: Registrar asiento

```bash
curl -X POST "http://localhost:3027/api/v1/moves" \
  -H "Content-Type: application/json" \
  -H "X-OmniLedger-Tenant-Id: 1" \
  -d '{
    "ref": "FAC-2024-001",
    "date": "2024-01-15T10:30:00Z",
    "state": "draft",
    "description": "Venta de productos",
    "partner_id": 123,
    "lines": [
      {"account_code": "4110", "debit": 100.00, "credit": 0.00, "description": "Producto A"},
      {"account_code": "4120", "debit": 0.00, "credit": 100.00, "description": "IVA 10%"}
    ]
  }'
```

**Validación:** Si $\sum\text{Débitos} \neq \sum\text{Créditos}$, recibirás `HTTP 422 Unprocessable Entity`.

---

## 🏢 Multi-Tenant

### Concepto de Tenant

Cada cliente/empresa en OmniFlow tiene su propio `tenant_id`. Todas las operaciones están aisladas a nivel de base de datos mediante **Row-Level Security (RLS)**.

### ¿Cómo funciona?

1. Todas las tablas nacen con columna `tenant_id INTEGER NOT NULL`
2. Políticas RLS de PostgreSQL aseguran que los queries solo vean registros de su tenant
3. Nunca se elimina `tenant_id` de ningún query (regla AGENTS.md)

### Ejemplo de query con tenant isolation

```sql
SELECT * FROM account_moves WHERE tenant_id = 5;
-- Solo ve los moves del tenant 5, aunque la app no especifique WHERE tenant_id
-- La política RLS se encarga automáticamente.
```

---

## 🔄 Integración con OrderFlow (Backend Dinámico)

OmniLedger se integra con OrderFlow a través del **Integration Worker** (NestJS + BullMQ). La selección del backend es dinámica por tenant:

### Flujo de Eventos

```
Odoo CE / ERP
   │
   ▼
Addon OrderFlow Integration
   │
   ▼
Redis Queue
   │
   ▼
WebhookEventListener (OrderFlow Backend)
   │
   ├──▶ Consulta tabla integrations[tenantId] donde type=OMNILEDGER y active=true
   │
   ├──▶ Si existe OMNILEDGER activo:
   │      └──▶ POST a OmniLedger /api/v1/moves
   │
   └──▶ Siempre: POST a OrderFlow API (si webhookOrderConfirmedUrl existe)
```

### Configuración Dinámica

En OrderFlow, crear un registro en la tabla `integrations`:

```json
{
  "tenantId": "uuid-del-tenant",
  "type": "OMNILEDGER",
  "active": true,
  "config": {
    "url": "https://ledger.pesallaccia.com/api/v1",
    "apiKey": "sk_omniledger_xxx"
  }
}
```

### Header de Autenticación

El Integration Worker envía el header `X-OmniLedger-Tenant-Id` con el ID del tenant para aislamiento automático.

---

## 📊 Reportes Fiscales DNIT

### Libro de Ventas

```bash
curl "http://localhost:3027/api/v1/reports/libro-ventas?periodo=2024-01"
```

### Libro de Compras

```bash
curl "http://localhost:3027/api/v1/reports/libro-compras?periodo=2024-01"
```

Formatos disponibles: CSV, XLSX (mínimo). Los datos provienen de `account_moves` + `account_move_lines`.

---

## ⚠️ Troubleshooting

### Errores comunes

| Síntoma | Causa | Solución |
|---|---|---|
| `HTTP 422` al crear asiento | $\sum\text{Débitos} \neq \sum\text{Créditos}$ | Verificar que las líneas de asiento estén balanceadas |
| `403 Forbidden` en consultas | RLS policy bloqueando query | Confirmar que `tenant_id` esté seteado en la conexión |
| `500 Internal` en `/health` | Base de datos no disponible | Verificar que PostgreSQL esté corriendo y migraciones aplicadas |
| Eventos no llegan a OmniLedger | Integración no activa | Verificar `active=true` en tabla `integrations` de OrderFlow |

Consultar [`docs/troubleshooting/README.md`](docs/troubleshooting/README.md) para el índice completo.

---

## 🔧 Desarrollo

### Añadir nueva entidad

1. Crear modelo en `src/db/models.py` con `tenant_id INTEGER NOT NULL`
2. Generar nueva migración Alembic: `uv run alembic revision --autogenerate -m "descripción"`
3. Agregar endpoint en `src/app/main.py` o crear nuevo router
4. Ejecutar tests: `uv run pytest`

### Validación de partida doble

Todas las escrituras pasan por validación atómica en el servicio. Nunca se permite un asiento desbalanceado en la base de datos.

---