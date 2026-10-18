import asyncio
from app.services import knowledge_service

scheduler = None

async def daily_refresh_job():
    print("[scheduler] Starting daily sitemap sync and freshness check...")
    try:
        result = await knowledge_service.run_ingestion(mode="incremental", max_pages=50)
        print(f"[scheduler] Daily sync completed: {result.get('stats')}")
    except Exception as e:
        print(f"[scheduler] Daily sync error: {e}")

def start_scheduler():
    global scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(daily_refresh_job, "cron", hour=2, minute=0, id="daily_freshness_sync")
        scheduler.start()
        print("[scheduler] APScheduler initialized.")
    except ImportError:
        print("[scheduler] apscheduler not installed in environment. Background scheduler skipped.")
