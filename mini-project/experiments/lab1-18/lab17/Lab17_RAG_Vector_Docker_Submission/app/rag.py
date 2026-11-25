import os, re
from datetime import datetime, timezone
import numpy as np
from pymongo import MongoClient
from sklearn.feature_extraction.text import HashingVectorizer

DOCUMENTS = {
 "phishing": "Phishing is a social engineering attack that tricks users into opening malicious links or sharing credentials. Defenders should use phishing-resistant multifactor authentication, train users to report suspicious messages, verify domains independently, and isolate compromised accounts quickly. Never enter passwords into links in unexpected messages.",
 "ransomware": "Ransomware encrypts or exfiltrates data and may disrupt operations. Maintain tested offline backups, patch vulnerable services, restrict administrator privileges, monitor endpoint alerts, and isolate infected devices. Preserve logs and follow an approved incident response plan before restoration.",
 "vulnerabilities": "Vulnerability management inventories assets, prioritizes exploited vulnerabilities and critical internet-facing systems, applies vendor patches, and validates remediation. Use CISA KEV where appropriate, scan systems with authorization, and document exceptions and compensating controls.",
 "malware": "Malware may spread through malicious downloads, compromised software, or stolen credentials. Defenders should enable endpoint protection, apply software updates, restrict untrusted executables, and inspect suspicious processes with authorized security tools. Preserve forensic evidence before removing suspicious files.",
 "network": "Network intrusion detection monitors unexpected connections and anomalous traffic patterns. Segment sensitive resources, restrict inbound services, centralize logging, and correlate alerts with host-level events. Treat unusual traffic as an investigation lead rather than proof of compromise."
}

VECTORIZER = HashingVectorizer(n_features=384, alternate_sign=False, norm=None, ngram_range=(1,2))

def chunks(text, width=100, overlap=20):
    if not 0 <= overlap < width: raise ValueError('overlap must be < width')
    words=text.split(); step=width-overlap
    return [' '.join(words[i:i+width]) for i in range(0,len(words),step) if words[i:i+width]]

def local_embed(texts):
    return VECTORIZER.transform(texts).toarray().astype('float32')

def embed(texts):
    key=os.getenv('VOYAGE_API_KEY')
    if key:
        import requests
        r=requests.post('https://api.voyageai.com/v1/embeddings',headers={'Authorization':f'Bearer {key}'},json={'input':texts,'model':'voyage-3.5-lite'},timeout=45)
        r.raise_for_status()
        data=sorted(r.json()['data'],key=lambda item:item['index'])
        return np.array([x['embedding'] for x in data],dtype='float32'),'voyage-3.5-lite'
    return local_embed(texts),'hashing-384-local-baseline'

def normalize(x):
    x=np.asarray(x,dtype=np.float32); return x/(np.linalg.norm(x,axis=-1,keepdims=True)+1e-12)

def seed(db):
    records=[]
    for source,text in DOCUMENTS.items():
        for i,part in enumerate(chunks(text)):
            records.append({'source':source,'chunk_id':i,'text':part})
    vectors,model=embed([r['text'] for r in records])
    for r,v in zip(records,vectors): r.update(embedding=v.tolist(),embedding_model=model)
    db.documents.delete_many({})
    db.documents.insert_many(records)
    db.conversations.create_index([('user_id',1),('timestamp',-1)])
    return len(records),model,vectors.shape[1]

def retrieve(db,query,limit=3,atlas=False):
    models=db.documents.distinct('embedding_model')
    if not models: raise RuntimeError('Seed first: python -m scripts.lab17_1 seed')
    q,model=embed([query]);q=q[0]
    if model not in models: raise RuntimeError('Embedding model changed; reseed documents with current VOYAGE_API_KEY setting')
    if atlas:
        pipeline=[{'$vectorSearch':{'index':os.getenv('ATLAS_VECTOR_INDEX','threat_vector_index'),'path':'embedding','queryVector':q.tolist(),'numCandidates':max(20,limit*10),'limit':limit}},{'$project':{'_id':0,'text':1,'source':1,'score':{'$meta':'vectorSearchScore'}}}]
        return list(db.documents.aggregate(pipeline))
    docs=list(db.documents.find({'embedding_model':model},{'_id':0,'text':1,'source':1,'embedding':1}))
    matrix=normalize(np.array([d['embedding'] for d in docs],dtype=np.float32)); scores=matrix@normalize(q)
    order=np.argsort(-scores)[:limit]
    return [{'text':docs[i]['text'],'source':docs[i]['source'],'score':round(float(scores[i]),5)} for i in order]

def history(db,user_id):
    # last five exchanges means up to 10 message records
    messages=list(db.conversations.find({'user_id':user_id},{'_id':0,'role':1,'content':1}).sort('timestamp',-1).limit(10))
    return list(reversed(messages))

def answer(db,user_id,query,atlas=False):
    prior=history(db,user_id)
    results=retrieve(db,query,atlas=atlas)
    context='\n'.join('['+r['source']+'] '+r['text'] for r in results)
    instruction='Answer only using the provided source context. If insufficient, say so. Include short source labels.'
    messages=[{'role':'system','content':instruction+'\nSOURCE CONTEXT:\n'+context}]
    for msg in prior: messages.append({'role':msg['role'],'content':msg['content']})
    messages.append({'role':'user','content':query})
    api_key=os.getenv('OPENAI_API_KEY')
    if api_key:
        import requests
        response=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f'Bearer {api_key}'},json={'model':os.getenv('OPENAI_MODEL','gpt-4o-mini'),'messages':messages,'temperature':0},timeout=60)
        response.raise_for_status()
        response_text=response.json()['choices'][0]['message']['content'];generation='external-llm'
    else:
        response_text='No LLM configured. Retrieved context (extractive fallback):\n'+context;generation='extractive-fallback-not-an-llm'
    now=datetime.now(timezone.utc)
    db.conversations.insert_many([{'user_id':user_id,'role':'user','content':query,'timestamp':now},{'user_id':user_id,'role':'assistant','content':response_text,'timestamp':datetime.now(timezone.utc)}])
    return {'answer':response_text,'generation':generation,'top_chunks':results,'previous_messages_used':len(prior)}

def connect():
    return MongoClient(os.getenv('MONGO_URI','mongodb://mongo:27017'),serverSelectionTimeoutMS=12000)['lab17_rag']
