# **🗺️ ROADMAP MAESTRO: OMNILEDGER Y HUB DE INTEROPERABILIDAD**

> **Documento:** `docs/planes/ROADMAP_OMNILEDGER_MAESTRO.md`
> **Versión:** 4.0 — **documento único y canónico**
> **Fecha:** 27 de agosto de 2026
> **Estado:** ✅ Reemplaza y deja obsoletos a los siguientes documentos (archivar, no borrar, para historial):
> - `ROADMAP_ODOO_TO_FASTAPI_TRANSITION.md` (v3.5)
> - `ROADMAP_ODOO_FASTAPI_TRANSICION_E_INTEROPERABILIDAD.md` (v3.5)
> - `ROADMAP_LEGACY_ADAPTERS.md` (v1.0)
>
> A partir de esta versión, **este es el único roadmap estratégico vigente** para la transición contable y la estrategia de interoperabilidad de OmniFlow/OrderFlow. Cualquier cambio de fecha, alcance o arquitectura se versiona acá, no en un documento nuevo.

---

## **1. VISIÓN Y PRINCIPIO RECTOR**

OmniFlow se consolida bajo un principio único: **independencia total entre la experiencia comercial de alta velocidad (Front-Office) y los motores de registro contable-administrativo (Back-Office)**, con la capacidad de conectarse — de forma permanente, nunca solo transitoria — a cualquier sistema contable/ERP que el cliente ya tenga.

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONT-OFFICE OMNIFLOW                    │
│  POS Offline-First (Tauri) · Catálogo Social · B2B ·        │
│  Facturación electrónica SIFEN/DNIT vía FacturaSend API     │
└──────────────────────────────┬───────────────────────────────┘
                               │ (Eventos JSON vía BullMQ/Redis)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│         INTEGRATION WORKER (Node.js — consumidor único)     │
│    Enruta por tenant hacia uno o más conectores (fan-out)   │
└──┬──────────────┬──────────────┬──────────────┬──────────────┘
  │              │              │              │
  ▼              ▼              ▼              ▼
Odoo CE/EE     SAP/Dynamics   OmniLedger     Otros legacy
(adaptador)    /NetSuite      (nativo,       (staging SQL,
              (adaptador)    FastAPI)       webhooks, batch)
