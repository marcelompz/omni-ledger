# 🛠️ Troubleshooting — OmniLedger Index

Índice de guías de resolución de problemas para `omniledger-standalone`. Cada entrada incluye síntomas, causa raíz y solución aplicada.

---

## 📑 Índice por Documento

| # | Título | Área | Síntoma Principal | Estado |
|---|--------|------|-------------------|--------|
| **01** | **Partida Doble Desbalanceada (`HTTP 422`)** | Engine / DoubleEntry | Error 422 al intentar registrar asiento donde $\sum \text{Débitos} \neq \sum \text{Créditos}$ | ✅ Previsto por diseño |
| **02** | **Aislamiento RLS PostgreSQL** | Database / RLS / Security | Incapacidad de consultar registros entre diferentes `tenant_id` | ✅ Enforzado por RLS |
| **03** | **Inmutabilidad Post-`posted`** | Engine / Audit | Rechazo de actualización directa sobre un `account_move` publicado | ✅ Usar Reversal Move |
