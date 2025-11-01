"""
Session management utility for Streamlit application.
Handles session state across different pages of the application.
"""
from typing import Dict, List, Optional, Any
import streamlit as st
from models.extracted_item import ExtractedItem


class SessionManager:
    """
    Manages Streamlit session state for the PDF Receipt Expense Splitter application.
    Provides methods to store and retrieve data across different pages.
    """
    
    @staticmethod
    def initialize_session() -> None:
        """
        Initialize the session state with default values if they don't exist.
        """
        if 'initialized' not in st.session_state:
            st.session_state.uploaded_file = None
            st.session_state.participants = []
            st.session_state.extracted_items = []
            st.session_state.item_assignments = {}  # Dict[item_id, List[person_name]]
            st.session_state.initialized = True
    
    @staticmethod
    def store_uploaded_file(file: Any) -> None:
        """
        Store the uploaded PDF file in the session state.
        
        Args:
            file: The uploaded file object from Streamlit's file_uploader
        """
        st.session_state.uploaded_file = file
    
    @staticmethod
    def get_uploaded_file() -> Optional[Any]:
        """
        Get the currently uploaded file from session state.
        
        Returns:
            The uploaded file object or None if no file has been uploaded
        """
        return st.session_state.get('uploaded_file')
    
    @staticmethod
    def store_participants(participants: List[str]) -> None:
        """
        Store the list of participants in the session state.
        
        Args:
            participants: List of participant names
        """
        st.session_state.participants = participants
    
    @staticmethod
    def get_participants() -> List[str]:
        """
        Get the list of participants from session state.
        
        Returns:
            List of participant names
        """
        return st.session_state.get('participants', [])
    
    @staticmethod
    def store_extracted_items(items: List[ExtractedItem]) -> None:
        """
        Store the list of extracted items in the session state.
        
        Args:
            items: List of ExtractedItem objects
        """
        st.session_state.extracted_items = items
        
        # Initialize item assignments if not already done
        if not st.session_state.get('item_assignments'):
            st.session_state.item_assignments = {item.id: [] for item in items}
    
    @staticmethod
    def get_extracted_items() -> List[ExtractedItem]:
        """
        Get the list of extracted items from session state.
        
        Returns:
            List of ExtractedItem objects
        """
        return st.session_state.get('extracted_items', [])
    
    @staticmethod
    def update_item_assignment(item_id: str, person_name: str, assigned: bool) -> None:
        """
        Update the assignment of a person to an item.
        
        Args:
            item_id: The ID of the item
            person_name: The name of the person
            assigned: True to assign the person to the item, False to remove the assignment
        """
        if 'item_assignments' not in st.session_state:
            st.session_state.item_assignments = {}
            
        if item_id not in st.session_state.item_assignments:
            st.session_state.item_assignments[item_id] = []
            
        current_assignments = st.session_state.item_assignments[item_id]
        
        if assigned and person_name not in current_assignments:
            current_assignments.append(person_name)
        elif not assigned and person_name in current_assignments:
            current_assignments.remove(person_name)
            
        st.session_state.item_assignments[item_id] = current_assignments
    
    @staticmethod
    def get_item_assignments(item_id: str) -> List[str]:
        """
        Get the list of people assigned to a specific item.
        
        Args:
            item_id: The ID of the item
            
        Returns:
            List of person names assigned to the item
        """
        if 'item_assignments' not in st.session_state:
            return []
            
        return st.session_state.item_assignments.get(item_id, [])
    
    @staticmethod
    def get_all_assignments() -> Dict[str, List[str]]:
        """
        Get all item assignments.
        
        Returns:
            Dictionary mapping item IDs to lists of assigned person names
        """
        return st.session_state.get('item_assignments', {})
    
    @staticmethod
    def clear_session() -> None:
        """
        Clear all session state data.
        Useful for starting over or debugging.
        """
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        SessionManager.initialize_session()