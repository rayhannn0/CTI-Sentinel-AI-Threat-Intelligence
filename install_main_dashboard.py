"""Safe, repeatable, additive CTI Sentinel main-dashboard installer.
Run: python3 install_main_dashboard.py from the existing project directory.
"""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
server=ROOT/'server.py'; sentinel=ROOT/'static/sentinel.html'; advisor=ROOT/'static/advisor.html'
required=[server,sentinel,ROOT/'static/dashboard.html',ROOT/'static/dashboard.css',ROOT/'static/dashboard.js']
missing=[str(p) for p in required if not p.is_file()]
if missing:raise SystemExit('Missing files: '+', '.join(missing)+'\nExtract the ZIP into ~/Downloads first.')
def edit(path,update):
    before=path.read_text(); after=update(before)
    if before!=after:
        backup=path.with_name(path.name+'.before_main_dashboard.bak')
        if not backup.exists():shutil.copy2(path,backup)
        path.write_text(after)
        print('Updated',path.relative_to(ROOT))
    else:print('Already updated',path.relative_to(ROOT))
def add_routes(s):
    if "@app.get('/dashboard')" not in s and '@app.get("/dashboard")' not in s:
        block="\n# Unified navigation landing page (keeps every existing lab and advisor route).\n@app.get('/dashboard')\ndef main_dashboard_page():\n    return FileResponse(ROOT / 'static/dashboard.html', headers={'Cache-Control':'no-store, max-age=0'})\n\n"
        anchor="if __name__ == '__main__':"
        if anchor in s:s=s.replace(anchor,block+anchor,1)
        else:s+=block
    # Keep the old /index.html resource available under /static/index.html.
    orig="def index(): return FileResponse(ROOT / 'static/index.html')"
    if orig in s:s=s.replace(orig,"def index(): return FileResponse(ROOT / 'static/dashboard.html', headers={'Cache-Control':'no-store, max-age=0'})",1)
    return s
edit(server,add_routes)
def add_lab_nav(s):
    link='<a class="pill violet" href="/dashboard" style="text-decoration:none">◈ Main Dashboard</a>'
    if 'href="/dashboard"' not in s:
        marker='<div class="top-actions">'
        if marker not in s:raise RuntimeError('Could not locate lab top navigation: no files changed beyond server')
        s=s.replace(marker,marker+link,1)
    return s
edit(sentinel,add_lab_nav)
if advisor.exists():
    def add_advisor_nav(s):
        link='<a class="nav" href="/dashboard">◈ Main Dashboard</a>'
        if 'href="/dashboard"' not in s:
            marker='<a class="nav" href="/sentinel?lab=18">'
            if marker in s:s=s.replace(marker,link+marker,1)
            else:s=s.replace('<div class="side-caption">WORKSPACE</div>','<div class="side-caption">WORKSPACE</div>'+link,1)
        return s
    edit(advisor,add_advisor_nav)
print('Installed: http://127.0.0.1:8765/dashboard  |  http://127.0.0.1:8765/')
