from typing import Dict, List, Union, Optional

from models.person import Person
from models.expense import Expense
from models.extracted_item import ExtractedItem
from models.receipt_data import ReceiptData


class ExpenseCalculator:
    """
    Calculates how much each person owes based on expense data.
    Supports both legacy Expense objects and new ExtractedItem objects.
    """

    @staticmethod
    def calculate_debts(expenses: List[Union[Expense, ExtractedItem]]) -> Dict[str, Person]:
        """
        Calculate how much each person owes based on the expenses.

        Args:
            expenses: List of Expense or ExtractedItem objects

        Returns:
            Dictionary mapping person names to Person objects with their debts
        """
        people = {}

        for expense in expenses:
            # Handle both Expense and ExtractedItem objects
            if isinstance(expense, Expense):
                price_per_person = expense.price_per_person
                item_name = expense.item_name
                people_included = expense.people_included
            else:  # ExtractedItem
                price_per_person = expense.price_per_person
                item_name = expense.name
                people_included = expense.assigned_people

            for person_name in people_included:
                if person_name not in people:
                    people[person_name] = Person(name=person_name)

                # Add this expense to the person's account
                people[person_name].add_expense(item_name, price_per_person)

        return people
    
    @staticmethod
    def calculate_from_receipt(receipt_data: ReceiptData) -> Dict[str, Person]:
        """
        Calculate how much each person owes based on a ReceiptData object.
        
        Args:
            receipt_data: ReceiptData object containing items and assignments
            
        Returns:
            Dictionary mapping person names to Person objects with their debts
        """
        return ExpenseCalculator.calculate_debts(receipt_data.items)
    
    @staticmethod
    def validate_receipt_totals(receipt_data: ReceiptData) -> Dict[str, float]:
        """
        Validate that the sum of all person totals equals the receipt total.
        
        Args:
            receipt_data: ReceiptData object to validate
            
        Returns:
            Dictionary with validation results:
            {
                'receipt_total': float,
                'calculated_total': float,
                'person_totals_sum': float,
                'is_valid': bool,
                'difference': float
            }
        """
        receipt_total = receipt_data.total_amount
        calculated_total = receipt_data.calculated_total
        
        # Calculate sum of all person totals
        people = ExpenseCalculator.calculate_from_receipt(receipt_data)
        person_totals_sum = sum(person.total_owed for person in people.values())
        
        # Check if the totals match (within a small tolerance for floating point errors)
        is_valid = abs(receipt_total - person_totals_sum) < 0.01
        
        return {
            'receipt_total': receipt_total,
            'calculated_total': calculated_total,
            'person_totals_sum': person_totals_sum,
            'is_valid': is_valid,
            'difference': receipt_total - person_totals_sum
        }