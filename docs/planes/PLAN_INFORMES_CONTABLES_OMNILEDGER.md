# **📊 PLAN: INFORMES CONTABLES DINÁMICOS EN OMNILEDGER**

> **Documento:** `docs/planes/PLAN_INFORMES_CONTABLES_OMNILEDGER.md`
> **Versión:** 1.0
> **Fecha:** 27 de agosto de 2026
> **Extiende:** `ROADMAP_OMNILEDGER_MAESTRO.md` (v4.0), Fase 4 — "Motor de impuestos + libros fiscales"
> **Depende de:** `PLAN_IMPLEMENTACION_OMNILEDGER.md` (v2.0), Sección 3 (modelo de datos)

---

## **1. CONTEXTO Y OBJETIVO**

Hoy los informes contables se emiten desde Odoo Enterprise Edition. Crossnexion está migrando esos informes a Odoo CE, pero por ahora solo `RG90` (registro electrónico de comprobantes de la SET vía Marangatú, Resolución General 90/2021) está disponible en CE. El resto de los informes que hoy dependen de EE queda sin fecha cierta de migración.

**Objetivo de este plan:** construir en OmniLedger, en paralelo a esa migración, la generación de informes contables — empezando por `RG90` porque ya tiene una especificación validada y disponible en CE — para reducir la dependencia de Odoo (CE o EE) en la parte de generación de informes, no solo en la de asientos.

**Objetivo secundario, igual de importante:** resolver el problema de fondo que hizo doloroso este trabajo en Odoo — el etiquetado manual de cuentas contables para poder armar fórmulas de informes — con un mecanismo que no requiera tocar cada cuenta una por una.

---

## **2. DOS FAMILIAS DE INFORMES, DOS MECANISMOS DISTINTOS**

No todos los "informes contables" tienen la misma naturaleza, y tratarlos con el mismo motor es lo que probablemente generó parte de la fricción original en Odoo. Conviene separarlos desde el diseño:

### **2.1. Informes transaccionales / regulatorios** (ej. `RG90`, Libro IVA Ventas/Compras)
Son **listados de comprobantes**, no agregaciones contables — cada fila es una factura/nota de crédito real con sus columnas fiscales (RUC, timbrado, CDC, fecha, montos por tasa de IVA). No necesitan fórmulas ni jerarquía de cuentas: es una consulta directa y bien definida sobre `account_moves` + `account_move_lines`, filtrada por diario y período, mapeada a las columnas exactas que exige el formato regulatorio (Marangatú, en el caso de RG90).

### **2.2. Informes financieros agregados** (Balance General, Estado de Resultados, Balance de Comprobación)
Son **agregaciones jerárquicas de cuentas** con fórmulas entre grupos ("Utilidad Bruta = Ingresos − Costo de Ventas"). Acá es donde el etiquetado manual dolía en Odoo, y donde vale la pena invertir en un mecanismo mejor.

Esta separación evita construir un motor de fórmulas genérico para algo (RG90) que en realidad es solo una consulta con formato de exportación fijo.

---

## **3. INFORME RG90 — PRIMER ENTREGABLE**

### **3.1. Qué exige realmente**
Según la Resolución General 90/2021 de la SET: registro electrónico de todos los comprobantes de ingresos, egresos, compras y ventas en el sistema Marangatú, ya sea por carga manual o por **importación de un archivo** (reemplaza a Hechauka/Aranduka). La información registrada tiene carácter de declaración jurada, y toda confirmación tardía es sancionable — por lo que la generación automática y confiable de este archivo tiene valor directo (evita multas por atraso o inconsistencia).

### **3.2. Fuente de la especificación exacta**
No conviene inferir el layout de columnas del archivo de memoria — hay que extraerlo de una fuente confiable, siguiendo la misma decisión ya tomada para el resto de la localización paraguaya:

1. **Prioridad 1:** el módulo CE que Crossnexion ya migró para RG90 — es la especificación más actualizada y ya validada en producción por otro equipo. Pedirles el mapeo de campos o el propio código del módulo si es accesible.
2. **Prioridad 2:** `../odoo-l10n-py` (ya definido como fuente de solo lectura en el plan de implementación) — buscar ahí el módulo de localización que genera el archivo de Marangatú.
3. **Prioridad 3:** documentación oficial de la SET/Marangatú, si las dos anteriores no alcanzan para casos borde (notas de crédito, comprobantes sin nominación, etc.)

### **3.3. Implementación**
- Nuevo endpoint: `GET /api/v1/reports/rg90?periodo=YYYY-MM&tipo=compras|ventas`
- Consulta directa sobre `account_moves`/`account_move_lines` del período, sin necesidad de motor de fórmulas.
- Exportación en el formato de importación de Marangatú (a confirmar el formato exacto — CSV/Excel — contra la fuente de la sección 3.2).
- Este informe **no depende de la Sección 4** (motor de reportes dinámicos) — puede construirse primero y de forma independiente.

---

## **4. MOTOR DE INFORMES FINANCIEROS DINÁMICOS — LA PARTE QUE RESUELVE EL DOLOR DE ODOO**

### **4.1. Por qué el etiquetado manual fue tan costoso**
En Odoo, cada cuenta contable necesita una o más etiquetas (`account.account.tag`) asignadas a mano, y cada línea de informe referencia esas etiquetas en su fórmula. El costo no es poner una etiqueta — es que **cada cuenta nueva que se crea después** hay que recordar etiquetarla también, o el informe queda incompleto silenciosamente. Es un sistema que no se auto-mantiene.

