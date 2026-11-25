import os
from pymongo import MongoClient
from connection import client,HOST,PORT,CA
from common import save

def main():
    plain=MongoClient(HOST,PORT,serverSelectionTimeoutMS=1600)
    plain_rejected=False
    try: plain.admin.command('ping')
    except Exception as e:
        plain_rejected=True
        print('Plaintext rejected:',type(e).__name__)
    secure=client(use_cert=True)
    secure.admin.command('ping')
    found=secure.lab12.employees.find_one({'employee_id':'E1'},{'_id':0})
    r={'activity':'Lab 12.2','plaintext_connection_rejected':plain_rejected,'tls_connection_succeeded':found is not None,'tls_client_cert_supplied':True,'query_result':found,'verified':plain_rejected and found is not None}
    print(r); save('lab_12_2',r)
    if not r['verified']:raise AssertionError('TLS test failed')
if __name__=='__main__':main()
