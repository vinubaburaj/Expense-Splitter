import unittest
from models.extracted_item import ExtractedItem


class TestExtractedItem(unittest.TestCase):
    """Test cases for ExtractedItem dataclass."""

    def test_basic_creation(self):
        """Test basic ExtractedItem creation."""
        item = ExtractedItem(
            name="Coffee",
            total_price=4.50,
            confidence_score=0.9
        )
        
        self.assertEqual(item.name, "Coffee")
        self.assertEqual(item.total_price, 4.50)
        self.assertEqual(item.confidence_score, 0.9)
        self.assertIsNone(item.quantity)
        self.assertIsNone(item.unit_price)
        self.assertFalse(item.is_special_charge)
        self.assertEqual(item.assigned_people, [])
        self.assertIsNotNone(item.id)

    def test_creation_with_quantity(self):
        """Test ExtractedItem creation with quantity."""
        item = ExtractedItem(
            name="Apples",
            total_price=6.00,
            confidence_score=0.8,
            quantity=3
        )
        
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.unit_price, 2.00)  # Auto-calculated

    def test_creation_with_unit_price_and_quantity(self):
        """Test ExtractedItem creation with both unit price and quantity."""
        item = ExtractedItem(
            name="Bananas",
            total_price=0.0,  # Will be calculated
            confidence_score=0.7,
            quantity=2,
            unit_price=1.50
        )
        
        self.assertEqual(item.total_price, 3.00)  # Auto-calculated

    def test_special_charge_creation(self):
        """Test ExtractedItem creation for special charges."""
        item = ExtractedItem(
            name="Tip",
            total_price=5.00,
            confidence_score=0.95,
            is_special_charge=True
        )
        
        self.assertTrue(item.is_special_charge)

    def test_negative_price_validation(self):
        """Test that negative prices raise ValueError."""
        with self.assertRaises(ValueError):
            ExtractedItem(
                name="Invalid",
                total_price=-1.00,
                confidence_score=0.5
            )

    def test_invalid_confidence_score_validation(self):
        """Test that invalid confidence scores raise ValueError."""
        with self.assertRaises(ValueError):
            ExtractedItem(
                name="Invalid",
                total_price=5.00,
                confidence_score=1.5
            )
        
        with self.assertRaises(ValueError):
            ExtractedItem(
                name="Invalid",
                total_price=5.00,
                confidence_score=-0.1
            )

    def test_invalid_quantity_validation(self):
        """Test that invalid quantities raise ValueError."""
        with self.assertRaises(ValueError):
            ExtractedItem(
                name="Invalid",
                total_price=5.00,
                confidence_score=0.8,
                quantity=0
            )

    def test_negative_unit_price_validation(self):
        """Test that negative unit prices raise ValueError."""
        with self.assertRaises(ValueError):
            ExtractedItem(
                name="Invalid",
                total_price=5.00,
                confidence_score=0.8,
                unit_price=-1.00
            )

    def test_price_per_person_calculation(self):
        """Test price per person calculation."""
        item = ExtractedItem(
            name="Pizza",
            total_price=20.00,
            confidence_score=0.9
        )
        
        # No people assigned
        self.assertEqual(item.price_per_person, 0.0)
        
        # Add people
        item.add_person("Alice")
        item.add_person("Bob")
        self.assertEqual(item.price_per_person, 10.0)

    def test_add_person(self):
        """Test adding people to item assignment."""
        item = ExtractedItem(
            name="Lunch",
            total_price=15.00,
            confidence_score=0.8
        )
        
        item.add_person("Alice")
        self.assertIn("Alice", item.assigned_people)
        
        # Adding same person again should not duplicate
        item.add_person("Alice")
        self.assertEqual(item.assigned_people.count("Alice"), 1)

    def test_remove_person(self):
        """Test removing people from item assignment."""
        item = ExtractedItem(
            name="Dinner",
            total_price=25.00,
            confidence_score=0.9,
            assigned_people=["Alice", "Bob", "Charlie"]
        )
        
        item.remove_person("Bob")
        self.assertNotIn("Bob", item.assigned_people)
        self.assertIn("Alice", item.assigned_people)
        self.assertIn("Charlie", item.assigned_people)
        
        # Removing non-existent person should not raise error
        item.remove_person("David")

    def test_is_high_confidence(self):
        """Test confidence threshold checking."""
        high_confidence_item = ExtractedItem(
            name="Clear Item",
            total_price=10.00,
            confidence_score=0.9
        )
        
        low_confidence_item = ExtractedItem(
            name="Unclear Item",
            total_price=10.00,
            confidence_score=0.6
        )
        
        self.assertTrue(high_confidence_item.is_high_confidence())
        self.assertFalse(low_confidence_item.is_high_confidence())
        
        # Test custom threshold
        self.assertTrue(low_confidence_item.is_high_confidence(threshold=0.5))


if __name__ == '__main__':
    unittest.main()