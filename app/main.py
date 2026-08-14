"""Streamlit entry point for the HACCP compliance assistant."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.db import init_db, save_conversation, save_feedback
from src.rag import rag

st.set_page_config(page_title="HACCP Compliance Assistant", page_icon="🥗")

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

st.title("HACCP Compliance Assistant")

question = st.text_input("Ask a food safety compliance question")

if question and question != st.session_state.get("last_question"):
    with st.spinner("Searching regulations and generating answer..."):
        result = rag(question)

    st.session_state.last_question = question
    st.session_state.last_result = result
    st.session_state.conversation_id = save_conversation(question, result)
    st.session_state.feedback_sent = False

if question and question == st.session_state.get("last_question"):
    result = st.session_state.last_result

    st.write(result["answer"])
    st.caption(
        f"Model: {result['model_used']} · {result['response_time']:.1f}s · "
        f"Relevance: {result['relevance']}"
    )

    if st.session_state.feedback_sent:
        st.caption("Thanks for the feedback!")
    else:
        col1, col2 = st.columns(2)
        if col1.button("👍 Helpful"):
            save_feedback(st.session_state.conversation_id, 1)
            st.session_state.feedback_sent = True
            st.rerun()
        if col2.button("👎 Not helpful"):
            save_feedback(st.session_state.conversation_id, -1)
            st.session_state.feedback_sent = True
            st.rerun()
