"""Activity 10.2: throughput benchmarks (1,4,8,16 workers) and unsafe nontransactional failure illustration."""
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from importlib.util import spec_from_file_location,module_from_spec
from connection import get_client,get_db
from common import dump,exported
source=Path(__file__).resolve().parents[1]/'03_Lab_10_2'/'lab_10_2.py'
spec=spec_from_file_location('lab10_inventory',source);lab=module_from_spec(spec);spec.loader.exec_module(lab)

def main():
    client=get_client();db=get_db(client);measurements=[]
    for workers in [1,4,8,16]:
        lab.prepare(db,40)
        result=lab.compete(client,40,workers)
        final=db.inventory.find_one({'product_id':'P100'})
        assert final['stock']==40-result['successful']
        assert db.orders.count_documents({})==result['successful']
        measurements.append(result)
        print(f"workers={workers}: {result['successful_per_second']} successful reservations/sec; {result['successful']} successes")
    # Illustrate why nontransactional decrement then failed order insertion is unsafe.
    # This is a deliberately injected failure, not claimed to be a database error.
    lab.prepare(db,2)
    db.inventory.find_one_and_update({'product_id':'P100','stock':{'$gte':1}},{'$inc':{'stock':-1,'version':1}})
    injected='SIMULATED order insert failed after nontransactional stock decrement'
    inconsistent={'stock_after':db.inventory.find_one({'product_id':'P100'})['stock'],'order_count':db.orders.count_documents({}),'injected_failure':injected}
    assert inconsistent['stock_after']==1 and inconsistent['order_count']==0
    result={'activity':'Activity 10.2','benchmark':measurements,'note':'Concurrency throughput is environment-dependent; no guaranteed monotonic trend.','nontransactional_failure_example':inconsistent}
    print(result);dump('activity_10_2.json',result)
    exported('activity_10_2_export.json',[db.inventory,db.orders]);client.close()

if __name__=='__main__':main()
