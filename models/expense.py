from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Expense:
    """
    Represents an expense item from the CSV file or extracted from PDF.
    Enhanced to support quantities and confidence scores for PDF processing.
    """
    item_name: str
    total_price: float
    people_included: List[str]
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    confidence_score: Optional[float] = None
    is_special_charge: bool = False

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if self.total_price < 0:
            raise ValueError("Total price cannot be negative")
        
        if self.confidence_score is not None and (self.confidence_score < 0 or self.confidence_score > 1):
            raise ValueError("Confidence score must be between 0 and 1")
        
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.unit_price is not None and self.unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        
        # Calculate unit price if quantity is provided but unit price is not
        if self.quantity and self.unit_price is None and self.quantity > 0:
            self.unit_price = self.total_price / self.quantity

    @property
    def price_per_person(self) -> float:
        """Calculate price per person for this expense."""
        if not self.people_included:
            return 0.0
        return self.total_price / len(self.people_included)

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the extraction confidence is above the threshold."""
        if self.confidence_score is None:
            return True  # Assume high confidence for manually entered items
        return self.confidence_score >= threshold