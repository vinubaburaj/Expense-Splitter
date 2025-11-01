"""
Extraction Page - Second step in the PDF Receipt Expense Splitter workflow

This page allows users to:
1. View automatically extracted items from the receipt
2. Edit item details if needed
3. Assign participants to each item
4. Add or remove items manually
"""

import streamlit as st
import uuid
import logging
from typing import List, Dict, Optional, Tuple
from models.extracted_item import ExtractedItem
from utils.session_manager import SessionManager
from utils.validation import Validator
from services.pdf_processor import PDFProcessor, PDFProcessingError
from services.receipt_parser import ReceiptParser, ReceiptParsingError

# Set up logging
logger = logging.getLogger(__name__)

# Initialize session state
SessionManager.initialize_session()


def calculate_total(items: List[ExtractedItem]) -> float:
    """
    Calculate the total amount from all items.

    Args:
        items: List of ExtractedItem objects

    Returns:
        Total amount as float
    """
    return sum(item.total_price for item in items)


def display_item_editor(
    items: List[ExtractedItem], participants: List[str]
) -> List[ExtractedItem]:
    """
    Display and allow editing of extracted items.

    Args:
        items: List of ExtractedItem objects
        participants: List of participant names

    Returns:
        Updated list of ExtractedItem objects
    """
    if not items:
        st.warning("No items found. Add items manually below.")
        return []

    st.subheader("Edit Extracted Items")
    st.write(
        "Review and edit the extracted items below. Check the boxes to assign participants to each item."
    )

    # Create a container for the items
    items_container = st.container()

    # Display each item in an editable format
    updated_items = []
    with items_container:
        for i, item in enumerate(items):
            with st.expander(f"{item.name} - ${item.total_price:.2f}", expanded=True):
                # Item details
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    new_name = st.text_input(
                        "Item name", value=item.name, key=f"name_{i}"
                    )

                    # Show confidence score as a progress bar
                    st.progress(
                        item.confidence_score,
                        text=f"Confidence: {item.confidence_score:.0%}",
                    )

                with col2:
                    # Validate and sanitize quantity to prevent JavaScript number bounds errors
                    # Streamlit requires values <= (1 << 53) - 1, but we'll use a more reasonable limit
                    safe_quantity = 1
                    if item.quantity is not None:
                        try:
                            # Convert to int and ensure it's within reasonable bounds
                            qty_int = int(item.quantity)
                            # Reasonable max quantity (way below JS safe integer limit)
                            max_safe_quantity = 10000
                            if 1 <= qty_int <= max_safe_quantity:
                                safe_quantity = qty_int
                        except (ValueError, TypeError, OverflowError):
                            # If conversion fails, use default
                            safe_quantity = 1

                    new_quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        value=safe_quantity,
                        step=1,
                        key=f"qty_{i}",
                    )

                with col3:
                    # Validate and sanitize price to prevent JavaScript number bounds errors
                    safe_price = 0.01
                    if item.total_price is not None:
                        try:
                            # Convert to float and ensure it's within reasonable bounds
                            price_float = float(item.total_price)
                            # Reasonable max price (way below JS safe integer limit)
                            max_safe_price = 1000000.0  # $1 million max
                            if 0.01 <= price_float <= max_safe_price:
                                safe_price = price_float
                        except (ValueError, TypeError, OverflowError):
                            # If conversion fails, use default
                            safe_price = 0.01

                    new_price = st.number_input(
                        "Price",
                        min_value=0.01,
                        value=safe_price,
                        step=0.01,
                        format="%.2f",
                        key=f"price_{i}",
                    )

                # Participant assignment section
                st.write("Assign to participants:")
                participant_cols = st.columns(min(4, len(participants)))

                # Get current assignments for this item
                current_assignments = SessionManager.get_item_assignments(item.id)

                # Create checkboxes for each participant
                for j, person in enumerate(participants):
                    col_idx = j % len(participant_cols)
                    with participant_cols[col_idx]:
                        is_assigned = person in current_assignments
                        if st.checkbox(
                            person, value=is_assigned, key=f"assign_{i}_{j}"
                        ):
                            if person not in current_assignments:
                                SessionManager.update_item_assignment(
                                    item.id, person, True
                                )
                        else:
                            if person in current_assignments:
                                SessionManager.update_item_assignment(
                                    item.id, person, False
                                )

                # Delete button
                if st.button("Delete Item", key=f"delete_{i}"):
                    # Skip this item in the updated list
                    continue

                # Create updated item with new values
                updated_item = ExtractedItem(
                    id=item.id,
                    name=new_name,
                    quantity=new_quantity,
                    total_price=new_price,
                    unit_price=new_price / new_quantity if new_quantity > 0 else None,
                    confidence_score=item.confidence_score,
                    is_special_charge=item.is_special_charge,
                    assigned_people=current_assignments,
                )

                updated_items.append(updated_item)

    return updated_items


