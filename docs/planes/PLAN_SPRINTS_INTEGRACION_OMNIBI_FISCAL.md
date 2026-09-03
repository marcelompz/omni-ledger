# **🚀 PLAN MAESTRO DE SPRINTS: INTEGRATION WORKER, PIPELINE OMNIBI Y PLUGIN FISCAL DNIT**

> **Documento:** `docs/planes/PLAN_SPRINTS_INTEGRACION_OMNIBI_FISCAL.md`  
> **Fecha de creación:** 3 de septiembre de 2026  
> **Estado:** Listo para ejecución técnica  
> **Referencias:**

> - `OmniFlow_Arquitectura_Comparativa_ERP.md` (Tesis de las Cuatro Verdades)  
> - `ARQUITECTURA_TRES_CAPAS_OMNILEDGER_OMNIBI.md` (Core NIIF, Satélite Fiscal y Hub BI)  
> - `ROADMAP_ODOO_TO_FASTAPI_TRANSITION.md` (Estrategia de Conmutación Odoo ➔ FastAPI)

---

## **1\. Visión Holística del Plan**

Este plan operacionaliza la transición hacia la **Enterprise Composable Architecture** de OmniFlow, dividiendo el desarrollo en **4 Sprints de 2 semanas (8 semanas totales)**.

Cada sprint avanza en paralelo sobre los tres tracks estratégicos asegurando que los contratos y dependencias entre capas permanezcan perfectamente sincronizados:

┌─────────────────────────────────────────────────────────────────────────────────────────┐

│ TRACK 1: THE AGNOSTIC BRIDGE (Integration Worker BullMQ / Redis)                        │

│ Desacopla la operación física (OmniFlow) de la persistencia contable (Odoo / OmniLedger)│

├─────────────────────────────────────────────────────────────────────────────────────────┤

│ TRACK 2: THE DECISION PIPELINE (OmniBI Async Stream & Simulation)                       │

│ Ingesta asíncrona de alto rendimiento y motores What-If (LIFO, Reposición, Menú)        │

├─────────────────────────────────────────────────────────────────────────────────────────┤

│ TRACK 3: THE SATELLITE FISCAL ENGINE (Plugin DNIT / Paraguay)                           │

│ Proyecciones de solo lectura, SIFEN, Libros IVA y Conciliación Extracontable NIIF/Fiscal │

└─────────────────────────────────────────────────────────────────────────────────────────┘

---

## **2\. Mapa de Dependencias entre Tracks y Sprints**

| Sprint | Track 1: Integration Worker (Event Bridge) | Track 2: Pipeline OmniBI (Analytics) | Track 3: Plugin Fiscal DNIT (Paraguay) |
| :---- | :---- | :---- | :---- |
| **Sprint 1** | Especificación de DTOs canónicos y adaptador dual (Odoo XML-RPC / Mock Ledger). | Definición de contratos de lectura de Kardex contable e interfaz de eventos BI. | Creación de tabla satélite `l10n_py_fiscal_moves` y DTO `FiscalPayload`. |
| **Sprint 2** | Conmutador dinámico Odoo ➔ FastAPI Ledger e inyección atómica de asientos. | Endpoints de streaming/keyset pagination (`/analytics/kardex-feed`) en FastAPI. | Vistas de proyección para Libro Ventas y Libro Compras IVA (Ley 6380). |
| **Sprint 3** | Idempotencia con claves Redis, reintentos exponenciales y Dead Letter Queue (DLQ). | Motores de simulación What-If LIFO, Costo de Reposición y Menu Engineering en TS. | Generador oficial de archivo RG90 y motor de conciliación libro vs. fiscal. |
| **Sprint 4** | Benchmark de latencia (\<10ms por asiento) y pruebas de desconexión Odoo. | Optimización con réplicas de lectura / vistas materializadas para analítica. | Pruebas de homologación fiscal y auditoría cruzada NIIF vs. Marangatu. |

---

## **3\. Desglose Detallado por Sprints**

### ***═══════════════════════════════════════════════════════════***

### ***SPRINT 1: Cimientos de Eventos y Contratos Satélites***

**Duración:** Semanas 1 y 2  
**Objetivo:** Establecer los contratos de datos canónicos, aislar el payload fiscal en origen y preparar el worker para despacho agnóstico.

### ***═══════════════════════════════════════════════════════════***

#### **Track 1: Integration Worker (Agnostic Event Bridge)**

