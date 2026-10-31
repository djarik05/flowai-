"""
Application service for GestureFlow AI backend.

Central service that manages backend state and coordinates
initialization of future modules.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings
from app.schemas.status import BackendState, ComponentState, ModelState

logger = logging.getLogger(__name__)


@dataclass
class ComponentStatus:
    """Tracks the status of a backend component."""

    name: str
    state: ComponentState | ModelState = ComponentState.NOT_INITIALIZED
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class ApplicationService:
    """
    Core application service managing backend lifecycle and state.

    In Phase 1, this service:
    - Tracks backend initialization state
    - Provides status information
    - Prepares interfaces for future modules

    Future phases will extend this with:
    - Camera manager integration
    - Hand tracking service
    - Model loading and inference
    - Controller management
    """

    def __init__(self) -> None:
        """Initialize the application service."""
        self._backend_state: BackendState = BackendState.STARTING
        self._components: dict[str, ComponentStatus] = {}
        self._initialized: bool = False

        # Register known components with initial states
        self._register_component("camera", ComponentState.NOT_INITIALIZED)
        self._register_component("tracking", ComponentState.NOT_INITIALIZED)
        self._register_component("model", ModelState.NOT_LOADED)
        self._register_component("controller", ComponentState.DISABLED)

    def _register_component(
        self,
        name: str,
        initial_state: ComponentState | ModelState,
        metadata: Optional[dict] = None,
    ) -> None:
        """Register a component for status tracking."""
        self._components[name] = ComponentStatus(
            name=name,
            state=initial_state,
            metadata=metadata or {},
        )

    async def initialize(self) -> None:
        """Initialize the application service."""
        if self._initialized:
            logger.warning("Application service already initialized")
            return

        logger.info("Initializing application service")
        self._backend_state = BackendState.READY
        self._initialized = True
        logger.info("Application service initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the application service gracefully."""
        logger.info("Shutting down application service")

        # Stop tracking service if running
        tracking_comp = self.get_component_status("tracking")
        if tracking_comp and tracking_comp.metadata.get("instance"):
            try:
                tracking_comp.metadata["instance"].stop()
            except Exception as e:
                logger.debug("Error stopping tracking on shutdown: %s", e)

        # Stop camera manager if running
        camera_comp = self.get_component_status("camera")
        if camera_comp and camera_comp.metadata.get("instance"):
            try:
                camera_comp.metadata["instance"].stop()
            except Exception as e:
                logger.debug("Error stopping camera on shutdown: %s", e)

        # Stop dataset collector if running
        try:
            from app.api.routes.collection import _collector
            if _collector and _collector.is_active:
                _collector.stop_collection()
        except Exception as e:
            logger.debug("Error stopping dataset collector on shutdown: %s", e)

        # Stop mouse controller if running
        try:
            from app.services.mouse_controller import get_mouse_controller
            get_mouse_controller().stop()
        except Exception as e:
            logger.debug("Error stopping mouse controller on shutdown: %s", e)

        self._backend_state = BackendState.SHUTTING_DOWN
        self._initialized = False
        logger.info("Application service shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if service has been initialized."""
        return self._initialized

    @property
    def backend_state(self) -> BackendState:
        """Get current backend state."""
        return self._backend_state

    def get_component_status(self, name: str) -> Optional[ComponentStatus]:
        """Get status of a specific component."""
        return self._components.get(name)

    def get_all_component_statuses(self) -> dict[str, ComponentStatus]:
        """Get status of all registered components."""
        return self._components.copy()

    def set_component_state(
        self,
        name: str,
        state: ComponentState | ModelState,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Update a component's state.

        Args:
            name: Component name
            state: New state
            error: Optional error message
            metadata: Optional additional metadata

        Returns:
            True if component was found and updated
        """
        if name not in self._components:
            logger.warning("Attempted to update unknown component: %s", name)
            return False

        self._components[name].state = state
        if error is not None:
            self._components[name].error = error
        if metadata:
            self._components[name].metadata.update(metadata)

        logger.debug("Component %s state changed to %s", name, state)
        return True

    def get_status_summary(self) -> dict:
        """
        Get a summary of application status for API responses.

        Returns:
            Dictionary with status information
        """
        return {
            "application": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "backend_state": self._backend_state.value,
            "current_phase": 1,
            "camera_state": self._components["camera"].state.value,
            "tracking_state": self._components["tracking"].state.value,
            "model_state": self._components["model"].state.value,
            "controller_state": self._components["controller"].state.value,
        }