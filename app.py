"""
app.py

QuAIzR - quiz system powered by AI Agents

Built with ADK + Gemini 2.5 Flash Lite.

Developed by Lim, Chooi Guan
https://linkedin.com/in/cgl88
"""

import os
import pandas as pd
import streamlit as st
import asyncio

from dotenv import load_dotenv
from datetime import datetime
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent

# Observabiliy
from google.adk.plugins.logging_plugin import (
    LoggingPlugin,
)

# Import helper functions
from helpers import click_button, click_start_quiz, store_hint_feedback

# --------- Load environment variables ----------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error(icon="❌",body="Missing GOOGLE_API_KEY environment variable. Ensure that this environment variable is set.")
    st.stop()

# --------- Retry configuration ----------
retry_config = types.HttpRetryOptions(
    attempts=10,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

# --- Agent 1: Hint Agent ---
hint_agent = LlmAgent(
    name="hint_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_config=retry_config
    ),
    description="Provides short, non-revealing hints for GCP quiz questions.",
    instruction="""
You are a GCP expert. Provide short hints.
Rules:
- Never reveal the correct answer.
- Max 15 words.
- Focus on the core concept being tested.
""",
    tools=[],   # No tools — fast & cheap
)

# --- Agent 2: Explanation Agent ---
explanation_agent = LlmAgent(
    name="explanation_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_config=retry_config
    ),
    description="Explains correct or incorrect GCP answers with references.",
    instruction="""
You explain GCP concepts in concise detail.
Rules:
- If unsure, use Google Search.
- Provide official Google Cloud documentation URLs.
- Keep explanations to 2–3 sentences unless asked otherwise.
""",
    tools=[google_search],  # ✅ MUST use google_search
)

# Use LoggingPlugin in both so you keep observability
plugins = [LoggingPlugin()]

hint_runner = InMemoryRunner(
    app_name="agents_hint",
    agent=hint_agent,
    plugins=plugins,
)

explanation_runner = InMemoryRunner(
    app_name="agents_explain",
    agent=explanation_agent,
    plugins=plugins,
)

# --------- Load CSV questions ----------
QUESTIONS_FILE = "questions.csv"
df = pd.read_csv(QUESTIONS_FILE)

# ---------- Restore state from URL query params ----------
params = st.query_params.to_dict()
# Keep track of current question, score, and state of the start button
if "current_q" not in st.session_state:
    st.session_state.current_q = int(params.get("current_q", [0])[0])
if "score" not in st.session_state:
    st.session_state.score = int(params.get("score", [0])[0])
if 'button' not in st.session_state:
    st.session_state.button = False
# For intro screen
if "name" not in st.session_state:
    st.session_state.name = params.get("name", "")
if "explain_ai" not in st.session_state:
    st.session_state.explain_ai = params.get("explain_ai", "True") == "True"
if "started" not in st.session_state:
    st.session_state.started = params.get("started", "False") == "True"

# Troubleshooting purposes
# print(str(st.session_state.current_q))
# print(str(st.session_state.score))
# print(str(st.session_state.button))
# print(str(st.session_state.name))
# print(str(st.session_state.explain_ai))
# print(str(st.session_state.started))

# --------- Streamlit UI ----------
st.set_page_config(page_title="QuAIzR - quiz system powered by AI Agents", page_icon="☁️", layout="centered")
# st.title("☁️ QuAIzR")
st.image("app.png") 
st.caption("Powered with Gemini and ADK")

# ---------- Intro screen ----------
if not st.session_state.started:
    st.subheader("👋 Welcome to the Google Cloud Quiz!")

    # Prefill name and toggle from session
    name_input = st.text_input("Enter your full name:", value=st.session_state.name)
    explain_toggle = st.toggle("Explain answers using AI assistant", value=str(st.session_state.explain_ai) == "True")
    
    # Update session state with name and explain ai toggle
    st.session_state.update({"name": name_input, "explain_ai": str(explain_toggle)})

    start_disabled = not st.session_state.name.strip()
    st.button("Start Quiz", type="primary", disabled=start_disabled, on_click=click_start_quiz)
    st.stop()

