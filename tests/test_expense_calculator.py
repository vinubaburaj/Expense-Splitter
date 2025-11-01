import unittest
from models.expense import Expense
from models.extracted_item import ExtractedItem
from models.receipt_data import ReceiptData
from services.expense_calculator import ExpenseCalculator


class TestExpenseCalculator(unittest.TestCase):
    def test_calculate_debts_with_expense_objects(self):
        """Test calculating debts with legacy Expense objects."""
        expenses = [
            Expense(item_name="Pizza", total_price=20.0, people_included=["Alice", "Bob"]),
            Expense(item_name="Salad", total_price=10.0, people_included=["Alice"]),
            Expense(item_name="Drinks", total_price=15.0, people_included=["Alice", "Bob", "Charlie"])
        ]
        
        result = ExpenseCalculator.calculate_debts(expenses)
        
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result["Alice"].total_owed, 10.0 + 10.0 + 5.0)
        self.assertAlmostEqual(result["Bob"].total_owed, 10.0 + 5.0)
        self.assertAlmostEqual(result["Charlie"].total_owed, 5.0)
        
        # Check items are correctly assigned
        self.assertEqual(result["Alice"].items, {"Pizza", "Salad", "Drinks"})
        self.assertEqual(result["Bob"].items, {"Pizza", "Drinks"})
        self.assertEqual(result["Charlie"].items, {"Drinks"})

    def test_calculate_debts_with_extracted_items(self):
        """Test calculating debts with new ExtractedItem objects."""
        items = [
            ExtractedItem(name="Pizza", total_price=20.0, confidence_score=0.9, assigned_people=["Alice", "Bob"]),
            ExtractedItem(name="Salad", total_price=10.0, confidence_score=0.8, assigned_people=["Alice"]),
            ExtractedItem(name="Drinks", total_price=15.0, confidence_score=0.95, assigned_people=["Alice", "Bob", "Charlie"])
        ]
        
        result = ExpenseCalculator.calculate_debts(items)
        
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result["Alice"].total_owed, 10.0 + 10.0 + 5.0)
        self.assertAlmostEqual(result["Bob"].total_owed, 10.0 + 5.0)
        self.assertAlmostEqual(result["Charlie"].total_owed, 5.0)
        
        # Check items are correctly assigned
        self.assertEqual(result["Alice"].items, {"Pizza", "Salad", "Drinks"})
        self.assertEqual(result["Bob"].items, {"Pizza", "Drinks"})
        self.assertEqual(result["Charlie"].items, {"Drinks"})

    def test_calculate_debts_with_mixed_objects(self):
        """Test calculating debts with a mix of Expense and ExtractedItem objects."""
        expenses = [
            Expense(item_name="Pizza", total_price=20.0, people_included=["Alice", "Bob"]),
            ExtractedItem(name="Salad", total_price=10.0, confidence_score=0.8, assigned_people=["Alice"]),
            ExtractedItem(name="Drinks", total_price=15.0, confidence_score=0.95, assigned_people=["Alice", "Bob", "Charlie"])
        ]
        
        result = ExpenseCalculator.calculate_debts(expenses)
        
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result["Alice"].total_owed, 10.0 + 10.0 + 5.0)
        self.assertAlmostEqual(result["Bob"].total_owed, 10.0 + 5.0)
        self.assertAlmostEqual(result["Charlie"].total_owed, 5.0)

    def test_calculate_from_receipt(self):
        """Test calculating debts from a ReceiptData object."""
        items = [
            ExtractedItem(name="Pizza", total_price=20.0, confidence_score=0.9, assigned_people=["Alice", "Bob"]),
            ExtractedItem(name="Salad", total_price=10.0, confidence_score=0.8, assigned_people=["Alice"]),
            ExtractedItem(name="Drinks", total_price=15.0, confidence_score=0.95, assigned_people=["Alice", "Bob", "Charlie"])
        ]
        
        receipt = ReceiptData(
            items=items,
            participants=["Alice", "Bob", "Charlie"],
            total_amount=45.0
        )
        
        result = ExpenseCalculator.calculate_from_receipt(receipt)
        
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result["Alice"].total_owed, 25.0)
        self.assertAlmostEqual(result["Bob"].total_owed, 15.0)
        self.assertAlmostEqual(result["Charlie"].total_owed, 5.0)

    def test_quantity_based_calculations(self):
        """Test calculations with quantity and unit price."""
        items = [
            ExtractedItem(
                name="Pizza", 
                quantity=2, 
                unit_price=10.0, 
                total_price=20.0, 
                confidence_score=0.9, 
                assigned_people=["Alice", "Bob"]
            ),
            ExtractedItem(
                name="Drinks", 
                quantity=3, 
                unit_price=5.0, 
                total_price=15.0, 
                confidence_score=0.95, 
                assigned_people=["Alice", "Bob", "Charlie"]
            )
        ]
        
        receipt = ReceiptData(
            items=items,
            participants=["Alice", "Bob", "Charlie"],
            total_amount=35.0
        )
        
        result = ExpenseCalculator.calculate_from_receipt(receipt)
        
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result["Alice"].total_owed, 10.0 + 5.0)
        self.assertAlmostEqual(result["Bob"].total_owed, 10.0 + 5.0)
        self.assertAlmostEqual(result["Charlie"].total_owed, 5.0)

    def test_validate_receipt_totals_valid(self):
        """Test validation with valid totals."""
        items = [
            ExtractedItem(name="Pizza", total_price=20.0, confidence_score=0.9, assigned_people=["Alice", "Bob"]),
            ExtractedItem(name="Salad", total_price=10.0, confidence_score=0.8, assigned_people=["Alice"]),
            ExtractedItem(name="Drinks", total_price=15.0, confidence_score=0.95, assigned_people=["Alice", "Bob", "Charlie"])
        ]
        
        receipt = ReceiptData(
            items=items,
            participants=["Alice", "Bob", "Charlie"],
            total_amount=45.0
        )
        
        validation = ExpenseCalculator.validate_receipt_totals(receipt)
        
        self.assertTrue(validation["is_valid"])
        self.assertAlmostEqual(validation["receipt_total"], 45.0)
        self.assertAlmostEqual(validation["calculated_total"], 45.0)
        self.assertAlmostEqual(validation["person_totals_sum"], 45.0)
        self.assertAlmostEqual(validation["difference"], 0.0)

    def test_validate_receipt_totals_invalid(self):
        """Test validation with invalid totals."""
        items = [
            ExtractedItem(name="Pizza", total_price=20.0, confidence_score=0.9, assigned_people=["Alice", "Bob"]),
            ExtractedItem(name="Salad", total_price=10.0, confidence_score=0.8, assigned_people=["Alice"]),
            # This item has no people assigned
            ExtractedItem(name="Drinks", total_price=15.0, confidence_score=0.95, assigned_people=[])
        ]
        
        receipt = ReceiptData(
            items=items,
            participants=["Alice", "Bob", "Charlie"],
            total_amount=45.0
        )
        
        validation = ExpenseCalculator.validate_receipt_totals(receipt)
        
        self.assertFalse(validation["is_valid"])
        self.assertAlmostEqual(validation["receipt_total"], 45.0)
        self.assertAlmostEqual(validation["calculated_total"], 45.0)
        self.assertAlmostEqual(validation["person_totals_sum"], 30.0)
        self.assertAlmostEqual(validation["difference"], 15.0)

    def test_special_charges(self):
        """Test calculations with special charges like tips and service fees."""
        items = [
            ExtractedItem(name="Pizza", total_price=20.0, confidence_score=0.9, assigned_people=["Alice", "Bob"]),
            ExtractedItem(name="Tip", total_price=5.0, confidence_score=1.0, is_special_charge=True, 
                         assigned_people=["Alice", "Bob", "Charlie"]),
            ExtractedItem(name="Service Fee", total_price=3.0, confidence_score=1.0, is_special_charge=True,
                         assigned_people=["Alice", "Bob", "Charlie"])
        ]
        
        receipt = ReceiptData(
            items=items,
            participants=["Alice", "Bob", "Charlie"],
            total_amount=28.0
        )
        
        result = ExpenseCalculator.calculate_from_receipt(receipt)
        
        self.assertEqual(len(result), 3)
        # Alice and Bob each pay $10 for pizza + $1.67 for tip + $1 for service fee
        self.assertAlmostEqual(result["Alice"].total_owed, 10.0 + (5.0/3) + (3.0/3), places=2)
        self.assertAlmostEqual(result["Bob"].total_owed, 10.0 + (5.0/3) + (3.0/3), places=2)
        # Charlie only pays for tip and service fee
        self.assertAlmostEqual(result["Charlie"].total_owed, (5.0/3) + (3.0/3), places=2)


if __name__ == "__main__":
    unittest.main()