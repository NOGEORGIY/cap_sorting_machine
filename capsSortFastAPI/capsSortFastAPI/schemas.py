from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

# доступные цвета
class ColorEnum(str, Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    LBLUE = "lightblue"
    BLUE = "blue"
    WHITE = "white"
    BLACK = "black"

# настройки
class SettingsResponse(BaseModel):
    target_color: ColorEnum
    is_enabled: bool
    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    target_color: Optional[ColorEnum] = None

# логирование
class LogResponse(BaseModel):
    id: int
    timestamp: datetime
    detected_color: str
    target_color: str
    is_success: bool
    class Config:
        from_attributes = True

class LogCreate(BaseModel):
    detected_color: ColorEnum
    target_color: ColorEnum
    is_success: bool