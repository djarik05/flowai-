"""
Mouse Controller Service for GestureFlow AI (Phase 6A).

Provides hand-controlled desktop mouse movement with:
- Configurable cursor sensitivity
- Exponential Moving Average (EMA) smoothing
- Active tracking box coordinate mapping
- Primary display boundary clamping
- Tracking-loss safety and jump prevention
- Dead zone around center to ignore micro-movements
- Asynchronous non-blocking worker thread
- Zero-dependency native Windows user32 driver with mock fallback for tests
"""

import ctypes
from ctypes import wintypes
import logging
import math
import platform
import queue
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any

from app.schemas.mouse import MouseSettings, MouseStatusResponse

logger = logging.getLogger(__name__)


class MouseDriver(ABC):
    """Abstract interface for OS-level cursor movement and display metrics."""

    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """Return (width, height) of primary desktop screen in pixels."""
        pass

    @abstractmethod
    def move_to(self, x: int, y: int) -> None:
        """Move desktop cursor to absolute pixel coordinates (x, y)."""
        pass

    @abstractmethod
    def click_left(self) -> None:
        """Execute a single left mouse click."""
        pass

    @abstractmethod
    def click_right(self) -> None:
        """Execute a single right mouse click."""
        pass

    @abstractmethod
    def get_position(self) -> Tuple[int, int]:
        """Get current desktop cursor coordinates (x, y)."""
        pass

    @abstractmethod
    def prepare_thread(self) -> bool:
        """Prepare calling thread with required OS desktop access."""
        pass


class WindowsUser32MouseDriver(MouseDriver):
    """Native Windows User32 cursor driver via ctypes SendInput & mouse_event fallback."""

    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32
        self._thread_local = threading.local()

        # Enable Per-Monitor DPI Awareness so Windows returns true physical pixel dimensions
        try:
            shcore = getattr(ctypes.windll, "shcore", None)
            if shcore and hasattr(shcore, "SetProcessDpiAwareness"):
                shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            else:
                self._user32.SetProcessDPIAware()
        except Exception:
            try:
                self._user32.SetProcessDPIAware()
            except Exception:
                pass

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [("mi", MOUSEINPUT)]
            _anonymous_ = ("_input",)
            _fields_ = [
                ("type", wintypes.DWORD),
                ("_input", _INPUT),
            ]

        self._point_cls = POINT
        self._input_cls = INPUT
        self._mouse_input_cls = MOUSEINPUT

        # Explicit ctypes function prototypes
        self._user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        self._user32.GetCursorPos.restype = ctypes.c_bool
        self._user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        self._user32.SetCursorPos.restype = ctypes.c_bool
        self._user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self._user32.SendInput.restype = wintypes.UINT

        self.prepare_thread()

    def prepare_thread(self) -> bool:
        """
        Attaches the current calling thread to the interactive 'default' desktop on WinSta0.
        Required when the process is spawned by services, scripts, background workers, or threadpool.
        """
        try:
            # 0x037F = WINSTA_ALL_ACCESS
            hwinsta = self._user32.OpenWindowStationW("WinSta0", False, 0x037F)
            if hwinsta:
                self._user32.SetProcessWindowStation(hwinsta)
            # 0x01FF = DESKTOP_ALL_ACCESS
            hdesk = self._user32.OpenDesktopW("default", 0, False, 0x01FF)
            if hdesk:
                ret = self._user32.SetThreadDesktop(hdesk)
                if ret:
                    self._thread_local.attached = True
                    return True
        except Exception as e:
            logger.debug("prepare_thread note: %s", e)
        return False

    def _ensure_attached(self) -> None:
        """Ensure current calling thread is attached to interactive desktop before input operations."""
        if not getattr(self._thread_local, "attached", False):
            self.prepare_thread()

    def get_screen_size(self) -> Tuple[int, int]:
        self._ensure_attached()
        w = int(self._user32.GetSystemMetrics(0))  # SM_CXSCREEN
        h = int(self._user32.GetSystemMetrics(1))  # SM_CYSCREEN
        return max(1, w), max(1, h)

    def move_to(self, x: int, y: int) -> None:
        self._ensure_attached()
        ret = self._user32.SetCursorPos(int(x), int(y))
        if not ret:
            # If rejected (e.g. desktop context changed), re-attach and retry
            self.prepare_thread()
            self._user32.SetCursorPos(int(x), int(y))

    def _send_mouse_event(self, flags: int, data: int = 0) -> bool:
        """Send mouse input event via SendInput, with fallback to mouse_event."""
        self._ensure_attached()
        try:
            inp = self._input_cls()
            inp.type = 0  # INPUT_MOUSE
            inp.mi.dx = 0
            inp.mi.dy = 0
            inp.mi.mouseData = data
            inp.mi.dwFlags = flags
            inp.mi.time = 0
            inp.mi.dwExtraInfo = None

            ret = self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(self._input_cls))
            if ret == 1:
                return True
            err = ctypes.GetLastError()
            logger.debug("SendInput returned %d (err=%d); falling back to mouse_event", ret, err)
        except Exception as e:
            logger.debug("SendInput exception %s; falling back to mouse_event", e)

        # Fallback to user32 mouse_event
        try:
            self._user32.mouse_event(flags, 0, 0, data, 0)
            return True
        except Exception as e:
            logger.error("mouse_event fallback failed: %s", e)
            return False

    def click_left(self) -> None:
        """Execute a single native Windows left click using SendInput (with mouse_event fallback)."""
        self._ensure_attached()
        try:
            # 0x0002 = MOUSEEVENTF_LEFTDOWN, 0x0004 = MOUSEEVENTF_LEFTUP
            self._send_mouse_event(0x0002)
            time.sleep(0.015)
            self._send_mouse_event(0x0004)
        except Exception as e:
            logger.error("WindowsUser32MouseDriver click_left error: %s", e)
            self.prepare_thread()

    def click_right(self) -> None:
        """Execute a single native Windows right click using SendInput (with mouse_event fallback)."""
        self._ensure_attached()
        try:
            # 0x0008 = MOUSEEVENTF_RIGHTDOWN, 0x0010 = MOUSEEVENTF_RIGHTUP
            self._send_mouse_event(0x0008)
            time.sleep(0.015)
            self._send_mouse_event(0x0010)
        except Exception as e:
            logger.error("WindowsUser32MouseDriver click_right error: %s", e)
            self.prepare_thread()

    def get_position(self) -> Tuple[int, int]:
        self._ensure_attached()
        pt = self._point_cls()
        ret = self._user32.GetCursorPos(ctypes.byref(pt))
        if not ret or (pt.x == 0 and pt.y == 0):
            self.prepare_thread()
            self._user32.GetCursorPos(ctypes.byref(pt))
        return int(pt.x), int(pt.y)


