from app.db import mongo_client, cassandra_cluster, graph_driver

def setup_mongo(db):
    db.full_threats.create_index([('threat_id',1)], unique=True)
    db.full_threats.create_index([('from_source',1), ('timestamp',-1)])
    db.full_threats.create_index([('target',1), ('timestamp',-1)])
    db.full_threats.create_index([('day',1),('threat_type',1)])
    db.threats.create_index('from_source',unique=True)

def setup_cassandra(session):
    session.execute("CREATE KEYSPACE IF NOT EXISTS threat_intel WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
    session.set_keyspace('threat_intel')
    session.execute('''CREATE TABLE IF NOT EXISTS threats_by_source (
        from_source text, timestamp timestamp, threat_id text, target text,
        threat_type text, fingerprint text, confidence double, is_false_positive boolean,
        PRIMARY KEY ((from_source),timestamp,threat_id)) WITH CLUSTERING ORDER BY (timestamp DESC, threat_id ASC)''')
    session.execute('''CREATE TABLE IF NOT EXISTS threats_by_type (
        threat_type text, timestamp timestamp, threat_id text, from_source text,
        target text, confidence double,
        PRIMARY KEY ((threat_type),timestamp,threat_id)) WITH CLUSTERING ORDER BY (timestamp DESC, threat_id ASC)''')
    session.execute('''CREATE TABLE IF NOT EXISTS threats_by_target (
        target text, timestamp timestamp, threat_id text, from_source text,
        threat_type text, PRIMARY KEY ((target),timestamp,threat_id)) WITH CLUSTERING ORDER BY (timestamp DESC, threat_id ASC)''')
    session.execute('''CREATE TABLE IF NOT EXISTS daily_volume (
        day text, from_source text, volume bigint, PRIMARY KEY ((day),from_source))''')

def setup_neo4j(driver):
    with driver.session() as s:
        s.run('CREATE CONSTRAINT source_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE').consume()
        s.run('CREATE CONSTRAINT threat_unique IF NOT EXISTS FOR (t:Threat) REQUIRE t.id IS UNIQUE').consume()
        s.run('CREATE INDEX threat_time IF NOT EXISTS FOR (t:Threat) ON (t.timestamp)').consume()
        s.run('CREATE INDEX threat_target IF NOT EXISTS FOR (t:Threat) ON (t.target)').consume()
