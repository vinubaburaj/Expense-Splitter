"""
Upload Page - First step in the PDF Receipt Expense Splitter workflow

This page allows users to:
1. Upload a PDF receipt file
2. Add participant names for expense splitting
3. Validate inputs before proceeding to extraction
"""
import streamlit as st
import os
import logging
from utils.session_manager import SessionManager
from utils.validation import Validator

# Set up logging
logger = logging.getLogger(__name__)

# Initialize session state
SessionManager.initialize_session()

# Constants
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

def validate_pdf_file(uploaded_file):
    """
    Validate the uploaded PDF file using the Validator utility.
    
    Args:
        uploaded_file: The file uploaded through Streamlit's file_uploader
        
    Returns:
        tuple: (is_valid, error_message)
    """
    return Validator.validate_pdf_file(uploaded_file, MAX_FILE_SIZE_MB)

def participant_input_section():
    """
    Render the participant input section with add/remove functionality.
    
    Returns:
        list: List of participant names
    """
    st.subheader("Add Participants")
    st.write("Enter the names of people who will share the expenses.")
    
    # Get existing participants from session state
    participants = SessionManager.get_participants()
    
    # New participant input
    col1, col2 = st.columns([3, 1])
    with col1:
        new_participant = st.text_input("Participant name", key="new_participant")
    with col2:
        if st.button("Add", key="add_participant"):
            if new_participant and new_participant.strip():
                # Check for duplicates
                if new_participant in participants:
                    st.warning(f"'{new_participant}' is already in the list.")
                else:
                    participants.append(new_participant)
                    SessionManager.store_participants(participants)
                    # st.session_state.new_participant = ""  # Clear the input field
                    new_participant = "" # Clear the input field
                    st.rerun()
    
    # Display and manage existing participants
    if participants:
        st.write("Current participants:")
        for i, name in enumerate(participants):
            cols = st.columns([3, 1])
            with cols[0]:
                st.text(name)
            with cols[1]:
                if st.button("Remove", key=f"remove_{i}"):
                    participants.pop(i)
                    SessionManager.store_participants(participants)
                    st.rerun()
    
    # Validation message
    if len(participants) < 2:
        st.info("Please add at least 2 participants to continue.")
    
    return participants

def main():
    """Main function to render the upload page."""
    
    st.title("Upload Receipt")
    st.subheader("Step 1: Upload your PDF receipt and add participants")
    
    # File upload section
    st.write(f"Please upload a PDF receipt file (max {MAX_FILE_SIZE_MB}MB)")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    # Validate uploaded file
    if uploaded_file is not None:
        is_valid, error_message = validate_pdf_file(uploaded_file)
        if not is_valid:
            st.error(error_message)
        else:
            st.success(f"Successfully uploaded: {uploaded_file.name}")
            # Store the file in session state
            SessionManager.store_uploaded_file(uploaded_file)
    
    # Participant input section
    participants = participant_input_section()
    
    # Navigation button - enabled only when all validations pass
    file_valid = uploaded_file is not None and validate_pdf_file(uploaded_file)[0]
    participants_valid, participants_error = Validator.validate_participants(participants)
    
    # Show validation status
    if not file_valid and uploaded_file is not None:
        st.error("⚠️ Please fix the file upload issues before continuing.")
    
    if not participants_valid:
        st.warning(f"⚠️ {participants_error}")
    
    if st.button("Continue to Item Extraction", disabled=not (file_valid and participants_valid)):
        # Log the transition
        logger.info(f"Proceeding to extraction page with {len(participants)} participants")
        
        # Double-check validations before proceeding
        if not file_valid:
            st.error("Please upload a valid PDF file before continuing.")
        elif not participants_valid:
            st.error(participants_error)
        else:
            # All validations passed, proceed to next page
            st.success("Proceeding to item extraction...")
            # Use Streamlit's page navigation
            st.switch_page("pages/2_extraction_page.py")

if __name__ == "__main__":
    main()