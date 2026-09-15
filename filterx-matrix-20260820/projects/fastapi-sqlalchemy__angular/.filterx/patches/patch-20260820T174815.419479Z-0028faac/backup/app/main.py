from fastapi import FastAPI
from app import models as _models

app = FastAPI(title='FilterX matrix fixture')

@app.get('/health')
def health(): return {'ok': True}

# FILTERX:ROUTER_MOUNT
