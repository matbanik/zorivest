"""Bootstrap convenience — re-exports LoggingManager for direct usage.

Usage examples from the spec (01a-logging.md §bootstrap.py):

    from zorivest_infra.logging.bootstrap import LoggingManager

    manager = LoggingManager()
    manager.bootstrap()                       # Phase 1: file-only
    manager.configure_from_settings(settings) # Phase 2: queue-based
    manager.shutdown()                        # Graceful stop
"""

from .config import LoggingManager

__all__ = ["LoggingManager"]
