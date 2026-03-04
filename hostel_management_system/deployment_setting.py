"""
Compatibility settings module.
Use hostel_management_system.settings for both local and Render deployment.
"""

from .settings import *  # noqa: F401,F403

# Keep production-safe defaults if this module is explicitly selected.
DEBUG = False