* **Historia de Usuario 1.1:** Como sistema OmniFlow, necesito emitir eventos de venta, cobro y anulación en formato canónico hacia Redis/BullMQ sin acoplarme al motor contable de destino.  
* **Entregables Técnicos:**  
  1. Definición del paquete `@omniflow/canonical-events` con esquemas TypeScript estrictos:  
     - `CREATE_INVOICE_MOVE` (Venta contado / crédito).  
     - `CREATE_PAYMENT_MOVE` (Cobranza y aplicación a factura).  
     - `REVERSE_MOVE` (Notas de crédito y cancelaciones).  
  2. Implementación de la interfaz `ILedgerAdapter`:  
     export interface ILedgerAdapter {

       postInvoiceMove(event: CanonicalInvoiceEvent): Promise\<LedgerResponse\>;

       postPaymentMove(event: CanonicalPaymentEvent): Promise\<LedgerResponse\>;

       reverseMove(moveId: string, reason: string): Promise\<LedgerResponse\>;

     }

  3. `OdooXmlRpcAdapter`: Implementación del adaptador que traduce el evento canónico a llamadas `execute_kw('account.move', 'create', ...)` en Odoo CE.  
  4. `FastApiLedgerAdapter (Stub)`: Cliente HTTP preparado con Axios/Fetch para apuntar a OmniLedger.

#### **Track 2: Pipeline OmniBI (Analytics Core)**

* **Historia de Usuario 2.1:** Como arquitecto de datos, necesito definir el modelo de kardex analítico desnormalizado para que OmniBI pueda simular costos sin sobrecargar el ledger contable.  
* **Entregables Técnicos:**  
  1. Especificación del contrato `InventoryMovementRaw` y `KardexLineDTO`.  
  2. Diseño de la topología de ingesta en OmniBI: Consumo asíncrono de eventos `INVENTORY_VALUATION_MOVE` emitidos tras el commit en el ledger.  
  3. Estructura de almacenamiento en OmniBI: Cache analítico en Redis / SQLite en memoria para procesar pilas de simulación LIFO sin golpear la base de datos principal.

#### **Track 3: Plugin Fiscal DNIT (Paraguay)**

* **Historia de Usuario 3.1:** Como contador en Paraguay, necesito que los datos específicos de SIFEN y DNIT (CDC de 44 dígitos, timbrado, tipo de comprobante) se capturen sin modificar la tabla `account_moves`.  
* **Entregables Técnicos:**  
  1. Migración Alembic `002_l10n_py_fiscal.py` creando `l10n_py_fiscal_moves` con clave foránea 1:1 a `account_moves.id` y Row Level Security por `tenant_id`.  
  2. Definición del DTO `PyFiscalPayload`:  
     class PyFiscalPayload(BaseModel):

         is\_electronic: bool \= False

         cdc: Optional\[str\] \= Field(None, min\_length=44, max\_length=44)

         stamped: str

         stamped\_date\_due: Optional\[date\] \= None

         fiscal\_number: str

         invoice\_condition: Literal\["CONTADO", "CREDITO"\]

         receipt\_type\_code: str  \# Ej: '109' Factura Electrónica

  3. Hook de persistencia satélite en FastAPI: Si `fiscal_payload` está presente en `AccountMoveCreateDTO`, se inserta en `l10n_py_fiscal_moves` dentro de la misma transacción atómica de base de datos.

---

### ***═══════════════════════════════════════════════════════════***

### ***SPRINT 2: Conmutación en Caliente y Streaming de Datos***

**Duración:** Semanas 3 y 4  
**Objetivo:** Conectar el Integration Worker directamente a OmniLedger FastAPI y habilitar la extracción de datos de alta velocidad para OmniBI.

### ***═══════════════════════════════════════════════════════════***

#### **Track 1: Integration Worker (Agnostic Event Bridge)**

* **Historia de Usuario 1.2:** Como operador del sistema, necesito conmutar el destino contable de un tenant de Odoo CE a OmniLedger mediante una variable de configuración sin detener el POS.  
* **Entregables Técnicos:**  
  1. Patrón Factory para selección dinámica del adaptador en el worker basado en `tenant_config.ledger_backend` (`ODOO_CE` | `FASTAPI_LEDGER`).  
  2. Implementación completa de `FastApiLedgerAdapter`: Llamada asíncrona a `POST /api/v1/moves` con autenticación Bearer Token y cabecera de aislamiento `X-Tenant-ID`.  
  3. Mapeo automático de errores de desbalanceo contable: Manejo del error HTTP 422 de FastAPI (Partida Doble desbalanceada) con logs de diagnóstico detallados.

