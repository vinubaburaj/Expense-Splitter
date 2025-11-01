"""
Manual Entry Page - Alternative workflow for entering expenses manually

This page allows users to:
1. Add participants involved in the expense
2. Add each item manually with name, price, and participant assignments
3. Calculate and display expense breakdown
"""

import streamlit as st
import uuid
import logging
from typing import List, Optional
from models.extracted_item import ExtractedItem
from models.expense import Expense
from models.person import Person
from utils.session_manager import SessionManager
from utils.validation import Validator
from services.expense_calculator import ExpenseCalculator

# Set up logging
logger = logging.getLogger(__name__)

# Initialize session state
SessionManager.initialize_session()


def participant_input_section() -> List[str]:
    """
    Render the participant input section with add/remove functionality.

    Returns:
        list: List of participant names
    """
    st.subheader("Step 1: Add Participants")
    st.write("Enter the names of people who will share the expenses.")

    # Get existing participants from session state
    participants = SessionManager.get_participants()

    # New participant input
    col1, col2 = st.columns([3, 1])
    with col1:
        new_participant = st.text_input(
            "Participant name",
            key="manual_new_participant",
            label_visibility="collapsed",
        )
    with col2:
        if st.button("Add", key="manual_add_participant"):
            if new_participant and new_participant.strip():
                # Check for duplicates
                if new_participant.strip() in participants:
                    st.warning(f"'{new_participant.strip()}' is already in the list.")
                else:
                    participants.append(new_participant.strip())
                    SessionManager.store_participants(participants)
                    st.rerun()

    # Display and manage existing participants
    if participants:
        st.write("**Current participants:**")
        for i, name in enumerate(participants):
            cols = st.columns([3, 1])
            with cols[0]:
                st.write(f"• {name}")
            with cols[1]:
                if st.button("Remove", key=f"manual_remove_{i}"):
                    participants.pop(i)
                    SessionManager.store_participants(participants)
                    st.rerun()

    # Validation message
    if len(participants) < 2:
        st.info("⚠️ Please add at least 2 participants to continue.")

    return participants


def add_item_form(participants: List[str]) -> Optional[ExtractedItem]:
    """
    Display form to add a new expense item.

    Args:
        participants: List of participant names

    Returns:
        New ExtractedItem object or None if form not submitted
    """
    st.subheader("Step 2: Add Expense Items")
    st.write(
        "Add each expense item individually. Enter the item name, total price, and select who is sharing this expense."
    )

    with st.form("manual_add_item_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            item_name = st.text_input(
                "Item Name *",
                placeholder="e.g., Pizza, Coffee, etc.",
                key="manual_item_name",
            )

        with col2:
            item_price = st.number_input(
                "Total Price ($) *",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f",
                key="manual_item_price",
            )

        # Participant selection (multi-select)
        st.write("**Select participants sharing this expense:**")
        selected_participants = st.multiselect(
            "Participants *",
            options=participants,
            default=participants,  # Default to all participants
            key="manual_item_participants",
            help="Select all participants who should share this expense",
        )

        submitted = st.form_submit_button(
            "Add Item", type="primary", use_container_width=True
        )

        if submitted:
            # Validate inputs
            if not item_name or not item_name.strip():
                st.error("Please enter an item name")
                return None

            if item_price <= 0:
                st.error("Price must be greater than zero")
                return None

            if not selected_participants or len(selected_participants) == 0:
                st.error("Please select at least one participant")
                return None

            # Validate item name using the validator
            name_valid, name_error = Validator.validate_item_name(item_name)
            if not name_valid:
                st.error(f"Invalid item name: {name_error}")
                return None

            # Create new item
            item_id = str(uuid.uuid4())

            new_item = ExtractedItem(
                id=item_id,
                name=item_name.strip().title(),
                quantity=1,
                total_price=item_price,
                unit_price=item_price,
                confidence_score=1.0,  # Manual items have perfect confidence
                is_special_charge=False,
                assigned_people=selected_participants,
            )

            # Update session state with assignments
            for person in selected_participants:
                SessionManager.update_item_assignment(item_id, person, True)

            # Get existing items and add new one
            existing_items = SessionManager.get_extracted_items()
            existing_items.append(new_item)
            SessionManager.store_extracted_items(existing_items)

            logger.info(
                f"Manual item added: {item_name} (${item_price:.2f}) for {len(selected_participants)} participants"
            )
            st.success(f"✅ Added: {item_name} (${item_price:.2f})")

            return new_item

    return None