def add_new_item_form(participants: List[str]) -> Optional[ExtractedItem]:
    """
    Display form to add a new item manually with enhanced validation.

    Args:
        participants: List of participant names

    Returns:
        New ExtractedItem object or None if form not submitted
    """
    st.subheader("Add New Item")

    with st.form("add_item_form"):
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            name = st.text_input("Item name", key="new_item_name")
            # Show help text for item name
            st.caption("Enter a descriptive name for the item")

        with col2:
            quantity = st.number_input(
                "Quantity", min_value=1, value=1, step=1, key="new_item_qty"
            )

        with col3:
            price = st.number_input(
                "Price",
                min_value=0.01,
                value=0.00,
                step=0.01,
                format="%.2f",
                key="new_item_price",
            )

        # Participant assignment with clearer instructions
        st.write("Assign to participants (select at least one):")
        participant_cols = st.columns(min(4, len(participants)))

        # Create a dictionary to store participant assignments
        new_item_assignments = {}
        for i, person in enumerate(participants):
            col_idx = i % len(participant_cols)
            with participant_cols[col_idx]:
                new_item_assignments[person] = st.checkbox(
                    person, key=f"new_assign_{i}"
                )

        # Add a "select all" option
        if st.checkbox("Select all participants", key="select_all_new"):
            for person in participants:
                new_item_assignments[person] = True

        submitted = st.form_submit_button("Add Item")

        if submitted:
            # Validate item name using the validator
            name_valid, name_error = Validator.validate_item_name(name)
            if not name_valid:
                st.error(f"Invalid item name: {name_error}")
                return None

            # Validate price
            if price <= 0:
                st.error("Price must be greater than zero")
                return None

            # Validate quantity
            if quantity <= 0:
                st.error("Quantity must be greater than zero")
                return None

            # Validate participant assignments
            assigned_people = [
                person for person, assigned in new_item_assignments.items() if assigned
            ]
            if not assigned_people:
                st.error("Please assign at least one participant to this item")
                return None

            # Create new item with validated data
            item_id = str(uuid.uuid4())

            new_item = ExtractedItem(
                id=item_id,
                name=name.strip().title(),  # Normalize name format
                quantity=quantity,
                total_price=price,
                unit_price=price / quantity if quantity > 0 else None,
                confidence_score=1.0,  # Manual items have perfect confidence
                is_special_charge=False,
                assigned_people=assigned_people,
            )

            # Update session state with assignments
            for person in assigned_people:
                SessionManager.update_item_assignment(item_id, person, True)

            # Log the new item creation
            logger.info(f"New item added manually: {name} (${price:.2f})")

            return new_item

    return None


