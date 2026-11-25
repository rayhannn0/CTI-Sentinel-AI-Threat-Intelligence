"""Compare equivalent university queries in MongoDB, Cassandra, Neo4j."""
from time import perf_counter
from app.connections import mongo_client, cassandra_session, neo4j_driver


def timed(label, fn):
    start=perf_counter(); result=fn(); print(f"{label} ({(perf_counter()-start)*1000:.2f} ms): {result}")

def main():
    mongo=mongo_client(); cluster,cass=cassandra_session(); neo=neo4j_driver()
    try:
        db=mongo.lab16
        timed('MongoDB courses for Alice',lambda: [db.courses.find_one({'course_id': c},{'_id':0,'title':1})['title'] for c in db.students.find_one({'student_id':'s1'})['course_ids']])
        timed('MongoDB students in Databases', lambda: [db.students.find_one({'student_id':s},{'_id':0,'name':1})['name'] for s in db.courses.find_one({'course_id':'c1'})['student_ids']])
        timed('MongoDB Alice classmates',lambda: sorted(set(st['name'] for st in db.students.find({'course_ids':{'$in': db.students.find_one({'student_id':'s1'})['course_ids']},'student_id':{'$ne':'s1'}},{'_id':0,'name':1}))))
        courses=cass.prepare('SELECT title FROM university.student_courses WHERE student_id = ?')
        roster=cass.prepare('SELECT name FROM university.course_students WHERE course_id = ?')
        timed('Cassandra courses for Alice', lambda: [r.title for r in cass.execute(courses,('s1',))])
        timed('Cassandra students in Databases',lambda:[r.name for r in cass.execute(roster,('c1',))])
        def cass_classmates():
            course_ids=[r.course_id for r in cass.execute('SELECT course_id FROM university.student_courses WHERE student_id = %s',('s1',))]
            return sorted({r.name for cid in course_ids for r in cass.execute(roster,(cid,)) if r.name!='Alice'})
        timed('Cassandra Alice classmates',cass_classmates)
        def cypher(q,**params):
            with neo.session() as s: return [r['name'] for r in s.run(q,**params)]
        timed('Neo4j courses for Alice', lambda: cypher('MATCH (:Student {id:$sid})-[:ENROLLED_IN]->(c:Course) RETURN c.title AS name ORDER BY name',sid='s1'))
        timed('Neo4j students in Databases', lambda: cypher('MATCH (s:Student)-[:ENROLLED_IN]->(:Course {id:$cid}) RETURN s.name AS name ORDER BY name',cid='c1'))
        timed('Neo4j Alice classmates',lambda: cypher('MATCH (:Student {id:$sid})-[:ENROLLED_IN]->(:Course)<-[:ENROLLED_IN]-(other:Student) WHERE other.id <> $sid RETURN DISTINCT other.name AS name ORDER BY name',sid='s1'))
        timed('Neo4j prerequisites for Networks',lambda: cypher('MATCH (:Course {id:$cid})-[:REQUIRES*1..5]->(pre:Course) RETURN DISTINCT pre.title AS name ORDER BY name',cid='c3'))
        print('LAB 16.1 COMPLETE')
    finally:
        mongo.close();cluster.shutdown();neo.close()
if __name__=='__main__':main()
