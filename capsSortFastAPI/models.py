from sqlalchemy import Column, Integer, Boolean, String, DateTime, CheckConstraint
from sqlalchemy.sql import func
from database import Base

# таблица текущего состояния
class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    target_color = Column(String, nullable=False, default="blue")
    is_enabled = Column(Boolean, nullable=False, default=False)
    proximity_active = Column(Boolean, nullable=False, default=False)

    # в таблице может быть только одна строка с id=1
    __table_args__ = (
        CheckConstraint('id = 1', name='check_single_row'),
    )

# таблица логирования
class SortingLog(Base):
    __tablename__ = "sorting_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    detected_color = Column(String, nullable=False)
    target_color = Column(String, nullable=False)
    is_success = Column(Boolean, nullable=False, index=True)