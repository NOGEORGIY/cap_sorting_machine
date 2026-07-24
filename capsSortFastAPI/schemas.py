from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum

# доступные цвета
class ColorEnum(str, Enum):
    WHITE = "white"
    BLACK = "black"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    SKY_BLUE = "sky_blue"
    BLUE = "blue"
    PURPLE = "purple"
    PINK = "pink"
    BROWN = "brown"
    UNKNOWN = "unknown"

# настройки
class SettingsResponse(BaseModel):
    target_color: ColorEnum
    is_enabled: bool
    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    target_color: Optional[ColorEnum] = None
    
    @validator('target_color')
    def validate_color(cls, v):
        if v is None:
            raise ValueError('Цвет не может быть пустым')
        return v

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