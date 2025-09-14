from dotenv import load_dotenv
from fastapi import FastAPI, Request
from datetime import datetime
import asyncpg
import os
import dotenv
import httpx

load_dotenv()
app = FastAPI()

DB_URL = os.getenv("DATABASE_URL")  # Supabase connection string
BOT_ID = os.getenv("BOT_ID")        # GroupMe Bot ID

@app.on_event("startup")
async def startup():
    app.state.db = await asyncpg.create_pool(DB_URL)

@app.post("/groupme")
async def groupme_webhook(request: Request):
    data = await request.json()
    user = data.get("name")
    text = data.get("text")

    # Only log bets with the right prefix
    if text and text.startswith("BET - "):
        bet_text = text[len("BET - "):].strip()
        async with app.state.db.acquire() as conn:
            await conn.execute(
                "insert into bets (user_name, bet_text, timestamp) values ($1, $2, $3)",
                user, bet_text, datetime.utcnow()
            )

        # Optional: reply in GroupMe
        if BOT_ID:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://api.groupme.com/v3/bots/post",
                    json={"bot_id": BOT_ID, "text": f"Bet logged: {bet_text}"}
                )

    return {"status": "ok"}
