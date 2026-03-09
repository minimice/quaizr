"""
Unit tests for helpers.py

Tests the following functions:
- click_button() - Verify toggles st.session_state.button
- click_start_quiz() - Verify initializes quiz state and query params
- store_hint_feedback() - Verify appends feedback data correctly
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestClickButton:
    """Tests for the click_button function."""

    def test_click_button_toggles_from_false_to_true(self, mock_streamlit):
        """Test that click_button toggles button from False to True."""
        from helpers import click_button

        # Initial state
        mock_streamlit['session_state'].button = False

        # Call function
        click_button()

        # Verify toggle
        assert mock_streamlit['session_state'].button is True

    def test_click_button_toggles_from_true_to_false(self, mock_streamlit):
        """Test that click_button toggles button from True to False."""
        from helpers import click_button

        # Initial state
        mock_streamlit['session_state'].button = True

        # Call function
        click_button()

        # Verify toggle
        assert mock_streamlit['session_state'].button is False

    def test_click_button_multiple_toggles(self, mock_streamlit):
        """Test that click_button correctly toggles multiple times."""
        from helpers import click_button

        mock_streamlit['session_state'].button = False

        # Toggle multiple times
        click_button()
        assert mock_streamlit['session_state'].button is True

        click_button()
        assert mock_streamlit['session_state'].button is False

        click_button()
        assert mock_streamlit['session_state'].button is True


class TestClickStartQuiz:
    """Tests for the click_start_quiz function."""

    def test_click_start_quiz_initializes_state(self, mock_streamlit):
        """Test that click_start_quiz initializes quiz state correctly."""
        from helpers import click_start_quiz

        # Set initial state (simulating pre-quiz)
        mock_streamlit['session_state'].started = False
        mock_streamlit['session_state'].score = None
        mock_streamlit['session_state'].current_q = None
        mock_streamlit['session_state'].name = "Test User"
        mock_streamlit['session_state'].explain_ai = True

        # Call function
        click_start_quiz()

        # Verify state updates
        assert mock_streamlit['session_state'].started is True
        assert mock_streamlit['session_state'].score == 0
        assert mock_streamlit['session_state'].current_q == 0

    def test_click_start_quiz_updates_query_params(self, mock_streamlit):
        """Test that click_start_quiz updates query parameters."""
        from helpers import click_start_quiz

        mock_streamlit['session_state'].name = "John Doe"
        mock_streamlit['session_state'].explain_ai = True

        click_start_quiz()

        # Verify query params updated
        assert mock_streamlit['query_params'].explain_ai is True
        assert mock_streamlit['query_params'].name == "John Doe"

    def test_click_start_quiz_with_explain_ai_false(self, mock_streamlit):
        """Test that click_start_quiz handles explain_ai=False correctly."""
        from helpers import click_start_quiz

        mock_streamlit['session_state'].name = "Test User"
        mock_streamlit['session_state'].explain_ai = False

        click_start_quiz()

        assert mock_streamlit['query_params'].explain_ai is False


class TestStoreHintFeedback:
    """Tests for the store_hint_feedback function."""

    def test_store_hint_feedback_appends_data(self, mock_streamlit):
        """Test that store_hint_feedback appends feedback data correctly."""
        from helpers import store_hint_feedback
        import streamlit as st

        # Setup session state
        st.session_state.name = "Test User"
        st.session_state.current_q = 0
        st.session_state.hint_feedback = []

        # Call function
        store_hint_feedback(
            st,
            question="What is Cloud Storage?",
            hint="Think about object storage",
            hint_state=True
        )

        # Verify feedback was appended
        assert len(st.session_state.hint_feedback) == 1

        feedback = st.session_state.hint_feedback[0]
        assert feedback['question'] == "What is Cloud Storage?"
        assert feedback['hint'] == "Think about object storage"
        assert feedback['useful'] is True
        assert feedback['username'] == "Test User"
        assert feedback['question_number'] == 1  # current_q + 1
        assert 'timestamp' in feedback
        assert feedback['quiz_name'] == "Quiz"

    def test_store_hint_feedback_with_negative_feedback(self, mock_streamlit):
        """Test that store_hint_feedback handles negative feedback correctly."""
        from helpers import store_hint_feedback
        import streamlit as st

        st.session_state.name = "Test User"
        st.session_state.current_q = 2
        st.session_state.hint_feedback = []

        store_hint_feedback(
            st,
            question="What is Compute Engine?",
            hint="This is not the right service",
            hint_state=False
        )

        feedback = st.session_state.hint_feedback[0]
        assert feedback['useful'] is False
        assert feedback['question_number'] == 3  # current_q + 1

    def test_store_hint_feedback_multiple_entries(self, mock_streamlit):
        """Test that store_hint_feedback can store multiple feedback entries."""
        from helpers import store_hint_feedback
        import streamlit as st

        st.session_state.name = "Test User"
        st.session_state.current_q = 0
        st.session_state.hint_feedback = []

        # Add multiple feedback entries
        store_hint_feedback(st, "Question 1", "Hint 1", True)
        store_hint_feedback(st, "Question 2", "Hint 2", False)
        store_hint_feedback(st, "Question 3", "Hint 3", True)

        assert len(st.session_state.hint_feedback) == 3

        # Verify each entry
        assert st.session_state.hint_feedback[0]['question'] == "Question 1"
        assert st.session_state.hint_feedback[1]['question'] == "Question 2"
        assert st.session_state.hint_feedback[2]['question'] == "Question 3"

    def test_store_hint_feedback_timestamp_format(self, mock_streamlit):
        """Test that store_hint_feedback generates valid ISO timestamp."""
        from helpers import store_hint_feedback
        from datetime import datetime, timezone
        import streamlit as st

        st.session_state.name = "Test User"
        st.session_state.current_q = 0
        st.session_state.hint_feedback = []

        store_hint_feedback(st, "Test Question", "Test Hint", True)

        feedback = st.session_state.hint_feedback[0]
        # Verify timestamp is valid ISO format
        timestamp = feedback['timestamp']
        # Should not raise an exception
        datetime.fromisoformat(timestamp)
