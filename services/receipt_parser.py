"""
Receipt Parser Service for extracting items from receipt text.

This module provides functionality to parse receipt text and extract
items, prices, quantities, and special charges like tips and service fees.
"""

import re
import logging
import uuid
from typing import List, Dict, Tuple, Optional, Match
from dataclasses import dataclass

from models.extracted_item import ExtractedItem

logger = logging.getLogger(__name__)


class ReceiptParsingError(Exception):
    """Custom exception for receipt parsing errors."""
    pass


@dataclass
class ParsedLine:
    """Helper class to store parsed line data during processing."""
    text: str
    item_name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    confidence_score: float = 0.0
    is_special_charge: bool = False


class ReceiptParser:
    """
    Parses receipt text to extract items, quantities, and prices.
    
    Uses regex patterns to identify common receipt formats and extract
    structured data from unstructured text.
    """
    
    # Common special charge keywords
    SPECIAL_CHARGE_KEYWORDS = {
        'tip': ['tip', 'gratuity'],
        'service': ['service fee', 'service charge', 'service'],
        'delivery': ['delivery fee', 'delivery charge', 'delivery']
    }
    
    # Regex patterns for item extraction
    ITEM_PATTERNS = [
        # Pattern 3: Item with quantity and unit price (e.g., "2 x Coffee 2.50 5.00")
        r'(?P<quantity>\d+)\s*x\s+(?P<name>[A-Za-z0-9\s&\-\'\.]+?)\s+(?P<unit_price>\d+\.\d{2})\s+(?P<price>\d+\.\d{2})',
        
        # Pattern 1: Item with quantity and price (e.g., "2 Coffee 5.00")
        r'(?P<quantity>\d+)\s+(?P<name>[A-Za-z0-9\s&\-\'\.]+?)\s+(?P<price>\d+\.\d{2})',
        
        # Pattern 2: Item with price at end (e.g., "Coffee 5.00")
        r'(?P<name>[A-Za-z0-9\s&\-\'\.]+?)\s+(?P<price>\d+\.\d{2})',
    ]
    
    # Regex patterns for total extraction
    TOTAL_PATTERNS = [
        r'total\s*(?::|$|\s)\s*(?P<total>\d+\.\d{2})',
        r'(?:sub)?total\s*(?::|$|\s)\s*(?P<total>\d+\.\d{2})',
        r'amount\s*(?::|$|\s)\s*(?P<total>\d+\.\d{2})',
        r'(?:grand|final)\s*total\s*(?::|$|\s)\s*(?P<total>\d+\.\d{2})'
    ]
    
    # Regex patterns for special charges
    SPECIAL_CHARGE_PATTERNS = [
        # Tip pattern
        r'(?:tip|gratuity)\s*(?::|$|\s)\s*(?P<amount>\d+\.\d{2})',
        
        # Service charge pattern
        r'(?:service\s*(?:charge|fee))\s*(?::|$|\s)\s*(?P<amount>\d+\.\d{2})',
        
        # Delivery fee pattern
        r'(?:delivery\s*(?:charge|fee))\s*(?::|$|\s)\s*(?P<amount>\d+\.\d{2})'
    ]
    
    def __init__(self):
        """Initialize the ReceiptParser with compiled regex patterns."""
        # Compile regex patterns for better performance
        self.item_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.ITEM_PATTERNS]
        self.total_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.TOTAL_PATTERNS]
        self.special_charge_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SPECIAL_CHARGE_PATTERNS]
    
    def parse_receipt_text(self, text: str) -> List[ExtractedItem]:
        """
        Parse receipt text to extract items.
        
        Args:
            text: Raw text extracted from receipt
            
        Returns:
            List of ExtractedItem objects
            
        Raises:
            ReceiptParsingError: If parsing fails or no items found
        """
        parsing_errors = []
        
        if not text or not text.strip():
            logger.error("Empty or blank receipt text provided")
            raise ReceiptParsingError("The receipt text is empty or blank")
        
        try:
            # Clean and normalize the text
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text or len(cleaned_text) < 10:  # Arbitrary minimum length for valid receipt
                parsing_errors.append("Receipt text too short after cleaning")
                logger.warning("Receipt text too short after cleaning")
            
            # Split into lines
            lines = cleaned_text.split('\n')
            
            if len(lines) < 2:  # A receipt should have at least a few lines
                parsing_errors.append("Too few lines in receipt text")
                logger.warning("Too few lines in receipt text")
            
            # Parse each line
            parsed_lines = self._parse_lines(lines)
            
            if not parsed_lines:
                parsing_errors.append("No valid items found in receipt lines")
                logger.warning("No valid items found in receipt lines")
            
            # Extract special charges
            try:
                special_charges = self._extract_special_charges(cleaned_text)
            except Exception as e:
                special_charges = []
                parsing_errors.append(f"Error extracting special charges: {str(e)}")
                logger.warning(f"Error extracting special charges: {str(e)}")
            
            # Convert parsed lines to ExtractedItem objects
            items = self._convert_to_extracted_items(parsed_lines)
            
            # Add special charges to items
            items.extend(special_charges)
            
            # Validate and clean items
            items = self._clean_and_validate_items(items)
            
            if not items:
                error_msg = "No valid items could be extracted from the receipt"
                if parsing_errors:
                    error_msg += f": {'; '.join(parsing_errors)}"
                logger.warning(error_msg)
                raise ReceiptParsingError(error_msg)
            
            # Log success with item count
            logger.info(f"Successfully extracted {len(items)} items from receipt")
            return items
            
        except ReceiptParsingError:
            # Re-raise existing ReceiptParsingError
            raise
        except Exception as e:
            error_msg = f"Failed to parse receipt text: {str(e)}"
            if parsing_errors:
                error_msg += f" Additional errors: {'; '.join(parsing_errors)}"
            logger.error(error_msg)
            raise ReceiptParsingError(error_msg)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize receipt text.
        
        Args:
            text: Raw text from receipt
            
        Returns:
            Cleaned text
        """
        # Convert to lowercase for easier pattern matching
        text = text.lower()
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with parsing
        text = re.sub(r'[^\w\s\.\$\:]', '', text)
        
        # Remove dollar signs
        text = text.replace('$', '')
        
        # Split into lines and strip each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    def _parse_lines(self, lines: List[str]) -> List[ParsedLine]:
        """
        Parse each line of the receipt.
        
        Args:
            lines: List of text lines from receipt
            
        Returns:
            List of ParsedLine objects
        """
        parsed_lines = []
        
        for line in lines:
            parsed_line = ParsedLine(text=line)
            
            # Try each pattern until one matches
            for pattern in self.item_patterns:
                match = pattern.search(line)
                if match:
                    self._extract_item_from_match(match, parsed_line)
                    parsed_lines.append(parsed_line)
                    break
        
        return parsed_lines
    
    def _extract_item_from_match(self, match: Match, parsed_line: ParsedLine) -> None:
        """
        Extract item details from regex match.
        
        Args:
            match: Regex match object
            parsed_line: ParsedLine object to update
        """
        groups = match.groupdict()
        
        # Extract item name
        if 'name' in groups:
            parsed_line.item_name = groups['name'].strip()
        
        # Extract quantity if present
        if 'quantity' in groups:
            try:
                parsed_line.quantity = int(groups['quantity'])
            except ValueError:
                parsed_line.quantity = None
        
        # Extract unit price if present
        if 'unit_price' in groups:
            try:
                parsed_line.unit_price = float(groups['unit_price'])
            except ValueError:
                parsed_line.unit_price = None
        
        # Extract total price
        if 'price' in groups:
            try:
                parsed_line.total_price = float(groups['price'])
            except ValueError:
                parsed_line.total_price = None
        
        # Calculate confidence score based on completeness
        parsed_line.confidence_score = self._calculate_confidence_score(parsed_line)
    
    def _calculate_confidence_score(self, parsed_line: ParsedLine) -> float:
        """
        Calculate confidence score for a parsed line.
        
        Args:
            parsed_line: ParsedLine object
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0
        
        # Base score for having an item name
        if parsed_line.item_name:
            score += 0.3
        
        # Additional score for having a price
        if parsed_line.total_price is not None:
            score += 0.3
        
        # Additional score for having quantity or unit price
        if parsed_line.quantity is not None:
            score += 0.15
        
        if parsed_line.unit_price is not None:
            score += 0.15
        
        # Check if the item name is likely valid (not just numbers or symbols)
        if parsed_line.item_name and re.search(r'[a-zA-Z]{3,}', parsed_line.item_name):
            score += 0.1
        else:
            score -= 0.1
        
        # Check if the price is reasonable (between 0.01 and 1000.00)
        if parsed_line.total_price and 0.01 <= parsed_line.total_price <= 1000.00:
            score += 0.1
        else:
            score -= 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _extract_special_charges(self, text: str) -> List[ExtractedItem]:
        """
        Extract special charges like tip, service fee, and delivery fee.
        
        Args:
            text: Cleaned receipt text
            
        Returns:
            List of ExtractedItem objects for special charges
        """
        special_charges = []
        
        # Check for special charges using regex patterns
        for i, pattern in enumerate(self.special_charge_patterns):
            for match in pattern.finditer(text):
                if 'amount' in match.groupdict():
                    try:
                        amount = float(match.group('amount'))
                        
                        # Determine the type of special charge based on pattern index
                        if i == 0:
                            charge_type = "Tip"
                        elif i == 1:
                            charge_type = "Service Charge"
                        elif i == 2:
                            charge_type = "Delivery Fee"
                        else:
                            charge_type = self._determine_special_charge_type(match.group(0))
                        
                        special_charges.append(ExtractedItem(
                            name=charge_type,
                            total_price=amount,
                            confidence_score=0.9,  # High confidence for special charges
                            is_special_charge=True
                        ))
                    except ValueError:
                        continue
        
        return special_charges
    
    def _determine_special_charge_type(self, text: str) -> str:
        """
        Determine the type of special charge from text.
        
        Args:
            text: Text containing the special charge
            
        Returns:
            Type of special charge (Tip, Service Charge, or Delivery Fee)
        """
        text = text.lower()
        
        if any(keyword in text for keyword in self.SPECIAL_CHARGE_KEYWORDS['tip']):
            return "Tip"
        elif any(keyword in text for keyword in self.SPECIAL_CHARGE_KEYWORDS['service']):
            return "Service Charge"
        elif any(keyword in text for keyword in self.SPECIAL_CHARGE_KEYWORDS['delivery']):
            return "Delivery Fee"
        else:
            return "Other Charge"
    
    def _convert_to_extracted_items(self, parsed_lines: List[ParsedLine]) -> List[ExtractedItem]:
        """
        Convert ParsedLine objects to ExtractedItem objects.
        
        Args:
            parsed_lines: List of ParsedLine objects
            
        Returns:
            List of ExtractedItem objects
        """
        items = []
        
        for line in parsed_lines:
            if line.item_name and line.total_price is not None:
                items.append(ExtractedItem(
                    name=line.item_name.title(),  # Capitalize item name
                    total_price=line.total_price,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    confidence_score=line.confidence_score,
                    is_special_charge=line.is_special_charge
                ))
        
        return items
    
    def _clean_and_validate_items(self, items: List[ExtractedItem]) -> List[ExtractedItem]:
        """
        Clean and validate extracted items.
        
        Args:
            items: List of ExtractedItem objects
            
        Returns:
            Cleaned and validated list of ExtractedItem objects
        """
        valid_items = []
        
        for item in items:
            # Skip items with empty names
            if not item.name or not item.name.strip():
                continue
            
            # Skip items with zero or negative prices
            if item.total_price <= 0:
                continue
            
            # Clean up item name
            item.name = self._clean_item_name(item.name)
            
            valid_items.append(item)
        
        return valid_items
    
    def _clean_item_name(self, name: str) -> str:
        """
        Clean up item name.
        
        Args:
            name: Raw item name
            
        Returns:
            Cleaned item name
        """
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name)
        
        # Remove common prefixes like item numbers
        name = re.sub(r'^\d+[\.\)\-]\s*', '', name)
        
        # Capitalize first letter of each word
        name = name.title()
        
        return name
    
    def identify_special_charges(self, text: str) -> List[ExtractedItem]:
        """
        Identify and extract special charges from receipt text.
        
        Args:
            text: Receipt text
            
        Returns:
            List of ExtractedItem objects for special charges
        """
        return self._extract_special_charges(self._clean_text(text))