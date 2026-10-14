from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import engine

app = FastAPI(title="Namotai", version="0.1.0")


@app.get("/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"api": "ok", "db": "ok"}
    except Exception as e:
        return {"api": "ok", "db": f"error: {e}"}
