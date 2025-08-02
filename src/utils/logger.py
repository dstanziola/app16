"""
Logger alias for compatibility
Provides get_logger function as alias to LoggingHelper
"""

from .logging_helper import LoggingHelper


def get_logger(name: str):
    """
    Get logger instance using LoggingHelper
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    # Extract meaningful name from module path
    if '.' in name:
        parts = name.split('.')
        if 'ui' in parts and 'forms' in parts:
            # UI form logger
            form_name = parts[-1] if parts else name
            return LoggingHelper.get_ui_logger(form_name)
        elif 'services' in parts:
            # Service logger
            service_name = parts[-1] if parts else name
            return LoggingHelper.get_service_logger(service_name)
        else:
            # System logger
            return LoggingHelper.get_system_logger()
    else:
        # Fallback to system logger
        return LoggingHelper.get_system_logger()
