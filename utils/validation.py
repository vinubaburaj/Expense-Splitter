"""
Validation utility for the PDF Receipt Expense Splitter application.

This module provides validation functions for user inputs, file uploads,
and data integrity checks throughout the application.
"""
from typing import Dict, List, Tuple, Optional, Any
import re
from models.extracted_item import ExtractedItem


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class Validator:
    """
    Provides validation methods for various aspects of the application.
    """
    
    @staticmethod
    def validate_pdf_file(uploaded_file: Any, max_size_mb: int = 10) -> Tuple[bool, str]:
        """
        Validate the uploaded PDF file.
        
        Args:
            uploaded_file: The file uploaded through Streamlit's file_uploader
            max_size_mb: Maximum allowed file size in MB
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if uploaded_file is None:
            return False, "No file uploaded"
        
        # Check file type
        if not uploaded_file.name.lower().endswith('.pdf'):
            return False, f"Invalid file format. Please upload a PDF file. You uploaded: {uploaded_file.name}"
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        if uploaded_file.size > max_size_bytes:
            return False, f"File size exceeds the {max_size_mb}MB limit. Please upload a smaller file."
        
        return True, ""
    
    @staticmethod
    def validate_participants(participants: List[str]) -> Tuple[bool, str]:
        """
        Validate the list of participants.
        
        Args:
            participants: List of participant names
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not participants:
            return False, "No participants added"
        
        if len(participants) < 2:
            return False, "At least 2 participants are required"
        
        # Check for empty names
        empty_names = [i for i, name in enumerate(participants) if not name.strip()]
        if empty_names:
            return False, "Participant names cannot be empty"
        
        # Check for duplicate names
        if len(participants) != len(set(participants)):
            return False, "Duplicate participant names are not allowed"
        
        return True, ""
    
    @staticmethod
    def validate_item(name: str, price: float, quantity: int) -> Tuple[bool, str]:
        """
        Validate an expense item.
        
        Args:
            name: Item name
            price: Item price
            quantity: Item quantity
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Item name is required"
        
        if price <= 0:
            return False, "Price must be greater than zero"
        
        if quantity <= 0:
            return False, "Quantity must be greater than zero"
        
        return True, ""
    
    @staticmethod
    def validate_item_assignments(items: List[ExtractedItem], assignments: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
        """
        Validate that all items have participants assigned.
        
        Args:
            items: List of ExtractedItem objects
            assignments: Dictionary mapping item IDs to lists of assigned person names
            
        Returns:
            tuple: (is_valid, list_of_unassigned_item_names)
        """
        unassigned_items = []
        
        for item in items:
            if not assignments.get(item.id, []):
                unassigned_items.append(item.name)
        
        return len(unassigned_items) == 0, unassigned_items
    
    @staticmethod
    def validate_totals(total_receipt: float, total_shares: float, tolerance: float = 0.01) -> bool:
        """
        Validate that the sum of all shares equals the receipt total.
        
        Args:
            total_receipt: Total receipt amount
            total_shares: Sum of all individual shares
            tolerance: Allowed difference between totals (to account for floating-point errors)
            
        Returns:
            True if the totals match (within tolerance), False otherwise
        """
        return abs(total_receipt - total_shares) <= tolerance
    
    @staticmethod
    def validate_item_name(name: str) -> Tuple[bool, str]:
        """
        Validate an item name.
        
        Args:
            name: Item name to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Item name cannot be empty"
        
        if len(name.strip()) < 2:
            return False, "Item name must be at least 2 characters long"
        
        # Check for invalid characters
        if re.search(r'[^\w\s\.\-\&\'\(\)]', name):
            return False, "Item name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_extracted_items(items: List[ExtractedItem]) -> Tuple[bool, str]:
        """
        Validate a list of extracted items.
        
        Args:
            items: List of ExtractedItem objects
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not items:
            return False, "No items extracted"
        
        for item in items:
            # Validate item name
            name_valid, name_error = Validator.validate_item_name(item.name)
            if not name_valid:
                return False, f"Invalid item '{item.name}': {name_error}"
            
            # Validate price
            if item.total_price <= 0:
                return False, f"Item '{item.name}' has an invalid price: ${item.total_price}"
            
            # Validate quantity if present
            if item.quantity is not None and item.quantity <= 0:
                return False, f"Item '{item.name}' has an invalid quantity: {item.quantity}"
        
        return True, ""
# </content>