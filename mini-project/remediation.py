"""Conservative user-approved quarantine for files in the user's Downloads folder.

Not an antivirus or automatic malware classification engine. The user chooses an
individual file, checks its SHA-256, and explicitly authorizes a reversible move.
No elevated permissions, shell commands, system path changes, process termination,
or AI-initiated remediations are supported.
"""
from __future__ import annotations

import hashlib
import os
import platform
import re
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from pymongo import MongoClient

router = APIRouter()
MONGO_URI = os.getenv('ADVISOR_MONGO_URI', os.getenv('LAB18_THREAT_URI', 'mongodb://127.0.0.1:27021'))
MAX_FILE = 100 * 1024 * 1024

class PreviewBody(BaseModel):
    session_id: str = Field(min_length=1, max_length=90, pattern=r'^[\w.\-]+$')
    filename: str = Field(min_length=1, max_length=255)

class QuarantineBody(PreviewBody):
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    confirmation: Literal['QUARANTINE_THIS_EXACT_FILE']

class RestoreBody(BaseModel):
    session_id: str = Field(min_length=1, max_length=90, pattern=r'^[\w.\-]+$')
    quarantine_id: str = Field(pattern=r'^[0-9a-f\-]{36}$')
    confirmation: Literal['RESTORE_THIS_EXACT_FILE']


def local_only(request: Request):
    if (request.client is None or request.client.host not in ('127.0.0.1', '::1')
            or platform.system() != 'Darwin'):
        raise HTTPException(403, 'Quarantine requires the native macOS local server.')
    origin = request.headers.get('origin')
    if origin and origin not in ('http://127.0.0.1:8765', 'http://localhost:8765'):
        raise HTTPException(403, 'Cross-origin requests are not permitted.')


def downloads():
    return Path.home() / 'Downloads'


def quarantine_dir():
    return Path.home() / '.cti_sentinel_quarantine'


def safe_filename(filename: str):
    if (filename in ('.', '..') or filename.startswith('.') or '/' in filename
            or '\\' in filename or '\x00' in filename or filename != Path(filename).name):
        raise HTTPException(422, 'Enter only a non-hidden filename directly in Downloads (not a path).')
    return filename


def open_source(filename):
    filename = safe_filename(filename)
    directory = downloads()
    try:
        folder_fd = os.open(directory, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    except OSError:
        raise HTTPException(409, 'Downloads folder is unavailable.')
    try:
        fd = os.open(filename, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=folder_fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_FILE:
            raise HTTPException(422, 'Only regular files under 100 MiB with no additional hard links are allowed.')
        if info.st_uid != os.getuid():
            raise HTTPException(403, 'Only files owned by the current user can be quarantined.')
        return folder_fd, fd, info
    except HTTPException:
        os.close(folder_fd)
        raise
    except OSError:
        os.close(folder_fd)
        raise HTTPException(404, 'File not found or not safely accessible in Downloads.')


def digest_file(fd):
    sha = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        data = os.read(fd, 1024 * 1024)
        if not data:
            break
        sha.update(data)
    return sha.hexdigest()


def connect():
    c = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500, connectTimeoutMS=2500)
    c.admin.command('ping')
    return c, c['cti_advisor']['quarantined_files']


@router.post('/api/advisor/quarantine/preview')
def preview(body: PreviewBody, request: Request):
    local_only(request)
    folder_fd, fd, info = open_source(body.filename)
    try:
        return {'ok': True, 'filename':body.filename, 'sha256':digest_file(fd), 'size':info.st_size,
                'assessment':'Unclassified. A hash match alone does not establish malware.',
                'next_step':'Review this exact filename and fingerprint before authorizing quarantine.'}
    finally:
        os.close(fd)
        os.close(folder_fd)


@router.post('/api/advisor/quarantine/apply')
def quarantine(body: QuarantineBody, request: Request):
    local_only(request)
    folder_fd, fd, info = open_source(body.filename)
    try:
        if digest_file(fd) != body.sha256:
            raise HTTPException(409, 'File changed since preview; preview it again.')
        # The privileged scanner must never quarantine an arbitrary path or a folder.
        home_quarantine = quarantine_dir()
        home_quarantine.mkdir(mode=0o700, exist_ok=True)
        if home_quarantine.is_symlink() or not home_quarantine.is_dir():
            raise HTTPException(409, 'Unsafe quarantine folder.')
        os.chmod(home_quarantine, 0o700)
        qid = str(uuid.uuid4())
        target_name = qid + '.quarantined'
        # Open both directories and verify the file fingerprint/identity immediately
        # before the atomic rename. Never overwrite or execute the file.
        qfd = os.open(home_quarantine, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0))
        try:
            current = os.stat(body.filename, dir_fd=folder_fd, follow_symlinks=False)
            if (current.st_ino != info.st_ino or current.st_dev != info.st_dev
                    or current.st_size != info.st_size or current.st_mtime_ns != info.st_mtime_ns):
                raise HTTPException(409, 'File changed since preview; preview it again.')
            c, col = connect()
            try:
                # Preallocate the record: no file move if storage is unavailable.
                record={'quarantine_id':qid,'session_id':body.session_id,
                        'filename':body.filename,'sha256':body.sha256,'size':info.st_size,
                        'created_at':datetime.now(timezone.utc),'state':'pending',
                        'scope':'User-authorized file quarantine, not verified malware detection'}
                col.insert_one(record)
                try:
                    os.rename(body.filename, target_name, src_dir_fd=folder_fd, dst_dir_fd=qfd)
                except OSError:
                    col.delete_one({'quarantine_id':qid,'state':'pending'})
                    raise HTTPException(409, 'Could not move file into quarantine.')
                col.update_one({'quarantine_id':qid},{'$set':{'state':'quarantined'}})
                return {'ok':True,'quarantine_id':qid,'filename':body.filename,
                        'message':'File moved to private quarantine; no other files or settings changed.',
                        'can_restore':True}
            finally:
                c.close()
        finally:
            os.close(qfd)
    finally:
        os.close(fd)
        os.close(folder_fd)


