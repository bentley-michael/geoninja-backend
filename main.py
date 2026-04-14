# Geography Ninja — FastAPI Backend
# pip install fastapi uvicorn supabase python-dotenv pydantic resend

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime, timedelta
import os
import resend
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = FastAPI(title="Geography Ninja API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://geographyninja.com",
        "https://geoninja-zeta.vercel.app",
        "http://localhost:5173",
    ],
    allow_origin_regex="https://geoninja.*\\.vercel\\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Clients ──────────────────────────────────────────────────────────────────
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"],
)
resend.api_key = os.environ["RESEND_API_KEY"]
FROM_EMAIL = "GeoNinja <onboarding@resend.dev>"

# ─── Models ───────────────────────────────────────────────────────────────────
class SaveScoreRequest(BaseModel):
    user_id: str
    username: Optional[str] = "Ninja"
    score: int
    total: int = 10
    game_date: str

class RegisterEmailRequest(BaseModel):
    user_id: str
    email: EmailStr

# ─── Email Templates ──────────────────────────────────────────────────────────
def streak_reminder_html(streak: int, best_streak: int) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0e1a;font-family:system-ui,sans-serif;">
  <div style="max-width:480px;margin:0 auto;padding:32px 24px;">
    <div style="text-align:center;margin-bottom:32px;">
      <div style="font-size:56px;">🥷</div>
      <h1 style="color:#f1f5f9;font-size:28px;margin:0;">Geography <span style="color:#6366f1;">Ninja</span></h1>
    </div>
    <div style="background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);border-radius:16px;padding:24px;text-align:center;margin-bottom:24px;">
      <div style="font-size:36px;">🔥</div>
      <div style="color:#fbbf24;font-size:24px;font-weight:700;">{streak} Day Streak</div>
      <div style="color:#64748b;font-size:14px;margin-top:4px;">Best: {best_streak} days — don't break it now</div>
    </div>
    <div style="text-align:center;margin-bottom:32px;">
      <p style="color:#94a3b8;font-size:16px;">Today's 10-question challenge is ready. Keep the streak alive.</p>
      <a href="https://geographyninja.com" style="display:inline-block;background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;text-decoration:none;padding:16px 40px;border-radius:12px;font-size:17px;font-weight:700;">Play Today's Challenge →</a>
    </div>
    <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.06);padding-top:20px;">
      <p style="color:#334155;font-size:12px;">Geography Ninja · <a href="https://geographyninja.com" style="color:#475569;">geographyninja.com</a><br>
      <a href="https://geographyninja.com/unsubscribe" style="color:#475569;">Unsubscribe</a></p>
    </div>
  </div>
</body>
</html>"""


def welcome_html() -> str:
    return """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0e1a;font-family:system-ui,sans-serif;">
  <div style="max-width:480px;margin:0 auto;padding:32px 24px;">
    <div style="text-align:center;margin-bottom:32px;">
      <div style="font-size:56px;">🥷</div>
      <h1 style="color:#f1f5f9;font-size:28px;margin:0;">Welcome to Geography <span style="color:#6366f1;">Ninja</span></h1>
    </div>
    <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);border-radius:16px;padding:24px;margin-bottom:24px;">
      <p style="color:#94a3b8;font-size:15px;margin:0 0 8px;">You're in. Here's what happens next:</p>
      <ul style="color:#cbd5e1;font-size:14px;padding-left:20px;margin:0;line-height:2;">
        <li>A new 10-question challenge every day</li>
        <li>Daily reminder so you never break your streak</li>
        <li>Climb the ranks from White Belt to Black Belt 🥋</li>
      </ul>
    </div>
    <div style="text-align:center;margin-bottom:32px;">
      <a href="https://geographyninja.com" style="display:inline-block;background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;text-decoration:none;padding:16px 40px;border-radius:12px;font-size:17px;font-weight:700;">Play Today's Challenge →</a>
    </div>
    <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.06);padding-top:20px;">
      <p style="color:#334155;font-size:12px;">Geography Ninja · <a href="https://geographyninja.com" style="color:#475569;">geographyninja.com</a><br>
      <a href="https://geographyninja.com/unsubscribe" style="color:#475569;">Unsubscribe</a></p>
    </div>
  </div>
