"""
Utility functions (buttons, feedback, state logic)

Developed by Lim, Chooi Guan
https://linkedin.com/in/cgl88
"""

import streamlit as st
from datetime import datetime

# Toggles the Submit Answer button
def click_button():
    st.session_state.button = not st.session_state.button

# When the start quiz button is clicked, update the session variables
# and query params
def click_start_quiz():
    st.session_state.update({"started": True, "score": 0, "current_q": 0})
    st.query_params.explain_ai=st.session_state.explain_ai
    st.query_params.name=st.session_state.name

def store_hint_feedback(stapp, question, hint, hint_state):
    stapp.session_state.hint_feedback.append({
        "timestamp": datetime.utcnow().isoformat(),
        "username": stapp.session_state.name,
        "quiz_name": "Quiz",
        "question_number": stapp.session_state.current_q + 1,
        "question": question,
        "hint": hint,
        "useful": hint_state
    })