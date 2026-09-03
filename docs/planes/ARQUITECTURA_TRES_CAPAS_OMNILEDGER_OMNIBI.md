# **🏛️ ARQUITECTURA TRES CAPAS: OMNILEDGER CORE, PLUGINS FISCALES Y OMNIBI HUB**

> **Documento:** `docs/planes/ARQUITECTURA_TRES_CAPAS_OMNILEDGER_OMNIBI.md`  
> **Estado:** Aprobado para implementación  
> **Referencia:** Extensión de `ROADMAP_OMNILEDGER_MAESTRO.md` y `PLAN_IMPLEMENTACION_OMNILEDGER.md`

---

## **1\. Topología y Flujo Unidireccional de Datos**

El sistema divide el tratamiento financiero, fiscal y comercial en tres contextos estrictamente delimitados. La regla cardinal es la **unidireccionalidad**: la Capa 1 es la única fuente de verdad contable y jamás recibe retroescritura de las capas satélite.

┌─────────────────────────────────────────────────────────────────────────┐

│              CAPA 1: CORE OMNILEDGER (NIIF / Ledger Inmutable)          │

│  \- Fuente única de verdad contable y financiera (General Ledger).        │

│  \- Estricta partida doble: ∑ Débitos \= ∑ Créditos (Rechazo HTTP 422).   │

│  \- Inmutabilidad post-posted: Solo corrección vía Reversal Moves.       │

│  \- NIC 2: FIFO, CPP e Identificación Específica (Bloqueo total de LIFO).│

└────────────────────────────────────┬────────────────────────────────────┘

                                     │

                         Flujo Unidireccional (Read-Only)

                                     │

         ┌───────────────────────────┴───────────────────────────┐

         ▼                                                       ▼

┌──────────────────────────────────────┐ ┌──────────────────────────────────────┐

│  CAPA 2: PLUGINS FISCALES DE PAÍS    │ │    CAPA 3: OMNIBI HUB (OmniFlow)     │

│  \- Proyecciones de cumplimiento ley. │ │  \- Inteligencia comercial y margen.  │

│  \- Tablas satélite (l10n\_py\_\*).      │ │  \- Simulaciones What-If (LIFO, etc.).│

│  \- SIFEN (CDC, timbrados), IVA, RG90.│ │  \- Menu Engineering y Costo Reposic. │

│  \- Conciliación Libro vs. Fiscal.    │ │  \- Sin restricciones normativas NIIF.│

│  \- Salida: Libros y DDJJ oficiales.  │ │  \- Salida: Dashboards y decisiones.  │

└──────────────────────────────────────┘ └──────────────────────────────────────┘

---

## **2\. Definición de Capas**

### ***Capa 1: Core OmniLedger (NIIF / Ledger Inmutable)***

- **Rol:** Única fuente de verdad contable auditable.  
- **Reglas:**  
  - Partida doble atómica: $\\sum \\text{Débitos} \= \\sum \\text{Créditos}$ obligatoria (`HTTP 422` ante descuadres).  
  - Cumplimiento estricto de NIC 2: Soporta FIFO, CPP (Costo Promedio Ponderado) e Identificación Específica por categoría o ítem.  
  - Bloqueo absoluto de UEPS/LIFO a nivel de esquema Pydantic.  
  - Inmutabilidad: Asientos en estado `posted` no admiten `UPDATE` ni `DELETE`. Correcciones solo vía contra-asiento (`POST /api/v1/moves/{id}/reverse`).  
  - Cero contaminación tributaria en las 8 tablas canónicas del ledger.

### ***Capa 2: Plugins Fiscales de País (Proyecciones de Solo Lectura)***

- **Rol:** Cumplimiento tributario local y declaraciones juradas (iniciando con Paraguay: Ley 6380, DNIT, RG90, SIFEN).  
- **Reglas:**  
  - Reside en tablas de extensión satélite (`l10n_py_fiscal_moves`), vinculadas 1:1 por clave foránea a `account_moves`.  
  - Lee los datos contables del Core y los proyecta a formatos fiscales oficiales (Libro Ventas, Libro Compras, ZIP RG90).  
  - Si una normativa tributaria exige un criterio divergente (ej. amortizaciones aceleradas o LIFO fiscal), la capa genera la conciliación extracontable sin alterar los saldos del Core NIIF.  
  - Nunca escribe de vuelta en las tablas centrales.

