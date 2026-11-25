"""Optional separate Docker demonstration; integrated website uses its existing server.py."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from advisor import router
app=FastAPI(title='CTI Sentinel Appendix A Threat Advisor')
app.mount('/static',StaticFiles(directory=Path(__file__).resolve().parent/'static'),name='static')
app.include_router(router)
@app.get('/health')
def health():return {'ok':True,'component':'CTI Sentinel AI Threat Advisor'}
