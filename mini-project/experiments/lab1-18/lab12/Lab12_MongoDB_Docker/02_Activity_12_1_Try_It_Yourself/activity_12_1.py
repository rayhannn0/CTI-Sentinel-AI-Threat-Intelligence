import os
from pymongo.errors import OperationFailure
from connection import client
from common import save

def main():
    reader=client(os.environ['READ_USER'],os.environ['READ_PASSWORD'])['lab12']
    hr=client(os.environ['HR_USER'],os.environ['HR_PASSWORD'])['lab12']
    safe=list(reader.employees_public.find({},{'_id':0}))
    private=list(hr.employees.find({},{'_id':0}))
    hidden=all('salary' not in x for x in safe)
    hr_access=all('salary' in x for x in private)
    unauthorized=False
    try: list(reader.employees.find({}))
    except OperationFailure as e: unauthorized=(e.code==13)
    r={'activity':'Try it yourself 12.1','view_name':'employees_public','public_records':safe,'hr_salary_visible':hr_access,'reader_salary_hidden':hidden,'reader_direct_access_denied':unauthorized,'verified':hidden and hr_access and unauthorized}
    print(r);save('activity_12_1',r)
    if not r['verified']:raise AssertionError('View security failed')
if __name__=='__main__':main()
