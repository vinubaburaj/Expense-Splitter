from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class Person:
    """
    Class to track what a person owes and which items they're included in.
    """
    name: str
    total_owed: float = 0.0
    items: Set[str] = field(default_factory=set)

    def add_expense(self, item_name: str, amount: float) -> None:
        """
        Add an expense to this person's account.

        Args:
            item_name: The name of the item
            amount: The amount this person owes for the item
        """
        self.total_owed += amount
        self.items.add(item_name)