class MockMouseDriver(MouseDriver):
    """Mock mouse driver for automated tests and headless environments."""

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_x = screen_width // 2
        self.current_y = screen_height // 2
        self.move_history: list[Tuple[int, int]] = []
        self.clicks: list[dict] = []

    def prepare_thread(self) -> bool:
        return True

    def get_screen_size(self) -> Tuple[int, int]:
        return self.screen_width, self.screen_height

    def move_to(self, x: int, y: int) -> None:
        self.current_x = int(x)
        self.current_y = int(y)
        self.move_history.append((self.current_x, self.current_y))

    def click_left(self) -> None:
        self.clicks.append({
            "button": "left",
            "time": time.time(),
            "pos": (self.current_x, self.current_y),
        })

    def click_right(self) -> None:
        self.clicks.append({
            "button": "right",
            "time": time.time(),
            "pos": (self.current_x, self.current_y),
        })

    def get_position(self) -> Tuple[int, int]:
        return self.current_x, self.current_y


def _create_default_driver() -> MouseDriver:
    """Create Windows driver if on Windows and not in test mode, else MockMouseDriver."""
    if platform.system() == "Windows" and hasattr(ctypes, "windll"):
        try:
            return WindowsUser32MouseDriver()
        except Exception as e:
            logger.warning("Could not initialize WindowsUser32MouseDriver: %s. Using MockMouseDriver.", e)
            return MockMouseDriver()
    return MockMouseDriver()


