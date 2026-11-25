import argparse,json
from app.rag import connect,seed,answer

parser=argparse.ArgumentParser()
parser.add_argument('action',choices=['seed','ask','demo','index-definition'])
parser.add_argument('--question',default='How can we reduce ransomware risk?')
parser.add_argument('--user',default='student1')
parser.add_argument('--atlas',action='store_true',help='Use real Atlas $vectorSearch (requires Atlas index and matching embeddings)')
a=parser.parse_args(); db=connect()
if a.action=='seed':
    count,model,dims=seed(db);print(f'SEED PASS: {count} chunks; embedding={model}; dimensions={dims}')
elif a.action=='index-definition':
    sample=db.documents.find_one({})
    if not sample: raise SystemExit('seed first')
    dims=len(sample['embedding'])
    print(json.dumps({'name':'threat_vector_index','type':'vectorSearch','definition':{'fields':[{'type':'vector','path':'embedding','numDimensions':dims,'similarity':'cosine'}]}},indent=2))
elif a.action=='ask':
    print(json.dumps(answer(db,a.user,a.question,atlas=a.atlas),indent=2))
else:
    for q in ['What is ransomware and how can it be mitigated?','What did we discuss and what backups help?']:
        result=answer(db,a.user,q,atlas=a.atlas)
        print(json.dumps({'question':q,**result},indent=2))
    print('LAB 17.1 DEMO COMPLETE')