</body>
</html>"""

# ─── Helpers ──────────────────────────────────────────────────────────────────
def send_welcome_email(to_email: str):
    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": "🥷 You're in — Geography Ninja daily challenge",
            "html": welcome_html(),
        })
    except Exception as e:
        print(f"Welcome email failed: {e}")


def send_streak_reminders():
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    rows = supabase.table("user_streaks") \
        .select("email, streak, best_streak, last_played") \
        .not_.is_("email", "null") \
        .eq("last_played", yesterday) \
        .execute()
    sent = 0
    for row in rows.data:
        email = row.get("email")
        if not email:
            continue
        try:
            resend.Emails.send({
                "from": FROM_EMAIL,
                "to": email,
                "subject": f"🔥 {row['streak']} day streak — play today's Geography Ninja",
                "html": streak_reminder_html(row["streak"], row["best_streak"]),
            })
            sent += 1
        except Exception as e:
            print(f"Reminder failed for {email}: {e}")
    return {"sent": sent, "date": today}

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "service": "Geography Ninja API"}

@app.get("/health")
def health():
    return {"status": "healthy", "time": datetime.utcnow().isoformat()}

@app.post("/scores")
def save_score(req: SaveScoreRequest):
    today = req.game_date
    yesterday = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    supabase.table("game_results").upsert({
        "user_id": req.user_id, "game_date": today, "score": req.score,
        "total": req.total, "username": req.username,
    }, on_conflict="user_id,game_date").execute()
    streak_row = supabase.table("user_streaks").select("*").eq("user_id", req.user_id).execute()
    if streak_row.data:
        row = streak_row.data[0]
        last = row.get("last_played")
        current_streak = row.get("streak", 0)
        new_streak = current_streak + 1 if last == yesterday else (current_streak if last == today else 1)
        best = max(row.get("best_streak", 0), new_streak)
        total_games = row.get("total_games", 0) + (0 if last == today else 1)
        total_correct = row.get("total_correct", 0) + (0 if last == today else req.score)
        supabase.table("user_streaks").update({
            "streak": new_streak, "best_streak": best, "last_played": today,
            "total_games": total_games, "total_correct": total_correct,
        }).eq("user_id", req.user_id).execute()
        return {"streak": new_streak, "best_streak": best, "total_games": total_games, "total_correct": total_correct}
    else:
        supabase.table("user_streaks").insert({
            "user_id": req.user_id, "streak": 1, "best_streak": 1, "last_played": today,
            "total_games": 1, "total_correct": req.score, "username": req.username,
        }).execute()
        return {"streak": 1, "best_streak": 1, "total_games": 1, "total_correct": req.score}

@app.post("/register-email")
def register_email(req: RegisterEmailRequest, background_tasks: BackgroundTasks):
    existing = supabase.table("user_streaks").select("user_id").eq("user_id", req.user_id).execute()
    if existing.data:
        supabase.table("user_streaks").update({"email": req.email}).eq("user_id", req.user_id).execute()
    else:
        supabase.table("user_streaks").insert({
            "user_id": req.user_id, "email": req.email,
            "streak": 0, "best_streak": 0, "total_games": 0, "total_correct": 0,
        }).execute()
    background_tasks.add_task(send_welcome_email, req.email)
    return {"status": "ok"}

@app.get("/streaks/{user_id}")
def get_streak(user_id: str):
    row = supabase.table("user_streaks").select("*").eq("user_id", user_id).execute()
    if not row.data:
        return {"streak": 0, "best_streak": 0, "total_games": 0, "total_correct": 0}
    return row.data[0]

@app.get("/leaderboard/daily")
def daily_leaderboard():
    today = date.today().isoformat()
    result = supabase.table("game_results").select("username, score, user_id") \
        .eq("game_date", today).order("score", desc=True).limit(20).execute()
    return {"date": today, "leaderboard": result.data}

@app.get("/leaderboard/alltime")
def alltime_leaderboard():
    result = supabase.table("user_streaks") \
        .select("username, best_streak, total_correct, total_games") \
        .order("best_streak", desc=True).limit(20).execute()
    return {"leaderboard": result.data}

@app.post("/cron/send-reminders")
def cron_send_reminders(secret: str = ""):
    cron_secret = os.environ.get("CRON_SECRET", "")
    if not cron_secret or secret != cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return send_streak_reminders()

@app.get("/unsubscribe")
def unsubscribe(email: str):
    supabase.table("user_streaks").update({"email": None}).eq("email", email).execute()
    return {"status": "ok", "message": "Unsubscribed"}
