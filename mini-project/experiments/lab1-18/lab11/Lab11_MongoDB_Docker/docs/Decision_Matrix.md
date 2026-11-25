# Lab 11.1 — Decision matrix

| Shard key | Cardinality | Write distribution | Query targeting | Verdict |
|---|---|---|---|---|
| order_id (ranged) | Very high | Depends on ID sequence; increasing values can hotspot | Order equality targeted, customer queries scatter | Poor for customer-centric workload |
| customer_id (ranged) | High | Skew from large customers | Customer equality and ranges targeted | Good for range-heavy customer queries |
| order_date (ranged) | High | Chronological hotspot risk | Time ranges targeted | Avoid for heavy ingest unless mitigated |
| customer_id (hashed) | High | Usually balanced across chunks | Customer equality targeted; customer ranges scatter | **Recommended** |

## MongoDB 5.0+ resharding

Plan and verify requirements; choose new key and appropriate index; run `reshardCollection` through mongos; monitor data copy, write catch-up, and cutover; verify query plans and distribution. Exact restrictions vary by MongoDB version; consult official docs before production changes.