#### **Track 2: Pipeline OmniBI (Analytics Core)**

* **Historia de Usuario 2.2:** Como analista de negocio, necesito extraer masivamente los movimientos históricos de inventario y costos desde OmniLedger con latencia mínima.  
* **Entregables Técnicos:**  
  1. Endpoint en FastAPI con Keyset Pagination: `GET /api/v1/analytics/kardex-feed?after_id={cursor}&limit=1000`  
     - Optimizado con índices compuestos en PostgreSQL: `(tenant_id, product_sku, date, id)`.  
     - Serialización directa con ujson/orjson sin pasar por ORM pesado.  
  2. Cliente de sincronización incremental en Node.js para OmniFlow Hub que almacena el último `cursor_id` procesado.

#### **Track 3: Plugin Fiscal DNIT (Paraguay)**

* **Historia de Usuario 3.2:** Como auditor fiscal, necesito generar el Libro IVA Ventas y Libro IVA Compras según las especificaciones de la Ley 6380 combinando datos del Core y de la tabla satélite.  
* **Entregables Técnicos:**  
  1. Implementación de `ParaguayFiscalReportingService`:  
     - Endpoint `GET /api/v1/plugins/py/reports/libro-ventas`.  
     - Endpoint `GET /api/v1/plugins/py/reports/libro-compras`.  
  2. Consulta SQL optimizada mediante `JOIN` de solo lectura entre `account_moves`, `account_move_lines` y `l10n_py_fiscal_moves`.  
  3. Mapeo de discriminación de IVA (10%, 5% y Exento) a partir del `tax_code` de las líneas de asiento contable.

---

### ***═══════════════════════════════════════════════════════════***

### ***SPRINT 3: Resiliencia, Simulaciones What-If y RG90***

**Duración:** Semanas 5 y 6  
**Objetivo:** Blindar la tolerancia a fallos del bus de eventos, ejecutar simulaciones analíticas complejas en OmniBI y exportar archivos tributarios oficiales.

### ***═══════════════════════════════════════════════════════════***

#### **Track 1: Integration Worker (Agnostic Event Bridge)**

* **Historia de Usuario 1.3:** Como DevOps, requiero que ningún evento contable se pierda ante caídas de base de datos o indisponibilidad de la red.  
* **Entregables Técnicos:**  
  1. Claves de Idempotencia en Redis: `idempotency:{tenant_id}:{event_id}` con TTL de 7 días para evitar asientos duplicados por reintentos de red.  
  2. Estrategia de reintentos exponenciales con Jitter (Backoff exponencial: 1s, 5s, 30s, 2m, 10m).  
  3. Cola de Fallas (Dead-Letter Queue \- DLQ): Captura de eventos fallidos con interfaz de inspección y re-encolado manual.

#### **Track 2: Pipeline OmniBI (Analytics Core)**

* **Historia de Usuario 2.3:** Como director comercial, quiero comparar el margen de contribución real bajo NIIF (CPP) frente a un escenario simulado LIFO y costo de reposición.  
* **Entregables Técnicos:**  
  1. Implementación de `OmniBiSimulationEngine` en TypeScript:  
     - Algoritmo de vaciado de pila LIFO sobre el kardex desnormalizado.  
     - Estimador de Costo de Reposición (*Replacement Cost* basado en última orden de compra aprobada).  
  2. Matriz de *Menu Engineering* (Matriz Boston Consulting Group adaptada a gastronomía/retail):  
     - Clasificación cuadrante: Estrellas, Caballos de batalla, Rompecabezas y Perros.  
  3. Dashboard reactivo en OmniFlow Front-Office con comparativa de márgenes: `Margen Real NIIF` vs. `Margen LIFO Inflacionario`.

#### **Track 3: Plugin Fiscal DNIT (Paraguay)**

* **Historia de Usuario 3.3:** Como responsable tributario, necesito generar el archivo electrónico de comprobantes RG90 para su importación directa en el sistema Marangatu de la DNIT.  
* **Entregables Técnicos:**  
  1. Generador de archivo zip/csv RG90: Formato oficial de 16 campos normalizados (Tipo Comprobante, RUC/Cédula, Razón Social, Imputación IVA/IRE/IRP, Base Gravada 10%, Base Gravada 5%, Exentas).  
  2. Motor de Conciliación Libro vs. Fiscal:  
     - Informe de divergencias temporarias (ej. depreciaciones aceleradas admitidas fiscalmente pero no por NIIF).  
     - Validación de retenciones aplicadas vs. comprobantes de retención recibidos.