@router.get('/api/advisor/quarantine/history')
def history(request:Request, session_id:str='demo'):
    local_only(request)
    if not re.fullmatch(r'[\w.\-]{1,90}', session_id):
        raise HTTPException(422, 'Invalid session ID.')
    c,col=connect()
    try:
        docs=list(col.find({'session_id':session_id,'state':{'$in':['quarantined','restored','pending']}},
                           {'_id':0,'quarantine_id':1,'filename':1,'state':1,'sha256':1})
                    .sort('created_at',-1).limit(20))
        return {'ok':True,'items':docs}
    finally:c.close()


@router.post('/api/advisor/quarantine/restore')
def restore(body:RestoreBody,request:Request):
    local_only(request)
    c,col=connect()
    try:
        row=col.find_one({'quarantine_id':body.quarantine_id,'session_id':body.session_id,'state':'quarantined'})
        if not row:
            raise HTTPException(404, 'Quarantined file not found for this session.')
        safe_filename(row['filename'])
        qdir=quarantine_dir()
        qfd=os.open(qdir, os.O_RDONLY | getattr(os,'O_DIRECTORY',0) | getattr(os,'O_NOFOLLOW',0))
        dfd=os.open(downloads(), os.O_RDONLY | getattr(os,'O_DIRECTORY',0))
        try:
            name=body.quarantine_id+'.quarantined'
            fd=os.open(name, os.O_RDONLY | getattr(os,'O_NOFOLLOW',0),dir_fd=qfd)
            try:
                info=os.fstat(fd)
                if (not stat.S_ISREG(info.st_mode) or info.st_size!=row['size']
                        or digest_file(fd)!=row['sha256']):
                    raise HTTPException(409,'Quarantined file failed integrity verification.')
                try:
                    # Atomic no-overwrite restore needs a hard link into Downloads
                    # followed by unlink from quarantine, only on same filesystem.
                    os.link(name,row['filename'],src_dir_fd=qfd,dst_dir_fd=dfd,follow_symlinks=False)
                except FileExistsError:
                    raise HTTPException(409,'Restore stopped: filename already exists in Downloads.')
                except OSError:
                    raise HTTPException(409,'Restore unavailable on this filesystem; no file changed.')
                os.unlink(name,dir_fd=qfd)
                col.update_one({'quarantine_id':body.quarantine_id},{'$set':{'state':'restored','restored_at':datetime.now(timezone.utc)}})
                return {'ok':True,'filename':row['filename'],'message':'Restored to Downloads without overwriting an existing file.'}
            finally:os.close(fd)
        finally:
            os.close(qfd)
            os.close(dfd)
    finally:c.close()
