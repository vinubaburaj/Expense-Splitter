from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .extracted_item import ExtractedItem


@dataclass
class ReceiptData:
    """
    Manages complete receipt information including extracted items,
    participants, and overall processing metadata.
    """
    items: List[ExtractedItem] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    total_amount: float = 0.0
    extraction_confidence: float = 0.0
    filename: Optional[str] = None
    processing_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate and calculate derived values after initialization."""
        if self.total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        
        if self.extraction_confidence < 0 or self.extraction_confidence > 1:
            raise ValueError("Extraction confidence must be between 0 and 1")
        
        # Calculate total from items if not provided
        if not self.total_amount and self.items:
            self.total_amount = sum(item.total_price for item in self.items)
        
        # Calculate average extraction confidence if not provided
        if not self.extraction_confidence and self.items:
            self.extraction_confidence = sum(item.confidence_score for item in self.items) / len(self.items)

    @property
    def calculated_total(self) -> float:
        """Calculate total from all items."""
        return sum(item.total_price for item in self.items)

    @property
    def unassigned_items(self) -> List[ExtractedItem]:
        """Get items that have no people assigned."""
        return [item for item in self.items if not item.assigned_people]

    @property
    def special_charges(self) -> List[ExtractedItem]:
        """Get items that are special charges (tip, service, delivery)."""
        return [item for item in self.items if item.is_special_charge]

    @property
    def regular_items(self) -> List[ExtractedItem]:
        """Get items that are not special charges."""
        return [item for item in self.items if not item.is_special_charge]

    def add_item(self, item: ExtractedItem) -> None:
        """Add an item to the receipt."""
        self.items.append(item)
        self._recalculate_totals()

    def remove_item(self, item_id: str) -> bool:
        """Remove an item by ID. Returns True if item was found and removed."""
        original_length = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        if len(self.items) < original_length:
            self._recalculate_totals()
            return True
        return False

    def get_item_by_id(self, item_id: str) -> Optional[ExtractedItem]:
        """Get an item by its ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def add_participant(self, name: str) -> None:
        """Add a participant to the receipt."""
        if name not in self.participants:
            self.participants.append(name)

    def remove_participant(self, name: str) -> None:
        """Remove a participant and their assignments from all items."""
        if name in self.participants:
            self.participants.remove(name)
            # Remove from all item assignments
            for item in self.items:
                item.remove_person(name)

    def get_person_total(self, person_name: str) -> float:
        """Calculate total amount owed by a specific person."""
        total = 0.0
        for item in self.items:
            if person_name in item.assigned_people:
                total += item.price_per_person
        return total

    def get_person_items(self, person_name: str) -> List[ExtractedItem]:
        """Get all items assigned to a specific person."""
        return [item for item in self.items if person_name in item.assigned_people]

    def validate_assignments(self) -> List[str]:
        """Validate that all items have assignments and return any errors."""
        errors = []
        
        if not self.participants:
            errors.append("No participants defined")
        
        unassigned = self.unassigned_items
        if unassigned:
            errors.append(f"{len(unassigned)} items have no people assigned")
        
        # Check if calculated total matches expected total (within small tolerance)
        calculated = self.calculated_total
        if abs(calculated - self.total_amount) > 0.01:
            errors.append(f"Item total ({calculated:.2f}) doesn't match receipt total ({self.total_amount:.2f})")
        
        return errors

    def _recalculate_totals(self) -> None:
        """Recalculate total amount and extraction confidence."""
        if self.items:
            self.total_amount = self.calculated_total
            self.extraction_confidence = sum(item.confidence_score for item in self.items) / len(self.items)
        else:
            self.total_amount = 0.0
            self.extraction_confidence = 0.0