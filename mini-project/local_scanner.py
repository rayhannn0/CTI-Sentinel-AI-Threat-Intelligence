"""Opt-in, read-only macOS diagnostic checks for CTI Sentinel.

Not malware detection, vulnerability scanning, or remediation. The user must
explicitly request each local scan and separately consent to Gemini analysis.
"""
from __future__ import annotations
import os
import platform
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from pymongo import MongoClient, DESCENDING

router = APIRouter()
MONGO_URI = os.getenv('ADVISOR_MONGO_URI', os.getenv('LAB18_THREAT_URI', 'mongodb://127.0.0.1:27021'))

class ScanRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=90, pattern=r'^[\w.\-]+$')
    confirmation: Literal['RUN_READ_ONLY_MACOS_SCAN']

class AnalyzeRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=90, pattern=r'^[\w.\-]+$')
    scan_id: str = Field(min_length=1, max_length=45, pattern=r'^[a-f0-9\-]+$')
    confirmation: Literal['SEND_SUMMARY_TO_GEMINI']


def local_only(request: Request):
    # Service listens on loopback by default; protect even if reconfigured.
    if request.client is None or request.client.host not in ('127.0.0.1', '::1'):
        raise HTTPException(403, 'Local scanner can only be used from this computer.')
    origin = request.headers.get('origin')
    if origin and origin not in ('http://127.0.0.1:8765', 'http://localhost:8765'):
        raise HTTPException(403, 'Cross-origin scanner requests are not permitted.')
    if platform.system() != 'Darwin':
        raise HTTPException(409, 'Local scanner requires native macOS; Docker/Linux backend cannot scan your Mac host.')


