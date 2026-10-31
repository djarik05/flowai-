"""
Gesture schemas for GestureFlow AI backend.

Defines Pydantic models for custom gesture definitions and management.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class GestureBase(BaseModel):
    """Base schema for gesture definition."""

    id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9_\-]+$",
        description="Unique gesture identifier (e.g., G001, Open_Palm)",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the gesture",
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Detailed description of the gesture posture or motion",
    )
    type: str = Field(
        default="static",
        description="Gesture type: 'static' or 'temporal'",
    )
    action: str = Field(
        default="no_action",
        description="Bound action name or shortcut",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this gesture is actively recognized",
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="Minimum detection confidence threshold",
    )
    icon: str = Field(
        default="Hand",
        description="UI icon name identifier",
    )
    is_default: bool = Field(
        default=False,
        description="Whether this is a system default gesture",
    )


class GestureCreate(BaseModel):
    """Schema for creating a new custom gesture."""

    id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9_\-]+$",
        description="Optional custom gesture ID; if omitted, assigned automatically",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Gesture display name",
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Gesture description",
    )
    type: str = Field(
        default="static",
        description="'static' or 'temporal'",
    )
    action: str = Field(
        default="no_action",
        description="Bound controller action",
    )
    enabled: bool = Field(
        default=True,
        description="Whether enabled",
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="Minimum confidence",
    )
    icon: str = Field(
        default="Hand",
        description="Icon name",
    )


class GestureUpdate(BaseModel):
    """Schema for updating an existing gesture."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    type: Optional[str] = None
    action: Optional[str] = None
    enabled: Optional[bool] = None
    confidence_threshold: Optional[float] = Field(default=None, ge=0.1, le=1.0)
    icon: Optional[str] = None


class GestureResponse(GestureBase):
    """Full gesture response including sample count and timestamps."""

    sample_count: int = Field(default=0, ge=0, description="Total collected samples for this gesture")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class GestureListResponse(BaseModel):
    """List response of registered gestures."""

    gestures: List[GestureResponse]
    total: int
