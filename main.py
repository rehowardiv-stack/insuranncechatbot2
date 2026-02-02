# main.py - Complete Insurance AI Chatbot with Facebook Integration
import os
import json
import sqlite3
import uuid
import hashlib
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import aiofiles
from pydantic import BaseModel
from groq import Groq
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Insurance AI Assistant", version="1.0")

# Security
security = HTTPBasic()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "insurance_bot_2025")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
DB_FILE = "insurance_leads.db"

# Validate required environment variables
if not GROQ_API_KEY:
    logger.error("❌ GROQ_API_KEY not found in environment")
if not FB_PAGE_ACCESS_TOKEN:
    logger.warning("Facebook integration disabled - FB_PAGE_ACCESS_TOKEN not set")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------------------
# Database Setup
# ---------------------------
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Leads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            location TEXT,
            home_value TEXT,
            interest_level TEXT DEFAULT 'low',
            source TEXT DEFAULT 'web',
            conversation_summary TEXT,
            affiliate_clicked BOOLEAN DEFAULT 0,
            quote_requested BOOLEAN DEFAULT 0
        )
    ''')
    
    # Chat history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            role TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')
    
    # Admin logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            admin_user TEXT,
            action TEXT,
            details TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

# ---------------------------
# Database Functions
# ---------------------------
def save_lead(data: Dict):
    """Save lead to database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO leads 
        (session_id, name, email, phone, location, home_value, 
         interest_level, source, conversation_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('session_id'),
        data.get('name'),
        data.get('email'),
        data.get('phone'),
        data.get('location'),
        data.get('home_value'),
        data.get('interest_level', 'low'),
        data.get('source', 'web'),
        data.get('conversation_summary', '')
    ))
    
    conn.commit()
    conn.close()
    logger.info(f"✅ Lead saved: {data.get('email', 'No email')}")

def save_chat_message(session_id: str, role: str, message: str):
    """Save chat message to history"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_history (session_id, role, message)
        VALUES (?, ?, ?)
    ''', (session_id, role, message))
    
    conn.commit()
    conn.close()

def get_chat_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Get chat history for session"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT role, message, timestamp 
        FROM chat_history 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (session_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"role": row[0], "message": row[1], "timestamp": row[2]} for row in rows[::-1]]

def get_all_leads() -> List[Dict]:
    """Get all leads for admin"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM leads ORDER BY timestamp DESC
    ''')
    
    columns = [column[0] for column in cursor.description]
    leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return leads

def get_lead_count() -> int:
    """Get total lead count"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM leads")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def log_admin_action(admin_user: str, action: str, details: str = ""):
    """Log admin activity"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO admin_logs (admin_user, action, details)
        VALUES (?, ?, ?)
    ''', (admin_user, action, details))
    
    conn.commit()
    conn.close()

# ---------------------------
# AI Functions
# ---------------------------
async def get_ai_response(messages: List[Dict]) -> str:
    """Get response from Groq AI"""
    system_prompt = """You are a professional home insurance assistant. Help users with:
    1. Insurance information and quotes
    2. Coverage explanations
    3. Risk assessment guidance
    4. Premium estimations
    
    Always be helpful, professional, and suggest speaking with licensed agents.
    When users ask for quotes, collect: location, home value, and contact info.
    Never give financial advice - recommend consulting professionals."""
    
    formatted_messages = [{"role": "system", "content": system_prompt}]
    
    # Add last 6 messages for context
    for msg in messages[-6:]:
        formatted_messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["message"]
        })
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=formatted_messages,
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=500
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try again or use our quick quote form."

# ---------------------------
# Authentication
# ---------------------------
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    if credentials.username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid username")
    
    # Check password hash
    password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    if ADMIN_PASSWORD_HASH and password_hash != ADMIN_PASSWORD_HASH:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Allow default password for development
    if not ADMIN_PASSWORD_HASH and credentials.password != "admin123":
        raise HTTPException(status_code=401, detail="Invalid password")
    
    return credentials.username

# ---------------------------
# Facebook Integration
# ---------------------------
async def send_facebook_message(recipient_id: str, message: str):
    """Send message via Facebook Messenger"""
    if not FB_PAGE_ACCESS_TOKEN:
        return False
    
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={FB_PAGE_ACCESS_TOKEN}"
    
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message}
    }
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Facebook send error: {e}")
        return False

# ---------------------------
# Routes
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Chat interface page"""
    session_id = str(uuid.uuid4())
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "session_id": session_id
    })