### ***Capa 3: OmniBI Hub (Inteligencia de Negocios en OmniFlow)***

- **Rol:** Analítica comercial, optimización de márgenes y soporte a decisiones estratégicas.  
- **Reglas:**  
  - No emite estados financieros reglamentarios ni declaraciones juradas; por ende, opera con total libertad metodológica fuera del estándar NIIF.  
  - Ejecuta análisis *What-If* (ej. "¿Qué margen hubiéramos tenido con LIFO vs. el CPP real registrado?").  
  - Modela *Menu Engineering*, costos de reposición y estados de resultados dinámicos.  
  - Consume datos del Core de forma asíncrona (vía API de lectura o eventos BullMQ) sin bloquear las operaciones de caja ni alterar el historial contable.

---

## **3\. Especificaciones de Implementación**

### ***3.1 Esquema Pydantic v2 (FastAPI \- Core NIIF)***

\# src/schemas/move\_dto.py

from datetime import date

from decimal import Decimal, ROUND\_HALF\_EVEN

from enum import Enum

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, model\_validator

class Nic2ValuationMethod(str, Enum):

    FIFO \= "FIFO"

    CPP \= "CPP"  \# Costo Promedio Ponderado

    SPECIFIC \= "SPECIFIC"  \# Bienes no fungibles / serializados

    \# LIFO \= "LIFO" \-\> Prohibido expresamente bajo NIC 2 (Violación NIC 2 párr. 25\)

class AccountMoveLineDTO(BaseModel):

    account\_code: str \= Field(..., max\_length=100)

    partner\_id: Optional\[int\] \= None

    description: Optional\[str\] \= None

    debit: Decimal \= Field(default=Decimal("0.00"), ge=0)

    credit: Decimal \= Field(default=Decimal("0.00"), ge=0)

    product\_sku: Optional\[str\] \= None

    serial\_number: Optional\[str\] \= None

    valuation\_method: Optional\[Nic2ValuationMethod\] \= None

class AccountMoveCreateDTO(BaseModel):

    ref: Optional\[str\] \= Field(None, max\_length=100)

    date: date

    journal\_code: str \= Field(..., max\_length=50)

    description: Optional\[str\] \= None

    partner\_id: Optional\[int\] \= None

    lines: List\[AccountMoveLineDTO\] \= Field(..., min\_length=2)

    fiscal\_payload: Optional\[Dict\[str, Any\]\] \= None

    @model\_validator(mode="after")

    def validate\_core\_integrity(self) \-\> "AccountMoveCreateDTO":

        total\_debit \= sum((l.debit for l in self.lines), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND\_HALF\_EVEN)

        total\_credit \= sum((l.credit for l in self.lines), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND\_HALF\_EVEN)

        if total\_debit \!= total\_credit:

            raise ValueError(

                f"Partida doble desbalanceada: Débito ({total\_debit}) \!= Crédito ({total\_credit}). Diferencia: {abs(total\_debit \- total\_credit)}"

            )

        for line in self.lines:

            if line.valuation\_method \== Nic2ValuationMethod.SPECIFIC and not line.serial\_number:

                raise ValueError(

                    f"Cuenta {line.account\_code}: Requiere 'serial\_number' bajo método SPECIFIC (NIC 2)."

                )

        return self

### ***3.2 Migración Alembic Satélite para Paraguay (l10n\_py\_fiscal\_moves)***

"""add\_l10n\_py\_fiscal\_moves\_extension

Revision ID: 002\_l10n\_py\_fiscal

Revises: 001\_canonical\_core

Create Date: 2026-09-03 10:55:00.000000

"""

from alembic import op

import sqlalchemy as sa

revision \= "002\_l10n\_py\_fiscal"

down\_revision \= "001\_canonical\_core"

branch\_labels \= None

depends\_on \= None

