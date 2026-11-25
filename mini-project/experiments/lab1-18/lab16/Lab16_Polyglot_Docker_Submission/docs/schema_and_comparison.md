# Lab 16.1 — Three database models

## MongoDB: document-oriented
- `lab16.students`: `{student_id, name, course_ids: [...]}`
- `lab16.courses`: `{course_id, title, student_ids: [...]}`
- `lab16.transactions`: `{txn_id, user_id, amount, merchant, timestamp, risk_score}`
- Indexed identifiers for flexible lookups. Arrays duplicate enrollment membership for direct reads; updates require coordinating both collections.

## Cassandra: query-driven wide-column
- `university.student_courses`: `PRIMARY KEY (student_id, course_id)`
- `university.course_students`: `PRIMARY KEY (course_id, student_id)`
- `fraud.user_profiles`: `PRIMARY KEY ((user_id), event_time)`, descending time ordering.
- `fraud.audit_events`: same ordered by-user layout for audit history.
- Duplication supports both access patterns without `ALLOW FILTERING`; Cassandra is poor at arbitrary cross-partition joins.

## Neo4j: graph model
- `(Student {id, name})-[:ENROLLED_IN]->(Course {id, title})`
- `(Course)-[:REQUIRES]->(Course)` for prerequisites.
- `(User)-[:TRANSFERRED_TO]->(User)` for fraud network exploration.

## Comparable query patterns
| Question | MongoDB | Cassandra | Neo4j |
|---|---|---|---|
| Courses of Alice | `students.find_one` then IDs / course lookup | `SELECT ... WHERE student_id=?` | `MATCH (s)-[:ENROLLED_IN]->(c)` |
| Students in Databases | course roster IDs then student lookup | `SELECT ... WHERE course_id=?` | `MATCH (s)-[:ENROLLED_IN]->(c)` |
| Students sharing a course | `$in` array lookup | read courses, query course_students per course, deduplicate | two-hop `MATCH` graph traversal |
| Prerequisite chain | repeated application joins | precomputed/query-specific tables | variable-length REQUIRES traversal |

## Expected behavior (not a universal performance ranking)
- MongoDB: flexible operational documents; cheap indexed lookups, but application joins for denormalized lists.
- Cassandra: efficient partition-key, time-ordered reads and high append throughput; not optimized for ad hoc joins.
- Neo4j: expressive multi-hop relationships and prerequisite traversals; graph traversal costs increase with hop count/density.
- Latency depends on hardware, indexes, warm caches, query shape, and data size. Lab scripts print measured local times; do not treat illustrative millisecond ranges as benchmarks.

## Lab 16.1 Try It Yourself — Hybrid architecture
- MongoDB = operational student/course records and flexible transaction documents.
- Cassandra = ordered audit logs and user event histories (immutable event design).
- Neo4j = prerequisite chains and fraud rings (relationships).
- Service layer joins results by stable IDs, not distributed cross-database transactions. Write failures require idempotent retries or an outbox/event pipeline. Consider eventual consistency and health checks.

## Lab 16.2 Circuit breaker and pooling
- PyMongo: pool `maxPoolSize=10`; Cassandra: `executor_threads=4`; Neo4j: `max_connection_pool_size=10`.
- Separate circuit breaker per backend: opens after 3 consecutive errors, skips calls for 30 seconds, then probes.
- Merged responses preserve results from healthy databases and report backend errors/individual timings.
- Tests use mocked drivers; integration executes real MongoDB, Cassandra, Neo4j.