def run_checked(args, timeout=7):
    """Fixed command + arguments only; no shell, sudo, changes or recursive scans."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return ((p.stdout or p.stderr).strip()[:1100], p.returncode)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return (type(exc).__name__ + ': command unavailable or timed out', -1)


def clean(value, limit=150):
    # Restrict local content to short printable strings; no user paths in scan.
    return re.sub(r'[\x00-\x1f\x7f]', ' ', str(value)).strip()[:limit]


def scan():
    results=[]
    def add(check, status, details, recommendation):
        results.append({'check':check,'status':status,'details':clean(details,250),'recommendation':recommendation})

    version, rc = run_checked(['/usr/bin/sw_vers', '-productVersion'])
    add('macOS version', 'info' if rc == 0 else 'unknown', version if rc == 0 else 'Unable to query version',
        'Check Apple security updates and supported macOS releases.')

    gatekeeper, rc = run_checked(['/usr/sbin/spctl', '--status'])
    if rc == 0 and 'enabled' in gatekeeper.lower():
        state='pass'
    elif rc == 0 and 'disabled' in gatekeeper.lower():
        state='review'
    else:
        state='unknown'
    add('Gatekeeper', state, gatekeeper, 'Review Gatekeeper settings in System Settings if disabled.')

    fv, rc = run_checked(['/usr/bin/fdesetup', 'status'])
    fv_low=fv.lower()
    state='pass' if 'filevault is on' in fv_low else 'review' if 'filevault is off' in fv_low else 'unknown'
    add('FileVault', state, fv, 'Consider FileVault disk encryption after confirming recovery-key access.')

    updates, rc = run_checked(['/usr/sbin/softwareupdate', '--schedule'])
    state='info' if rc == 0 else 'unknown'
    add('Automatic update check',state,updates if rc == 0 else 'Unavailable',
        'Verify macOS security updates and automatic-update settings manually.')

    # Only show counts and generic names, never home directory paths or command lines.
    for label, path in [('User LaunchAgents', Path.home()/'Library'/'LaunchAgents'),
                        ('System LaunchAgents', Path('/Library/LaunchAgents')),
                        ('System LaunchDaemons', Path('/Library/LaunchDaemons'))]:
        try:
            names=[p.name for p in path.iterdir() if p.is_file() and p.suffix=='.plist']
            add(label, 'info', f'{len(names)} launch configuration file(s) detected',
                'Review unfamiliar startup items manually; their presence alone is not malicious.')
        except (OSError, PermissionError):
            add(label, 'unknown', 'Location unavailable or access denied',
                'Review Login Items and background services in System Settings.')

    # No process arguments, filenames, addresses, browsing, contacts, or secrets collected.
    # Listening socket count is a simple exposure clue, not proof of a threat.
    out,rc=run_checked(['/usr/sbin/lsof','-nP','-iTCP','-sTCP:LISTEN'],timeout=9)
    if rc == 0:
        count=max(0,len(out.splitlines())-1)
        add('TCP listeners', 'info', f'{count} listening socket entries (not classified as malicious)',
            'Review unexpected listening services using trusted local tools.')
    else:
        add('TCP listeners', 'unknown', 'Listener count unavailable',
            'Inspect open listening services manually if needed.')

    return results


def db_connection():
    c=MongoClient(MONGO_URI,serverSelectionTimeoutMS=2400,connectTimeoutMS=2400)
    c.admin.command('ping')
    db=c['cti_advisor']
    db.local_scans.create_index([('session_id',1),('created_at',DESCENDING)])
    return c,db

@router.post('/api/advisor/local-scan')
def local_scan(body: ScanRequest, request: Request):
    local_only(request)
    c, db = db_connection()
    try:
        # Avoid repeated accidental clicks; no background polling.
        recent=db.local_scans.find_one({'session_id':body.session_id},sort=[('created_at',-1)])
        if recent:
            previous_time = recent.get('created_at')
            # PyMongo returns naive UTC datetimes by default. Normalize before
            # subtracting from an aware UTC datetime (especially for old sessions).
            if isinstance(previous_time, datetime):
                if previous_time.tzinfo is None:
                    previous_time = previous_time.replace(tzinfo=timezone.utc)
                else:
                    previous_time = previous_time.astimezone(timezone.utc)
                if (datetime.now(timezone.utc) - previous_time).total_seconds() < 15:
                    raise HTTPException(429, 'Please allow 15 seconds between manual scans.')
        findings=scan()
        record={'scan_id':str(uuid.uuid4()),'session_id':body.session_id,
                'created_at':datetime.now(timezone.utc),'platform':'macOS',
                'scope':'Limited local configuration checks; not a malware or CVE scan',
                'findings':findings,'gemini_analysis':None}
        db.local_scans.insert_one(record)
        return {'ok':True,'scan_id':record['scan_id'],'created_at':record['created_at'].isoformat(),
                'scope':record['scope'],'findings':findings,'data_sent_to_gemini':False}
    finally:c.close()

@router.get('/api/advisor/local-scans')
def local_scans(request: Request, session_id: str= 'demo'):
    local_only(request)
    if not re.fullmatch(r'[\w.\-]{1,90}',session_id):
        raise HTTPException(422,'Invalid session ID')
    c,db=db_connection()
    try:
        rows=list(db.local_scans.find({'session_id':session_id},
            {'_id':0,'scan_id':1,'created_at':1,'scope':1,'findings':1,'gemini_analysis':1})
            .sort('created_at',-1).limit(10))
        for row in rows:row['created_at']=row['created_at'].isoformat()
        return {'ok':True,'scans':rows}
    finally:c.close()

@router.post('/api/advisor/analyze-local-scan')
def analyze_local_scan(body: AnalyzeRequest,request: Request):
    local_only(request)
    c,db=db_connection()
    try:
        row=db.local_scans.find_one({'scan_id':body.scan_id,'session_id':body.session_id})
        if not row:raise HTTPException(404,'Scan was not found for this session.')
        # Only bounded check statuses and generic summaries leave the computer.
        safe=[{'check':r['check'],'status':r['status'],'details':r['details']} for r in row['findings']]
        prompt=('Analyze these *limited read-only macOS configuration observations*. '
                'They are NOT confirmed threats, malware detections, or live CVEs. '
                'Explain each observation, sensible verification steps and reversible defensive advice. '
                'Separate observations from uncertainties. Do not claim to have performed any fixes. '
                'No user-private content or system commands should be requested.\n\n'
                + __import__('json').dumps(safe,ensure_ascii=False))
        from advisor import llm
        answer, status=llm(prompt)
        if not answer:
            return {'ok':False,'model_status':status,'analysis':None,
                    'message':'Gemini unavailable; local scan findings remain saved.'}
        db.local_scans.update_one({'scan_id':body.scan_id,'session_id':body.session_id},
                                  {'$set':{'gemini_analysis':answer[:14000]}})
        return {'ok':True,'model_status':status,'analysis':answer,
                'message':'Only the limited scan summary was submitted to Gemini.'}
    finally:c.close()
