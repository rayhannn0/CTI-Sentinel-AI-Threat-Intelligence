"""Idempotently seed university and fraud examples into all three databases."""
from datetime import datetime, timezone, timedelta
from app.connections import mongo_client, cassandra_session, neo4j_driver

STUDENTS = [("s1", "Alice"), ("s2", "Bob"), ("s3", "Carla"), ("s4", "David")]
COURSES = [("c1", "Databases"), ("c2", "Machine Learning"), ("c3", "Networks")]
ENROLLMENTS = [("s1", "c1"), ("s1", "c2"), ("s2", "c1"), ("s3", "c2"), ("s4", "c3")]


def seed_mongo(client):
    db = client.lab16
    ids = {s: [c for sid, c in ENROLLMENTS if sid == s] for s, _ in STUDENTS}
    for sid, name in STUDENTS:
        db.students.replace_one({"student_id": sid}, {"student_id": sid, "name": name, "course_ids": ids[sid]}, upsert=True)
    for cid, title in COURSES:
        db.courses.replace_one({"course_id": cid}, {"course_id": cid, "title": title, "student_ids": [s for s,c in ENROLLMENTS if c == cid]}, upsert=True)
    for txn_id, user_id, amount, merchant, risk in [("tx100","u1",1200,"StoreA",0.82),("tx101","u2",500,"StoreB",0.12),("tx102","u1",3000,"StoreC",0.94)]:
        db.transactions.replace_one({"txn_id":txn_id}, {"txn_id":txn_id,"user_id":user_id,"amount":amount,"merchant":merchant,"timestamp":datetime.now(timezone.utc),"risk_score":risk},upsert=True)
    db.students.create_index("student_id", unique=True)
    db.courses.create_index("course_id", unique=True)
    db.transactions.create_index("txn_id", unique=True)
    print("MongoDB: 4 students, 3 courses, 3 fraud transactions")


def seed_cassandra(session):
    session.execute("CREATE KEYSPACE IF NOT EXISTS university WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
    session.execute("CREATE TABLE IF NOT EXISTS university.student_courses (student_id text, course_id text, title text, PRIMARY KEY (student_id, course_id))")
    session.execute("CREATE TABLE IF NOT EXISTS university.course_students (course_id text, student_id text, name text, PRIMARY KEY (course_id, student_id))")
    session.execute("CREATE KEYSPACE IF NOT EXISTS fraud WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
    session.execute("CREATE TABLE IF NOT EXISTS fraud.user_profiles (user_id text, event_time timestamp, txn_id text, amount double, event_type text, PRIMARY KEY ((user_id), event_time)) WITH CLUSTERING ORDER BY (event_time DESC)")
    session.execute("CREATE TABLE IF NOT EXISTS fraud.audit_events (user_id text, event_time timestamp, action text, details text, PRIMARY KEY ((user_id), event_time)) WITH CLUSTERING ORDER BY (event_time DESC)")
    student_names=dict(STUDENTS); titles=dict(COURSES)
    p1=session.prepare("INSERT INTO university.student_courses (student_id, course_id, title) VALUES (?, ?, ?)")
    p2=session.prepare("INSERT INTO university.course_students (course_id, student_id, name) VALUES (?, ?, ?)")
    for sid,cid in ENROLLMENTS:
        session.execute(p1,(sid,cid,titles[cid])); session.execute(p2,(cid,sid,student_names[sid]))
    now=datetime(2026,1,1,tzinfo=timezone.utc)
    p3=session.prepare("INSERT INTO fraud.user_profiles (user_id, event_time, txn_id, amount, event_type) VALUES (?, ?, ?, ?, ?)")
    p4=session.prepare("INSERT INTO fraud.audit_events (user_id, event_time, action, details) VALUES (?, ?, ?, ?)")
    for i,(uid,txn,amount) in enumerate([("u1","tx100",1200.),("u2","tx101",500.),("u1","tx102",3000.)]):
        tm=now+timedelta(minutes=i)
        session.execute(p3,(uid,tm,txn,amount,"purchase"))
        session.execute(p4,(uid,tm,"purchase",txn))
    print("Cassandra: university enrollment lookups + fraud time-series + audit")


def seed_neo4j(driver):
    with driver.session() as session:
        session.run("CREATE CONSTRAINT student_id_unique IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE").consume()
        session.run("CREATE CONSTRAINT course_id_unique IF NOT EXISTS FOR (c:Course) REQUIRE c.id IS UNIQUE").consume()
        session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE").consume()
        for sid,name in STUDENTS: session.run("MERGE (s:Student {id:$id}) SET s.name=$name",id=sid,name=name).consume()
        for cid,title in COURSES: session.run("MERGE (c:Course {id:$id}) SET c.title=$title",id=cid,title=title).consume()
        for sid,cid in ENROLLMENTS: session.run("MATCH (s:Student {id:$sid}),(c:Course {id:$cid}) MERGE (s)-[:ENROLLED_IN]->(c)",sid=sid,cid=cid).consume()
        session.run("MATCH (a:Course {id:'c1'}),(b:Course {id:'c2'}) MERGE (b)-[:REQUIRES]->(a)").consume()
        session.run("MATCH (a:Course {id:'c2'}),(b:Course {id:'c3'}) MERGE (b)-[:REQUIRES]->(a)").consume()
        for uid in ('u1','u2','u3','u4'): session.run("MERGE (:User {id:$uid})",uid=uid).consume()
        for a,b in [('u1','u2'),('u2','u3'),('u3','u1'),('u3','u4')]:
            session.run("MATCH (a:User {id:$a}),(b:User {id:$b}) MERGE (a)-[:TRANSFERRED_TO]->(b)",a=a,b=b).consume()
    print("Neo4j: enrollment edges, prerequisite chain, fraud transfer ring")


def main():
    mc=mongo_client(); cluster,cs=cassandra_session(); driver=neo4j_driver()
    try:
        seed_mongo(mc); seed_cassandra(cs); seed_neo4j(driver)
        print("SEED COMPLETE")
    finally:
        mc.close(); cluster.shutdown(); driver.close()

if __name__=='__main__': main()
