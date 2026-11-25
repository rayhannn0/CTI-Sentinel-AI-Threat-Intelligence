"""Lab 10.1: multi-document bank transfer, history, insufficient funds rollback."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pymongo.errors import PyMongoError
from connection import get_client, get_db
from common import dump, exported

class InsufficientFunds(Exception): pass

def transfer(client, from_id, to_id, amount):
    if amount <= 0: raise ValueError('Transfer amount must be positive')
    db=get_db(client)
    with client.start_session() as session:
        with session.start_transaction():
            source=db.accounts.find_one({'account_id':from_id}, session=session)
            destination=db.accounts.find_one({'account_id':to_id}, session=session)
            if source is None or destination is None: raise ValueError('Missing account')
            if source['balance'] < amount: raise InsufficientFunds('Insufficient balance')
            debit=db.accounts.update_one({'account_id':from_id,'balance':{'$gte':amount}}, {'$inc':{'balance':-amount,'version':1}}, session=session)
            if debit.modified_count != 1: raise InsufficientFunds('Balance changed; debit rejected')
            credit=db.accounts.update_one({'account_id':to_id}, {'$inc':{'balance':amount,'version':1}}, session=session)
            if credit.modified_count != 1: raise ValueError('Credit failed')
            db.transfer_history.insert_one({'from':from_id, 'to':to_id,'amount':amount,'status':'completed'}, session=session)
    return True

def main():
    c=get_client(); db=get_db(c)
    db.accounts.drop(); db.transfer_history.drop()
    db.accounts.create_index('account_id',unique=True)
    db.accounts.insert_many([{'account_id':'A100','balance':1000,'version':0}, {'account_id':'B200','balance':500,'version':0}])
    original=list(db.accounts.find({}, {'_id':0}).sort('account_id'))
    transfer(c,'A100','B200',250)
    after_success=list(db.accounts.find({}, {'_id':0}).sort('account_id'))
    history_count_before=db.transfer_history.count_documents({})
    try: transfer(c,'A100','B200',99999)
    except InsufficientFunds as e: print('Insufficient funds correctly rejected:', e)
    else: raise AssertionError('Insufficient transfer unexpectedly succeeded')
    after_reject=list(db.accounts.find({}, {'_id':0}).sort('account_id'))
    assert after_reject==after_success, 'Balances changed after aborted transfer!'
    assert db.transfer_history.count_documents({})==history_count_before, 'History inserted for rejected transfer!'
    result={'activity':'Lab 10.1', 'initial':original,'after_valid_transfer':after_success,'after_insufficient_funds':after_reject,'history_count':history_count_before,'rollback_verified':True}
    print(result); dump('lab_10_1.json',result)
    exported('lab_10_1_export.json',[db.accounts,db.transfer_history]); c.close()

if __name__=='__main__':main()