class MouseController:
    """
    Core Mouse Controller for Phase 6A.

    Coordinates hand tracking landmarks with desktop cursor movement.
    Guarantees:
    - Disabled by default (Safety Rule #1)
    - Reinitializes smoothing state on tracking resume (prevents cursor jumps)
    - Halts movement when tracking is lost or data is stale (>150ms TTL)
    - Dead zone around center of active tracking box to ignore micro-movements
    - Runs in a dedicated background worker to never block FastAPI or camera capture
    """

    def __init__(self, driver: Optional[MouseDriver] = None) -> None:
        self._lock = threading.RLock()
        self._driver: MouseDriver = driver if driver is not None else _create_default_driver()
        self._settings = MouseSettings()

        # Operational state
        self._is_enabled: bool = False
        self._is_running: bool = False
        self._stop_event = threading.Event()
        self._target_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # Tracking and smoothing state
        self._last_landmark_time: float = 0.0
        self._last_diag_log_time: float = 0.0
        self._hand_detected: bool = False
        self._tracking_lost: bool = True
        self._latest_norm_x: Optional[float] = None
        self._latest_norm_y: Optional[float] = None
        self._prev_smoothed_x: Optional[float] = None
        self._prev_smoothed_y: Optional[float] = None
        self._last_moved_x: Optional[int] = None
        self._last_moved_y: Optional[int] = None
        self._last_error: Optional[str] = None

        # Phase 6B.1: Left Click and Pinch State
        self._pinch_state: str = "idle"  # "idle", "pinched", "cooldown", "disabled"
        self._latest_pinch_distance: Optional[float] = None
        self._last_click_time: float = 0.0
        self._last_click_pos: Optional[Dict[str, int]] = None
        self._click_count: int = 0
        self._awaiting_pinch_release: bool = False

        # Phase 6B.2: Right Click and Right Pinch State (Thumb + Middle, L4 & L12)
        self._right_pinch_state: str = "idle"  # "idle", "pinched", "cooldown", "disabled"
        self._latest_right_pinch_distance: Optional[float] = None
        self._last_right_click_time: float = 0.0
        self._last_right_click_pos: Optional[Dict[str, int]] = None
        self._right_click_count: int = 0
        self._awaiting_right_pinch_release: bool = False

        # Dedicated worker click execution queue for guaranteed desktop thread attachment
        self._click_queue: queue.Queue = queue.Queue()
        self._current_cursor_pos: Tuple[int, int] = (0, 0)

    @property
    def is_enabled(self) -> bool:
        """Check if mouse control is currently enabled."""
        with self._lock:
            return self._is_enabled

    @property
    def is_running(self) -> bool:
        """Check if background mouse worker is active."""
        with self._lock:
            return self._is_running

    def set_driver(self, driver: MouseDriver) -> None:
        """Inject a custom mouse driver (e.g. for testing)."""
        with self._lock:
            self._driver = driver

    def initialize(self) -> bool:
        """Initialize mouse controller."""
        with self._lock:
            self._reset_smoothing_state()
            logger.info("MouseController initialized (default state: DISABLED)")
            return True

    def start(self) -> bool:
        """
        Enable mouse control and start background worker.
        Idempotent and thread-safe.
        """
        with self._lock:
            if self._is_enabled and self._is_running:
                logger.debug("MouseController already running")
                return True

            self._is_enabled = True
            self._reset_smoothing_state()
            self._awaiting_pinch_release = False
            self._awaiting_right_pinch_release = False
            self._stop_event.clear()
            self._target_event.clear()

            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(
                    target=self._worker_loop,
                    name="MouseControllerWorker",
                    daemon=True,
                )
                self._worker_thread.start()

            self._is_running = True
            logger.info("MouseController started (ENABLED)")
            return True

    def stop(self) -> bool:
        """
        Disable mouse control and stop background worker.
        Idempotent and thread-safe.
        """
        with self._lock:
            self._is_enabled = False
            self._is_running = False
            self._reset_smoothing_state()
            self._stop_event.set()
            self._target_event.set()

        if self._worker_thread and self._worker_thread.is_alive():
            if threading.current_thread() != self._worker_thread:
                self._worker_thread.join(timeout=1.5)
            self._worker_thread = None

        logger.info("MouseController stopped (DISABLED)")
        return True

    def _reset_smoothing_state(self) -> None:
        """Reset smoothing memory to prevent cursor snap when tracking resumes."""
        self._tracking_lost = True
        self._hand_detected = False
        self._prev_smoothed_x = None
        self._prev_smoothed_y = None
        self._latest_norm_x = None
        self._latest_norm_y = None
        self._latest_pinch_distance = None
        self._latest_right_pinch_distance = None
        # Only require pinch release if hand was actively pinched when tracking dropped
        if self._pinch_state != "pinched":
            self._awaiting_pinch_release = False
        if not self._is_enabled or not self._settings.left_click_enabled:
            self._pinch_state = "disabled"
        else:
            self._pinch_state = "idle"

        if self._right_pinch_state != "pinched":
            self._awaiting_right_pinch_release = False
        if not self._is_enabled or not self._settings.right_click_enabled:
            self._right_pinch_state = "disabled"
        else:
            self._right_pinch_state = "idle"

    def update_settings(self, **kwargs: Any) -> MouseSettings:
        """
        Update mouse controller settings with boundary validation.
        """
        with self._lock:
            current = self._settings.model_dump()
            for key, val in kwargs.items():
                if val is not None and key in current:
                    current[key] = val
            self._settings = MouseSettings(**current)
            if not self._settings.left_click_enabled:
                self._pinch_state = "disabled"
            elif self._pinch_state == "disabled" and self._is_enabled:
                self._pinch_state = "idle"

            if not self._settings.right_click_enabled:
                self._right_pinch_state = "disabled"
            elif self._right_pinch_state == "disabled" and self._is_enabled:
                self._right_pinch_state = "idle"
            logger.info("Updated MouseController settings: %s", self._settings.model_dump())
            return self._settings

    def on_landmark_point(
        self,
        norm_x: float,
        norm_y: float,
        capture_time: Optional[float] = None,
        pinch_distance: Optional[float] = None,
        thumb_x: Optional[float] = None,
        thumb_y: Optional[float] = None,
        right_pinch_distance: Optional[float] = None,
        middle_x: Optional[float] = None,
        middle_y: Optional[float] = None,
    ) -> bool:
        """
        Feed an index fingertip control point, left pinch distance (L4 to L8),
        and right pinch distance (L4 to L12) into the controller.
        Thread-safe, non-blocking: updates latest target and signals worker.

        Args:
            norm_x: Normalized index fingertip X coordinate [0.0, 1.0]
            norm_y: Normalized index fingertip Y coordinate [0.0, 1.0]
            capture_time: Optional capture timestamp
            pinch_distance: Optional normalized Euclidean distance between thumb tip and index fingertip
            thumb_x: Optional normalized thumb tip X coordinate
            thumb_y: Optional normalized thumb tip Y coordinate
            right_pinch_distance: Optional normalized Euclidean distance between thumb tip and middle fingertip
            middle_x: Optional normalized middle fingertip X coordinate
            middle_y: Optional normalized middle fingertip Y coordinate

        Returns:
            True if a left or right click was executed during this frame.
        """
        if not self._is_enabled:
            return False

        # Validate finite numeric coordinates
        try:
            fx = float(norm_x)
            fy = float(norm_y)
            if not math.isfinite(fx) or not math.isfinite(fy):
                return False
        except (ValueError, TypeError):
            return False

        with self._lock:
            # Clamp input to valid [0.0, 1.0] range
            self._latest_norm_x = max(0.0, min(1.0, fx))
            self._latest_norm_y = max(0.0, min(1.0, fy))
            # Server-side monotonic arrival timestamp to prevent client-server clock skew staleness
            self._last_landmark_time = time.time()
            self._hand_detected = True

            # Calculate left pinch distance (thumb to index) if thumb given and distance not directly supplied
            calc_pinch = pinch_distance
            if calc_pinch is None and thumb_x is not None and thumb_y is not None:
                try:
                    tx = float(thumb_x)
                    ty = float(thumb_y)
                    if math.isfinite(tx) and math.isfinite(ty):
                        calc_pinch = math.hypot(self._latest_norm_x - tx, self._latest_norm_y - ty)
                except (ValueError, TypeError):
                    pass

            # Calculate right pinch distance (thumb to middle) if thumb and middle given and distance not directly supplied
            calc_right_pinch = right_pinch_distance
            if calc_right_pinch is None and thumb_x is not None and thumb_y is not None and middle_x is not None and middle_y is not None:
                try:
                    tx = float(thumb_x)
                    ty = float(thumb_y)
                    mx = float(middle_x)
                    my = float(middle_y)
                    if math.isfinite(tx) and math.isfinite(ty) and math.isfinite(mx) and math.isfinite(my):
                        calc_right_pinch = math.hypot(mx - tx, my - ty)
                except (ValueError, TypeError):
                    pass

            # Mutual exclusion: if both left pinch (L4+L8) and right pinch (L4+L12) are actively within their
            # activation thresholds simultaneously (e.g. closing into a fist or touching all fingers),
            # suppress both clicks to prevent accidental triggers.
            is_left_activating = False
            if calc_pinch is not None:
                try:
                    fp = float(calc_pinch)
                    if math.isfinite(fp) and fp <= self._settings.pinch_activation_threshold:
                        is_left_activating = True
                except (ValueError, TypeError):
                    pass

            is_right_activating = False
            if calc_right_pinch is not None:
                try:
                    frp = float(calc_right_pinch)
                    if math.isfinite(frp) and frp <= self._settings.right_pinch_activation_threshold:
                        is_right_activating = True
                except (ValueError, TypeError):
                    pass

            mutual_exclusion_active = (is_left_activating and is_right_activating)
            if mutual_exclusion_active:
                self._awaiting_pinch_release = True
                self._awaiting_right_pinch_release = True
                logger.debug("Mutual exclusion active: simultaneous left and right pinches suppressed")

            left_triggered = False
            if calc_pinch is not None:
                try:
                    f_pinch = float(calc_pinch)
                    if math.isfinite(f_pinch) and f_pinch >= 0.0:
                        self._latest_pinch_distance = round(f_pinch, 4)
                        if not mutual_exclusion_active:
                            left_triggered = self._process_pinch(f_pinch)
                        else:
                            self._pinch_state = "pinched"
                except (ValueError, TypeError):
                    pass

            right_triggered = False
            if calc_right_pinch is not None:
                try:
                    f_rpinch = float(calc_right_pinch)
                    if math.isfinite(f_rpinch) and f_rpinch >= 0.0:
                        self._latest_right_pinch_distance = round(f_rpinch, 4)
                        if not mutual_exclusion_active:
                            right_triggered = self._process_right_pinch(f_rpinch)
                        else:
                            self._right_pinch_state = "pinched"
                except (ValueError, TypeError):
                    pass

            self._target_event.set()
            return left_triggered or right_triggered

    def _process_pinch(self, pinch_dist: float) -> bool:
        """
        Evaluate pinch distance against hysteresis thresholds, debouncing, and cooldown.
        Must be called with self._lock acquired.
        Returns True if a left click was triggered.
        """
        if not self._is_enabled or not self._settings.left_click_enabled:
            self._pinch_state = "disabled"
            return False

        now = time.time()
        cooldown_sec = self._settings.click_cooldown_ms / 1000.0
        time_since_click = now - self._last_click_time

        # Pinch release check (Hysteresis):
        # Must release past pinch_release_threshold to disarm latch for the next click
        if pinch_dist >= self._settings.pinch_release_threshold:
            self._awaiting_pinch_release = False

        # Cooldown check
        if time_since_click < cooldown_sec:
            self._pinch_state = "cooldown"
            return False

        # Pinch activation check
        if pinch_dist <= self._settings.pinch_activation_threshold:
            if not self._awaiting_pinch_release:
                # Trigger single left click (One click per pinch action)
                self._awaiting_pinch_release = True
                self._pinch_state = "pinched"
                self._last_click_time = now
                pos_x, pos_y = self._driver.get_position()
                if pos_x == 0 and pos_y == 0 and self._last_moved_x is not None and self._last_moved_y is not None:
                    pos_x, pos_y = self._last_moved_x, self._last_moved_y
                self._last_click_pos = {"x": pos_x, "y": pos_y}
                self._click_count += 1

                is_mock = isinstance(self._driver, MockMouseDriver) or not self._is_running
                if not is_mock:
                    self._click_queue.put("left")
                    self._target_event.set()
                    logger.info(
                        "[CLICK_DIAG] LEFT_PINCH_ENQUEUED: dist=%.4f thresh=%.4f pos=(%d, %d) total=%d",
                        pinch_dist, self._settings.pinch_activation_threshold, pos_x, pos_y, self._click_count
                    )
                    return True
                else:
                    try:
                        self._driver.click_left()
                        logger.info(
                            "[CLICK_DIAG] LEFT_CLICK_PINCH: dist=%.4f thresh=%.4f pos=(%d, %d) total=%d",
                            pinch_dist, self._settings.pinch_activation_threshold, pos_x, pos_y, self._click_count
                        )
                        return True
                    except Exception as e:
                        self._last_error = f"Left click error: {e}"
                        logger.error(self._last_error)
                        return False
            else:
                # Still holding pinch: no repeated clicks
                self._pinch_state = "pinched"
                return False
        else:
            # Distance is above activation threshold
            if self._awaiting_pinch_release:
                # Inside hysteresis deadband between activation and release
                self._pinch_state = "pinched"
            else:
                self._pinch_state = "idle"
            return False

    def _process_right_pinch(self, pinch_dist: float) -> bool:
        """
        Evaluate middle-finger pinch distance against hysteresis thresholds, debouncing, and cooldown.
        Must be called with self._lock acquired.
        Returns True if a right click was triggered.
        """
        if not self._is_enabled or not self._settings.right_click_enabled:
            self._right_pinch_state = "disabled"
            return False

        now = time.time()
        cooldown_sec = self._settings.right_click_cooldown_ms / 1000.0
        time_since_click = now - self._last_right_click_time

        # Pinch release check (Hysteresis):
        # Must release past right_pinch_release_threshold to disarm latch for the next click
        if pinch_dist >= self._settings.right_pinch_release_threshold:
            self._awaiting_right_pinch_release = False

        # Cooldown check
        if time_since_click < cooldown_sec:
            self._right_pinch_state = "cooldown"
            return False

        # Pinch activation check
        if pinch_dist <= self._settings.right_pinch_activation_threshold:
            if not self._awaiting_right_pinch_release:
                # Trigger single right click (One click per pinch action)
                self._awaiting_right_pinch_release = True
                self._right_pinch_state = "pinched"
                self._last_right_click_time = now
                pos_x, pos_y = self._driver.get_position()
                if pos_x == 0 and pos_y == 0 and self._last_moved_x is not None and self._last_moved_y is not None:
                    pos_x, pos_y = self._last_moved_x, self._last_moved_y
                self._last_right_click_pos = {"x": pos_x, "y": pos_y}
                self._right_click_count += 1

                is_mock = isinstance(self._driver, MockMouseDriver) or not self._is_running
                if not is_mock:
                    self._click_queue.put("right")
                    self._target_event.set()
                    logger.info(
                        "[CLICK_DIAG] RIGHT_PINCH_ENQUEUED: dist=%.4f thresh=%.4f pos=(%d, %d) total=%d",
                        pinch_dist, self._settings.right_pinch_activation_threshold, pos_x, pos_y, self._right_click_count
                    )
                    return True
                else:
                    try:
                        self._driver.click_right()
                        logger.info(
                            "[CLICK_DIAG] RIGHT_CLICK_PINCH: dist=%.4f thresh=%.4f pos=(%d, %d) total=%d",
                            pinch_dist, self._settings.right_pinch_activation_threshold, pos_x, pos_y, self._right_click_count
                        )
                        return True
                    except Exception as e:
                        self._last_error = f"Right click error: {e}"
                        logger.error(self._last_error)
                        return False
            else:
                # Still holding pinch: no repeated clicks
                self._right_pinch_state = "pinched"
                return False
        else:
            # Distance is above activation threshold
            if self._awaiting_right_pinch_release:
                # Inside hysteresis deadband between activation and release
                self._right_pinch_state = "pinched"
            else:
                self._right_pinch_state = "idle"
            return False

    def trigger_left_click(self) -> bool:
        """
        Explicitly trigger a left mouse click safely.
        Subject to enabled state and cooldown debouncing.
        Returns True if click was executed.
        """
        with self._lock:
            if not self._is_enabled or not self._settings.left_click_enabled:
                return False

            now = time.time()
            cooldown_sec = self._settings.click_cooldown_ms / 1000.0
            if now - self._last_click_time < cooldown_sec:
                return False

            self._last_click_time = now
            pos_x, pos_y = self._driver.get_position()
            if pos_x == 0 and pos_y == 0 and self._last_moved_x is not None and self._last_moved_y is not None:
                pos_x, pos_y = self._last_moved_x, self._last_moved_y
            self._last_click_pos = {"x": pos_x, "y": pos_y}
            self._click_count += 1
            self._pinch_state = "pinched"

            is_mock = isinstance(self._driver, MockMouseDriver) or not self._is_running
            if not is_mock:
                self._click_queue.put("left")
                self._target_event.set()
                logger.info("[CLICK_DIAG] LEFT_CLICK_ENQUEUED: pos=(%d, %d) total=%d cooldown=%.0fms", pos_x, pos_y, self._click_count, self._settings.click_cooldown_ms)
                return True
            else:
                try:
                    self._driver.click_left()
                    logger.info("[CLICK_DIAG] LEFT_CLICK_EXPLICIT: pos=(%d, %d) total=%d cooldown=%.0fms", pos_x, pos_y, self._click_count, self._settings.click_cooldown_ms)
                    return True
                except Exception as e:
                    self._last_error = f"Left click error: {e}"
                    logger.error(self._last_error)
                    return False

    def trigger_right_click(self) -> bool:
        """
        Explicitly trigger a right mouse click safely.
        Subject to enabled state and cooldown debouncing.
        Returns True if click was executed.
        """
        with self._lock:
            if not self._is_enabled or not self._settings.right_click_enabled:
                return False

            now = time.time()
            cooldown_sec = self._settings.right_click_cooldown_ms / 1000.0
            if now - self._last_right_click_time < cooldown_sec:
                return False

            self._last_right_click_time = now
            pos_x, pos_y = self._driver.get_position()
            if pos_x == 0 and pos_y == 0 and self._last_moved_x is not None and self._last_moved_y is not None:
                pos_x, pos_y = self._last_moved_x, self._last_moved_y
            self._last_right_click_pos = {"x": pos_x, "y": pos_y}
            self._right_click_count += 1
            self._right_pinch_state = "pinched"

            is_mock = isinstance(self._driver, MockMouseDriver) or not self._is_running
            if not is_mock:
                self._click_queue.put("right")
                self._target_event.set()
                logger.info("[CLICK_DIAG] RIGHT_CLICK_ENQUEUED: pos=(%d, %d) total=%d cooldown=%.0fms", pos_x, pos_y, self._right_click_count, self._settings.right_click_cooldown_ms)
                return True
            else:
                try:
                    self._driver.click_right()
                    logger.info("[CLICK_DIAG] RIGHT_CLICK_EXPLICIT: pos=(%d, %d) total=%d cooldown=%.0fms", pos_x, pos_y, self._right_click_count, self._settings.right_click_cooldown_ms)
                    return True
                except Exception as e:
                    self._last_error = f"Right click error: {e}"
                    logger.error(self._last_error)
                    return False

    def on_tracking_loss(self) -> None:
        """
        Notify controller that tracking was lost or no valid hand is in frame.
        Immediately stops cursor movement and resets smoothing.
        Disarms pinch clickers so a hand re-entering in a pinched pose does not fire an accidental click.
        """
        with self._lock:
            self._reset_smoothing_state()
            self._awaiting_pinch_release = True
            self._awaiting_right_pinch_release = True

    def _apply_dead_zone(self, u: float, v: float) -> Tuple[float, float]:
        """
        Apply dead zone around the center of the active tracking box.

        The dead zone is a circular region around the center of the active tracking box
        where small movements are ignored to prevent cursor jitter from hand tremors.
        
        This is applied to coordinates that are already normalized to the active
        tracking box [0.0, 1.0] x [0.0, 1.0], where (0.5, 0.5) is the center.
        
        The dead zone ONLY snaps to center when WITHIN the dead zone radius.
        It does NOT scale or pull coordinates that are outside the dead zone.
        
        Args:
            u: Normalized X coordinate in active tracking box [0.0, 1.0]
            v: Normalized Y coordinate in active tracking box [0.0, 1.0]
            
        Returns:
            Tuple of (adjusted_u, adjusted_v) with dead zone applied
        """
        dead_zone = self._settings.dead_zone
        if dead_zone <= 0.0:
            return u, v

        # Center of the active tracking box is at (0.5, 0.5)
        center_u = 0.5
        center_v = 0.5

        du = u - 0.5
        dv = v - 0.5
        distance = math.hypot(du, dv)

        if distance <= dead_zone:
            # Within dead zone: snap to center
            return 0.5, 0.5

        # Outside dead zone: return original coordinates unchanged
        # This preserves edge movements and prevents cursor being pulled toward center
        return u, v

    def map_coordinates(self, norm_x: float, norm_y: float) -> Tuple[int, int]:
        """
        Convert normalized webcam coordinates into desktop screen coordinates
        applying active tracking margin, sensitivity, dead zone, and screen boundary clamping.

        Args:
            norm_x: Normalized X [0.0, 1.0]
            norm_y: Normalized Y [0.0, 1.0]

        Returns:
            Tuple of (clamped_screen_x, clamped_screen_y)
        """
        screen_w, screen_h = self._driver.get_screen_size()
        margin_x = self._settings.active_margin_x
        margin_y = self._settings.active_margin_y

        # Active tracking box normalization
        span_x = max(0.1, 1.0 - 2.0 * margin_x)
        span_y = max(0.1, 1.0 - 2.0 * margin_y)

        # Check if the input coordinates are outside the active tracking box
        # Coordinates outside the active box should be clamped to screen edges
        # WITHOUT dead zone processing (dead zone only applies within active box)
        outside_active_box = (
            norm_x < margin_x or norm_x > (1.0 - margin_x) or
            norm_y < margin_y or norm_y > (1.0 - margin_y)
        )

        # Clamped position inside active box [0.0, 1.0]
        u = max(0.0, min(1.0, (norm_x - margin_x) / span_x))
        v = max(0.0, min(1.0, (norm_y - margin_y) / span_y))

        # Apply dead zone ONLY for coordinates within the active tracking box
        # Coordinates outside the active box skip dead zone and go straight to screen edges
        if not outside_active_box:
            u, v = self._apply_dead_zone(u, v)

        # Base screen coordinates (without sensitivity)
        base_x = u * (screen_w - 1)
        base_y = v * (screen_h - 1)

        # Apply sensitivity centered around display midpoint
        sensitivity = self._settings.sensitivity
        center_x = (screen_w - 1) / 2.0
        center_y = (screen_h - 1) / 2.0

        scaled_x = center_x + sensitivity * (base_x - center_x)
        scaled_y = center_y + sensitivity * (base_y - center_y)

        # Strict clamping to screen boundaries
        clamped_x = int(round(max(0.0, min(float(screen_w - 1), scaled_x))))
        clamped_y = int(round(max(0.0, min(float(screen_h - 1), scaled_y))))

        return clamped_x, clamped_y

    def move_to(self, x: int, y: int) -> None:
        """
        Safely move cursor via driver with screen boundary clamping.
        """
        screen_w, screen_h = self._driver.get_screen_size()
        clamped_x = max(0, min(screen_w - 1, int(x)))
        clamped_y = max(0, min(screen_h - 1, int(y)))
        try:
            self._driver.move_to(clamped_x, clamped_y)
            self._last_moved_x = clamped_x
            self._last_moved_y = clamped_y
            self._last_error = None
        except Exception as e:
            self._last_error = f"Cursor move error: {e}"
            logger.error(self._last_error)

    def _process_click_queue_on_worker(self) -> None:
        """Process pending clicks directly on the worker thread with interactive desktop access."""
        while not self._click_queue.empty():
            try:
                action = self._click_queue.get_nowait()
                if action == "left":
                    self._driver.click_left()
                    logger.info("[CLICK_DIAG] LEFT_CLICK_EXECUTED on worker thread: pos=%s", self._last_click_pos)
                elif action == "right":
                    self._driver.click_right()
                    logger.info("[CLICK_DIAG] RIGHT_CLICK_EXECUTED on worker thread: pos=%s", self._last_right_click_pos)
            except queue.Empty:
                break
            except Exception as e:
                logger.error("Click execution error on worker: %s", e)

    def _worker_loop(self) -> None:
        """Dedicated background worker loop: processes cursor movements at up to 120 Hz."""
        logger.debug("MouseController worker started")
        # Ensure worker thread is attached to user's interactive desktop
        if hasattr(self._driver, "prepare_thread"):
            self._driver.prepare_thread()

        timeout_sec = self._settings.tracking_timeout_ms / 1000.0

        while not self._stop_event.is_set():
            # Wait for target event with timeout
            if not self._target_event.wait(timeout=0.05):
                # Process any enqueued clicks even during cursor idle/pause
                self._process_click_queue_on_worker()

                # Check for tracking loss timeout
                now = time.time()
                with self._lock:
                    if self._is_enabled and (now - self._last_landmark_time > timeout_sec):
                        if not self._tracking_lost:
                            self._reset_smoothing_state()
                continue

            self._target_event.clear()
            self._process_click_queue_on_worker()

            if self._stop_event.is_set() or not self._is_enabled:
                break

            with self._lock:
                now = time.time()
                # Safety Rule: reject stale landmark points
                if now - self._last_landmark_time > timeout_sec or self._latest_norm_x is None:
                    self._reset_smoothing_state()
                    continue

                norm_x = self._latest_norm_x
                norm_y = self._latest_norm_y

            # Calculate raw screen coordinates
            target_x, target_y = self.map_coordinates(norm_x, norm_y)

            # Apply Exponential Moving Average (EMA) smoothing
            with self._lock:
                alpha = self._settings.smoothing_alpha
                if self._tracking_lost or self._prev_smoothed_x is None or self._prev_smoothed_y is None:
                    # Initial frame after tracking acquisition: initialize without smoothing to avoid jump
                    smoothed_x = float(target_x)
                    smoothed_y = float(target_y)
                    self._tracking_lost = False
                else:
                    smoothed_x = alpha * float(target_x) + (1.0 - alpha) * self._prev_smoothed_x
                    smoothed_y = alpha * float(target_y) + (1.0 - alpha) * self._prev_smoothed_y

                self._prev_smoothed_x = smoothed_x
                self._prev_smoothed_y = smoothed_y

            # Clamp and round to integer screen coordinates
            screen_w, screen_h = self._driver.get_screen_size()
            final_x = int(round(max(0.0, min(float(screen_w - 1), smoothed_x))))
            final_y = int(round(max(0.0, min(float(screen_h - 1), smoothed_y))))

            # Avoid redundant OS moves if position has not changed
            if final_x != self._last_moved_x or final_y != self._last_moved_y:
                self.move_to(final_x, final_y)

                # Diagnostic logging throttled to 1 Hz
                now_diag = time.time()
                if now_diag - self._last_diag_log_time >= 1.0:
                    self._last_diag_log_time = now_diag
                    logger.info(
                        "MOUSE_DIAG: norm=(%.3f, %.3f) screen=(%d, %d) moved=(%d, %d)",
                        norm_x, norm_y, target_x, target_y, final_x, final_y
                    )

            # Rate limit to ~120 Hz max (8ms)
            time.sleep(0.008)

        logger.debug("MouseController worker ended")

    def get_status(self) -> MouseStatusResponse:
        """Return current status and telemetry."""
        with self._lock:
            screen_w, screen_h = self._driver.get_screen_size()
            pos_x, pos_y = self._driver.get_position()
            if pos_x == 0 and pos_y == 0 and self._last_moved_x is not None and self._last_moved_y is not None:
                pos_x, pos_y = self._last_moved_x, self._last_moved_y

            now = time.time()
            timeout_sec = self._settings.tracking_timeout_ms / 1000.0
            is_stale = (now - self._last_landmark_time > timeout_sec)

            if not self._is_enabled:
                state = "disabled"
            elif self._last_error is not None:
                state = "error"
            elif self._hand_detected and not is_stale:
                state = "active"
            else:
                state = "waiting_for_hand"

            control_point = None
            if self._latest_norm_x is not None and self._latest_norm_y is not None and not is_stale:
                control_point = {
                    "x": round(self._latest_norm_x, 3),
                    "y": round(self._latest_norm_y, 3),
                }

            pinch_state = self._pinch_state
            if not self._is_enabled or not self._settings.left_click_enabled:
                pinch_state = "disabled"
            elif is_stale or not self._hand_detected:
                pinch_state = "idle"

            right_pinch_state = self._right_pinch_state
            if not self._is_enabled or not self._settings.right_click_enabled:
                right_pinch_state = "disabled"
            elif is_stale or not self._hand_detected:
                right_pinch_state = "idle"

            return MouseStatusResponse(
                enabled=self._is_enabled,
                state=state,
                hand_detected=self._hand_detected and not is_stale,
                control_point=control_point,
                cursor_position={"x": pos_x, "y": pos_y},
                screen_size={"width": screen_w, "height": screen_h},
                sensitivity=self._settings.sensitivity,
                smoothing_alpha=self._settings.smoothing_alpha,
                active_margin_x=self._settings.active_margin_x,
                active_margin_y=self._settings.active_margin_y,
                dead_zone=self._settings.dead_zone,
                last_error=self._last_error,
                # Phase 6B.1 Left Click Telemetry
                left_click_enabled=self._settings.left_click_enabled,
                pinch_distance=self._latest_pinch_distance if not is_stale else None,
                pinch_state=pinch_state,
                pinch_activation_threshold=self._settings.pinch_activation_threshold,
                pinch_release_threshold=self._settings.pinch_release_threshold,
                click_cooldown_ms=self._settings.click_cooldown_ms,
                last_click_time=self._last_click_time if self._last_click_time > 0 else None,
                last_click_position=self._last_click_pos,
                click_count=self._click_count,
                # Phase 6B.2 Right Click Telemetry
                right_click_enabled=self._settings.right_click_enabled,
                right_pinch_distance=self._latest_right_pinch_distance if not is_stale else None,
                right_pinch_state=right_pinch_state,
                right_pinch_activation_threshold=self._settings.right_pinch_activation_threshold,
                right_pinch_release_threshold=self._settings.right_pinch_release_threshold,
                right_click_cooldown_ms=self._settings.right_click_cooldown_ms,
                last_right_click_time=self._last_right_click_time if self._last_right_click_time > 0 else None,
                last_right_click_position=self._last_right_click_pos,
                right_click_count=self._right_click_count,
            )


# Global singleton instance
_mouse_controller: Optional[MouseController] = None
_mouse_controller_lock = threading.Lock()


def get_mouse_controller() -> MouseController:
    """Get the singleton MouseController instance."""
    global _mouse_controller
    with _mouse_controller_lock:
        if _mouse_controller is None:
            _mouse_controller = MouseController()
            _mouse_controller.initialize()
        return _mouse_controller