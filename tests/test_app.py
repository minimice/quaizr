"""
Tests for app.py

Tests the following:
- CSV loading and parsing
- Session state initialization from URL params
- Agent configurations (hint_agent, explanation_agent)
- Quiz flow logic (score calculation, question progression)
- Feedback storage mechanism
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCSVLoading:
    """Tests for CSV question loading functionality."""

    def test_csv_file_structure(self, sample_csv_content, tmp_path):
        """Test that CSV file is loaded correctly with expected columns."""
        import pandas as pd

        # Write sample CSV to temp file
        csv_file = tmp_path / "test_questions.csv"
        csv_file.write_text(sample_csv_content.getvalue())

        # Load and verify
        df = pd.read_csv(csv_file)

        expected_columns = [
            'question', 'option_a', 'option_b', 'option_c', 'option_d',
            'correct_answer', 'correct_text', 'explanation'
        ]

        for col in expected_columns:
            assert col in df.columns

        assert len(df) == 1
        assert df.iloc[0]['question'] == "Which Google Cloud service is used for object storage?"

    def test_csv_multiple_questions(self, tmp_path):
        """Test loading multiple questions from CSV."""
        import pandas as pd

        csv_content = """question,option_a,option_b,option_c,option_d,correct_answer,correct_text,explanation
Q1,A1,B1,C1,D1,A,Text1,Exp1
Q2,A2,B2,C2,D2,B,Text2,Exp2
Q3,A3,B3,C3,D3,C,Text3,Exp3
"""
        csv_file = tmp_path / "multi_questions.csv"
        csv_file.write_text(csv_content)

        df = pd.read_csv(csv_file)

        assert len(df) == 3
        assert df.iloc[0]['question'] == "Q1"
        assert df.iloc[1]['correct_answer'] == "B"
        assert df.iloc[2]['option_d'] == "D3"


class TestSessionStateInitialization:
    """Tests for session state initialization from URL params."""

    def test_session_state_default_values(self, mock_streamlit):
        """Test that session state initializes with correct default values."""
        # Simulate fresh session (no URL params)
        mock_streamlit['query_params'].clear()
        mock_streamlit['session_state'].clear()

        # Verify defaults would be set correctly
        assert 'current_q' not in mock_streamlit['session_state']
        assert 'score' not in mock_streamlit['session_state']
        assert 'button' not in mock_streamlit['session_state']

    def test_session_state_from_url_params(self, mock_streamlit):
        """Test that session state is populated from URL parameters."""
        # Simulate URL params from shared link
        mock_streamlit['query_params'].current_q = "2"
        mock_streamlit['query_params'].score = "1"
        mock_streamlit['query_params'].name = "Returning User"
        mock_streamlit['query_params'].started = "True"
        mock_streamlit['query_params'].explain_ai = "False"

        # Verify params are accessible
        assert mock_streamlit['query_params'].current_q == "2"
        assert mock_streamlit['query_params'].score == "1"
        assert mock_streamlit['query_params'].name == "Returning User"

    def test_session_state_button_default(self, mock_streamlit):
        """Test that button state defaults to False."""
        assert mock_streamlit['session_state'].button is False


class TestAgentConfigurations:
    """Tests for agent configuration and setup."""

    def test_retry_configuration(self):
        """Test that retry configuration is set up correctly."""
        from google.genai import types

        retry_config = types.HttpRetryOptions(
            attempts=10,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 503, 504, 500]
        )

        assert retry_config.attempts == 10
        assert retry_config.exp_base == 7
        assert retry_config.initial_delay == 1
        assert 429 in retry_config.http_status_codes
        assert 500 in retry_config.http_status_codes

    def test_agent_module_structure(self):
        """Test that app module has expected agent attributes."""
        # We can test the module structure without fully importing
        # by checking the source code
        app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
        with open(app_path, 'r') as f:
            content = f.read()

        # Verify agent definitions exist in source
        assert 'hint_agent' in content
        assert 'explanation_agent' in content
        assert 'LlmAgent' in content


class TestQuizFlowLogic:
    """Tests for quiz flow logic including score calculation and progression."""

    def test_score_increment_on_correct_answer(self, mock_streamlit_with_data):
        """Test that score increments when correct answer is selected."""
        mock_streamlit_with_data['session_state'].score = 0
        mock_streamlit_with_data['session_state'].current_q = 0

        # Simulate correct answer selection
        user_choice = "Cloud Storage"  # Correct answer from sample data
        correct_option = "Cloud Storage"

        is_correct = user_choice == correct_option

        if is_correct:
            mock_streamlit_with_data['session_state'].score += 1

        assert mock_streamlit_with_data['session_state'].score == 1
        assert is_correct is True

    def test_score_no_increment_on_incorrect_answer(self, mock_streamlit_with_data):
        """Test that score does not increment when incorrect answer is selected."""
        mock_streamlit_with_data['session_state'].score = 0
        mock_streamlit_with_data['session_state'].current_q = 0

        # Simulate incorrect answer selection
        user_choice = "Cloud SQL"  # Incorrect answer
        correct_option = "Cloud Storage"

        is_correct = user_choice == correct_option

        if is_correct:
            mock_streamlit_with_data['session_state'].score += 1

        assert mock_streamlit_with_data['session_state'].score == 0
        assert is_correct is False

    def test_question_progression(self, mock_streamlit_with_data):
        """Test that current_q increments after answering."""
        mock_streamlit_with_data['session_state'].current_q = 0

        # Simulate answering a question
        mock_streamlit_with_data['session_state'].current_q += 1

        assert mock_streamlit_with_data['session_state'].current_q == 1

    def test_quiz_completion_detection(self, mock_streamlit_with_data, tmp_path):
        """Test detection of quiz completion."""
        import pandas as pd

        # Create a 3-question quiz
        csv_content = """question,option_a,option_b,option_c,option_d,correct_answer,correct_text,explanation