def process_pdf_and_extract_items() -> List[ExtractedItem]:
    """
    Process the uploaded PDF and extract items.

    Returns:
        List of ExtractedItem objects
    """
    # Get the uploaded file
    uploaded_file = SessionManager.get_uploaded_file()

    if not uploaded_file:
        logger.warning("No uploaded file found in session state")
        return []

    # Check if we already have extracted items
    existing_items = SessionManager.get_extracted_items()
    if existing_items:
        logger.info(f"Using {len(existing_items)} previously extracted items")
        return existing_items

    # Create a placeholder for progress indicators
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    error_details_expander = st.empty()

    # Create a progress bar
    progress_bar = progress_placeholder.progress(
        0, text="Initializing PDF processing..."
    )

    try:
        # Step 1: Initialize PDF processor
        status_placeholder.info("Initializing PDF processor...")
        pdf_processor = PDFProcessor()
        progress_bar.progress(10, text="PDF processor initialized")

        # Step 2: Extract text from PDF using comprehensive method
        status_placeholder.info("Extracting text from PDF (this may take a moment)...")

        try:
            # Use the comprehensive method that tries multiple approaches
            receipt_text = pdf_processor.process_pdf_comprehensive(uploaded_file)

            if (
                not receipt_text or len(receipt_text.strip()) < 20
            ):  # Arbitrary minimum length
                raise PDFProcessingError("Extracted text is too short or empty")

            progress_bar.progress(60, text="Text extracted successfully")
            status_placeholder.success("Successfully extracted text from PDF")

            # Show a sample of the extracted text for debugging
            with error_details_expander.expander("View extracted text sample"):
                st.text(receipt_text[:500] + ("..." if len(receipt_text) > 500 else ""))

        except PDFProcessingError as e:
            progress_bar.progress(60, text="PDF processing failed")
            status_placeholder.error(f"PDF processing error: {str(e)}")

            with error_details_expander.expander("Error details"):
                st.error(str(e))
                st.markdown(
                    """
                **Possible reasons for failure:**
                - The PDF might be scanned as an image with poor quality
                - The PDF might be password protected
                - The PDF might have unusual formatting
                
                **What you can do:**
                - Try a different PDF file
                - Add items manually using the form below
                """
                )

            logger.error(f"PDF processing error: {str(e)}")
            return []

        except Exception as e:
            progress_bar.progress(60, text="PDF processing failed")
            status_placeholder.error("Unexpected error during PDF processing")

            with error_details_expander.expander("Error details"):
                st.error(f"Unexpected error: {str(e)}")

            logger.exception("Unexpected error during PDF processing")
            return []

        # Step 3: Parse receipt text
        status_placeholder.info("Analyzing receipt text and extracting items...")
        progress_bar.progress(80, text="Parsing receipt text...")

        try:
            receipt_parser = ReceiptParser()
            extracted_items = receipt_parser.parse_receipt_text(receipt_text)

            # Validate extracted items
            is_valid, validation_error = Validator.validate_extracted_items(
                extracted_items
            )
            if not is_valid:
                logger.warning(f"Extracted items validation failed: {validation_error}")
                status_placeholder.warning("Some extracted items may be invalid")

            # Step 4: Finalize
            progress_bar.progress(100, text="Processing complete!")
            status_placeholder.success(
                f"Successfully extracted {len(extracted_items)} items from receipt"
            )

            # Store extracted items in session state
            SessionManager.store_extracted_items(extracted_items)

            # If no items were extracted, show a message
            if not extracted_items:
                st.warning(
                    "No items could be extracted from the receipt. Please add items manually below."
                )
            elif len(extracted_items) < 3:  # If very few items were extracted
                st.info(
                    "Only a few items were extracted. You may need to add more items manually."
                )

            return extracted_items

        except ReceiptParsingError as e:
            progress_bar.progress(100, text="Receipt parsing failed")
            status_placeholder.error("Failed to identify items in your receipt")

            with error_details_expander.expander("Error details"):
                st.error(f"Receipt parsing error: {str(e)}")
                st.markdown(
                    """
                **Possible reasons for failure:**
                - The receipt format might not be recognized
                - The text extraction might have produced poor quality text
                - The receipt might have unusual formatting
                
                **What you can do:**
                - Add items manually using the form below
                """
                )

            logger.error(f"Receipt parsing error: {str(e)}")
            return []

        except Exception as e:
            progress_bar.progress(100, text="Processing failed")
            status_placeholder.error("Unexpected error during receipt parsing")

            with error_details_expander.expander("Error details"):
                st.error(f"Unexpected error: {str(e)}")

            logger.exception("Unexpected error during receipt parsing")
            return []

    except Exception as e:
        progress_bar.progress(100, text="Processing failed")
        status_placeholder.error("PDF processing failed")

        with error_details_expander.expander("Error details"):
            st.error(f"Unexpected error: {str(e)}")

        logger.exception("Unexpected error in process_pdf_and_extract_items")
        st.info("You can still add items manually using the form below.")
        return []


