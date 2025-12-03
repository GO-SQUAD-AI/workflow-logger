"""
Example usage of the AxiomLogger package.
"""

import os

from workflow_logger import AxiomLogger


def main():
    """Demonstrate AxiomLogger usage."""

    # Initialize logger with field patterns
    # Supports two types of patterns:
    # - Literal strings: exact field name matches (case-insensitive)
    # - Compiled regex: for complex pattern matching

    import re  # For compiled regex examples

    logger = AxiomLogger(
        service_name="example-service",
        axiom_token=os.environ.get("AXIOM_TOKEN", "your-axiom-token-here"),
        axiom_dataset=os.environ.get("AXIOM_DATASET", "local"),
        allowed_fields=[
            "id",
            "name",
            "status",
            "user_id",  # Literal: exact match for user_id field
            "account_id",  # Literal: exact match for account_id field
            "data",
            "data.id",  # Literal: exact match for nested path
            "data.name",  # Literal: exact match for nested path
            "data.user_id",  # Literal: exact match for nested user_id
            "data.evaluation.score",  # Literal: deep nested path
            re.compile(r".*_id$"),  # Regex: any field ending in _id
            re.compile(r"^evaluation\..*_id$"),  # Regex: any _id in evaluation context
            re.compile(r"^user_\d+$"),  # Regex: user_123, user_456, etc.
        ],
        axiom_output=False,
        console_output=True,
    )

    # Example 1: Log an error
    # try:
    #     # Simulate an error
    #     result = 10 / 0
    # except Exception as e:
    #     success = logger.error(
    #         error=e,
    #         context={
    #             "aws_request_id": "12345678-1234-1234-1234-123456789012",
    #             "function_name": "data-validation-function",
    #             "function_version": "$LATEST",
    #             "memory_limit": "128",
    #             "remaining_time": "29850",
    #         },
    #         event_data={
    #             "id": "op_123",
    #             "name": "Division Operation",
    #             "password": "secret123",  # This will be redacted
    #             "api_key": "sk_test_123",  # This will be redacted
    #             "status": "failed",
    #         },
    #     )
    #     print(f"Error logged successfully: {success}")

    # # Example 2: Log info message
    # success = logger.info(
    #     message="Processing batch completed",
    #     context={
    #         "aws_request_id": "87654321-4321-4321-4321-210987654321",
    #         "function_name": "batch-processing-function",
    #         "function_version": "v1.2.3",
    #         "memory_limit": "256",
    #         "remaining_time": "25000"
    #     },
    #     event_data={
    #         "id": "batch_456",
    #         "name": "User Data Batch",
    #         "record_count": 1000,
    #         "sensitive_field": "private_data",  # This will be redacted
    #         "status": "completed"
    #     }
    # )
    # print(f"Info logged successfully: {success}")

    # # Example 3: Log warning
    # success = logger.warning(
    #     message="High memory usage detected",
    #     context={
    #         "aws_request_id": "abcd1234-5678-9012-3456-789012345678",
    #         "function_name": "memory-intensive-function",
    #         "function_version": "v2.0.1",
    #         "memory_limit": "512",
    #         "remaining_time": "15750"
    #     },
    #     event_data={
    #         "id": "alert_789",
    #         "name": "Memory Alert",
    #         "server_details": "sensitive_server_info",  # This will be redacted
    #         "status": "warning"
    #     }
    # )
    # print(f"Warning logged successfully: {success}")

    # Example 4: Log an error unwrapping body
    try:
        logger.info(
            "@@@ Dividing by zero to trigger error logging...",
            context={},
            event_data={"n": 10, "d": 0},
        )
        # Simulate an error
        result = 10 / 0
    except Exception as e:
        success = logger.error(
            error=e,
            context={
                "aws_request_id": "12345678-1234-1234-1234-123456789012",
                "function_name": "data-validation-function",
                "function_version": "$LATEST",
                "memory_limit": "128",
                "remaining_time": "29850",
            },
            event_data={
                "body": '{"data": {"id": 12345, "user_id": "user_789", "name": "Bruno Test John Doe", "secret_token": "abc123", "evaluation": {"score": 85, "admin_id": "admin_456", "private_notes": "confidential"}}, "account_id": "acc_999", "password": "hidden123"}'
            },
        )
        print(f"Error logged successfully: {success}")


if __name__ == "__main__":
    main()
