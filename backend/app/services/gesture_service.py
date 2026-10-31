"""
Gesture Registry & Management Service for GestureFlow AI.

Manages persistent gesture metadata in backend/datasets/gestures/gesture_registry.json.
Provides thread-safe CRUD operations, default gesture bootstrapping, and custom ID generation.
"""

import json
import logging
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings
from app.schemas.gesture import (
    GestureCreate,
    GestureResponse,
    GestureUpdate,
)

logger = logging.getLogger(__name__)

# Default standard gestures to bootstrap if registry is empty
DEFAULT_SYSTEM_GESTURES = [
    {
        "id": "G001",
        "name": "Open Palm",
        "description": "All five fingers extended openly with palm facing camera - Controls and moves desktop cursor",
        "type": "static",
        "action": "move_cursor",
        "enabled": True,
        "confidence_threshold": 0.8,
        "icon": "Hand",
        "is_default": True,
    },
    {
        "id": "G002",
        "name": "Closed Fist",
        "description": "All fingers tightly curled into palm forming a fist",
        "type": "static",
        "action": "no_action",
        "enabled": True,
        "confidence_threshold": 0.8,
        "icon": "Grab",
        "is_default": True,
    },
    {
        "id": "G003",
        "name": "Thumbs Up",
        "description": "Fist closed with thumb pointing straight upwards",
        "type": "static",
        "action": "no_action",
        "enabled": True,
        "confidence_threshold": 0.8,
        "icon": "ArrowUp",
        "is_default": True,
    },
    {
        "id": "G004",
        "name": "Peace Sign",
        "description": "Index and middle fingers extended apart in a V shape (Victory) - Triggers right click",
        "type": "static",
        "action": "right_click",
        "enabled": True,
        "confidence_threshold": 0.8,
        "icon": "Sparkles",
        "is_default": True,
    },
    {
        "id": "G005",
        "name": "Pointing",
        "description": "Index finger fully extended forward with other fingers curled - Triggers left click",
        "type": "static",
        "action": "left_click",
        "enabled": True,
        "confidence_threshold": 0.8,
        "icon": "MousePointer",
        "is_default": True,
    },
    {
        "id": "G006",
        "name": "Stop",
        "description": "Open hand held vertically with palm directed forward toward camera",
        "type": "static",
        "action": "no_action",
        "enabled": True,
        "confidence_threshold": 0.8,
        "icon": "CircleDot",
        "is_default": True,
    },
    {
        "id": "G007",
        "name": "Custom Gesture",
        "description": "General purpose custom template for user defined hand posture",
        "type": "static",
        "action": "no_action",
        "enabled": True,
        "confidence_threshold": 0.8,
        "icon": "Sparkles",
        "is_default": False,
    },
]


