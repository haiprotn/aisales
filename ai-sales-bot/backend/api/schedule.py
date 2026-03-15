"""Schedule API - manage posting schedules."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db, Schedule
from models.schemas import ScheduleCreate, ScheduleResponse
from utils.scheduler import remove_schedule, generate_post_times, get_scheduled_jobs

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


@router.get("/", response_model=list[ScheduleResponse])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).order_by(Schedule.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    schedule = Schedule(**data.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.put("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch")
    schedule.is_active = not schedule.is_active
    if not schedule.is_active:
        remove_schedule(schedule_id)
    await db.commit()
    return {"is_active": schedule.is_active}


@router.get("/preview-times")
async def preview_times(posts_per_day: int = 10, start_hour: int = 8, end_hour: int = 22):
    times = generate_post_times(posts_per_day, start_hour, end_hour)
    return {"times": [t.strftime("%H:%M") for t in times]}


@router.get("/jobs")
async def list_jobs():
    return {"jobs": get_scheduled_jobs()}


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch")
    remove_schedule(schedule_id)
    await db.delete(schedule)
    await db.commit()
    return {"success": True}
