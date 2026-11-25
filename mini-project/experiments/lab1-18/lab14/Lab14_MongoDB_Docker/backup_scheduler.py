"""Hourly backup scheduler with seven-day retention."""
import os, shutil, subprocess, time
from datetime import datetime
from pathlib import Path
import schedule
URI=os.getenv("MONGO_URI","mongodb://localhost:27017"); ROOT=Path(os.getenv("BACKUP_ROOT","backups")); DB="lab14"
def retention():
    cutoff=time.time()-7*86400; ROOT.mkdir(parents=True,exist_ok=True)
    for p in ROOT.iterdir():
        if p.is_dir() and p.stat().st_mtime<cutoff: shutil.rmtree(p); print("[RETENTION] Deleted",p,flush=True)
def backup():
    ROOT.mkdir(parents=True,exist_ok=True); dest=ROOT/("hourly_"+datetime.now().strftime("%Y%m%d-%H%M%S")); dest.mkdir(parents=True,exist_ok=True)
    r=subprocess.run(["mongodump",f"--uri={URI}",f"--db={DB}",f"--out={dest}"],capture_output=True,text=True)
    if r.returncode: print("[ERROR]",r.stderr[-1200:],flush=True)
    else: print("[OK] Backup:",dest,flush=True); retention()
if __name__=="__main__":
    backup(); schedule.every(1).hour.do(backup); print("Hourly backups scheduled; retention is 7 days.",flush=True)
    while True: schedule.run_pending(); time.sleep(1)
