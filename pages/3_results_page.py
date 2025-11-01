"""
Results Page - Final step in the PDF Receipt Expense Splitter workflow

This page allows users to:
1. View the final expense breakdown for each participant
2. See itemized lists of what each person owes
3. Verify that the total matches the receipt amount
"""
import streamlit as st
import logging
from typing import Dict, List, Tuple
from utils.session_manager import SessionManager
from utils.validation import Validator
from services.expense_calculator import ExpenseCalculator
from models.expense import Expense
from models.extracted_item import ExtractedItem
from models.person import Person

# Set up logging
logger = logging.getLogger(__name__)

# Initialize session state
SessionManager.initialize_session()

def convert_extracted_items_to_expenses(items: List[ExtractedItem], assignments: Dict[str, List[str]]) -> List[Expense]:
    """
    Convert ExtractedItem objects to Expense objects for calculation.
    
    Args:
        items: List of ExtractedItem objects
        assignments: Dictionary mapping item IDs to lists of assigned person names
        
    Returns:
        List of Expense objects
    """
    expenses = []
    
    for item in items:
        # Get the people assigned to this item
        people_included = assignments.get(item.id, [])
        
        # Skip items with no people assigned
        if not people_included:
            continue
        
        # Create an Expense object
        expense = Expense(
            item_name=item.name,
            total_price=item.total_price,
            people_included=people_included,
            quantity=item.quantity,
            unit_price=item.unit_price,
            confidence_score=item.confidence_score,
            is_special_charge=item.is_special_charge
        )
        
        expenses.append(expense)
    
    return expenses

def calculate_results() -> Tuple[Dict[str, Person], float, float]:
    """
    Calculate the expense breakdown for each person.
    
    Returns:
        Tuple containing:
        - Dictionary mapping person names to Person objects
        - Total receipt amount
        - Sum of all individual shares
    """
    # Get extracted items and assignments
    items = SessionManager.get_extracted_items()
    assignments = SessionManager.get_all_assignments()
    
    # Convert to expenses
    expenses = convert_extracted_items_to_expenses(items, assignments)
    
    # Calculate debts
    people = ExpenseCalculator.calculate_debts(expenses)
    
    # Calculate total receipt amount
    total_receipt_amount = sum(item.total_price for item in items)
    
    # Calculate sum of all individual shares
    total_shares = sum(person.total_owed for person in people.values())
    
    return people, total_receipt_amount, total_shares

def display_person_breakdown(person: Person, items: List[ExtractedItem], assignments: Dict[str, List[str]]) -> None:
    """
    Display the expense breakdown for a single person.
    
    Args:
        person: Person object
        items: List of ExtractedItem objects
        assignments: Dictionary mapping item IDs to lists of assigned person names
    """
    # Create a list of items this person is assigned to
    person_items = []
    for item in items:
        if person.name in assignments.get(item.id, []):
            person_items.append(item)
    
    # Display the breakdown in an expander
    with st.expander(f"{person.name} - ${person.total_owed:.2f}", expanded=True):
        if not person_items:
            st.info("No items assigned to this person.")
            return
        
        # Create a table of items
        item_data = []
        for item in person_items:
            # Calculate price per person for this item
            num_people = len(assignments.get(item.id, []))
            price_per_person = item.total_price / num_people if num_people > 0 else 0
            
            # Add to the table data
            item_data.append({
                "Item": item.name,
                "Total Price": f"${item.total_price:.2f}",
                "Shared With": f"{num_people} people",
                "Your Share": f"${price_per_person:.2f}"
            })
        
        # Display the table
        st.table(item_data)
        
        # Show the total
        st.markdown(f"**Total owed by {person.name}: ${person.total_owed:.2f}**")

def validate_totals(total_receipt: float, total_shares: float) -> bool:
    """
    Validate that the sum of all shares equals the receipt total.
    
    Args:
        total_receipt: Total receipt amount
        total_shares: Sum of all individual shares
        
    Returns:
        True if the totals match (within a small tolerance), False otherwise
    """
    # Use the validator utility for consistency
    return Validator.validate_totals(total_receipt, total_shares)

def main():
    """Main function to render the results page."""
    
    st.title("Expense Breakdown")
    st.subheader("Step 3: View how much each person owes")
    
    # Check if we have extracted items and assignments
    if not SessionManager.get_extracted_items() or not SessionManager.get_all_assignments():
        st.warning("Please complete the item extraction and assignment first.")
        st.button("Go to Extraction Page", on_click=lambda: st.switch_page("pages/2_extraction_page.py"))
        return
    
    # Calculate results
    people, total_receipt, total_shares = calculate_results()
    
    # Validate totals
    totals_valid = validate_totals(total_receipt, total_shares)
    
    # Display summary
    st.markdown("## Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Receipt Amount", f"${total_receipt:.2f}")
    
    with col2:
        st.metric("Total Shares", f"${total_shares:.2f}")
    
    # Show validation result
    if totals_valid:
        st.success("✅ Validation passed: The sum of all shares equals the receipt total.")
    else:
        st.error(f"❌ Validation failed: The sum of all shares (${total_shares:.2f}) does not equal the receipt total (${total_receipt:.2f}).")
        st.info("This may be due to rounding errors or unassigned items. Please go back and check your assignments.")
    
    # Display individual breakdowns
    st.markdown("## Individual Breakdowns")
    
    # Sort people by amount owed (highest first)
    sorted_people = sorted(people.values(), key=lambda p: p.total_owed, reverse=True)
    
    # Get items and assignments for display
    items = SessionManager.get_extracted_items()
    assignments = SessionManager.get_all_assignments()
    
    # Display each person's breakdown
    for person in sorted_people:
        display_person_breakdown(person, items, assignments)
    
    # Check for unassigned items using the validator
    is_valid, unassigned_item_names = Validator.validate_item_assignments(items, assignments)
    
    if not is_valid:
        total_unassigned_value = sum(item.total_price for item in items if not assignments.get(item.id, []))
        
        st.warning(f"⚠️ {len(unassigned_item_names)} items worth ${total_unassigned_value:.2f} have no participants assigned.")
        st.error("These items are not included in the calculations, which may cause discrepancies in the total.")
        
        with st.expander("View Unassigned Items"):
            for item in items:
                if not assignments.get(item.id, []):
                    st.write(f"- {item.name}: ${item.total_price:.2f}")
            
            st.info("To fix this issue, go back to the extraction page and assign participants to all items.")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("Back to Extraction", on_click=lambda: st.switch_page("pages/2_extraction_page.py"))
    with col2:
        st.button("Start Over", on_click=lambda: (SessionManager.clear_session(), st.switch_page("app.py")))

if __name__ == "__main__":
    main()