class GestureService:
    """Thread-safe persistent gesture registry management."""

    def __init__(self, registry_file: Optional[Path] = None) -> None:
        """Initialize gesture service with registry path."""
        self._lock = threading.RLock()
        if registry_file:
            self._registry_path = Path(registry_file)
        else:
            self._registry_path = settings.resolved_dataset_dir / "gestures" / "gesture_registry.json"

        self._gestures: Dict[str, dict] = {}
        self._ensure_registry()

    def _ensure_registry(self) -> None:
        """Ensure the directory exists and load or initialize the registry."""
        with self._lock:
            try:
                self._registry_path.parent.mkdir(parents=True, exist_ok=True)
                if not self._registry_path.exists() or self._registry_path.stat().st_size == 0:
                    # Initialize with default gestures
                    now = datetime.now().isoformat()
                    self._gestures = {
                        g["id"]: {
                            **g,
                            "created_at": now,
                            "updated_at": now,
                        }
                        for g in DEFAULT_SYSTEM_GESTURES
                    }
                    self._save_registry()
                    logger.info("Initialized default gesture registry with %d gestures", len(self._gestures))
                else:
                    with open(self._registry_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        self._gestures = {g["id"]: g for g in data if isinstance(g, dict) and "id" in g}
                    elif isinstance(data, dict):
                        self._gestures = data
                    else:
                        self._gestures = {}
                    logger.info("Loaded %d gestures from %s", len(self._gestures), self._registry_path)
            except Exception as e:
                logger.error("Failed to load gesture registry, starting fresh: %s", e)
                self._gestures = {
                    g["id"]: {
                        **g,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                    }
                    for g in DEFAULT_SYSTEM_GESTURES
                }
                self._save_registry()

    def _save_registry(self) -> None:
        """Atomic write to gesture_registry.json."""
        with self._lock:
            temp_path = self._registry_path.with_suffix(".tmp")
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(list(self._gestures.values()), f, indent=2, ensure_ascii=False)
                # Atomic replace
                os.replace(temp_path, self._registry_path)
            except Exception as e:
                logger.error("Error saving gesture registry: %s", e)
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass
                raise

    def get_all(self, sample_counts: Optional[Dict[str, int]] = None) -> List[GestureResponse]:
        """Get all registered gestures sorted by ID with live sample counts."""
        with self._lock:
            counts = sample_counts or {}
            result = []
            for g in self._gestures.values():
                gid = g["id"]
                result.append(
                    GestureResponse(
                        id=gid,
                        name=g.get("name", gid),
                        description=g.get("description", ""),
                        type=g.get("type", "static"),
                        action=g.get("action", "no_action"),
                        enabled=g.get("enabled", True),
                        confidence_threshold=g.get("confidence_threshold", 0.8),
                        icon=g.get("icon", "Hand"),
                        is_default=g.get("is_default", False),
                        sample_count=counts.get(gid, 0),
                        created_at=g.get("created_at", datetime.now().isoformat()),
                        updated_at=g.get("updated_at", datetime.now().isoformat()),
                    )
                )
            result.sort(key=lambda x: x.id)
            return result

    def get(self, gesture_id: str, sample_count: int = 0) -> Optional[GestureResponse]:
        """Get a specific gesture by ID."""
        with self._lock:
            g = self._gestures.get(gesture_id)
            if not g:
                return None
            return GestureResponse(
                id=g["id"],
                name=g.get("name", g["id"]),
                description=g.get("description", ""),
                type=g.get("type", "static"),
                action=g.get("action", "no_action"),
                enabled=g.get("enabled", True),
                confidence_threshold=g.get("confidence_threshold", 0.8),
                icon=g.get("icon", "Hand"),
                is_default=g.get("is_default", False),
                sample_count=sample_count,
                created_at=g.get("created_at", datetime.now().isoformat()),
                updated_at=g.get("updated_at", datetime.now().isoformat()),
            )

    def generate_next_id(self) -> str:
        """Generate the next sequential gesture ID (e.g., G008)."""
        with self._lock:
            existing_numbers = []
            for gid in self._gestures.keys():
                match = re.match(r"^G(\d+)$", gid)
                if match:
                    existing_numbers.append(int(match.group(1)))
            next_num = max(existing_numbers, default=0) + 1
            return f"G{next_num:03d}"

    def create(self, data: GestureCreate) -> GestureResponse:
        """Create a new custom gesture in the registry."""
        with self._lock:
            gid = data.id.strip() if data.id else self.generate_next_id()

            if gid in self._gestures:
                raise ValueError(f"Gesture with ID '{gid}' already exists.")

            now = datetime.now().isoformat()
            new_record = {
                "id": gid,
                "name": data.name.strip(),
                "description": data.description.strip(),
                "type": data.type,
                "action": data.action,
                "enabled": data.enabled,
                "confidence_threshold": data.confidence_threshold,
                "icon": data.icon,
                "is_default": False,
                "created_at": now,
                "updated_at": now,
            }

            self._gestures[gid] = new_record
            self._save_registry()
            logger.info("Created new gesture '%s' (ID: %s)", new_record["name"], gid)

            return GestureResponse(**new_record, sample_count=0)

    def update(self, gesture_id: str, updates: GestureUpdate, sample_count: int = 0) -> Optional[GestureResponse]:
        """Update fields of an existing gesture."""
        with self._lock:
            if gesture_id not in self._gestures:
                return None

            record = self._gestures[gesture_id]
            update_data = updates.model_dump(exclude_unset=True)

            for key, val in update_data.items():
                if val is not None:
                    record[key] = val

            record["updated_at"] = datetime.now().isoformat()
            self._save_registry()
            logger.info("Updated gesture ID: %s", gesture_id)

            return GestureResponse(**record, sample_count=sample_count)

    def delete(self, gesture_id: str) -> bool:
        """Delete a gesture from registry."""
        with self._lock:
            if gesture_id not in self._gestures:
                return False

            del self._gestures[gesture_id]
            self._save_registry()
            logger.info("Deleted gesture ID: %s from registry", gesture_id)
            return True
