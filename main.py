from db.engine import engine  
from jobs.score_messages import run_evaluate_job 
from jobs.fetch_messages import run_fetch_job
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import settings

async def main():
    scheduler = AsyncIOScheduler()

    # print(settings.fetch_interval_minutes)
    # scheduler.add_job(run_fetch_job,"interval", minutes=settings.fetch_interval_minutes)
    scheduler.add_job(run_evaluate_job, "interval", minutes=settings.evaluate_interval_minutes)
    # scheduler.add_job(run_forward_job,  "interval", minutes=settings.forward_interval_minutes)
    scheduler.start()

    # run once on startup too
    # await asyncio.gather(run_fetch_job(), run_evaluate_job(), run_forward_job())
    await asyncio.gather(run_evaluate_job())

    await asyncio.Event().wait()  # keep alive

if __name__ == "__main__":
    asyncio.run(main())
