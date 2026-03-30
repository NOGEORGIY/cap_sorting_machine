from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Optional, List

import models
import schemas

def get_settings(db: Session) -> Optional[models.SystemSettings]:
    return db.query(models.SystemSettings).filter(models.SystemSettings.id == 1).first()

def update_settings(db: Session, target_color: str = None, is_enabled: bool = None) -> Optional[models.SystemSettings]:
    """Обновить настройки системы"""
    settings = get_settings(db)
    if not settings:
        settings = initialize_settings(db)

    if target_color is not None:
        settings.target_color = target_color

    if is_enabled is not None:
        settings.is_enabled = is_enabled

    db.commit()
    db.refresh(settings)
    return settings

def initialize_settings(db: Session) -> models.SystemSettings:
    """Инициализировать настройки, если таблица пуста"""
    settings = get_settings(db)
    if not settings:
        settings = models.SystemSettings(
            id=1,
            target_color="blue",
            is_enabled=False,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

# журнал событий (логирование)
def create_log(
        db: Session,
        detected_color: str,
        target_color: str,
        is_success: bool
) -> models.SortingLog:
    """Создать запись в журнале событий (вызывается при отчете от CV)"""
    log = models.SortingLog(
        detected_color=detected_color,
        target_color=target_color,
        is_success=is_success
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_logs(
        db: Session,
        limit: int = 100,
        hours: int = 24
) -> List[models.SortingLog]:
    """Получить последние логи за N часов"""
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    return db.query(models.SortingLog).filter(models.SortingLog.timestamp >= time_threshold).order_by(models.SortingLog.timestamp.desc()).limit(limit).all()

# статистика

def get_statistics(db: Session, hours: int = 24) -> dict:
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    # Базовый запрос с фильтром по времени
    base_query = db.query(models.SortingLog).filter(models.SortingLog.timestamp >= time_threshold)

    total_count = base_query.count()
    success_count = base_query.filter(models.SortingLog.is_success == True).count()
    fail_count = total_count - success_count

    # Статистика по цветам (сколько крышек каждого цвета прошло)
    color_stats = db.query(
        models.SortingLog.detected_color,
        func.count(models.SortingLog.id)
    ).filter(
        models.SortingLog.timestamp >= time_threshold
    ).group_by(
        models.SortingLog.detected_color
    ).all()

    # Преобразуем результат в словарь {color: count}
    color_distribution = {color: count for color, count in color_stats}

    # Процент успеха
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0.0

    return {
        "total_processed": total_count,
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": round(success_rate, 2),
        "color_distribution": color_distribution,
        "period_hours": hours
    }