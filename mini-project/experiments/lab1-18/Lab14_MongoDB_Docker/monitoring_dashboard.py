"""Lab 14.1: MongoDB serverStatus monitoring and threshold alerts."""
import argparse, json, logging, os, time
from datetime import datetime, timezone
import requests
from pymongo import MongoClient
from rich.console import Console
from rich.table import Table

MONGO_URI=os.getenv("MONGO_URI","mongodb://localhost:27017")
LOG_DIR=os.getenv("LOG_DIR","logs")
os.makedirs(LOG_DIR,exist_ok=True)
LOG_FILE=os.path.join(LOG_DIR,"metrics.log")
logging.basicConfig(filename=LOG_FILE,level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s")
console=Console()

def replication_lag(client):
    try: repl=client.admin.command("replSetGetStatus")
    except Exception: return None
    members=repl.get("members",[])
    primaries=[m.get("optimeDate") for m in members if m.get("stateStr")=="PRIMARY" and m.get("optimeDate") is not None]
    if not primaries: return {}
    primary=max(primaries); result={}
    for m in members:
        if m.get("stateStr")=="SECONDARY" and m.get("optimeDate") is not None:
            result[m.get("name","secondary")]=max(0.0,(primary-m["optimeDate"]).total_seconds())
    return result

def get_metrics(client):
    s=client.admin.command("serverStatus"); wt=s.get("wiredTiger",{}).get("cache",{})
    con=s.get("connections",{}); ops=s.get("opcounters",{})
    requested=wt.get("pages requested from the cache",0); read=wt.get("pages read into cache",0)
    # Page-based estimate: fraction of cache page requests not requiring a page read.
    hit=None if not requested else max(0.0,(requested-read)/requested)
    return {"timestamp":datetime.now(timezone.utc).isoformat(),"connections_current":con.get("current",0),"connections_available":con.get("available",0),"opcounters":{k:ops.get(k,0) for k in ("insert","query","update","delete","getmore","command")},"cache_bytes_in_use":wt.get("bytes currently in the cache",0),"cache_max_bytes":wt.get("maximum bytes configured",0),"cache_dirty_bytes":wt.get("tracked dirty bytes in the cache",0),"cache_hit_ratio":hit,"replication_lag_seconds":replication_lag(client)}

def make_table(m):
    t=Table(title="MongoDB Metrics Dashboard"); t.add_column("Metric",style="cyan"); t.add_column("Value",justify="right",style="green")
    t.add_row("Connections (current)",str(m["connections_current"])); t.add_row("Connections (available)",str(m["connections_available"]))
    for k,v in m["opcounters"].items(): t.add_row("Opcounter: "+k,f"{v:,}")
    r=m["cache_hit_ratio"]; t.add_row("WiredTiger cache hit ratio","n/a" if r is None else f"{r*100:.2f}%")
    t.add_row("Cache bytes in use",f"{m['cache_bytes_in_use']:,}"); t.add_row("Cache maximum bytes",f"{m['cache_max_bytes']:,}"); t.add_row("Cache dirty bytes",f"{m['cache_dirty_bytes']:,}")
    lag=m["replication_lag_seconds"]
    if lag is None: t.add_row("Replica set","Not configured (standalone)")
    elif not lag: t.add_row("Replica set","No secondary lag data")
    else:
        for host,secs in lag.items(): t.add_row("Replication lag: "+host,f"{secs:.2f} seconds")
    return t

def alerts_for(m):
    a=[]; r=m["cache_hit_ratio"]
    if r is not None and r<0.80: a.append(f"WARNING: Cache hit ratio {r*100:.2f}% is below 80%.")
    lag=m["replication_lag_seconds"]
    if isinstance(lag,dict):
        for host,secs in lag.items():
            if secs>10: a.append(f"WARNING: Replication lag on {host} is {secs:.2f}s, above 10s.")
    return a

def webhook(alert):
    url=os.getenv("WEBHOOK_URL","").strip()
    if not url: return
    try:
        r=requests.post(url,json={"text":alert,"content":alert},timeout=8); r.raise_for_status()
    except requests.RequestException as e: logging.error("Webhook failed: %s",e)

def snapshot(client):
    m=get_metrics(client); console.print(make_table(m)); logging.info(json.dumps(m,default=str))
    for a in alerts_for(m): console.print(a,style="bold red"); logging.warning(a); webhook(a)

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--once",action="store_true"); p.add_argument("--interval",type=int,default=int(os.getenv("MONITOR_INTERVAL_SECONDS","30"))); args=p.parse_args(argv)
    c=MongoClient(MONGO_URI,serverSelectionTimeoutMS=5000)
    try:
        c.admin.command("ping"); console.print("[green][OK] Connected to MongoDB.[/green]")
        if args.once: snapshot(c); return
        console.print(f"Monitoring every {args.interval}s. Press Ctrl+C to stop.")
        while True: snapshot(c); time.sleep(args.interval)
    except KeyboardInterrupt: console.print("Monitoring stopped.")
    finally: c.close()
    print("Metrics log:",LOG_FILE)

if __name__=="__main__": main()
