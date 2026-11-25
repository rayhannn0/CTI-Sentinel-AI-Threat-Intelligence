from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock
import pytest
from app.fraud_service import FraudQueryService, CircuitBreaker, CircuitOpen


def make_service():
    mongo=Mock()
    mongo.transactions.find_one.return_value={'txn_id':'tx100','amount':1200}
    cass=Mock()
    cass.prepare.return_value='prepared_statement'
    cass.execute.return_value=[SimpleNamespace(event_time=datetime(2026,1,1,tzinfo=timezone.utc),txn_id='tx100',amount=1200.,event_type='purchase')]
    neo=Mock()
    neo.session.return_value=MagicMock()
    sess=Mock()
    sess.run.return_value=[{'related_user':'u2','hops':1}]
    neo.session.return_value.__enter__=Mock(return_value=sess)
    neo.session.return_value.__exit__=Mock(return_value=False)
    return FraudQueryService(mongo,cass,neo),mongo,cass,sess


def test_transaction():
    svc,mongo,_,_=make_service()
    assert svc.get_transaction('tx100')['amount']==1200
    mongo.transactions.find_one.assert_called_once_with({'txn_id':'tx100'},{'_id':0})


def test_user_profile():
    svc,_,cass,_=make_service()
    assert svc.get_user_profile('u1')[0]['txn_id']=='tx100'
    cass.execute.assert_called_once_with('prepared_statement',('u1',))


def test_fraud_rings():
    svc,_,_,session=make_service()
    assert svc.detect_fraud_rings('u1',3)==[{'related_user':'u2','hops':1}]
    assert '1..3' in session.run.call_args.args[0]
    with pytest.raises(ValueError):svc.detect_fraud_rings('u1',99)


def test_merged_result():
    svc,_,_,_=make_service()
    out=svc.analyze_user('u1','tx100')
    assert not out['errors']
    assert out['transaction']['txn_id']=='tx100'
    assert out['recent_events'][0]['txn_id']=='tx100'
    assert out['related_accounts'][0]['related_user']=='u2'


def test_circuit_breaker():
    current=[0.]
    cb=CircuitBreaker(clock=lambda:current[0])
    def failure(): raise RuntimeError('down')
    for _ in range(3):
        with pytest.raises(RuntimeError): cb.call(failure)
    with pytest.raises(CircuitOpen):cb.call(lambda:'should not execute')
    current[0]=31.
    assert cb.call(lambda:'recovered')=='recovered'
    assert cb.failures==0


def test_backend_failure_does_not_block_other_queries():
    svc,mongo,_,_=make_service()
    mongo.transactions.find_one.side_effect=RuntimeError('mongo unavailable')
    out=svc.analyze_user('u1','tx100')
    assert 'mongo' in out['errors']
    assert out['recent_events']
    assert out['related_accounts']
