"""Apply an additive advisor patch to the *current* CTI Sentinel files.
Does not replace the current server.py or any existing lab module.
"""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
SERVER=ROOT/'server.py';PAGE=ROOT/'static'/'sentinel.html'
assert SERVER.is_file() and PAGE.is_file(), 'Existing CTI Sentinel server.py and static/sentinel.html must be present.'
server=SERVER.read_text()
addition='\n# Add-on: Appendix A AI Threat Advisor\nfrom advisor import router as advisor_router\napp.include_router(advisor_router)\n'
if 'app.include_router(advisor_router)' not in server:
    # Register before the script entrypoint so running `python server.py` works.
    anchor="if __name__ == '__main__':"
    if anchor in server:server=server.replace(anchor,addition+'\n'+anchor,1)
    else:server+=addition
    shutil.copy2(SERVER,ROOT/'server.py.before_advisor.bak')
    SERVER.write_text(server)
    print('Registered AI Advisor endpoints in existing server.py')
else:print('Advisor router already installed.')
page=PAGE.read_text()
link='<a class="pill green" href="/advisor" style="text-decoration:none">◈ AI Threat Advisor · FINAL ASSESSMENT</a>'
if 'href="/advisor"' not in page:
    target='<div class="top-actions">'
    if target in page:page=page.replace(target,target+link,1)
    else:page=page.replace('</header>',link+'</header>',1)
    shutil.copy2(PAGE,ROOT/'static'/'sentinel.html.before_advisor.bak')
    PAGE.write_text(page)
    print('Added AI Advisor link to CTI Sentinel top navigation.')
else:print('Navigation link already installed.')
print('Success. Restart CTI Sentinel and open http://127.0.0.1:8765/advisor')
