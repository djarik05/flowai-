"""
Camera schemas for GestureFlow AI backend.

Defines typed models for camera management API.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CameraState(str, Enum):
    """Camera state enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    CAPTURING = "capturing"
    ERROR = "error"


class CameraInfo(BaseModel):
    """Camera device information."""

    index: int = Field(..., description="Camera device index")
    name: str = Field(default="", description="Camera display name")
    width: int = Field(default=0, description="Camera frame width")
    height: int = Field(default=0, description="Camera frame height")
    fps: float = Field(default=0.0, description="Camera frame rate")
    backend: str = Field(default="", description="OpenCV backend identifier")
    available: bool = Field(default=False, description="Whether camera is available")


class CameraStatusResponse(BaseModel):
    """Camera status response."""

    state: CameraState = Field(..., description="Current camera state")
    camera_index: int = Field(default=0, description="Selected camera index")
    actual_width: int = Field(default=0, description="Actual frame width")
    actual_height: int = Field(default=0, description="Actual frame height")
    actual_fps: float = Field(default=0.0, description="Actual frame rate")
    backend: str = Field(default="", description="OpenCV backend in use")
    is_capturing: bool = Field(default=False, description="Whether capture is active")
    last_frame_time: Optional[datetime] = Field(default=None, description="Timestamp of last captured frame")
    frames_captured: int = Field(default=0, description="Total frames captured")
    frames_dropped: int = Field(default=0, description="Total frames dropped")
    last_error: Optional[str] = Field(default=None, description="Last error message, if any")
    devices: List[CameraInfo] = Field(default_factory=list, description="Discovered camera devices")
    owner: str = Field(default="none", description="Current physical camera owner: 'none', 'browser', or 'backend'")


class CameraOwnershipRequest(BaseModel):
    """Camera ownership claim/release request."""

    owner: str = Field(default="browser", description="Target owner identifier: 'browser' or 'backend'")


class CameraOwnershipResponse(BaseModel):
    """Camera ownership status response."""

    success: bool = Field(..., description="Whether ownership operation succeeded")
    owner: str = Field(..., description="Active physical camera owner: 'none', 'browser', or 'backend'")
    message: str = Field(..., description="Status message")


class CameraConfigRequest(BaseModel):
    """Camera configuration request."""

    camera_index: Optional[int] = Field(default=None, ge=0, description="Camera device index")
    width: Optional[int] = Field(default=None, ge=160, le=3840, description="Requested frame width")
    height: Optional[int] = Field(default=None, ge=120, le=2160, description="Requested frame height")
    fps: Optional[int] = Field(default=None, ge=1, le=120, description="Requested frame rate")
    mirror: Optional[bool] = Field(default=None, description="Mirror frames horizontally")


class CameraConfigResponse(BaseModel):
    """Camera configuration response."""

    success: bool = Field(..., description="Whether configuration was applied")
    message: str = Field(..., description="Status message")
    applied_config: Optional[CameraConfigRequest] = Field(default=None, description="Applied configuration")