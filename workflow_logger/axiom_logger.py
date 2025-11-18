"""
Axiom logging utility for error tracking and monitoring.
"""
import os
import json
import traceback
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from axiom_py.client import Client
from axiom_py.logging import AxiomHandler
import logging

# Default fields that are allowed to show in logs (allowlist approach)
# Any field not in this list will be redacted for security
DEFAULT_ALLOWED_FIELDS = ["id"]

class AxiomLogger:
    """Utility class for logging errors and events to Axiom."""
    
    def __init__(self, service_name: str, axiom_token: str, axiom_dataset: str, allowed_fields: Optional[List[str]] = None):
        self.service_name = service_name
        self.allowed_fields = allowed_fields or DEFAULT_ALLOWED_FIELDS
        self.token = axiom_token
        self.dataset = axiom_dataset
        self.client = None
        self.handler = None
        self.logger = None
        self.last_error_time = None

        if self.token:
            try:
                self.client = Client(token=self.token)
                self.handler = AxiomHandler(self.client, self.dataset)
                logging.getLogger().addHandler(self.handler)
                self.logger = logging.getLogger(__name__)
            except Exception as e:
                print(f"Failed to initialize Axiom client: {e}")
        else:
            print("Warning: Axiom token not provided. Axiom logging disabled.")
    
    def redact_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively redacts fields from a dictionary that are not in the allowed_fields list.
        Only fields explicitly listed in allowed_fields will be shown, all others are redacted.
        
        Args:
            data: The dictionary to redact fields from
            
        Returns:
            Dict with non-allowed fields replaced with "[REDACTED]"
        """
        if not isinstance(data, dict):
            return data
        
        redacted_data = {}
        allowed_fields_lower = [field.lower() for field in self.allowed_fields]
        
        for key, value in data.items():
            if key.lower() not in allowed_fields_lower:
                redacted_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted_data[key] = self.redact_sensitive_fields(value)
            elif isinstance(value, list):
                redacted_data[key] = [
                    self.redact_sensitive_fields(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    def error(self, 
                  error: Exception, 
                  context: Optional[Dict[str, Any]] = None,
                  event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an error to Axiom with context and event data.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            event_data: The original event data that caused the error
            
        Returns:
            bool: True if logging succeeded, False otherwise
        """
        if not self.client:
            print("Axiom client not available. Error not logged to Axiom.")
            return False
        
        try:
            current_time = time.time()
            exclude_from_slack = False
            
            # Check if this is a repeated error call within 5 seconds
            if self.last_error_time is not None and (current_time - self.last_error_time) < 5:
                exclude_from_slack = True
            
            # Update the last error time
            self.last_error_time = current_time
            
            log_entry = {
                "level": "error",
                "_excludeFromSlackNotification": exclude_from_slack,
                "_type": "workflow",
                "_service": self.service_name,
                "context": context or {},
                "event": self.redact_sensitive_fields(event_data or {})
            }
           
            self.logger.error(str(error),
                             exc_info=True, 
                             extra=log_entry)
            return True
                
        except Exception as e:
            print(f"Exception while logging to Axiom: {e}")
            return False
    
    def info(self, 
                 message: str, 
                 context: Optional[Dict[str, Any]] = None,
                 event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an info message to Axiom.
        
        Args:
            message: The info message
            context: Additional context
            event_data: The event data
            
        Returns:
            bool: True if logging succeeded, False otherwise
        """
        if not self.client:
            return False
        
        try:
            log_entry = {
                "level": "info",
                "_type": "workflow",
                "_service": self.service_name,
                "context": context or {},
                "event": self.redact_sensitive_fields(event_data or {})
            }
            
            self.logger.info(message,
                             exc_info=True,
                             extra=log_entry)
            
        except Exception as e:
            print(f"Exception while logging to Axiom: {e}")
            return False
    
    def warning(self, 
                    message: str, 
                    context: Optional[Dict[str, Any]] = None,
                    event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log a warning message to Axiom.
        
        Args:
            message: The warning message
            context: Additional context
            event_data: The event data
            
        Returns:
            bool: True if logging succeeded, False otherwise
        """
        if not self.client:
            return False
        
        try:
            log_entry = {
                "level": "warning",
                "_type": "workflow",
                "_service": self.service_name,
                "context": context or {},
                "event": self.redact_sensitive_fields(event_data or {})
            }
            
            self.logger.warning(message,
                                exc_info=True,
                                extra=log_entry)
            
        except Exception as e:
            print(f"Exception while logging to Axiom: {e}")
            return False

