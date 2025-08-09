"""Pydantic models for Bond API data structures."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class DeviceType(str, Enum):
    """Bond device types."""
    FAN = "CF"  # Ceiling Fan
    FIREPLACE = "FP"  # Fireplace
    GENERIC = "GX"  # Generic device
    LIGHT = "LT"  # Light
    MOTORIZED_SHADES = "MS"  # Motorized Shades
    GARAGE_DOOR = "GD"  # Garage Door


class ActionType(str, Enum):
    """Available Bond actions."""
    TURN_ON = "TurnOn"
    TURN_OFF = "TurnOff"
    TOGGLE_POWER = "TogglePower"
    SET_SPEED = "SetSpeed"
    INCREASE_SPEED = "IncreaseSpeed"
    DECREASE_SPEED = "DecreaseSpeed"
    SET_DIRECTION = "SetDirection"
    TOGGLE_DIRECTION = "ToggleDirection"
    SET_BRIGHTNESS = "SetBrightness"
    INCREASE_BRIGHTNESS = "IncreaseBrightness"
    DECREASE_BRIGHTNESS = "DecreaseBrightness"
    OPEN = "Open"
    CLOSE = "Close"
    SET_POSITION = "SetPosition"
    HOLD = "Hold"
    PRESET = "Preset"


class DeviceInfo(BaseModel):
    """Device information model."""
    name: str
    type: DeviceType
    location: Optional[str] = None
    actions: List[ActionType] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class DeviceState(BaseModel):
    """Device state model."""
    power: Optional[int] = None  # 0 = off, 1 = on
    speed: Optional[int] = None  # Fan speed (0-8)
    direction: Optional[int] = None  # Fan direction (1 = forward, -1 = reverse)
    brightness: Optional[int] = None  # Light brightness (0-100)
    position: Optional[int] = None  # Shade position (0-100)
    timer: Optional[int] = None  # Timer in seconds
    
    @validator('speed')
    def validate_speed(cls, v):
        if v is not None and not (0 <= v <= 8):
            raise ValueError('Speed must be between 0 and 8')
        return v
    
    @validator('brightness', 'position')
    def validate_percentage(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError('Value must be between 0 and 100')
        return v
    
    @validator('direction')
    def validate_direction(cls, v):
        if v is not None and v not in [-1, 1]:
            raise ValueError('Direction must be -1 (reverse) or 1 (forward)')
        return v


class BridgeInfo(BaseModel):
    """Bond Bridge information model."""
    name: str
    location: Optional[str] = None
    bluelight: Optional[bool] = None
    mac: Optional[str] = None
    fw_ver: Optional[str] = None
    hw_ver: Optional[str] = None
    uptime_s: Optional[int] = None
    api: Optional[str] = None
    target: Optional[str] = None


class ActionRequest(BaseModel):
    """Request model for device actions."""
    device_id: str
    action: ActionType
    argument: Optional[int] = None
    
    @validator('argument')
    def validate_argument(cls, v, values):
        action = values.get('action')
        if action == ActionType.SET_SPEED and v is not None:
            if not (0 <= v <= 8):
                raise ValueError('Speed must be between 0 and 8')
        elif action in [ActionType.SET_BRIGHTNESS, ActionType.SET_POSITION] and v is not None:
            if not (0 <= v <= 100):
                raise ValueError('Brightness and position must be between 0 and 100')
        elif action == ActionType.SET_DIRECTION and v is not None:
            if v not in [-1, 1]:
                raise ValueError('Direction must be -1 or 1')
        return v


class DeviceListResponse(BaseModel):
    """Response model for device list."""
    devices: Dict[str, DeviceInfo] = Field(default_factory=dict)
    
    @classmethod
    def from_bond_api(cls, data: Dict[str, Any]) -> "DeviceListResponse":
        """Create from Bond API response."""
        devices = {}
        for device_id, device_data in data.items():
            if device_id.startswith('_'):  # Skip metadata fields
                continue
            devices[device_id] = DeviceInfo(**device_data)
        return cls(devices=devices)


class GroupInfo(BaseModel):
    """Device group information."""
    name: str
    devices: List[str] = Field(default_factory=list)
    location: Optional[str] = None


class ScheduleInfo(BaseModel):
    """Schedule information."""
    name: str
    device_id: str
    action: ActionType
    argument: Optional[int] = None
    days: List[int] = Field(default_factory=list)  # 0=Sunday, 1=Monday, etc.
    time: str  # HH:MM format
    enabled: bool = True


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    code: Optional[int] = None
    details: Optional[str] = None