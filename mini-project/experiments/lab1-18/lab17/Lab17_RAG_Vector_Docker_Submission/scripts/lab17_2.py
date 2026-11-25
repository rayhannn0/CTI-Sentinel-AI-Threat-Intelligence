import argparse,csv,json,time,os
import numpy as np
import faiss
from app.rag import normalize

parser=argparse.ArgumentParser()
parser.add_argument('--count',type=int,default=5000)
parser.add_argument('--dimensions',type=int,default=384)
parser.add_argument('--queries',type=int,default=100)
parser.add_argument('--topk',type=int,default=20)
a=parser.parse_args()
if a.count<=a.topk or a.dimensions<=0: parser.error('count must exceed topk and dimensions must be positive')
rng=np.random.default_rng(17)
# Synthetic, reproducible vector corpus: NOT Wikipedia/real sentence embeddings.
raw=rng.normal(size=(a.count,a.dimensions)).astype('float32')
# Add mild clustered structure for realistic approximate-nearest-neighbor tradeoffs.
centers=rng.normal(size=(100,a.dimensions)).astype('float32')
raw+=centers[rng.integers(0,100,a.count)]*0.45
vectors=normalize(raw).astype('float32')
query_ids=rng.choice(a.count,size=a.queries,replace=a.queries>a.count)
queries=vectors[query_ids].copy()
exact=faiss.IndexFlatIP(a.dimensions);exact.add(vectors)
_,ground_truth=exact.search(queries,a.topk)
rows=[]
def measure(name,parameter,index,build_time):
    elapsed=[];recalls=[]
    for q,gt in zip(queries,ground_truth):
        t=time.perf_counter();_,ids=index.search(q.reshape(1,-1),a.topk);elapsed.append((time.perf_counter()-t)*1000)
        recalls.append(len(set(map(int,ids[0]))&set(map(int,gt)))/a.topk)
    result={'index':name,'parameters':parameter,'build_seconds':round(build_time,3),'avg_latency_ms':round(float(np.mean(elapsed)),4),'recall_at_20_pct':round(float(np.mean(recalls))*100,2)}
    rows.append(result); print(json.dumps(result))

faiss.omp_set_num_threads(1)
for M in [8,16,32]:
    st=time.perf_counter();idx=faiss.IndexHNSWFlat(a.dimensions,M,faiss.METRIC_INNER_PRODUCT);idx.hnsw.efConstruction=64;idx.add(vectors);build=time.perf_counter()-st
    for ef in [16,64,128]:
        idx.hnsw.efSearch=ef;measure('HNSW',f'M={M};efConstruction=64;efSearch={ef}',idx,build)
for nlist in [50,100]:
    st=time.perf_counter();quant=faiss.IndexFlatIP(a.dimensions);idx=faiss.IndexIVFFlat(quant,a.dimensions,nlist,faiss.METRIC_INNER_PRODUCT)
    idx.train(vectors);idx.add(vectors);build=time.perf_counter()-st
    for nprobe in [1,5,20,50]:
        idx.nprobe=min(nprobe,nlist);measure('IVF',f'nlist={nlist};nprobe={idx.nprobe}',idx,build)

os.makedirs('/workspace/output',exist_ok=True)
with open('/workspace/output/lab17_vector_benchmark.csv','w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for name in ['HNSW','IVF']:
        group=[r for r in rows if r['index']==name]
        plt.scatter([r['avg_latency_ms'] for r in group],[r['recall_at_20_pct'] for r in group],label=name)
    plt.xlabel('Average query latency (ms)');plt.ylabel('Recall@20 (%)');plt.title('Local FAISS HNSW vs IVF (not Atlas)');plt.legend();plt.tight_layout()
    plt.savefig('/workspace/output/lab17_latency_recall.png',dpi=160);plt.close()
except ImportError:
    print('Matplotlib unavailable; CSV saved (plot skipped).')
print('LAB 17.2 LOCAL FAISS BENCHMARK COMPLETE; results in output/')
