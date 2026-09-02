"""
FastAPI application for Samsung Phone Query and Review System.
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from database import init_db, get_session, Phone
from chatbot.query_engine import PhoneQueryEngine
from chatbot.rag_chatbot import SamsungChatbot
from agents.multi_agent import AgentOrchestrator

app = FastAPI(title="Samsung Phone Query & Review System", version="1.0.0")

chatbot = None
orchestrator = None
query_engine = None


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    source: str = "chatbot"


def lazy_init():
    global chatbot, orchestrator, query_engine
    if chatbot is None:
        query_engine = PhoneQueryEngine()
        query_engine.build_index()
        chatbot = SamsungChatbot(llm_pipeline=None, embedder=None)
        chatbot.engine = query_engine
        orchestrator = AgentOrchestrator(llm=None)


@app.on_event("startup")
def startup():
    init_db()
    lazy_init()


@app.get("/")
def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/")


@app.get("/phones", include_in_schema=False)
def phones_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/phones")


@app.get("/phone/{name}", include_in_schema=False)
def phone_redirect(name: str):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/api/phone/{name}")


# --- API routes ---
@app.get("/api")
def api_root():
    return {
        "message": "Samsung Phone Query & Review System API",
        "endpoints": {
            "GET /api/phones": "List all phones",
            "GET /api/phone/{name}": "Get specs for a phone",
            "DELETE /api/phone/{name}": "Delete a phone",
            "DELETE /api/phones": "Delete all phones",
            "POST /api/query": "Ask any question about Samsung phones",
            "POST /api/review": "Get a multi-agent generated review",
            "POST /api/compare": "Compare two phones",
            "POST /api/scrape": "Scrape phone data from GSMArena",
            "POST /api/seed": "Seed database with fallback data",
        },
    }


@app.get("/api/phones")
def list_phones():
    lazy_init()
    phones = query_engine.list_all_phones()
    return {"count": len(phones), "phones": [p.to_dict() for p in phones]}


@app.delete("/api/phones")
def delete_all_phones():
    lazy_init()
    session = get_session()
    count = session.query(Phone).delete()
    session.commit()
    session.close()
    query_engine.build_index()
    return {"message": f"Deleted all {count} phones", "deleted_count": count}


@app.get("/api/phone/{name}")
def get_phone(name: str):
    lazy_init()
    phone = query_engine.get_phone_by_name(name)
    if not phone:
        raise HTTPException(status_code=404, detail=f"Phone '{name}' not found")
    return phone.to_dict()


@app.delete("/api/phone/{name}")
def delete_phone(name: str):
    lazy_init()
    session = get_session()
    phone = session.query(Phone).filter(Phone.name.ilike(f"%{name}%")).first()
    if not phone:
        session.close()
        raise HTTPException(status_code=404, detail=f"Phone '{name}' not found")
    session.delete(phone)
    session.commit()
    session.close()
    query_engine.build_index()
    return {"message": f"Deleted {phone.name}", "deleted": phone.name}


@app.post("/api/query", response_model=QueryResponse)
def ask_query(req: QueryRequest):
    lazy_init()
    answer = chatbot.answer_query(req.query)
    return QueryResponse(answer=answer)


@app.post("/api/review", response_model=QueryResponse)
def agent_review(req: QueryRequest):
    lazy_init()
    answer = orchestrator.handle_query(req.query)
    return QueryResponse(answer=answer, source="multi-agent")


@app.post("/api/compare")
def compare_phones(req: QueryRequest):
    lazy_init()
    answer = orchestrator.handle_query(req.query)
    return {"comparison": answer}


@app.post("/api/scrape")
def trigger_scrape():
    lazy_init()
    try:
        from scraper.gsmarena_scraper import scrape_all_phones
        from config import SAMSUNG_PHONES
        count = scrape_all_phones(SAMSUNG_PHONES)
        if count == 0:
            # Scrape failed (rate limited), fall back to seed data
            from scraper.seed_data import seed_database
            count = seed_database()
            query_engine.build_index()
            return {"message": f"GSMArena rate limited. Seeded {count} phones with fallback data."}
        query_engine.build_index()
        return {"message": f"Scraped {count} phones successfully from GSMArena"}
    except Exception as e:
        # Scrape failed, fall back to seed data
        from scraper.seed_data import seed_database
        count = seed_database()
        query_engine.build_index()
        return {"message": f"Scrape failed ({str(e)[:50]}). Seeded {count} phones with fallback data."}


@app.post("/api/seed")
def trigger_seed():
    lazy_init()
    try:
        from scraper.seed_data import seed_database
        count = seed_database()
        query_engine.build_index()
        return {"message": f"Seeded {count} phones successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static frontend at /ui (AFTER all API routes so they take priority)
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="frontend")