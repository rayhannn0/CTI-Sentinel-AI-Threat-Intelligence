from app.model import make_threat,generate
from scripts.communities import connected_components

def test_determinism(): assert make_threat(5)==make_threat(5)
def test_unique_ids(): assert len({x['threat_id'] for x in generate(100)})==100
def test_required_fields(): assert {'threat_id','timestamp','from_source','target','fingerprint','is_false_positive'}<=set(make_threat(0))
def test_false_positive_bool(): assert isinstance(make_threat(3)['is_false_positive'],bool)
def test_components(): assert connected_components([('a','b',3),('c','d',2)])==[['a','b'],['c','d']]
def test_filter_low_weights(): assert connected_components([('a','b',1)])==[]