@app.post("/api/chat")
async def chat_api(
    message: str = Form(...),
    session_id: str = Form(...)
):
    """API endpoint for chat"""
    # Save user message
    save_chat_message(session_id, "user", message)
    
    # Get chat history
    history = get_chat_history(session_id, limit=6)
    
    # Get AI response
    ai_response = await get_ai_response(history)
    
    # Save AI response
    save_chat_message(session_id, "assistant", ai_response)
    
    # Check if this is a quote request
    quote_keywords = ["quote", "price", "how much", "cost", "rate"]
    if any(keyword in message.lower() for keyword in quote_keywords):
        ai_response += "\n\n**Need actual quotes?** Provide your email for quotes from our partner carriers."
    
    return JSONResponse(content={
        "response": ai_response,
        "session_id": session_id
    })

@app.post("/api/lead")
async def save_lead_api(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    location: str = Form(""),
    home_value: str = Form(""),
    session_id: str = Form(...)
):
    """Save lead from form"""
    lead_data = {
        "session_id": session_id,
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "home_value": home_value,
        "interest_level": "high",
        "conversation_summary": "Form submission"
    }
    
    save_lead(lead_data)
    
    # Return affiliate link (The Zebra example)
    affiliate_link = f"https://www.thezebra.com/?agent=INSURANCEBOT&email={email}&source=chatbot"
    
    return JSONResponse(content={
        "success": True,
        "message": "Thank you! We'll contact you shortly.",
        "affiliate_link": affiliate_link
    })

# ---------------------------
# Facebook Webhook
# ---------------------------
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    """Facebook webhook verification"""
    if hub_mode == "subscribe" and hub_verify_token == FB_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def facebook_webhook(request: Request):
    """Handle Facebook Messenger messages"""
    try:
        data = await request.json()
        
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message_text = messaging.get("message", {}).get("text")
                
                if sender_id and message_text:
                    # Process message with AI
                    session_id = f"fb_{sender_id}"
                    save_chat_message(session_id, "user", message_text)
                    
                    history = get_chat_history(session_id, limit=6)
                    ai_response = await get_ai_response(history)
                    
                    save_chat_message(session_id, "assistant", ai_response)
                    
                    # Send response back via Messenger
                    await send_facebook_message(sender_id, ai_response)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

# ---------------------------
# Admin Routes
# ---------------------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, username: str = Depends(verify_admin)):
    """Admin dashboard"""
    leads = get_all_leads()
    lead_count = len(leads)
    
    # Get today's leads
    today = datetime.now().strftime("%Y-%m-%d")
    today_leads = [lead for lead in leads if lead["timestamp"].startswith(today)]
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "leads": leads,
        "lead_count": lead_count,
        "today_leads": len(today_leads),
        "username": username
    })

@app.get("/api/admin/leads")
async def get_leads_api(username: str = Depends(verify_admin)):
    """API endpoint for leads (for AJAX)"""
    leads = get_all_leads()
    return JSONResponse(content={"leads": leads})

@app.delete("/api/admin/lead/{lead_id}")
async def delete_lead(lead_id: int, username: str = Depends(verify_admin)):
    """Delete a lead"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    
    log_admin_action(username, "delete_lead", f"Deleted lead ID: {lead_id}")
    
    return JSONResponse(content={"success": True})

# ---------------------------
# Affiliate Tracking
# ---------------------------
@app.get("/track/{affiliate_id}")
async def track_affiliate_click(
    affiliate_id: str,
    email: Optional[str] = None,
    source: Optional[str] = None
):
    """Track affiliate link clicks"""
    # Log the click (you'd save this to a separate table)
    logger.info(f"Affiliate click: {affiliate_id}, Email: {email}, Source: {source}")
    
    # Redirect to actual affiliate URL
    if affiliate_id == "thezebra":
        redirect_url = "https://www.thezebra.com/?agent=INSURANCEBOT"
    elif affiliate_id == "policygenius":
        redirect_url = "https://www.policygenius.com/?ref=INSURANCEBOT"
    elif affiliate_id == "lemonade":
        redirect_url = "https://www.lemonade.com/landing/ref-INSURANCEBOT"
    else:
        redirect_url = "https://www.thezebra.com"
    
    # Add tracking parameters
    if email:
        redirect_url += f"&email={email}"
    if source:
        redirect_url += f"&source={source}"
    
    return RedirectResponse(url=redirect_url, status_code=302)

# ---------------------------
# Health Check
# ---------------------------
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ---------------------------
# Startup Event
# ---------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    init_database()
    logger.info("🚀 Insurance AI Assistant started successfully")

# Run with: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