def display_items_list(items: List[ExtractedItem], participants: List[str]):
    """
    Display the list of added items with ability to remove them.

    Args:
        items: List of ExtractedItem objects
        participants: List of participant names
    """
    if not items:
        return

    st.subheader("Added Items")
    st.write(f"You have added {len(items)} item(s).")

    # Display items in a table format
    for i, item in enumerate(items):
        assigned_people = SessionManager.get_item_assignments(item.id)
        num_people = (
            len(assigned_people) if assigned_people else len(item.assigned_people)
        )
        price_per_person = item.total_price / num_people if num_people > 0 else 0

        col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1.5, 2, 1])

        with col1:
            st.write(f"**{item.name}**")

        with col2:
            st.write(f"${item.total_price:.2f}")

        with col3:
            st.write(f"{num_people} people")

        with col4:
            if assigned_people:
                st.write(", ".join(assigned_people))
            elif item.assigned_people:
                st.write(", ".join(item.assigned_people))
            else:
                st.write("(No participants)")

        with col5:
            if st.button("Remove", key=f"manual_remove_item_{i}", type="secondary"):
                # Remove item from list
                items.pop(i)
                SessionManager.store_extracted_items(items)
                # Also remove assignments
                if "item_assignments" in st.session_state:
                    item_id_to_remove = item.id
                    if item_id_to_remove in st.session_state.item_assignments:
                        del st.session_state.item_assignments[item_id_to_remove]
                st.rerun()

    # Calculate and show total
    total = sum(item.total_price for item in items)
    st.markdown(f"### Total Amount: ${total:.2f}")


def calculate_and_display_results(items: List[ExtractedItem], participants: List[str]):
    """
    Calculate expense breakdown and display results.

    Args:
        items: List of ExtractedItem objects
        participants: List of participant names
    """
    if not items:
        return

    st.subheader("Step 3: Expense Breakdown")

    # Convert ExtractedItem objects to Expense objects
    expenses = []
    for item in items:
        assigned_people = SessionManager.get_item_assignments(item.id)
        if not assigned_people:
            assigned_people = item.assigned_people

        if assigned_people:  # Only include items with assigned people
            expense = Expense(
                item_name=item.name,
                total_price=item.total_price,
                people_included=assigned_people,
                quantity=item.quantity,
                unit_price=item.unit_price,
                confidence_score=item.confidence_score,
                is_special_charge=item.is_special_charge,
            )
            expenses.append(expense)

    if not expenses:
        st.warning(
            "No items have participants assigned. Please assign participants to items before calculating."
        )
        return

    # Calculate debts
    people = ExpenseCalculator.calculate_debts(expenses)

    # Display summary
    st.markdown("### Summary")
    col1, col2 = st.columns(2)

    total_amount = sum(item.total_price for item in items)
    total_shares = sum(person.total_owed for person in people.values())

    with col1:
        st.metric("Total Amount", f"${total_amount:.2f}")

    with col2:
        st.metric("Total Shares", f"${total_shares:.2f}")

    # Validate totals
    totals_valid = Validator.validate_totals(total_amount, total_shares)
    if totals_valid:
        st.success("✅ Totals match correctly!")
    else:
        st.warning(
            f"⚠️ Minor discrepancy in totals: ${abs(total_amount - total_shares):.2f}"
        )

    # Display individual breakdowns
    st.markdown("### Individual Breakdowns")

    # Sort people by amount owed (highest first)
    sorted_people = sorted(people.values(), key=lambda p: p.total_owed, reverse=True)

    for person in sorted_people:
        with st.expander(f"{person.name} - ${person.total_owed:.2f}", expanded=True):
            # Get items this person is involved in
            person_items = []
            for item in items:
                assigned_people = SessionManager.get_item_assignments(item.id)
                if not assigned_people:
                    assigned_people = item.assigned_people

                if person.name in assigned_people:
                    num_people = len(assigned_people)
                    price_per_person = (
                        item.total_price / num_people if num_people > 0 else 0
                    )
                    person_items.append(
                        {
                            "Item": item.name,
                            "Total Price": f"${item.total_price:.2f}",
                            "Shared With": f"{num_people} people",
                            "Your Share": f"${price_per_person:.2f}",
                        }
                    )

            if person_items:
                st.table(person_items)
            else:
                st.info("No items assigned to this person.")

            st.markdown(f"**Total owed by {person.name}: ${person.total_owed:.2f}**")


def main():
    """Main function to render the manual entry page."""

    st.title("Manual Expense Entry")
    st.subheader("Enter expenses manually without uploading files")

    # Step 1: Add participants
    participants = participant_input_section()

    # Check if we have enough participants
    participants_valid, participants_error = Validator.validate_participants(
        participants
    )

    if not participants_valid:
        st.warning(f"⚠️ {participants_error}")

    # Get current items
    items = SessionManager.get_extracted_items()

    # Step 2: Add items (only if we have participants)
    if participants_valid:
        # Add item form
        new_item = add_item_form(participants)

        # Display current items list
        if items:
            display_items_list(items, participants)

            # Step 3: Calculate and show results
            if st.button(
                "Calculate Expenses", type="primary", use_container_width=True
            ):
                calculate_and_display_results(items, participants)
        else:
            st.info(
                "📝 Start adding items above. Once you add items, you'll see them listed here and can calculate the breakdown."
            )
    else:
        st.info(
            "👆 Please add at least 2 participants above to start adding expense items."
        )

    # Navigation buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.switch_page("app.py")
    with col2:
        if st.button("🔄 Clear All Data", use_container_width=True):
            SessionManager.clear_session()
            st.success("All data cleared!")
            st.rerun()


if __name__ == "__main__":
    main()
