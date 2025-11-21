"""
Axiom logging utility for error tracking and monitoring.
Supports both Axiom cloud logging and local console output.
"""

import json
import logging
import os
import re
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern, Union

from axiom_py.client import Client
from axiom_py.logging import AxiomHandler

# Default fields that are allowed to show in logs (allowlist approach)
# Any field not in this list will be redacted for security
DEFAULT_ALLOWED_FIELDS = ["id"]


class AxiomLogger:
    """
    Utility class for logging errors and events to Axiom.

    Supports efficient field filtering using:
    - Literal strings: "id", "name", "data.score"
    - Compiled regex: re.compile(r'^user_\d+$'), re.compile(r'.*_id$')
    - Mixed lists: ["id", "name", re.compile(r'^data\.score$')]
    """

    def __init__(
        self,
        service_name: str,
        axiom_token: str,
        axiom_dataset: str,
        allowed_fields: Optional[List[str]] = None,
        console_output: bool = True,
    ):
        self.service_name = service_name
        base_fields = allowed_fields or DEFAULT_ALLOWED_FIELDS
        self.allowed_fields = base_fields + ["__body_unwrapped"]
        # Compile regex patterns for efficient matching
        self._compiled_patterns = self._compile_patterns(self.allowed_fields)
        self.token = axiom_token
        self.dataset = axiom_dataset
        self.client = None
        self.handler = None
        self.console_handler = None
        self.console_logger = None
        self.axiom_logger = None
        self.last_error_time = None
        self.console_output = console_output

        # Set up console logger
        self.console_logger = None
        if self.console_output:
            self.console_logger = logging.getLogger(f"console_{__name__}_{id(self)}")
            self.console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            self.console_handler.setFormatter(formatter)
            self.console_logger.addHandler(self.console_handler)
            # Prevent propagation to avoid duplicate console output
            self.console_logger.propagate = False

        # Set up Axiom logger
        self.axiom_logger = None
        if self.token:
            try:
                self.client = Client(token=self.token)
                self.handler = AxiomHandler(self.client, self.dataset)
                self.axiom_logger = logging.getLogger(f"axiom_{__name__}_{id(self)}")
                self.axiom_logger.addHandler(self.handler)
                # Prevent propagation to avoid duplicate console output
                self.axiom_logger.propagate = False
            except Exception as e:
                print(f"Failed to initialize Axiom client: {e}")
        else:
            print("Warning: Axiom token not provided. Axiom logging disabled.")

    def _compile_patterns(
        self, allowed_fields: List[Union[str, Pattern]]
    ) -> List[Pattern]:
        """
        Compile field patterns into regex objects for efficient matching.

        Args:
            allowed_fields: List of field patterns (literal strings or compiled regex)

        Returns:
            List of compiled regex patterns
        """
        compiled_patterns = []

        for field in allowed_fields:
            if isinstance(field, Pattern):
                # Already a compiled regex
                compiled_patterns.append(field)
            else:
                # Convert literal string to exact match regex (case-insensitive)
                pattern_str = str(field).lower()
                escaped = re.escape(pattern_str)

                try:
                    compiled_pattern = re.compile(f"^{escaped}$", re.IGNORECASE)
                    compiled_patterns.append(compiled_pattern)
                except re.error as e:
                    print(f"Warning: Invalid pattern '{field}': {e}")

        return compiled_patterns

    def _is_field_allowed(self, field_path: str, current_path: str = "") -> bool:
        """
        Check if a field is allowed using pre-compiled regex patterns.
        Much more efficient than the previous wildcard approach.

        Args:
            field_path: The field name to check
            current_path: The current nested path context

        Returns:
            bool: True if the field is allowed, False otherwise
        """
        full_path = f"{current_path}.{field_path}" if current_path else field_path

        # Test against all compiled patterns
        for pattern in self._compiled_patterns:
            # Check both field name and full path
            if pattern.match(field_path) or pattern.match(full_path):
                return True

        return False

    def redact_sensitive_fields(
        self, data: Dict[str, Any], current_path: str = ""
    ) -> Dict[str, Any]:
        """
        Recursively redacts fields from a dictionary that are not in the allowed_fields list.
        Only fields matching the allowed patterns will be shown, all others are redacted.

        Supports two types of patterns:
        - Literal strings: "id", "name", "data.score" (exact matches, case-insensitive)
        - Compiled regex: re.compile(r'.*_id$'), re.compile(r'^user_\d+$')

        If data only has one property called 'body' containing a JSON string, it will be unwrapped.

        Args:
            data: The dictionary to redact fields from
            current_path: The current nested path for pattern matching

        Returns:
            Dict with non-allowed fields replaced with "[REDACTED]"
        """
        if not isinstance(data, dict):
            return data

        # Check if data only has one prop 'body' and unwrap if it's a JSON string
        if len(data) == 1 and "body" in data and not current_path:
            body_value = data["body"]
            if isinstance(body_value, str):
                try:
                    # Try to parse the body as JSON
                    parsed_body = json.loads(body_value)
                    if isinstance(parsed_body, dict):
                        # Replace data with parsed body content and mark as unwrapped
                        data = {**parsed_body, "__body_unwrapped": True}
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, continue with original data
                    pass

        redacted_data = {}

        for key, value in data.items():
            if self._is_field_allowed(key, current_path):
                if isinstance(value, dict):
                    nested_path = f"{current_path}.{key}" if current_path else key
                    redacted_data[key] = self.redact_sensitive_fields(
                        value, nested_path
                    )
                elif isinstance(value, list):
                    nested_path = f"{current_path}.{key}" if current_path else key
                    redacted_data[key] = [
                        (
                            self.redact_sensitive_fields(item, nested_path)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
                else:
                    redacted_data[key] = value
            else:
                redacted_data[key] = "[REDACTED]"

        return redacted_data

    def error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log an error to Axiom with context and event data.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            event_data: The original event data that caused the error

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        axiom_success = False

        try:
            current_time = time.time()
            exclude_from_slack = False

            # Check if this is a repeated error call within 5 seconds
            if (
                self.last_error_time is not None
                and (current_time - self.last_error_time) < 5
            ):
                exclude_from_slack = True

            # Update the last error time
            self.last_error_time = current_time

            # Prepare log message for console
            error_msg = f"[{self.service_name}] {str(error)}"
            if context:
                error_msg += f" | Context: {json.dumps(context, default=str)}"

            # Log to console (if enabled)
            if self.console_logger:
                self.console_logger.error(error_msg, exc_info=True)

            # Log to Axiom (if available)
            if self.axiom_logger:
                try:
                    log_entry = {
                        "level": "error",
                        "_excludeFromSlackNotification": exclude_from_slack,
                        "_type": "workflow",
                        "_service": self.service_name,
                        "context": context or {},
                        "event": self.redact_sensitive_fields(event_data or {}),
                    }
                    self.axiom_logger.error(str(error), exc_info=True, extra=log_entry)
                    axiom_success = True
                except Exception as e:
                    print(f"Exception while logging to Axiom: {e}")
            else:
                print("Axiom client not available. Error not logged to Axiom.")

            return True  # Return True if at least console logging succeeded

        except Exception as e:
            print(f"Exception while logging: {e}")
            return False

    def info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log an info message to Axiom and console.

        Args:
            message: The info message
            context: Additional context
            event_data: The event data

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        try:
            # Prepare log message for console
            info_msg = f"[{self.service_name}] {message}"
            if context:
                info_msg += f" | Context: {json.dumps(context, default=str)}"

            # Log to console (if enabled)
            if self.console_logger:
                self.console_logger.info(info_msg)

            # Log to Axiom (if available)
            if self.axiom_logger:
                try:
                    log_entry = {
                        "level": "info",
                        "_type": "workflow",
                        "_service": self.service_name,
                        "context": context or {},
                        "event": self.redact_sensitive_fields(event_data or {}),
                    }
                    self.axiom_logger.info(message, extra=log_entry)
                except Exception as e:
                    print(f"Exception while logging to Axiom: {e}")

            return True

        except Exception as e:
            print(f"Exception while logging: {e}")
            return False

    def warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log a warning message to Axiom and console.

        Args:
            message: The warning message
            context: Additional context
            event_data: The event data

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        try:
            # Prepare log message for console
            warning_msg = f"[{self.service_name}] {message}"
            if context:
                warning_msg += f" | Context: {json.dumps(context, default=str)}"

            # Log to console (if enabled)
            if self.console_logger:
                self.console_logger.warning(warning_msg)

            # Log to Axiom (if available)
            if self.axiom_logger:
                try:
                    log_entry = {
                        "level": "warning",
                        "_type": "workflow",
                        "_service": self.service_name,
                        "context": context or {},
                        "event": self.redact_sensitive_fields(event_data or {}),
                    }
                    self.axiom_logger.warning(message, extra=log_entry)
                except Exception as e:
                    print(f"Exception while logging to Axiom: {e}")

            return True

        except Exception as e:
            print(f"Exception while logging: {e}")
            return False

    def flush(self) -> bool:
        """
        Flush any buffered logs to Axiom immediately.

        Returns:
            bool: True if flush succeeded, False otherwise
        """
        if not self.handler:
            print("Axiom handler not available. Cannot flush logs.")
            return False

        try:
            self.handler.flush()
            return True
        except Exception as e:
            print(f"Exception while flushing logs to Axiom: {e}")
            return False
