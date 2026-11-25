import os
from connection import client
from pymongo.errors import OperationFailure
from common import save

def main():
    c=client(); c.admin.command('ping'); admin=c['admin']; db=c['lab12']
    # Setup root-only sample data. Re-running resets lab-specific demo collections only.
    db['employees'].delete_many({}); db['orders'].delete_many({})
    db['employees'].insert_many([{'employee_id':'E1','name':'Asha','department':'Engineering','salary':84000},{'employee_id':'E2','name':'Kiran','department':'Sales','salary':65000}])
    if 'employees_public' in db.list_collection_names(): db.drop_collection('employees_public')
    db.command({'create':'employees_public','viewOn':'employees','pipeline':[{'$project':{'salary':0}}]})
    roles={
      'lab12AppReader':[{'resource':{'db':'lab12','collection':'employees_public'},'actions':['find']}],
      'lab12AppWriter':[{'resource':{'db':'lab12','collection':'orders'},'actions':['find','insert','update','remove']}],
      'lab12HR':[{'resource':{'db':'lab12','collection':'employees'},'actions':['find']}]
    }
    for name,priv in roles.items():
        if admin.command('rolesInfo',name,showPrivileges=False).get('roles'):
            admin.command({'updateRole':name,'privileges':priv,'roles':[]})
        else: admin.command({'createRole':name,'privileges':priv,'roles':[]})
    for name,pw,role in [(os.environ['READ_USER'],os.environ['READ_PASSWORD'],'lab12AppReader'),(os.environ['WRITE_USER'],os.environ['WRITE_PASSWORD'],'lab12AppWriter'),(os.environ['HR_USER'],os.environ['HR_PASSWORD'],'lab12HR')]:
        if admin.command('usersInfo',name).get('users'):
            admin.command({'updateUser':name,'pwd':pw,'roles':[{'role':role,'db':'admin'}]})
        else: admin.command({'createUser':name,'pwd':pw,'roles':[{'role':role,'db':'admin'}]})
    save('setup',{'created_users':['app_user_read','app_user_write','hr_user'],'roles':list(roles),'view':'employees_public','notice':'Passwords intentionally excluded'})
    print('Roles, users and redacted view ready.')
if __name__=='__main__':main()
