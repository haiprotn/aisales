"""Background scheduler for automated posting."""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Callable, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()


def schedule_post(
    post_id: int,
    scheduled_time: datetime,
    publish_callback: Callable
):
    """Schedule a single post for publishing at a specific time."""
    job_id = f"post_{post_id}"

    # Remove existing job if any
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)

    scheduler.add_job(
        publish_callback,
        trigger=DateTrigger(run_date=scheduled_time),
        id=job_id,
        args=[post_id],
        replace_existing=True
    )
    return job_id


def schedule_daily_posts(
    schedule_id: int,
    posts_per_day: int,
    start_hour: int,
    end_hour: int,
    days_of_week: list[int],
    publish_callback: Callable
):
    """Set up recurring daily posting schedule.
    
    Distributes posts evenly throughout the day between start_hour and end_hour.
    """
    job_id = f"schedule_{schedule_id}"

    # Remove existing schedule
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)

    # Convert days: 1=Mon to 0=Mon for APScheduler
    day_str = ",".join(str(d - 1) for d in days_of_week)

    # Run check every hour between start and end
    scheduler.add_job(
        publish_callback,
        trigger=CronTrigger(
            hour=f"{start_hour}-{end_hour}",
            day_of_week=day_str,
            minute=0
        ),
        id=job_id,
        args=[schedule_id, posts_per_day, start_hour, end_hour],
        replace_existing=True
    )
    return job_id


def generate_post_times(
    posts_per_day: int,
    start_hour: int = 8,
    end_hour: int = 22,
    date: datetime = None
) -> list[datetime]:
    """Generate evenly distributed posting times for a day.
    
    Adds slight randomness (±15 min) to avoid looking robotic.
    """
    if date is None:
        date = datetime.now()

    base_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    total_minutes = (end_hour - start_hour) * 60
    interval = total_minutes / max(posts_per_day, 1)

    times = []
    for i in range(posts_per_day):
        minutes_offset = start_hour * 60 + int(i * interval)
        # Add randomness ±15 minutes
        jitter = random.randint(-15, 15)
        minutes_offset = max(start_hour * 60, min(end_hour * 60, minutes_offset + jitter))

        post_time = base_date + timedelta(minutes=minutes_offset)
        times.append(post_time)

    return sorted(times)


def remove_schedule(schedule_id: int):
    """Remove a posting schedule."""
    job_id = f"schedule_{schedule_id}"
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)


def get_scheduled_jobs() -> list[dict]:
    """Get all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    return jobs
