"""
Error handling utility for the PDF Receipt Expense Splitter application.

This module provides consistent error handling and user-friendly error messages
throughout the application.
"""
import logging
import traceback
import streamlit as st
from typing import Optional, Tuple, Dict, Any, Callable

logger = logging.getLogger(__name__)

# Error message templates for common errors
ERROR_MESSAGES = {
    # PDF processing errors
    "pdf_invalid": "The uploaded file is not a valid PDF.",
    "pdf_corrupted": "The PDF file appears to be corrupted or damaged.",
    "pdf_encrypted": "The PDF file is encrypted or password-protected.",
    "pdf_empty": "The PDF file appears to be empty.",
    "pdf_too_large": "The PDF file is too large to process.",
    "pdf_extraction_failed": "Failed to extract text from the PDF.",
    
    # OCR errors
    "ocr_failed": "OCR processing failed. The image quality might be too low.",
    "ocr_not_available": "OCR processing is not available. Please check your installation.",
    
    # Receipt parsing errors
    "parsing_no_items": "No items could be found in the receipt.",
    "parsing_invalid_format": "The receipt format could not be recognized.",
    "parsing_low_confidence": "Items were extracted with low confidence. Please review carefully.",
    
    # Validation errors
    "validation_no_participants": "Please add at least 2 participants.",
    "validation_duplicate_participants": "Participant names must be unique.",
    "validation_empty_name": "Name fields cannot be empty.",
    "validation_unassigned_items": "Some items have no participants assigned.",
    "validation_total_mismatch": "The sum of all shares does not match the receipt total.",
    
    # General errors
    "unexpected_error": "An unexpected error occurred. Please try again.",
    "session_expired": "Your session has expired. Please start over.",
    "network_error": "A network error occurred. Please check your connection."
}

class ErrorHandler:
    """
    Provides consistent error handling and user-friendly error messages.
    """
    
    @staticmethod
    def get_error_message(error_code: str, details: Optional[str] = None) -> str:
        """
        Get a user-friendly error message for a given error code.
        
        Args:
            error_code: The error code
            details: Optional additional details
            
        Returns:
            User-friendly error message
        """
        message = ERROR_MESSAGES.get(error_code, "An error occurred.")
        
        if details:
            return f"{message} {details}"
        
        return message
    
    @staticmethod
    def show_error(error_code: str, details: Optional[str] = None) -> None:
        """
        Display an error message to the user using Streamlit.
        
        Args:
            error_code: The error code
            details: Optional additional details
        """
        message = ErrorHandler.get_error_message(error_code, details)
        st.error(message)
        
        # Log the error
        logger.error(f"Error {error_code}: {message}")
    
    @staticmethod
    def show_warning(error_code: str, details: Optional[str] = None) -> None:
        """
        Display a warning message to the user using Streamlit.
        
        Args:
            error_code: The error code
            details: Optional additional details
        """
        message = ErrorHandler.get_error_message(error_code, details)
        st.warning(message)
        
        # Log the warning
        logger.warning(f"Warning {error_code}: {message}")
    
    @staticmethod
    def handle_exception(e: Exception, error_code: str = "unexpected_error") -> None:
        """
        Handle an exception by logging it and showing an error message.
        
        Args:
            e: The exception
            error_code: The error code to use for the user-facing message
        """
        # Log the exception with traceback
        logger.exception(f"Exception in application: {str(e)}")
        
        # Show error to user
        ErrorHandler.show_error(error_code, str(e))
    
    @staticmethod
    def try_except_decorator(error_code: str = "unexpected_error"):
        """
        Decorator to wrap functions in try-except blocks with consistent error handling.
        
        Args:
            error_code: The error code to use for the user-facing message
            
        Returns:
            Decorated function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ErrorHandler.handle_exception(e, error_code)
                    return None
            return wrapper
        return decorator
    
    @staticmethod
    def safe_execute(func: Callable, error_code: str = "unexpected_error", *args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
        """
        Safely execute a function and handle any exceptions.
        
        Args:
            func: The function to execute
            error_code: The error code to use for the user-facing message
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Tuple containing:
            - Success flag (True if successful, False if an exception occurred)
            - Result of the function (or None if an exception occurred)
            - Error message (or None if successful)
        """
        try:
            result = func(*args, **kwargs)
            return True, result, None
        except Exception as e:
            error_message = ErrorHandler.get_error_message(error_code, str(e))
            logger.exception(f"Error in safe_execute: {error_message}")
            return False, None, error_message
# </content>