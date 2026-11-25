# Replica set commands (inside Docker network)

Start Docker Desktop, then run from the project folder:

```sh
python3 bootstrap.py
# Inspect election/member health (works on any live data-bearing node)
docker compose exec mongo1 mongosh --quiet --eval 'rs.status()'
# Print voting / priority configuration
docker compose exec mongo1 mongosh --quiet --eval 'rs.conf()'
# Insert on current primary (first identify using python3 connection.py)
docker compose exec mongo1 mongosh --quiet --eval 'db.getSiblingDB("lab8").replication_demo.insertOne({message:"Manual test"})'
# Read from a secondary (not arbiter)
docker compose exec mongo2 mongosh --quiet --eval 'db.getMongo().setReadPref("secondary"); printjson(db.getSiblingDB("lab8").replication_demo.find().toArray())'
# Force failover ONLY on current primary; replace mongo1 with actual primary
# In MongoDB shell this invokes rs.stepDown(20).
docker compose exec mongo1 mongosh --quiet --eval 'rs.stepDown(20)'
```

The Python scripts identify primaries automatically, avoiding the problem that mongo1 is not necessarily primary after the first election.