---

### ***═══════════════════════════════════════════════════════════***

### ***SPRINT 4: Hardening, Rendimiento Extremo y Certificación***

**Duración:** Semanas 7 y 8  
**Objetivo:** Pruebas de carga, verificación de inmutabilidad, auditoría cruzada NIIF y documentación para pase a producción.

### ***═══════════════════════════════════════════════════════════***

#### **Track 1: Integration Worker (Agnostic Event Bridge)**

* **Historia de Usuario 1.4:** Como arquitecto técnico, necesito certificar que el endpoint `POST /api/v1/moves` de OmniLedger procesa transacciones en \<10ms bajo alta carga.  
* **Entregables Técnicos:**  
  1. Pruebas de carga con k6 / Locust: 1,000 asientos por minuto concurrentes simulando horas pico de salones y sucursales POS.  
  2. Verificación de aislamiento estricto de multitenancy mediante PostgreSQL Row-Level Security (RLS).  
  3. Validación de apagado definitivo del conector Odoo CE para tenants certificados en OmniLedger.

#### **Track 2: Pipeline OmniBI (Analytics Core)**

* **Historia de Usuario 2.4:** Como analista BI, necesito ejecutar simulaciones anuales sin degradar las conexiones transaccionales del POS ni del Ledger.  
* **Entregables Técnicos:**  
  1. Configuración de réplica de lectura (Read Replica) en PostgreSQL dedicada exclusivamente a queries de OmniBI.  
  2. Vistas materializadas autolimpiables para agregaciones mensuales y trimestrales.  
  3. Pruebas de consistencia de datos entre el resultado contable oficial de OmniLedger y las métricas sintetizadas en OmniBI.

#### **Track 3: Plugin Fiscal DNIT (Paraguay)**

* **Historia de Usuario 3.4:** Como auditor legal, necesito verificar que ningún reporte fiscal altere los balances del Libro Mayor y que los archivos RG90 sean aceptados por Marangatu.  
* **Entregables Técnicos:**  
  1. Auditoría de solo lectura: Verificación formal de que los roles de base de datos de los plugins fiscales carecen de privilegios `INSERT`, `UPDATE` o `DELETE` sobre las tablas canónicas del Core.  
  2. Homologación de prueba de carga de archivos RG90 en el ambiente de prueba de la DNIT.  
  3. Suite de tests unitarios y de integración para validación cruzada: `∑ Débito Fiscal IVA Libro Ventas == Saldo Cuenta Pasivo IVA Débito en OmniLedger`.

---

## **4\. Definición de Hecho (Definition of Done \- DoD) General**

Para que cualquier historia de usuario de los tres tracks se considere completada, debe cumplir:

2. **Contrato Tipado:** Esquemas Pydantic v2 (Python) o interfaces TypeScript estrictas sin uso de `any`.  
3. **Cero Polución Contable:** Ningún campo fiscal o analítico debe persistir en las tablas raíz de `OmniLedger`.  
4. **Inmutabilidad Respetada:** Prohibido el uso de `UPDATE` sobre asientos en estado `posted`. Toda corrección debe ser testeada mediante `reverse_move`.  
5. **Pruebas Automatizadas:** Mínimo 85% de cobertura en tests unitarios para validadores matemáticos de partida doble y algoritmos LIFO.  
6. **Aislamiento Multi-Tenant:** Toda consulta debe filtrar explícitamente o via RLS por `tenant_id`.

---

## **5\. Cuadro de Mando de Hitos y Entregables**

Semana 2 (Sprint 1 DoD) ────────▶ Contratos Canónicos listos \+ Migración l10n\_py satélite

Semana 4 (Sprint 2 DoD) ────────▶ Conmutador Odoo/FastAPI operativo \+ Feed de Kardex OmniBI

Semana 6 (Sprint 3 DoD) ────────▶ Motor LIFO/Menú en TS \+ Generador oficial RG90 DNIT

Semana 8 (Sprint 4 DoD) ────────▶ Certificación de carga \<10ms \+ Auditoría NIIF/Fiscal aprobada