def main():
    """Main function to render the extraction page."""

    st.title("Extract and Edit Items")
    st.subheader("Step 2: Review extracted items and assign participants")

    # Check if we have an uploaded file
    if not SessionManager.get_uploaded_file():
        st.warning("Please upload a PDF receipt first.")
        st.button(
            "Go to Upload Page",
            on_click=lambda: st.switch_page("pages/1_upload_page.py"),
        )
        return

    # Check if we have participants
    participants = SessionManager.get_participants()
    if not participants:
        st.warning("Please add participants first.")
        st.button(
            "Go to Upload Page",
            on_click=lambda: st.switch_page("pages/1_upload_page.py"),
        )
        return

    # Display file information
    uploaded_file = SessionManager.get_uploaded_file()
    st.info(f"Processing receipt: {uploaded_file.name}")

    # Process PDF and extract items
    items = process_pdf_and_extract_items()

    # If no items were extracted, show a more prominent message and encourage manual entry
    if not items:
        st.warning("⚠️ No items could be extracted from your receipt.")
        st.info("Don't worry! You can add items manually using the form below.")

        # Add a button to retry processing with different settings
        if st.button("Retry Processing"):
            # Clear existing items to force reprocessing
            SessionManager.store_extracted_items([])
            st.rerun()
    elif len(items) < 3:  # If very few items were extracted
        st.warning(
            "Only a few items were extracted. You may need to add more items manually."
        )
    else:
        # Show success message with item count
        st.success(f"Successfully extracted {len(items)} items from your receipt!")

    # Display and edit items
    updated_items = display_item_editor(items, participants)

    # Add new item form with a more prominent header if no items were extracted
    if not items:
        st.markdown("### 👇 Add Your Items Manually")

    new_item = add_new_item_form(participants)
    if new_item:
        updated_items.append(new_item)
        # Update session state with the new item
        SessionManager.store_extracted_items(updated_items)
        st.success("New item added successfully!")
        st.rerun()  # Rerun to refresh the UI

    # Calculate and display total
    total_amount = calculate_total(updated_items)
    st.subheader(f"Total Amount: ${total_amount:.2f}")

    # Check for unassigned items using the validator
    is_valid, unassigned_item_names = Validator.validate_item_assignments(
        updated_items, SessionManager.get_all_assignments()
    )

    if not is_valid:
        st.warning(
            f"⚠️ {len(unassigned_item_names)} items have no participants assigned:"
        )
        # Show the unassigned items in a more visible way
        for item_name in unassigned_item_names:
            st.error(f"• {item_name} - Please assign at least one participant")
        st.info("Please assign participants to all items before continuing")

    # Update session state with edited items
    if updated_items != items:
        SessionManager.store_extracted_items(updated_items)

    # Help text for low confidence items
    low_confidence_items = [
        item for item in updated_items if item.confidence_score < 0.7
    ]
    if low_confidence_items:
        with st.expander("About Low Confidence Items"):
            st.markdown(
                """
            Some items were extracted with low confidence. This means:
            - The item name or price might not be accurate
            - You should review these items carefully
            - You can edit any incorrect information
            
            Items with a confidence score below 70% are considered low confidence.
            """
            )

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "Back to Upload", on_click=lambda: st.switch_page("pages/1_upload_page.py")
        )
    with col2:
        # Enable the continue button only if all items have participants assigned
        continue_disabled = not is_valid
        if continue_disabled:
            st.info("Please assign participants to all items before continuing")

        if st.button("Continue to Results", disabled=continue_disabled):
            st.switch_page("pages/3_results_page.py")


if __name__ == "__main__":
    main()
