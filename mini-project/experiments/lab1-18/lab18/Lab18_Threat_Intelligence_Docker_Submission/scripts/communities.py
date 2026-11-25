# Graph-based connected component heuristic and MongoDB cross-reference
import json
from collections import defaultdict,Counter
from pathlib import Path

def connected_components(edges, min_weight=2):
    graph=defaultdict(set)
    for a,b,w in edges:
        if w>=min_weight:
            graph[a].add(b);graph[b].add(a)
    seen=set();groups=[]
    for node in graph:
        if node in seen:continue
        stack=[node]; members=[]
        while stack:
            x=stack.pop()
            if x in seen:continue
            seen.add(x);members.append(x);stack.extend(graph[x]-seen)
        groups.append(sorted(members))
    return sorted(groups,key=len,reverse=True)

def main():
    from app.db import mongo_client,graph_driver
    gd=graph_driver();mc=mongo_client();db=mc.threat_intel
    with gd.session() as s:
        edges=[(x['a'],x['b'],x['weight']) for x in s.run('MATCH (a:Source)-[r:SUSPICIOUS]-(b:Source) WHERE a.id < b.id RETURN a.id AS a,b.id AS b,r.shared_fingerprints AS weight').data()]
    communities=connected_components(edges,min_weight=2)
    result=[]
    for members in communities[:10]:
        # compare graph-derived communities with raw Mongo records, not with inferred guilt
        docs=list(db.full_threats.find({'from_source':{'$in':members}},{'_id':0,'threat_id':1,'is_false_positive':1,'fingerprint':1}).limit(5000))
        samples=[d['threat_id'] for d in docs[:5]]
        flagged=sum(bool(x.get('is_false_positive')) for x in docs)
        result.append({'sources':members,'source_count':len(members),'mongo_sample_size':len(docs),'heuristic_false_positive_flags_in_sample':flagged,'sample_threat_ids':samples})
    Path('output').mkdir(exist_ok=True)
    Path('output/communities.json').write_text(json.dumps({'method':'connected-components on SUSPICIOUS graph edges (weight>=2); MongoDB cross-reference','communities':result},indent=2))
    print(json.dumps(result[:3],indent=2));print('GRAPH EXTENSION COMPLETE: output/communities.json')
    gd.close();mc.close()

if __name__=='__main__':main()
