from dataclasses import dataclass, field
from typing import Optional, List
import uuid


@dataclass
class ExtractedItem:
    """
    Represents an item extracted from a PDF receipt with OCR/ML processing.
    Includes confidence scoring and support for special charges like tips.
    """
    name: str
    total_price: float
    confidence_score: float
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    is_special_charge: bool = False
    assigned_people: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if self.total_price < 0:
            raise ValueError("Total price cannot be negative")
        
        if self.confidence_score < 0 or self.confidence_score > 1:
            raise ValueError("Confidence score must be between 0 and 1")
        
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.unit_price is not None and self.unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        
        # Calculate unit price if quantity is provided but unit price is not
        if self.quantity and self.unit_price is None and self.quantity > 0:
            self.unit_price = self.total_price / self.quantity
        
        # Calculate total price if quantity and unit price are provided
        if self.quantity and self.unit_price and not self.total_price:
            self.total_price = self.quantity * self.unit_price

    @property
    def price_per_person(self) -> float:
        """Calculate price per person for this item."""
        if not self.assigned_people:
            return 0.0
        return self.total_price / len(self.assigned_people)

    def add_person(self, person_name: str) -> None:
        """Add a person to this item's assignment."""
        if person_name not in self.assigned_people:
            self.assigned_people.append(person_name)

    def remove_person(self, person_name: str) -> None:
        """Remove a person from this item's assignment."""
        if person_name in self.assigned_people:
            self.assigned_people.remove(person_name)

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the extraction confidence is above the threshold."""
        return self.confidence_score >= threshold