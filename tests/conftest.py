"""
Shared fixtures and mock setup for QuAIzR tests.

Provides:
- Mocked streamlit module (st.session_state, st.query_params)
- Mocked ADK agents and runners
- Mocked asyncio.run
- Test data fixtures
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class MockSessionState(dict):
    """Mock for st.session_state that behaves like a dictionary."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MockSessionState' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError(name)


class MockQueryParams(dict):
    """Mock for st.query_params that behaves like a dictionary."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name in ('clear', 'to_dict', 'items', 'keys', 'values'):
            return super().__getattribute__(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MockQueryParams' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self[name] = value


def create_mock_streamlit():
    """Helper to create a fully mocked streamlit environment."""
    mocks = {}
    patches = []

    streamlit_attrs = [
        'session_state', 'query_params', 'spinner', 'success', 'error',
        'info', 'warning', 'button', 'radio', 'text_input', 'toggle',
        'image', 'title', 'subheader', 'markdown', 'columns', 'balloons',
        'rerun', 'stop', 'set_page_config', 'caption', 'sidebar'
    ]

    for attr in streamlit_attrs:
        if attr in ('session_state', 'query_params'):
            if attr == 'session_state':
                mock = MockSessionState()
                mock.button = False
                mock.show_hint = False
                mock.hint_text = ""
                mock.hint_feedback = []
                mock.hint_feedback_given = False
            else:
                mock = MockQueryParams()
                mock.explain_ai = "True"
                mock.name = ""
                mock.current_q = "0"
                mock.score = "0"
                mock.started = "False"
        else:
            mock = MagicMock()

        mocks[attr] = mock
        patches.append(patch(f'streamlit.{attr}', mock))

    for p in patches:
        p.start()

    return mocks


def stop_mock_streamlit(mocks):
    """Helper to stop all streamlit mocks."""
    patch.stopall()


@pytest.fixture
def mock_streamlit():
    """
    Fixture to mock the streamlit module.

    Provides mocked st.session_state and st.query_params.
    """
    mocks = create_mock_streamlit()

    yield {
        'session_state': mocks['session_state'],
        'query_params': mocks['query_params'],
        'spinner': mocks['spinner'],
        'success': mocks['success'],
        'error': mocks['error'],
        'info': mocks['info'],
        'warning': mocks['warning'],
        'button': mocks['button'],
        'radio': mocks['radio'],
        'text_input': mocks['text_input'],
        'toggle': mocks['toggle'],
        'image': mocks['image'],
        'title': mocks['title'],
        'subheader': mocks['subheader'],
        'markdown': mocks['markdown'],
        'columns': mocks['columns'],
        'balloons': mocks['balloons'],
        'rerun': mocks['rerun'],
        'stop': mocks['stop'],
        'set_page_config': mocks['set_page_config'],
        'caption': mocks['caption'],
    }

    stop_mock_streamlit(mocks)


@pytest.fixture
def mock_adk():
    """
    Fixture to mock Google ADK components.

    Provides mocked hint_runner and explanation_runner.
    """
    # Create mock response objects
    mock_hint_response = MagicMock()
    mock_hint_response.content.parts = [MagicMock()]
    mock_hint_response.content.parts[0].text = "This is a test hint about the key concept."

    mock_explanation_response = MagicMock()
    mock_explanation_response.content.parts = [MagicMock()]
    mock_explanation_response.content.parts[0].text = "This is a test explanation with documentation reference."

    # Create mock runners
    mock_hint_runner = MagicMock()
    mock_hint_runner.run_debug = AsyncMock(return_value=[mock_hint_response])

    mock_explanation_runner = MagicMock()
    mock_explanation_runner.run_debug = AsyncMock(return_value=[mock_explanation_response])

    with patch('google.adk.runners.InMemoryRunner') as mock_runner_class:
        mock_runner_class.side_effect = [mock_hint_runner, mock_explanation_runner]

        yield {
            'hint_runner': mock_hint_runner,
            'explanation_runner': mock_explanation_runner,
            'hint_response': mock_hint_response,
            'explanation_response': mock_explanation_response,
        }


@pytest.fixture
def mock_asyncio_run():
    """
    Fixture to mock asyncio.run for synchronous testing.
    """
    with patch('asyncio.run') as mock_run:
        yield mock_run


@pytest.fixture
def sample_question_data():
    """
    Fixture providing sample question data for testing.
    """
    return {
        'question': 'Which Google Cloud service is used for object storage?',
        'option_a': 'Cloud SQL',
        'option_b': 'Cloud Storage',
        'option_c': 'Compute Engine',
        'option_d': 'Cloud Functions',
        'correct_answer': 'B',
        'correct_text': 'Cloud Storage',
        'explanation': 'Cloud Storage is the correct answer because it is designed for object storage.'
    }


@pytest.fixture
def sample_csv_content(sample_question_data):
    """
    Fixture providing sample CSV content for testing.
    """
    import io
    csv_content = io.StringIO()
    csv_content.write("question,option_a,option_b,option_c,option_d,correct_answer,correct_text,explanation\n")
    csv_content.write(f"{sample_question_data['question']},{sample_question_data['option_a']},{sample_question_data['option_b']},{sample_question_data['option_c']},{sample_question_data['option_d']},{sample_question_data['correct_answer']},{sample_question_data['correct_text']},{sample_question_data['explanation']}\n")
    csv_content.seek(0)
    return csv_content


@pytest.fixture
def mock_streamlit_with_data(mock_streamlit, sample_question_data):
    """
    Combined fixture that provides mocked streamlit with pre-populated session state.
    """
    mock_streamlit['session_state'].name = "Test User"
    mock_streamlit['session_state'].started = True
    mock_streamlit['session_state'].current_q = 0
    mock_streamlit['session_state'].explain_ai = True
    mock_streamlit['session_state'].score = 0
    mock_streamlit['session_state'].button = False

    # Initialize vote tracking
    mock_streamlit['session_state']['hint_vote_q0'] = None

    return mock_streamlit
