from fastapi import FastAPI
from pydantic import BaseModel
from ..policy import Config
from ..pipeline import ZeroPHI

app = FastAPI(title="ZeroPHI PoC")
_cfg = Config()
_engine = ZeroPHI(_cfg)

class DeidRequest(BaseModel):
    text: str

class DeidResponse(BaseModel):
    text: str
    entities: list
    audit: list

@app.post("/deid", response_model=DeidResponse)
async def deid(req: DeidRequest):
    out = _engine.process(req.text)
    return DeidResponse(text=out.text, entities=out.entities, audit=out.audit)

@app.get("/health")
async def health():
    return {"status": "ok"}