def upgrade() \-\> None:

    op.create\_table(

        "l10n\_py\_fiscal\_moves",

        sa.Column("id", sa.Integer(), nullable=False, primary\_key=True),

        sa.Column(

            "move\_id",

            sa.Integer(),

            sa.ForeignKey("account\_moves.id", ondelete="CASCADE"),

            nullable=False,

            unique=True,

            comment="Vínculo 1:1 con la cabecera del asiento en el Core NIIF",

        ),

        sa.Column("tenant\_id", sa.Integer(), nullable=False, index=True),

        sa.Column("is\_electronic\_invoice", sa.Boolean(), nullable=False, server\_default=sa.text("false")),

        sa.Column("cdc", sa.String(length=44), nullable=True),

        sa.Column("stamped", sa.String(length=50), nullable=False),

        sa.Column("stamped\_date\_due", sa.Date(), nullable=True),

        sa.Column("fiscal\_number", sa.String(length=50), nullable=False),

        sa.Column("invoice\_condition", sa.String(length=10), nullable=False),

        sa.Column("installment\_qty", sa.Integer(), nullable=False, server\_default=sa.text("1")),

        sa.Column("receipt\_type\_code", sa.String(length=20), nullable=False),

        sa.Column("created\_at", sa.DateTime(timezone=True), nullable=False, server\_default=sa.func.now()),

    )

    op.create\_index("ix\_l10n\_py\_fiscal\_moves\_tenant\_cdc", "l10n\_py\_fiscal\_moves", \["tenant\_id", "cdc"\])

    op.create\_index("ix\_l10n\_py\_fiscal\_moves\_tenant\_number", "l10n\_py\_fiscal\_moves", \["tenant\_id", "fiscal\_number"\])

    op.execute("ALTER TABLE l10n\_py\_fiscal\_moves ENABLE ROW LEVEL SECURITY;")

    op.execute(

        """

        CREATE POLICY l10n\_py\_fiscal\_moves\_tenant\_isolation ON l10n\_py\_fiscal\_moves

        FOR ALL

        USING (tenant\_id \= NULLIF(current\_setting('app.current\_tenant\_id', true), '')::integer)

        WITH CHECK (tenant\_id \= NULLIF(current\_setting('app.current\_tenant\_id', true), '')::integer);

        """

    )

def downgrade() \-\> None:

    op.execute("DROP POLICY IF EXISTS l10n\_py\_fiscal\_moves\_tenant\_isolation ON l10n\_py\_fiscal\_moves;")

    op.drop\_index("ix\_l10n\_py\_fiscal\_moves\_tenant\_number", table\_name="l10n\_py\_fiscal\_moves")

    op.drop\_index("ix\_l10n\_py\_fiscal\_moves\_tenant\_cdc", table\_name="l10n\_py\_fiscal\_moves")

    op.drop\_table("l10n\_py\_fiscal\_moves")

### ***3.3 Servicio de Proyección Fiscal Paraguay (FastAPI \- Solo Lectura)***

\# src/plugins/paraguay/service.py

from datetime import date

from typing import List, Dict, Any

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AccountMove, AccountMoveLine

from src.plugins.paraguay.models import L10nPyFiscalMove

class ParaguayFiscalReportingService:

    """Proyecciones de solo lectura para DNIT / Ley 6380 sin alterar el Core."""

    def \_\_init\_\_(self, db: AsyncSession, tenant\_id: int):

        self.db \= db

        self.tenant\_id \= tenant\_id

    async def get\_libro\_ventas(self, date\_from: date, date\_to: date) \-\> List\[Dict\[str, Any\]\]:

        """Genera el Libro IVA Ventas combinando Core NIIF con metadata satélite."""

        query \= (

            select(AccountMove, L10nPyFiscalMove)

            .join(L10nPyFiscalMove, AccountMove.id \== L10nPyFiscalMove.move\_id)

            .where(

                AccountMove.tenant\_id \== self.tenant\_id,

                AccountMove.state \== "posted",

                AccountMove.date \>= date\_from,

                AccountMove.date \<= date\_to,

            )

            .order\_by(AccountMove.date.asc())

        )

        result \= await self.db.execute(query)

        rows \= result.all()

        report\_lines \= \[\]

        for move, fiscal in rows:

            report\_lines.append({

                "fecha": move.date.strftime("%d/%m/%Y"),

                "comprobante": fiscal.fiscal\_number,

                "timbrado": fiscal.stamped,

                "cdc": fiscal.cdc,

                "condicion": fiscal.invoice\_condition,

                "total\_asiento": sum(l.credit for l in move.lines if l.credit \> 0),

            })

        return report\_lines

