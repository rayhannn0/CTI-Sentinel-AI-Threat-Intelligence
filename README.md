# CTI Sentinel — Live NoSQL Labs 01–18

A dark, console-style website modeled on the user's reference screenshot. **New primary URL:** `http://127.0.0.1:8765/sentinel`.

## Start on macOS

1. Start Docker Desktop.
2. Keep the original Lab 18 Docker Compose stack running: `cd ~/Downloads/lab18/Lab18_Threat_Intelligence_Docker_Submission && docker compose up -d`
3. Ensure the separate Lab 10 single-node replica set `lab10-repl-mongo` is running and PRIMARY on port 27022:

   ```bash
   docker start lab10-repl-mongo
   docker exec lab10-repl-mongo mongosh --port 27022 --quiet --eval 'rs.status().members.map(m => ({name:m.name,state:m.stateStr}))'
   ```

   This reuses the already-created container. Don't re-run `docker run` or `rs.initiate`.
4. Stop the old website with Ctrl+C and in a new Terminal:

   ```bash
   cd ~/Downloads/NoSQL_Sentinel_18_Labs
   bash start_sentinel.command
   ```

5. Visit `http://127.0.0.1:8765/sentinel`. Select **Lab 10**.

The launcher connects transaction and demo operations to `mongodb://127.0.0.1:27022/?replicaSet=rsLab10`. It reads the original Lab 18 threat records separately on `127.0.0.1:27021`.

## Real actions

- Lab 10: Reset bank accounts, execute an atomic debit+credit+audit insert using MongoDB transactions, reject insufficient balances, simulate an error *inside* a transaction to demonstrate rollback, show actual balances and audit records. Lab 10.2: conditional stock reservation with real MongoDB updates.
- Labs 1–5, 15, 17: user-input forms and MongoDB-backed saved documents.
- Labs 6–9, 11–14, 16, 18: allowlisted live experiments using your existing workbench scripts. Some require replica-set topologies, sharding, authentication, Kubernetes, or additional connected database services. Missing prerequisites are reported rather than faked.
- Lab 18: live read-only synthetic threat exploration from the original Lab 18 MongoDB (port 27021).

This project preserves the prior `/`, `/models`, `/workbench`, and `/api/...` routes. The separate new page is `/sentinel`.

## Important limitations

- A **single-node replica set supports multi-document ACID transactions**, but it cannot demonstrate three-node elections, high availability, or replication under node failure.
- A rollback audit event is logged **outside** the aborted transaction so it can be inspected later. It is not a partially committed business transfer.
- The rollback experiment aborts after a transactional write; it is not proof of a real MongoDB `TransientTransactionError`. The PyMongo `with_transaction()` helper provides retry behavior for eligible transient failures, but this UI does not deliberately generate one.
- Only local educational synthetic data should be used; never expose the demonstration database publicly without authentication.
- Labs 1–18 are **not** all fully completed graded activities. The UI offers live models and checks, not a substitute for a correctly provisioned multi-node, sharded, Kubernetes, Cassandra, or vector-search cluster.