# --------- Quiz logic ----------
if st.session_state.current_q < len(df):
    q = df.iloc[st.session_state.current_q]

    # ---- Step 1: Create a permanent vote key for this question ----
    vote_key = f"hint_vote_q{st.session_state.current_q}"
    if vote_key not in st.session_state:
        st.session_state[vote_key] = None  # None = no vote yet
        
    st.subheader(f":orange[{q['question']}]")
    options = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
    user_choice = st.radio("Choose one:", options, index=None, disabled=st.session_state.button)

    # Hint related
    # ---------- Hint Box ----------
    if "show_hint" not in st.session_state:
        st.session_state.show_hint = False
    if "hint_text" not in st.session_state:
        st.session_state.hint_text = ""

    # --- Hint feedback storage ---
    if "hint_feedback" not in st.session_state:
        st.session_state.hint_feedback = []  # list of dicts
    if "hint_feedback_given" not in st.session_state:
        st.session_state.hint_feedback_given = False

    # Side bar
    with st.sidebar:
        # Statistics
        st.markdown("### :rainbow[Hey " + st.session_state.name + "!]")
        st.markdown(f":blue-background[Question {st.session_state.current_q + 1} of {str(len(df))}]")
        st.markdown(":streamlit: Your stats")
        st.markdown(f":blue-background[Score: {str(st.session_state.score)}]")
        
        # Hint section
        if not st.session_state.button:
            st.markdown("### 💡 Need a Hint?")
            if st.button("Get Hint"):
                st.session_state.show_hint = True
                # Get hint only if there was no hint prior
                if st.session_state.hint_text == "":
                    prompt = f"""As a GCP expert, provide a hint for this question.
                    Requirements:
                    - Do NOT reveal the answer
                    - Focus on the key concept being tested
                    - Keep it under 15 words
                    Question: '{q['question']}'"""
                    try:
                        with st.spinner("Fetching hint..."):
                            response = asyncio.run(hint_runner.run_debug(prompt))
                        st.session_state.hint_text = response[0].content.parts[0].text
                    except Exception as e:
                        st.session_state.hint_text = f"⚠️ Failed to fetch hint: {e}"

            if st.session_state.show_hint and st.session_state.hint_text:
                st.info("__Hint:__ " + st.session_state.hint_text)

                # ---- Hint Feedback Buttons ----
                vote_key = f"hint_vote_q{st.session_state.current_q}"

                if st.session_state[vote_key] is None:
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("👍 Useful", key=f"useful_btn_q{st.session_state.current_q}"):
                            st.session_state[vote_key] = True   # lock vote
                            store_hint_feedback(st, q["question"], st.session_state.hint_text, True)
                            st.rerun()  # 🚀 Prevents double vote

                    with col2:
                        if st.button("👎 Not Useful", key=f"notuseful_btn_q{st.session_state.current_q}"):
                            st.session_state[vote_key] = False  # lock vote
                            store_hint_feedback(st, q["question"], st.session_state.hint_text, False)
                            st.rerun()  # 🚀 Prevents double vote


    if user_choice and st.button("Submit Answer", on_click=click_button, disabled=st.session_state.button, type="primary"):

        # Clear hint when answer is submitted
        st.session_state.show_hint = False
        st.session_state.hint_text = ""
        st.session_state.hint_feedback_given = False
        
        correct_option = {"A": q["option_a"], "B": q["option_b"], "C": q["option_c"], "D": q["option_d"]}[q["correct_answer"]]
        is_correct = user_choice == correct_option

        # Ask Gemini for concise learning insight
        prompt = f"Explain why '{q['correct_text']}' is the correct choice in Google Cloud for the question '{q['question']}', in 2 concise sentences. Provide URL links to supporting documentation."

        if is_correct:
            st.success(icon="✅",body=f"Correct! {q['correct_text']} is the answer.")
            st.session_state.score += 1
        else:
            st.error(icon="❌",body=f"Incorrect. The correct answer is **{q['correct_text']}**.")
            st.info(icon="ℹ️",body=q["explanation"])
            prompt = f"Explain why '{user_choice}' is the incorrect choice in Google Cloud for the question '{q['question']}', in 2 concise sentences. Provide URL links to supporting documentation."

        # Enable Agent to explain
        if str(st.session_state.explain_ai) == "True":
            try:
                #response = asyncio.run(call_agent_async(prompt,runner,"agents","agents"))
                with st.spinner("___💭 Asking Gemini for insight...___"):
                    response = asyncio.run(explanation_runner.run_debug(prompt))
                # st.write("💡 Gemini insight:", response[0].content.parts[0].text)
                st.info(icon="💡",body=response[0].content.parts[0].text)
            except Exception as e:
                st.warning(icon="⚠️",body=f"Failed to fetch Gemini explanation: {e}")
        
        st.session_state.current_q += 1

        st.query_params.name=st.session_state.name
        st.query_params.explain_ai=str(st.session_state.explain_ai)
        st.query_params.current_q=str(st.session_state.current_q)
        st.query_params.score=str(st.session_state.score)
        st.query_params.started=str(st.session_state.started)

        st.button("Next Question", on_click=click_button)
        #st.button("Next Question", on_click=lambda: None)

else:
    st.success(icon="🎉",body="Quiz completed!")
    st.write(f"Your total score: **{st.session_state.score}/{len(df)}**")
    st.balloons()

    # ---- Save hint feedback automatically ----
    feedback_file = "hint_feedback.csv"

    if st.session_state.hint_feedback:
        feedback_df = pd.DataFrame(st.session_state.hint_feedback)

        # Write header only if file does not exist
        write_header = not os.path.exists(feedback_file)

        feedback_df.to_csv(
            feedback_file,
            mode='a',
            header=write_header,
            index=False
        )

        st.success("📁 Hint feedback saved to `hint_feedback.csv`")

    st.query_params.clear()