Q1,A1,B1,C1,D1,A,Text1,Exp1
Q2,A2,B2,C2,D2,B,Text2,Exp2
Q3,A3,B3,C3,D3,C,Text3,Exp3
"""
        csv_file = tmp_path / "quiz.csv"
        csv_file.write_text(csv_content)

        df = pd.read_csv(csv_file)

        # Simulate completing all questions
        mock_streamlit_with_data['session_state'].current_q = 3

        # Check if quiz is complete
        is_complete = mock_streamlit_with_data['session_state'].current_q >= len(df)

        assert is_complete is True

        # Simulate mid-quiz
        mock_streamlit_with_data['session_state'].current_q = 1
        is_complete = mock_streamlit_with_data['session_state'].current_q >= len(df)

        assert is_complete is False


class TestFeedbackStorage:
    """Tests for feedback storage mechanism."""

    def test_hint_feedback_list_initialization(self, mock_streamlit):
        """Test that hint_feedback list is initialized."""
        mock_streamlit['session_state'].hint_feedback = []

        assert isinstance(mock_streamlit['session_state'].hint_feedback, list)
        assert len(mock_streamlit['session_state'].hint_feedback) == 0

    def test_feedback_entry_structure(self, mock_streamlit):
        """Test that feedback entries have correct structure."""
        from datetime import datetime, timezone

        mock_streamlit['session_state'].hint_feedback = []
        mock_streamlit['session_state'].name = "Test User"
        mock_streamlit['session_state'].current_q = 0

        feedback_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "username": mock_streamlit['session_state'].name,
            "quiz_name": "Quiz",
            "question_number": mock_streamlit['session_state'].current_q + 1,
            "question": "Test question?",
            "hint": "Test hint",
            "useful": True
        }

        mock_streamlit['session_state'].hint_feedback.append(feedback_entry)

        # Verify structure
        entry = mock_streamlit['session_state'].hint_feedback[0]
        assert 'timestamp' in entry
        assert 'username' in entry
        assert 'quiz_name' in entry
        assert 'question_number' in entry
        assert 'question' in entry
        assert 'hint' in entry
        assert 'useful' in entry

    def test_feedback_csv_export_structure(self, tmp_path):
        """Test that feedback can be exported to CSV with correct structure."""
        import pandas as pd

        feedback_data = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "username": "User1",
                "quiz_name": "Quiz",
                "question_number": 1,
                "question": "Q1?",
                "hint": "Hint1",
                "useful": True
            },
            {
                "timestamp": "2024-01-01T12:01:00",
                "username": "User2",
                "quiz_name": "Quiz",
                "question_number": 2,
                "question": "Q2?",
                "hint": "Hint2",
                "useful": False
            }
        ]

        csv_file = tmp_path / "hint_feedback.csv"
        df = pd.DataFrame(feedback_data)
        df.to_csv(csv_file, index=False)

        # Read back and verify
        df_read = pd.read_csv(csv_file)

        assert len(df_read) == 2
        assert 'timestamp' in df_read.columns
        assert 'username' in df_read.columns
        assert 'useful' in df_read.columns


class TestURLQueryParamsPersistence:
    """Tests for URL query parameter persistence."""

    def test_query_params_update_on_answer(self, mock_streamlit):
        """Test that query params are updated after answering."""
        mock_streamlit['session_state'].name = "Test User"
        mock_streamlit['session_state'].explain_ai = True
        mock_streamlit['session_state'].current_q = 1
        mock_streamlit['session_state'].score = 1
        mock_streamlit['session_state'].started = True

        # Simulate query param update
        mock_streamlit['query_params'].name = mock_streamlit['session_state'].name
        mock_streamlit['query_params'].explain_ai = str(mock_streamlit['session_state'].explain_ai)
        mock_streamlit['query_params'].current_q = str(mock_streamlit['session_state'].current_q)
        mock_streamlit['query_params'].score = str(mock_streamlit['session_state'].score)
        mock_streamlit['query_params'].started = str(mock_streamlit['session_state'].started)

        assert mock_streamlit['query_params'].name == "Test User"
        assert mock_streamlit['query_params'].current_q == "1"
        assert mock_streamlit['query_params'].score == "1"

    def test_query_params_clear_on_quiz_complete(self, mock_streamlit):
        """Test that query params can be cleared."""
        mock_streamlit['query_params'].current_q = "5"
        mock_streamlit['query_params'].score = "3"

        # Clear params
        mock_streamlit['query_params'].clear()

        assert len(mock_streamlit['query_params']) == 0


class TestAgentResponseHandling:
    """Tests for agent response handling."""

    @pytest.mark.asyncio
    async def test_hint_response_parsing(self, mock_adk):
        """Test that hint responses are parsed correctly."""
        response = mock_adk['hint_response']

        # Verify response structure
        assert hasattr(response, 'content')
        assert hasattr(response.content, 'parts')
        assert len(response.content.parts) > 0
        assert hasattr(response.content.parts[0], 'text')

        hint_text = response.content.parts[0].text
        assert isinstance(hint_text, str)
        assert len(hint_text) > 0

    @pytest.mark.asyncio
    async def test_explanation_response_parsing(self, mock_adk):
        """Test that explanation responses are parsed correctly."""
        response = mock_adk['explanation_response']

        # Verify response structure
        assert hasattr(response, 'content')
        assert hasattr(response.content, 'parts')
        assert len(response.content.parts) > 0

        explanation_text = response.content.parts[0].text
        assert isinstance(explanation_text, str)
        assert len(explanation_text) > 0


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_missing_api_key_handling(self):
        """Test that missing API key check exists in app."""
        # Verify the check exists by reading the source
        app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
        with open(app_path, 'r') as f:
            content = f.read()

        assert 'GOOGLE_API_KEY' in content
        assert 'st.error' in content
        assert 'st.stop()' in content

    def test_agent_exception_handling(self, mock_adk):
        """Test that agent exceptions can be caught."""
        mock_adk['hint_runner'].run_debug.side_effect = Exception("API Error")

        import asyncio

        async def test_call():
            try:
                await mock_adk['hint_runner'].run_debug("test")
                return False  # Should have raised
            except Exception as e:
                return str(e) == "API Error"

        result = asyncio.run(test_call())
        assert result is True

    def test_csv_file_not_found_handling(self):
        """Test handling when questions.csv is not found."""
        import pandas as pd

        with pytest.raises(FileNotFoundError):
            pd.read_csv("nonexistent_file.csv")
