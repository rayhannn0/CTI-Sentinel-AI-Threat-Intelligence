"""Lab 16.2 fraud query service with pooled drivers and per-backend circuit breakers."""
import time
from datetime import datetime
from app.connections import mongo_client, cassandra_session, neo4j_driver


class CircuitOpen(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, threshold=3, cooldown=30, clock=time.monotonic):
        self.threshold=threshold
        self.cooldown=cooldown
        self.clock=clock
        self.failures=0
        self.opened_at=None

    def call(self, func):
        if self.opened_at is not None:
            if self.clock()-self.opened_at < self.cooldown:
                raise CircuitOpen('Backend temporarily unavailable')
            # Permit one trial request after cooldown.
            self.opened_at=None
        try:
            value=func()
        except Exception:
            self.failures+=1
            if self.failures>=self.threshold:
                self.opened_at=self.clock()
            raise
        self.failures=0
        self.opened_at=None
        return value


class FraudQueryService:
    def __init__(self, mongo_db, cassandra_session, neo4j_driver, clock=time.monotonic):
        self.mongo=mongo_db
        self.cassandra=cassandra_session
        self.neo4j=neo4j_driver
        self.breakers={k:CircuitBreaker(clock=clock) for k in ('mongo','cassandra','neo4j')}
        self.profile_stmt=self.cassandra.prepare('SELECT event_time, txn_id, amount, event_type FROM fraud.user_profiles WHERE user_id = ? ORDER BY event_time DESC LIMIT 10')

    def _call(self, backend, func):
        return self.breakers[backend].call(func)

    def get_transaction(self, txn_id):
        def query():
            row=self.mongo.transactions.find_one({'txn_id':txn_id},{'_id':0})
            return row
        return self._call('mongo',query)

    def get_user_profile(self, user_id):
        def query():
            return [{'event_time':r.event_time.isoformat() if isinstance(r.event_time,datetime) else str(r.event_time), 'txn_id':r.txn_id, 'amount':r.amount, 'event_type':r.event_type} for r in self.cassandra.execute(self.profile_stmt,(user_id,))]
        return self._call('cassandra',query)

    def detect_fraud_rings(self, user_id, max_hops=3):
        if not isinstance(max_hops,int) or not 1<=max_hops<=5:
            raise ValueError('max_hops must be an integer from 1 to 5')
        # Cypher cannot parameterize a variable length in older versions; only a validated integer is interpolated.
        cypher=f"""MATCH path=(u:User {{id:$uid}})-[:TRANSFERRED_TO*1..{max_hops}]-(connected:User)
        WHERE connected.id <> $uid
        RETURN DISTINCT connected.id AS related_user, length(path) AS hops
        ORDER BY hops, related_user LIMIT 50"""
        def query():
            with self.neo4j.session() as session:
                return [{'related_user':r['related_user'],'hops':r['hops']} for r in session.run(cypher,uid=user_id)]
        return self._call('neo4j',query)

    def analyze_user(self,user_id,txn_id,max_hops=3):
        """Best-effort merged response: backend failures do not prevent other lookups."""
        out={'user_id':user_id,'txn_id':txn_id,'transaction':None,'recent_events':[],'related_accounts':[],'errors':{},'latency_ms':{}}
        for backend, field, callback in [
            ('mongo','transaction',lambda:self.get_transaction(txn_id)),
            ('cassandra','recent_events',lambda:self.get_user_profile(user_id)),
            ('neo4j','related_accounts',lambda:self.detect_fraud_rings(user_id,max_hops))]:
            start=time.perf_counter()
            try: out[field]=callback()
            except Exception as exc: out['errors'][backend]=f'{type(exc).__name__}: {exc}'
            out['latency_ms'][backend]=round((time.perf_counter()-start)*1000,3)
        return out


def live_service():
    mongo_client_instance=mongo_client()
    cluster,cassandra=cassandra_session()
    neo=neo4j_driver()
    service=FraudQueryService(mongo_client_instance.lab16,cassandra,neo)
    return service,(mongo_client_instance,cluster,neo)
