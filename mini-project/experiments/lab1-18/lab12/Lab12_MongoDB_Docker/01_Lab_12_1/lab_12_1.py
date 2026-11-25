import os
from pymongo.errors import OperationFailure
from connection import client
from common import save

def denied(fn):
    try: fn(); return False
    except OperationFailure as e:
        if e.code == 13 or 'not authorized' in str(e).lower():return True
        raise

def main():
    read=client(os.environ['READ_USER'],os.environ['READ_PASSWORD'])['lab12']
    write=client(os.environ['WRITE_USER'],os.environ['WRITE_PASSWORD'])['lab12']
    read_view=list(read.employees_public.find({},{'_id':0}))
    reader_cannot_read_salary=denied(lambda:list(read.employees.find({})))
    reader_cannot_write=denied(lambda:read.orders.insert_one({'order_id':'blocked_reader'}))
    inserted=write.orders.insert_one({'order_id':'O100','status':'pending','total':99})
    writer_can_update=write.orders.update_one({'order_id':'O100'},{'$set':{'status':'paid'}}).modified_count==1
    writer_cannot_read_employees=denied(lambda:list(write.employees.find({})))
    result={'activity':'Lab 12.1','reader_view_count':len(read_view),'reader_salary_hidden':all('salary' not in e for e in read_view),'reader_underlying_collection_denied':reader_cannot_read_salary,'reader_write_denied':reader_cannot_write,'writer_insert_accepted':bool(inserted.inserted_id),'writer_update_accepted':writer_can_update,'writer_employees_denied':writer_cannot_read_employees}
    result['verified']=all(v for k,v in result.items() if k in ['reader_salary_hidden','reader_underlying_collection_denied','reader_write_denied','writer_insert_accepted','writer_update_accepted','writer_employees_denied'])
    print(result);save('lab_12_1',result)
    if not result['verified']:raise AssertionError('RBAC isolation failed')
if __name__=='__main__':main()
