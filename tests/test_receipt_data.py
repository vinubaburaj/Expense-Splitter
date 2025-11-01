import unittest
from models.receipt_data import ReceiptData
from models.extracted_item import ExtractedItem


class TestReceiptData(unittest.TestCase):
    """Test cases for ReceiptData dataclass."""

    def setUp(self):
        """Set up test fixtures."""
        self.item1 = ExtractedItem(
            name="Coffee",
            total_price=4.50,
            confidence_score=0.9
        )
        self.item2 = ExtractedItem(
            name="Sandwich",
            total_price=8.00,
            confidence_score=0.8
        )
        self.tip = ExtractedItem(
            name="Tip",
            total_price=2.50,
            confidence_score=0.95,
            is_special_charge=True
        )

    def test_basic_creation(self):
        """Test basic ReceiptData creation."""
        receipt = ReceiptData()
        
        self.assertEqual(receipt.items, [])
        self.assertEqual(receipt.participants, [])
        self.assertEqual(receipt.total_amount, 0.0)
        self.assertEqual(receipt.extraction_confidence, 0.0)
        self.assertIsNone(receipt.filename)
        self.assertEqual(receipt.processing_errors, [])

    def test_creation_with_items(self):
        """Test ReceiptData creation with items."""
        receipt = ReceiptData(
            items=[self.item1, self.item2],
            participants=["Alice", "Bob"],
            filename="receipt.pdf"
        )
        
        self.assertEqual(len(receipt.items), 2)
        self.assertEqual(receipt.participants, ["Alice", "Bob"])
        self.assertEqual(receipt.filename, "receipt.pdf")
        # Total should be auto-calculated
        self.assertEqual(receipt.total_amount, 12.50)
        # Confidence should be auto-calculated
        self.assertAlmostEqual(receipt.extraction_confidence, 0.85, places=2)

    def test_negative_total_validation(self):
        """Test that negative total amounts raise ValueError."""
        with self.assertRaises(ValueError):
            ReceiptData(total_amount=-10.0)

    def test_invalid_confidence_validation(self):
        """Test that invalid confidence scores raise ValueError."""
        with self.assertRaises(ValueError):
            ReceiptData(extraction_confidence=1.5)
        
        with self.assertRaises(ValueError):
            ReceiptData(extraction_confidence=-0.1)

    def test_calculated_total_property(self):
        """Test calculated total property."""
        receipt = ReceiptData(items=[self.item1, self.item2, self.tip])
        
        self.assertEqual(receipt.calculated_total, 15.0)

    def test_unassigned_items_property(self):
        """Test unassigned items property."""
        self.item1.add_person("Alice")
        # item2 and tip remain unassigned
        
        receipt = ReceiptData(items=[self.item1, self.item2, self.tip])
        unassigned = receipt.unassigned_items
        
        self.assertEqual(len(unassigned), 2)
        self.assertIn(self.item2, unassigned)
        self.assertIn(self.tip, unassigned)

    def test_special_charges_property(self):
        """Test special charges property."""
        receipt = ReceiptData(items=[self.item1, self.item2, self.tip])
        special_charges = receipt.special_charges
        
        self.assertEqual(len(special_charges), 1)
        self.assertIn(self.tip, special_charges)

    def test_regular_items_property(self):
        """Test regular items property."""
        receipt = ReceiptData(items=[self.item1, self.item2, self.tip])
        regular_items = receipt.regular_items
        
        self.assertEqual(len(regular_items), 2)
        self.assertIn(self.item1, regular_items)
        self.assertIn(self.item2, regular_items)

    def test_add_item(self):
        """Test adding items to receipt."""
        receipt = ReceiptData()
        receipt.add_item(self.item1)
        
        self.assertEqual(len(receipt.items), 1)
        self.assertEqual(receipt.total_amount, 4.50)
        self.assertEqual(receipt.extraction_confidence, 0.9)

    def test_remove_item(self):
        """Test removing items from receipt."""
        receipt = ReceiptData(items=[self.item1, self.item2])
        
        # Remove existing item
        result = receipt.remove_item(self.item1.id)
        self.assertTrue(result)
        self.assertEqual(len(receipt.items), 1)
        self.assertEqual(receipt.total_amount, 8.0)
        
        # Try to remove non-existent item
        result = receipt.remove_item("non-existent-id")
        self.assertFalse(result)

    def test_get_item_by_id(self):
        """Test getting item by ID."""
        receipt = ReceiptData(items=[self.item1, self.item2])
        
        found_item = receipt.get_item_by_id(self.item1.id)
        self.assertEqual(found_item, self.item1)
        
        not_found = receipt.get_item_by_id("non-existent-id")
        self.assertIsNone(not_found)

    def test_add_participant(self):
        """Test adding participants."""
        receipt = ReceiptData()
        receipt.add_participant("Alice")
        receipt.add_participant("Bob")
        
        self.assertEqual(receipt.participants, ["Alice", "Bob"])
        
        # Adding duplicate should not create duplicate
        receipt.add_participant("Alice")
        self.assertEqual(receipt.participants, ["Alice", "Bob"])

    def test_remove_participant(self):
        """Test removing participants and their assignments."""
        self.item1.add_person("Alice")
        self.item1.add_person("Bob")
        self.item2.add_person("Alice")
        
        receipt = ReceiptData(
            items=[self.item1, self.item2],
            participants=["Alice", "Bob", "Charlie"]
        )
        
        receipt.remove_participant("Alice")
        
        self.assertNotIn("Alice", receipt.participants)
        self.assertNotIn("Alice", self.item1.assigned_people)
        self.assertNotIn("Alice", self.item2.assigned_people)
        self.assertIn("Bob", self.item1.assigned_people)

    def test_get_person_total(self):
        """Test calculating person's total."""
        self.item1.add_person("Alice")
        self.item1.add_person("Bob")  # $4.50 / 2 = $2.25 each
        self.item2.add_person("Alice")  # $8.00 for Alice alone
        
        receipt = ReceiptData(items=[self.item1, self.item2])
        
        alice_total = receipt.get_person_total("Alice")
        bob_total = receipt.get_person_total("Bob")
        
        self.assertEqual(alice_total, 10.25)  # 2.25 + 8.00
        self.assertEqual(bob_total, 2.25)

    def test_get_person_items(self):
        """Test getting items assigned to a person."""
        self.item1.add_person("Alice")
        self.item2.add_person("Alice")
        self.tip.add_person("Bob")
        
        receipt = ReceiptData(items=[self.item1, self.item2, self.tip])
        
        alice_items = receipt.get_person_items("Alice")
        bob_items = receipt.get_person_items("Bob")
        
        self.assertEqual(len(alice_items), 2)
        self.assertIn(self.item1, alice_items)
        self.assertIn(self.item2, alice_items)
        
        self.assertEqual(len(bob_items), 1)
        self.assertIn(self.tip, bob_items)

    def test_validate_assignments_success(self):
        """Test successful assignment validation."""
        self.item1.add_person("Alice")
        self.item2.add_person("Bob")
        
        receipt = ReceiptData(
            items=[self.item1, self.item2],
            participants=["Alice", "Bob"],
            total_amount=12.50
        )
        
        errors = receipt.validate_assignments()
        self.assertEqual(errors, [])

    def test_validate_assignments_no_participants(self):
        """Test validation with no participants."""
        receipt = ReceiptData(items=[self.item1])
        
        errors = receipt.validate_assignments()
        self.assertIn("No participants defined", errors)

    def test_validate_assignments_unassigned_items(self):
        """Test validation with unassigned items."""
        receipt = ReceiptData(
            items=[self.item1, self.item2],
            participants=["Alice", "Bob"]
        )
        
        errors = receipt.validate_assignments()
        self.assertTrue(any("items have no people assigned" in error for error in errors))

    def test_validate_assignments_total_mismatch(self):
        """Test validation with total mismatch."""
        self.item1.add_person("Alice")
        
        receipt = ReceiptData(
            items=[self.item1],
            participants=["Alice"],
            total_amount=10.00  # Different from item1's 4.50
        )
        
        errors = receipt.validate_assignments()
        self.assertTrue(any("doesn't match receipt total" in error for error in errors))


if __name__ == '__main__':
    unittest.main()