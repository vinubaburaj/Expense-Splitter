import unittest
from models.expense import Expense


class TestExpense(unittest.TestCase):
    """Test cases for enhanced Expense dataclass."""

    def test_basic_creation(self):
        """Test basic Expense creation (backward compatibility)."""
        expense = Expense(
            item_name="Coffee",
            total_price=4.50,
            people_included=["Alice", "Bob"]
        )
        
        self.assertEqual(expense.item_name, "Coffee")
        self.assertEqual(expense.total_price, 4.50)
        self.assertEqual(expense.people_included, ["Alice", "Bob"])
        self.assertIsNone(expense.quantity)
        self.assertIsNone(expense.unit_price)
        self.assertIsNone(expense.confidence_score)
        self.assertFalse(expense.is_special_charge)

    def test_enhanced_creation(self):
        """Test Expense creation with new PDF processing fields."""
        expense = Expense(
            item_name="Pizza",
            total_price=20.00,
            people_included=["Alice", "Bob", "Charlie"],
            quantity=2,
            unit_price=10.00,
            confidence_score=0.9,
            is_special_charge=False
        )
        
        self.assertEqual(expense.quantity, 2)
        self.assertEqual(expense.unit_price, 10.00)
        self.assertEqual(expense.confidence_score, 0.9)
        self.assertFalse(expense.is_special_charge)

    def test_special_charge_creation(self):
        """Test Expense creation for special charges."""
        expense = Expense(
            item_name="Tip",
            total_price=5.00,
            people_included=["Alice", "Bob"],
            is_special_charge=True,
            confidence_score=0.95
        )
        
        self.assertTrue(expense.is_special_charge)

    def test_unit_price_calculation(self):
        """Test automatic unit price calculation."""
        expense = Expense(
            item_name="Apples",
            total_price=6.00,
            people_included=["Alice"],
            quantity=3
        )
        
        self.assertEqual(expense.unit_price, 2.00)

    def test_price_per_person_calculation(self):
        """Test price per person calculation."""
        expense = Expense(
            item_name="Lunch",
            total_price=30.00,
            people_included=["Alice", "Bob", "Charlie"]
        )
        
        self.assertEqual(expense.price_per_person, 10.00)

    def test_price_per_person_empty_list(self):
        """Test price per person with empty people list."""
        expense = Expense(
            item_name="Orphaned Item",
            total_price=15.00,
            people_included=[]
        )
        
        self.assertEqual(expense.price_per_person, 0.0)

    def test_negative_price_validation(self):
        """Test that negative prices raise ValueError."""
        with self.assertRaises(ValueError):
            Expense(
                item_name="Invalid",
                total_price=-5.00,
                people_included=["Alice"]
            )

    def test_invalid_confidence_score_validation(self):
        """Test that invalid confidence scores raise ValueError."""
        with self.assertRaises(ValueError):
            Expense(
                item_name="Invalid",
                total_price=10.00,
                people_included=["Alice"],
                confidence_score=1.5
            )
        
        with self.assertRaises(ValueError):
            Expense(
                item_name="Invalid",
                total_price=10.00,
                people_included=["Alice"],
                confidence_score=-0.1
            )

    def test_invalid_quantity_validation(self):
        """Test that invalid quantities raise ValueError."""
        with self.assertRaises(ValueError):
            Expense(
                item_name="Invalid",
                total_price=10.00,
                people_included=["Alice"],
                quantity=0
            )

    def test_negative_unit_price_validation(self):
        """Test that negative unit prices raise ValueError."""
        with self.assertRaises(ValueError):
            Expense(
                item_name="Invalid",
                total_price=10.00,
                people_included=["Alice"],
                unit_price=-2.00
            )

    def test_is_high_confidence(self):
        """Test confidence threshold checking."""
        high_confidence_expense = Expense(
            item_name="Clear Item",
            total_price=10.00,
            people_included=["Alice"],
            confidence_score=0.9
        )
        
        low_confidence_expense = Expense(
            item_name="Unclear Item",
            total_price=10.00,
            people_included=["Alice"],
            confidence_score=0.6
        )
        
        manual_expense = Expense(
            item_name="Manual Item",
            total_price=10.00,
            people_included=["Alice"]
        )
        
        self.assertTrue(high_confidence_expense.is_high_confidence())
        self.assertFalse(low_confidence_expense.is_high_confidence())
        self.assertTrue(manual_expense.is_high_confidence())  # No confidence score = manual = high confidence
        
        # Test custom threshold
        self.assertTrue(low_confidence_expense.is_high_confidence(threshold=0.5))


if __name__ == '__main__':
    unittest.main()