### **4.2. Mecanismo propuesto: jerarquía como mecanismo por defecto, etiquetas como excepción**

`account_accounts` ya tiene `parent_id` y `level` en el modelo (Sección 3 del plan de implementación) — esa jerarquía ya existe y hoy no se está aprovechando para informes. La propuesta:

1. **Por defecto, toda línea de informe se define sobre un nodo del árbol de cuentas, no sobre una lista de cuentas etiquetadas.** Ej.: "Ventas Netas" = suma de todo lo que cuelga del nodo `4.1` (Ingresos por Ventas), recursivamente. Una cuenta nueva creada bajo `4.1.05` se incluye automáticamente en el informe sin tocar nada — el mantenimiento cero es el punto central de este diseño.
2. **Filtros por patrón de código como alternativa** cuando la jerarquía no alcanza (ej. "todas las cuentas que empiezan con `4.1.` pero no `4.1.09`"): expresión de código (prefijo + exclusiones), evaluada en el momento de generar el informe, no mantenida como asignación estática por cuenta.
3. **Etiquetas (`account_tags`) solo para los casos que de verdad no se resuelven con jerarquía ni patrón** — por ejemplo, una cuenta que debe aparecer en dos informes distintos con roles distintos (activo corriente en el Balance, y además en un informe gerencial de liquidez). Esta es la minoría de los casos, no la mecánica principal como era en Odoo.
4. **Fórmulas entre líneas, no solo entre cuentas**: una línea de informe puede referenciar el resultado de otra línea ya calculada (`Utilidad Bruta = [Ventas Netas] - [Costo de Ventas]`), evitando repetir la definición de qué cuentas entran en cada cálculo.

### **4.3. Modelo de datos nuevo**

| Tabla | Contenido |
|---|---|
| `report_templates` | Definición de un informe (nombre, tipo: balance/resultado/comprobación, versión, tenant_id) |
| `report_lines` | Líneas del informe, ordenadas, con su tipo de fuente: `hierarchy_node` \| `code_pattern` \| `tag` \| `line_reference` |
| `report_line_sources` | El valor concreto de la fuente por línea (el `account_id` raíz, el patrón de código, el `tag_id`, o el `line_id` referenciado) |
| `report_snapshots` | Informes generados y guardados (período, valores calculados, fecha de generación) — para no tener que recalcular históricos cada vez que se consultan |

Esto se agrega como una extensión de la Fase 4 del plan de implementación, no reemplaza nada de lo ya definido en las 8 tablas base.

### **4.4. Constructor de informes (para que dejes de memorizar fórmulas)**
En vez de escribir fórmulas de memoria, la interfaz de construcción debería permitir:
- Seleccionar un nodo del árbol de cuentas visualmente y que la línea se arme sola con ese nodo como fuente.
- Ver en vivo qué cuentas caen dentro de un patrón de código antes de guardarlo (evita descubrir el error meses después, al cerrar un balance).
- Clonar un `report_template` existente como punto de partida de uno nuevo, en vez de empezar de cero.

Esto es más una decisión de UX/frontend que de backend — vale la pena que quede anotado acá para cuando se diseñe esa pantalla, pero no bloquea la Fase 4 del backend.

### **4.5. Endpoints nuevos**
- `POST /api/v1/report-templates` — crear/versionar una definición de informe
- `GET /api/v1/report-templates/{id}/preview?periodo=YYYY-MM` — calcular sin guardar (para validar antes de confirmar)
- `POST /api/v1/report-templates/{id}/generate?periodo=YYYY-MM` — generar y guardar en `report_snapshots`
- `GET /api/v1/reports/balance-general?periodo=YYYY-MM`
- `GET /api/v1/reports/estado-resultados?periodo=YYYY-MM`

(Estos dos últimos son casos particulares de `report_templates` con nombre reservado, para no obligar a reconstruirlos desde cero en cada tenant nuevo — se pueden clonar de una plantilla base.)

---

## **5. PRIORIZACIÓN**

1. **RG90** (Sección 3) — independiente, especificación ya validada externamente, valor inmediato (evita depender de Odoo CE/EE para esta obligación regulatoria puntual).
2. **Modelo de datos del motor de informes** (Sección 4.3) — se puede construir en paralelo a RG90, no depende de él.
3. **Balance General / Estado de Resultados como primeras plantillas reales** sobre el motor nuevo — validan el mecanismo de jerarquía + patrón antes de dar por buena la Sección 4.2.
4. **Constructor visual** (Sección 4.4) — última prioridad, es la capa de UX sobre un motor ya probado con datos reales.

---

## **6. RIESGO A VIGILAR**

El mecanismo de jerarquía (4.2.1) asume que el plan de cuentas está bien estructurado en árbol desde el día uno — si en algún tenant las cuentas se crearon planas o con una jerarquía inconsistente, el mecanismo por defecto no va a funcionar bien y se va a terminar recurriendo a etiquetas para todo, reproduciendo el mismo problema que se quiere evitar. Vale la pena que la validación de cobertura que ya está prevista en `account_mapping_rules` (Fase 1) incluya también una verificación de integridad jerárquica del plan de cuentas antes de activar el motor de informes para un tenant.
