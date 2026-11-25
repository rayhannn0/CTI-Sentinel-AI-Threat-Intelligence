"""Lab 10.2: transaction-backed reservation with contention, retry, and no overselling."""
import sys, time, uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pymongo.errors import PyMongoError
from connection import get_client,get_db
from common import dump,exported,retry_transient

class OutOfStock(Exception):pass

def prepare(db,stock=5):
    db.inventory.drop();db.orders.drop()
    db.inventory.create_index('product_id',unique=True)
    db.orders.create_index('order_id',unique=True)
    db.inventory.insert_one({'product_id':'P100','name':'USB-C Adapter','stock':stock,'version':0,'price':299.0})

def reserve_inventory(client,customer,qty=1):
    if qty<=0:raise ValueError('Quantity must be positive')
    db=get_db(client)
    order_id=uuid.uuid4().hex
    def transaction():
        with client.start_session() as session:
            with session.start_transaction():
                product=db.inventory.find_one({'product_id':'P100'},session=session)
                if not product or product['stock']<qty:raise OutOfStock('Stock unavailable')
                update=db.inventory.update_one({'product_id':'P100','stock':{'$gte':qty},'version':product['version']},{'$inc':{'stock':-qty,'version':1}},session=session)
                if update.modified_count!=1:raise OutOfStock('Stock/version changed')
                db.orders.insert_one({'order_id':order_id,'customer_id':customer,'items':[{'product_id':'P100','qty':qty,'price':product['price']}],'status':'pending','total':round(product['price']*qty,2)},session=session)
                # increase overlap to deliberately exercise contention; bounded small delay
                time.sleep(.015)
        return order_id
    return retry_transient(transaction,max_attempts=6,base_delay=.03)

def compete(client,n_requests,workers):
    start=time.perf_counter();wins=[];outs=[];errors=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        tasks=[pool.submit(reserve_inventory,client,f'Customer-{i:02d}') for i in range(n_requests)]
        for task in as_completed(tasks):
            try:wins.append(task.result())
            except OutOfStock as e:outs.append(str(e))
            except PyMongoError as e:errors.append(str(e))
    elapsed=time.perf_counter()-start
    return {'requests':n_requests,'workers':workers,'successful':len(wins),'out_of_stock':len(outs),'mongo_errors':len(errors),'errors':errors[:5],'seconds':round(elapsed,4),'successful_per_second':round(len(wins)/elapsed,2) if elapsed else None}

def main():
    c=get_client();db=get_db(c);prepare(db,5)
    competition=compete(c,8,8)
    final=db.inventory.find_one({'product_id':'P100'},{'_id':0})
    orders=db.orders.count_documents({})
    assert competition['successful']==5 and competition['out_of_stock']==3, competition
    assert final['stock']==0 and orders==5 and not competition['mongo_errors']
    result={'activity':'Lab 10.2','competition':competition,'inventory':final,'orders_count':orders,'no_overselling_verified':True}
    print(result);dump('lab_10_2.json',result)
    exported('lab_10_2_export.json',[db.inventory,db.orders]);c.close()

if __name__=='__main__':main()
