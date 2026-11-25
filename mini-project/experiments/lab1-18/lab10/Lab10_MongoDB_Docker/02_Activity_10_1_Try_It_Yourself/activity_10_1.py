"""Activity 10.1: exponential backoff on TransientTransactionError."""
import sys,time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pymongo.errors import OperationFailure
from connection import get_client,get_db
from common import dump,exported,retry_transient
from importlib.util import spec_from_file_location,module_from_spec
lab=Path(__file__).resolve().parents[1]/'01_Lab_10_1'/'lab_10_1.py'
spec=spec_from_file_location('lab10_bank',lab); mod=module_from_spec(spec); spec.loader.exec_module(mod)

def main():
    client=get_client(); db=get_db(client)
    db.accounts.drop(); db.transfer_history.drop()
    db.accounts.create_index('account_id',unique=True)
    db.accounts.insert_many([{'account_id':'A100','balance':600,'version':0},{'account_id':'B200','balance':300,'version':0}])
    simulated={'remaining':2,'attempts':0}
    def run_one():
        simulated['attempts']+=1
        if simulated['remaining']:
            simulated['remaining']-=1
            raise OperationFailure('Simulated transient write conflict', code=112, details={'errorLabels':['TransientTransactionError']})
        return mod.transfer(client,'A100','B200',150)
    start=time.perf_counter()
    retry_transient(run_one,max_attempts=5,base_delay=.1)
    balances=list(db.accounts.find({}, {'_id':0}).sort('account_id'))
    assert [x['balance'] for x in balances]==[450,450]
    assert db.transfer_history.count_documents({})==1
    result={'activity':'Activity 10.1','demonstration':'Two simulated labeled transient errors before a real MongoDB transfer','attempts':simulated['attempts'],'backoff_s':[.1,.2],'elapsed_ms':round((time.perf_counter()-start)*1000,2),'accounts':balances,'history_count':1,'verified':True}
    print(result);dump('activity_10_1.json',result)
    exported('activity_10_1_export.json',[db.accounts,db.transfer_history]);client.close()

if __name__=='__main__':main()