```

**Regla de oro #0 (nueva, resuelve la ambigüedad de versiones anteriores):** ningún conector es "el reemplazo final" de otro. La arquitectura de conectores es un producto permanente de OmniFlow, no un artefacto de migración temporal. OmniLedger es la opción **nativa por defecto** para tenants sin ERP previo — no es la meta final de una migración obligatoria para tenants que ya tienen Odoo, SAP u otro sistema funcionando.

---

## **2. ALCANCE EXPLÍCITO DE OMNILEDGER (sección nueva — resuelve la ambigüedad señalada)**

### ✅ Qué es OmniLedger
Un motor contable puro de partida doble: asientos, diarios, impuestos, cuentas corrientes de partners y reportes fiscales derivados. Inspirado en el modelo canónico de Odoo, pero **no es un fork funcional de Odoo**.

### ❌ Qué NO es OmniLedger, ni lo será
- No gestiona inventario, valuación de stock ni compras — eso ya lo cubren los módulos nativos de OmniFlow (gestión de inventario y OmniManufacturing/MRP), independientes tanto de Odoo como de OmniLedger.
- No gestiona manufactura, BoM ni planificación de producción.
- No gestiona RRHH, nómina, ni CRM.
- No reemplaza Odoo (ni SAP, ni Dynamics) para clientes que ya lo tienen funcionando y no piden migrar — para ellos, el adaptador correspondiente es **la solución permanente**, no un puente hacia OmniLedger.

### Consecuencia práctica
Un tenant sin ERP previo puede operar 100% sobre OmniFlow (Front-Office + OmniLedger + módulos nativos de inventario/MRP) sin depender nunca de Odoo. Un tenant con Odoo/SAP/Dynamics ya instalado puede seguir usándolo indefinidamente vía su adaptador — migrar a OmniLedger es una opción comercial, no una obligación técnica del roadmap.

---

## **3. MATRIZ DE CONECTORES DEL HUB DE INTEROPERABILIDAD**

| Conector | Protocolo | Estado | Público objetivo |
|---|---|---|---|
| **OmniLedger (nativo)** | REST interno | En desarrollo (ver `PLAN_IMPLEMENTACION_OMNILEDGER.md`) | Micro-PyMEs sin ERP previo |
| **Odoo CE/Enterprise (v14-v19)** | XML-RPC / JSON-RPC | ✅ En producción, sync bidireccional | Clientes con Odoo ya implementado |
| **SAP (ECC / S/4HANA)** | OData REST, RFC, BAPI | No iniciado | Clientes corporativos con SAP |
| **Microsoft Dynamics 365 / BC** | Dataverse / OData | No iniciado | Ecosistema Microsoft |
| **Oracle (NetSuite / ERP Cloud)** | REST / SuiteTalk | No iniciado | Distribuidoras y retail |
| **Legacy sin API** | Staging SQL / webhooks / batch | No iniciado | Sistemas contables locales sin nube |

Todo conector nuevo implementa la interfaz `IErpSyncAdapter` (consistente con el patrón `IMessagingAdapter` ya usado en OmniCatalog).

---

## **4. EL CONTRATO CANÓNICO UNIVERSAL**

Todo evento comercial (venta, cobro, compra, transferencia) se emite como un DTO agnóstico vía BullMQ, con namespace de eventos estable (`CREATE_INVOICE_MOVE`, `CREATE_PAYMENT_MOVE`, `CREATE_STOCK_MOVE`, `CREATE_PARTNER`, etc.) y versión de contrato explícita (`"version": "1.0"`).

```json
{
  "event": "CREATE_INVOICE_MOVE",
  "version": "1.0",
  "tenant_id": "empresa_cde_01",
  "payload": {
    "partner_id": 1042,
    "partner_external_ids": { "odoo_id": 887, "sap_kunnr": null },
    "partner_tax_id": "80012345-6",
    "journal_code": "POS_INV",
    "move_type": "out_invoice",
    "date": "2026-08-27",
    "invoice_date_due": "2026-09-26",
    "payment_type": "credit",
    "currency_code": "PYG",
    "fiscal_number": "001-001-0004589",
    "sifen_cdc": "01800123456001001000458912026082612345678901",
    "lines": [
      { "account_code": "4.1.1.01", "description": "Venta de mercaderías", "debit": 0, "credit": 1000000, "tax_code": "IVA_10", "tax_amount": 90909 }
    ],
    "receivable_line": { "account_code": "1.1.2.01", "debit": 1000000, "credit": 0 }
  }
}
```

- **Adaptador Odoo:** traduce el DTO a una llamada XML-RPC/JSON-RPC para crear y validar un `account.move`.
- **Adaptador OmniLedger:** hace `POST /api/v1/moves` directo al microservicio FastAPI.
- **Idempotencia por `tenant_id` + `event` + `fiscal_number`**, crítica cuando un mismo tenant tiene más de un conector activo simultáneamente (modo `hybrid_active`, ver sección 6).

---

## **5. CASO DE USO CRÍTICO: VENTA A CRÉDITO EN PDV**

1. Cajero verifica saldo/límite de crédito, emite venta a 30 días en OmniFlow POS.
2. FacturaSend API timbra la factura legal (CDC, QR, KUDE) — la fiscalidad nunca toca al backend contable.
3. Se encola `CREATE_INVOICE_MOVE`; el Integration Worker hace fan-out al/los conector(es) activo(s) del tenant.
4. Asiento atómico: DÉBITO Cuentas por Cobrar / CRÉDITO Ventas / CRÉDITO IVA Débito Fiscal.
5. Cobro posterior de cuota: `CREATE_PAYMENT_MOVE` — DÉBITO Caja / CRÉDITO Cuentas por Cobrar, saldo del partner actualizado en tiempo real, sin depender del cierre de caja diario (limitación nativa de Odoo CE que este flujo supera).

---

## **6. MODO DE TRANSICIÓN POR TENANT**

| Estado | Comportamiento |
|---|---|
| `legacy_only` | Todo el tráfico contable va al conector legacy (Odoo/SAP/etc.). |
| `hybrid_shadow` | Se envía al legacy (fuente de verdad) y se replica en OmniLedger solo para comparación/auditoría, sin exponerse al cliente. |
| `hybrid_active` | Ciertos flujos (ej. crédito en POS) ya corren en OmniLedger; el resto sigue en el legacy. Requiere reconciliación periódica explícita. |
| `omniledger_only` | Migración completa. El adaptador legacy queda desconectado pero **no eliminado del código** — puede reactivarse. |
| `native_only` | Tenant nuevo sin ERP previo, opera 100% sobre OmniLedger desde el día uno — no hay "migración" involucrada. |

El enrutamiento se resuelve por tenant y por tipo de evento en el Integration Worker (tabla `integrations`, ya implementada con el enum `IntegrationType`).

---

## **7. CRONOGRAMA ÚNICO (resuelve la discrepancia de fechas entre versiones anteriores)**

```
Sprint 0 (Sem. 1-2, sep 2026):    Scaffolding FastAPI + AsyncPG + Alembic + RLS base
Fase 1  (Sem. 3-4, sep-oct 2026): Modelo de datos completo (8 tablas) + migraciones
Fase 2  (Sem. 5-6, oct 2026):     Motor de partida doble + validación atómica
Fase 3  (Sem. 7-8, oct-nov 2026): Endpoints REST + cuentas corrientes/crédito POS
Fase 4  (Sem. 9-10, nov 2026):    Motor de impuestos + libros fiscales (Ventas/Compras)
Fase 5  (Sem. 11-12, dic 2026):   Suite de tests de paridad con Odoo CE (Pytest)
Fase 6  (ene-feb 2027):           Integración dual-write / hybrid_shadow con tenant piloto
Fase 7  (mar 2027):               hybrid_active en tenant piloto, verificación de paridad sostenida
```

Los conectores SAP/Dynamics/Oracle **no tienen fecha asignada todavía** — quedan en el backlog de la Sección 3 hasta que haya un cliente concreto que los demande; no se planifican especulativamente.

---

## **8. MATRIZ DE RIESGOS**

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Discrepancias de redondeo IVA/moneda | Media | Alto | Portar `test_account_move.py` de Odoo a Pytest; usar `Decimal` + redondeo half-even en todo el motor |
| Pérdida de asientos durante la transición | Baja | Crítico | Buffer persistente BullMQ con reintentos exponenciales y DLQ |
| Migración de datos históricos | Baja | Medio | Mismo modelo relacional (`account_move`/`account_move_line`) permite migración directa vía SQL |
| Mapeo de cuentas incompleto al activar un tenant | Alta | Alto | Checklist de cobertura obligatorio antes de pasar a `hybrid_active` (tabla `account_mapping_rules`) |
| Divergencia en `hybrid_active` sin reconciliación | Media | Alto | Job de reconciliación periódico + alertas de discrepancia por tenant |
| Documentación desincronizada del código real | **Alta (ya observado)** | Alto | Este documento es la única fuente de verdad estratégica; el estado real de implementación se audita contra el repo, no contra el README del servicio |

---

## **9. REGLAS DE ORO (consolidadas)**

1. **FacturaSend es soberano en fiscalidad** — ninguna lógica de firma digital, CDC o timbrado se programa en ningún conector contable.
2. **Validación atómica inquebrantable** — todo conector rechaza asientos donde ∑Débitos ≠ ∑Créditos, `HTTP 422` antes de persistir.
3. **Inmutabilidad contable** — un asiento `posted` no se edita; toda corrección es un *reversal move*.
4. **Desacoplamiento absoluto vía colas** — ninguna indisponibilidad de un conector destino frena una venta o cobro en el POS.
5. **Persistencia de la arquitectura de conectores** — ningún adaptador se elimina del código una vez construido; puede desactivarse, nunca borrarse.
6. **Este roadmap es único** — cualquier cambio de arquitectura, alcance o fecha se versiona en este mismo documento.

---

## **10. SINCRONIZACIÓN CON EL PROTOCOLO AGENTS.md**

Al avanzar cualquier fase de este roadmap, actualizar en el mismo paso: `VERSION`, `ROADMAP.md`, `CHANGELOG.md`, `docs/02-architecture.md`, el manifiesto correspondiente y la Wiki en `/opt/wiki/orderflow/`. El Feature ID de `featurelist.json` para OmniLedger debe **verificarse contra el archivo real antes de reservarse** — la última verificación (27 ago 2026) indicaba `FEAT-105` como próximo libre (`FEAT-088` ya está tomado por "OmniCatalog: Categorías POS"); reconfirmar si pasó tiempo desde entonces.
