"""
PDF Receipt Expense Splitter - Main Application

This is the main entry point for the Streamlit web application that allows users to:
1. Upload PDF receipts
2. Extract items using OCR
3. Assign expenses to participants
4. Calculate individual shares

The application uses a multi-page structure with Streamlit.
"""

import streamlit as st
import os
import logging
import sys
from utils.session_manager import SessionManager
from utils.error_handler import ErrorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)

# Configure the Streamlit page
st.set_page_config(
    page_title="PDF Receipt Expense Splitter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
SessionManager.initialize_session()


def main():
    """Main function to render the home page of the application."""

    try:
        # Application header
        st.title("PDF Receipt Expense Splitter")
        st.subheader("Upload, extract, and split expenses from PDF receipts")

        # Check if pages directory exists, if not display a message
        if not os.path.exists("pages"):
            ErrorHandler.show_warning(
                "missing_pages_directory",
                "This application uses Streamlit's multi-page feature. Please create a 'pages' directory with the required page files.",
            )

        # Application description
        st.markdown(
            """
        ### How it works:
        
        **Option 1: Upload PDF Receipt (Automated)**
        1. **Upload a PDF receipt** - We'll extract the items automatically
        2. **Add participants** - Tell us who's splitting the bill
        3. **Review extracted items** - Make corrections if needed
        4. **Assign expenses** - Choose who pays for what
        5. **Get the breakdown** - See how much each person owes
        
        **Option 2: Manual Entry**
        1. Add participants involved in the expense
        2. Add each item manually with name, price, and participants
        3. Get the breakdown - See how much each person owes
        
        ### Get Started
        
        Choose one of the options below to begin.
        """
        )

        # Two-column layout for entry options
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📄 Upload PDF Receipt")
            st.markdown("Use our automated extraction from PDF receipts")
            if st.button("📤 Upload Receipt", type="primary", use_container_width=True):
                st.switch_page("pages/1_upload_page.py")

        with col2:
            st.markdown("### ✍️ Manual Entry")
            st.markdown("Enter expenses manually without uploading files")
            if st.button(
                "➕ Upload Expense Manually", type="secondary", use_container_width=True
            ):
                st.switch_page("pages/0_manual_entry.py")

        # Display any errors from session state
        if "error" in st.session_state and st.session_state.error:
            st.error(st.session_state.error)
            if st.button("Clear Error"):
                st.session_state.error = None
                st.rerun()

        # Display application status
        with st.sidebar.expander("Application Status"):
            if SessionManager.get_uploaded_file():
                st.success("✅ PDF file uploaded")
            else:
                st.info("❌ No PDF file uploaded")

            participants = SessionManager.get_participants()
            if participants and len(participants) >= 2:
                st.success(f"✅ {len(participants)} participants added")
            elif participants:
                st.warning(
                    f"⚠️ Only {len(participants)} participant added (need at least 2)"
                )
            else:
                st.info("❌ No participants added")

            items = SessionManager.get_extracted_items()
            if items:
                st.success(f"✅ {len(items)} items extracted")
            else:
                st.info("❌ No items extracted")

        # Reset button with confirmation
        if st.sidebar.button("Reset Application"):
            if "reset_confirm" not in st.session_state:
                st.session_state.reset_confirm = True
                st.sidebar.warning("Are you sure? All data will be lost.")
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    if st.button("Yes, Reset"):
                        SessionManager.clear_session()
                        st.session_state.reset_confirm = False
                        st.success(
                            "Application has been reset. All data has been cleared."
                        )
                        st.rerun()
                with col2:
                    if st.button("Cancel"):
                        st.session_state.reset_confirm = False
                        st.rerun()

        # Add a help section
        with st.sidebar.expander("Help & Troubleshooting"):
            st.markdown(
                """
            **Common Issues:**
            
            - **PDF not recognized**: Try a different PDF or add items manually
            - **Extraction errors**: Check that your PDF is not password protected
            - **Missing items**: You can add items manually on the extraction page
            - **Calculation errors**: Ensure all items have participants assigned
            
            If you encounter persistent issues, try resetting the application.
            """
            )

    except Exception as e:
        # Log the exception
        logger.exception("Unexpected error in main application")

        # Show error to user
        st.error(f"An unexpected error occurred: {str(e)}")
        st.info("Please try refreshing the page or resetting the application.")

        # Add a button to reset the application
        if st.button("Reset Application"):
            SessionManager.clear_session()
            st.rerun()


if __name__ == "__main__":
    main()
