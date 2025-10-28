"""
Oracle Database Driver Compatibility Fix for Python 3.12

This module patches the Django Oracle backend to fix compatibility issues
with oracledb 2.x/3.x and Python 3.12.

The issue: Django's Oracle backend tries to use isinstance() with Database.Binary,
but the newer oracledb driver doesn't expose this type in a way that's compatible
with Python 3.12's stricter type checking in isinstance().

This patch must be imported BEFORE Django loads the Oracle backend.
Import this in settings.py or wsgi.py at the very top.
"""

import sys
import logging

logger = logging.getLogger(__name__)


def patch_oracle_isinstance():
    """
    Patch Django's Oracle backend to handle oracledb driver type issues.
    
    This fixes the "isinstance() arg 2 must be a type" error that occurs
    with Django 5.2+ and oracledb 2.x/3.x on Python 3.12.
    """
    try:
        # Only patch if we're using Oracle
        import oracledb as Database
        
        # Check if Database.Binary exists and is valid for isinstance()
        try:
            isinstance(b"test", Database.Binary)
            logger.info("Oracle Database.Binary is compatible, no patch needed")
            return
        except TypeError:
            logger.warning("Oracle Database.Binary is not compatible with isinstance(), applying patch")
        
        # Monkey-patch the OracleParam class in Django's Oracle backend
        from django.db.backends.oracle import base
        
        # Store the original __init__ method
        original_oracle_param_init = base.OracleParam.__init__
        
        def patched_oracle_param_init(self, param, cursor, strings_only):
            """
            Patched OracleParam.__init__ that handles Database.Binary type issues.
            """
            import datetime
            
            # Use the parent class logic but wrap isinstance calls safely
            if param is None:
                # Check if 'Database' module has NULL attribute
                if hasattr(Database, 'NULL'):
                    self.force_bytes = False
                    self.input_size = None
                    return
            
            # Handle datetime.timedelta safely
            try:
                if isinstance(param, datetime.timedelta):
                    self.force_bytes = False
                    self.input_size = None
                    return
            except TypeError:
                pass
            
            # Try to check for Database.Binary type safely
            try:
                # Check if Database.Binary is a valid type
                if hasattr(Database, 'Binary') and isinstance(Database.Binary, type):
                    if isinstance(param, Database.Binary):
                        self.force_bytes = False
                        self.input_size = None
                        return
            except (TypeError, AttributeError):
                # If Database.Binary check fails, skip it
                pass
            
            # Handle bytes type
            if isinstance(param, bytes):
                self.force_bytes = False
                self.input_size = None
                return
            
            # Call the rest of the original logic
            # We'll recreate the essential parts here
            if strings_only and isinstance(param, str):
                self.force_bytes = True
                # Use NVARCHAR2 by default for strings
                self.input_size = len(param) or 1
            else:
                self.force_bytes = False
                self.input_size = None
        
        # Apply the patch
        base.OracleParam.__init__ = patched_oracle_param_init
        logger.info("Successfully patched Django Oracle backend for Python 3.12 compatibility")
        
    except ImportError:
        # oracledb not installed, skip patching
        logger.debug("oracledb not installed, skipping Oracle compatibility patch")
    except Exception as e:
        logger.error(f"Failed to patch Oracle backend: {e}", exc_info=True)


def apply_oracle_fixes():
    """
    Apply all Oracle-related compatibility fixes.
    
    Call this function at the very beginning of settings.py or wsgi.py
    BEFORE Django initializes the database connection.
    """
    patch_oracle_isinstance()