### ***3.4 Motor Analítico en OmniBI Hub (TypeScript \- Front-Office)***

// omniflow-core/src/omnibi/simulation-engine.ts

export interface InventoryMovementRaw {

  movementId: string;

  sku: string;

  timestamp: string;

  type: 'IN' | 'OUT';

  quantity: number;

  unitCost: number; // Costo histórico de entrada

  priceSold?: number;

}

export interface SimulationResult {

  sku: string;

  quantitySold: number;

  realCmvNIIF: number; // Basado en CPP registrado en Core

  simulatedCmvLIFO: number; // Simulación para análisis gerencial

  marginDelta: number;

  variancePercentage: number;

}

export class OmniBiSimulationEngine {

  /\*\*

   \* Simulación What-If: Calcula la divergencia de margen entre el costo real 

   \* NIIF (Core) y una estimación LIFO para decisiones de precios en alta inflación.

   \*/

  public static simulateLifoMargin(

    movements: InventoryMovementRaw\[\],

    realCmvFromLedger: number

  ): SimulationResult {

    const lifoStack: { qty: number; cost: number }\[\] \= \[\];

    let simulatedCmvLifo \= 0;

    let totalQtySold \= 0;

    for (const mov of movements) {

      if (mov.type \=== 'IN') {

        lifoStack.push({ qty: mov.quantity, cost: mov.unitCost });

      } else if (mov.type \=== 'OUT') {

        let remainingToSell \= mov.quantity;

        totalQtySold \+= mov.quantity;

        // Consumo LIFO: Últimas entradas, primeras salidas (puro uso BI)

        while (remainingToSell \> 0 && lifoStack.length \> 0\) {

          const lastBatch \= lifoStack\[lifoStack.length \- 1\];

          if (lastBatch.qty \<= remainingToSell) {

            simulatedCmvLifo \+= lastBatch.qty \* lastBatch.cost;

            remainingToSell \-= lastBatch.qty;

            lifoStack.pop();

          } else {

            simulatedCmvLifo \+= remainingToSell \* lastBatch.cost;

            lastBatch.qty \-= remainingToSell;

            remainingToSell \= 0;

          }

        }

      }

    }

    const marginDelta \= realCmvFromLedger \- simulatedCmvLifo;

    const variancePercentage \= realCmvFromLedger \> 0 

      ? (marginDelta / realCmvFromLedger) \* 100 

      : 0;

    return {

      sku: movements\[0\]?.sku ?? 'UNKNOWN',

      quantitySold: totalQtySold,

      realCmvNIIF: realCmvFromLedger,

      simulatedCmvLIFO: simulatedCmvLifo,

      marginDelta,

      variancePercentage,

    };

  }

}

---

## **4\. Comparativa Arquitectónica**

| Opción | Ventajas | Desventajas | Nivel de Riesgo |
| :---- | :---- | :---- | :---- |
| **Enfoque A: Arquitectura de 2 Capas** *(Fiscal y Analítica dentro del Core)* | Evita mantener múltiples motores o microservicios analíticos; todo el procesamiento ocurre en una única base de datos Postgres. | Viola la pureza del libro mayor; contamina el schema con reglas impositivas locales de cada país; bloquea el ledger con consultas analíticas pesadas (Menu Engineering / simulaciones); imposibilita auditorías limpias bajo NIIF. | **Alto** *(Ruptura de inmutabilidad contable y degradación de rendimiento)* |
| **Enfoque B: Arquitectura de 3 Capas Segregadas** *(Core NIIF → Fiscal Satélite → OmniBI)* | Aislamiento absoluto de responsabilidades. El Core es 100% auditable y exportable a cualquier país de LATAM; los plugins fiscales se actualizan sin migrar el Core; OmniBI tiene libertad de cálculo sin arriesgar la contabilidad formal; flujo estrictamente unidireccional. | Requiere mantener contratos de integración y tipado sincronizados entre FastAPI y TypeScript; exige pipelines de sincronización asíncrona para que OmniBI mantenga sus datos analíticos actualizados. | **Bajo** *(Arquitectura modular, escalable y tolerante a cambios regulatorios)* |

