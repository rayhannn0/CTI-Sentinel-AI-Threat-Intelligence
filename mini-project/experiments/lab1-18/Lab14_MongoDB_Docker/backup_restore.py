"""Lab 14.2: timestamped mongodump, restore verification, and size benchmarks.
Only the dedicated lab14.backup_test collection is modified or dropped.
"""
import csv, hashlib, json, os, shutil, subprocess, time
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient

URI=os.getenv("MONGO_URI","mongodb://localhost:27017"); DB="lab14"; COLL="backup_test"
BACKUPS=Path(os.getenv("BACKUP_ROOT","backups")); OUTPUT=Path(os.getenv("OUTPUT_DIR","output")); SIZES=(1000,10000,100000)

def require_tools():
    missing=[x for x in ("mongodump","mongorestore") if shutil.which(x) is None]
    if missing: raise RuntimeError("MongoDB Database Tools missing: "+", ".join(missing))

def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{r.stdout[-1000:]}\n{r.stderr[-2000:]}")
    return r

def seed(col,n):
    col.drop(); batch=[]
    for i in range(n):
        batch.append({"sequence":i,"order_id":f"ORD-{i:06d}","customer_id":f"CUST-{i%500:04d}","amount":round(10+(i%1000)*1.37,2),"status":"created","payload":"lab14-backup-verification-"*4})
        if len(batch)>=2000: col.insert_many(batch); batch=[]
    if batch: col.insert_many(batch)

def checksum(col):
    h=hashlib.sha256()
    for d in col.find({}, {"_id":0}).sort("sequence",1): h.update(json.dumps(d,sort_keys=True,separators=(",",":"),default=str).encode()+b"\n")
    return h.hexdigest()

def retention():
    cutoff=time.time()-7*86400
    for p in BACKUPS.iterdir() if BACKUPS.exists() else []:
        if p.is_dir() and p.stat().st_mtime<cutoff: shutil.rmtree(p); print("[RETENTION] Removed",p)

def benchmark(client,n):
    col=client[DB][COLL]; stamp=datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dest=BACKUPS/f"{stamp}_{n}"; dest.mkdir(parents=True,exist_ok=True)
    print(f"\n=== {n:,} document benchmark ==="); seed(col,n)
    original_count=col.count_documents({}); original_hash=checksum(col); original_sample=col.find_one({"sequence":0},{"_id":0})
    archive=dest/"backup.archive"
    t=time.perf_counter()
    run(["mongodump",f"--uri={URI}",f"--db={DB}",f"--collection={COLL}",f"--archive={archive}"])
    dump_s=time.perf_counter()-t
    col.update_many({}, {"$set":{"status":"modified","verified":False}})
    t=time.perf_counter()
    restore_result=run(["mongorestore",f"--uri={URI}","--drop",f"--nsInclude={DB}.{COLL}",f"--archive={archive}"])
    restore_s=time.perf_counter()-t
    print("Restore output:", restore_result.stdout.strip(), restore_result.stderr.strip())
    restored=client[DB][COLL]
    count_ok=restored.count_documents({})==original_count
    hash_ok=checksum(restored)==original_hash
    restored_sample=restored.find_one({"sequence":0},{"_id":0})
    if not hash_ok:
        print("DEBUG original sample:", repr(original_sample))
        print("DEBUG restored sample:", repr(restored_sample))
        print("DEBUG original hash:", original_hash)
        print("DEBUG restored hash:", checksum(restored))
    print(f"Backup: {dump_s:.3f}s | Restore: {restore_s:.3f}s | Count: {'PASS' if count_ok else 'FAIL'} | Checksum: {'PASS' if hash_ok else 'FAIL'}")
    if not(count_ok and hash_ok): raise RuntimeError(f"Restore integrity failed for {n} docs")
    print("[OK] Restore verified: document count AND content checksum match.")
    return {"documents":n,"backup_seconds":round(dump_s,3),"restore_seconds":round(restore_s,3),"count_match":count_ok,"checksum_match":hash_ok,"backup_directory":str(dest)}

def main():
    require_tools(); BACKUPS.mkdir(parents=True,exist_ok=True); OUTPUT.mkdir(parents=True,exist_ok=True)
    c=MongoClient(URI,serverSelectionTimeoutMS=5000)
    try: c.admin.command("ping"); rows=[benchmark(c,n) for n in SIZES]
    finally: c.close()
    path=OUTPUT/"backup_benchmark.csv"
    with path.open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("\nDocuments | Backup(s) | Restore(s) | Verification")
    for r in rows: print(f"{r['documents']:>9} | {r['backup_seconds']:>9.3f} | {r['restore_seconds']:>10.3f} | PASS")
    print("RPO: 1 hour when hourly scheduler is enabled.")
    print(f"Measured restore component of RTO: {max(r['restore_seconds'] for r in rows):.3f}s (application restart excluded).")
    print("Benchmark CSV:",path); retention()

if __name__=="__main__": main()
