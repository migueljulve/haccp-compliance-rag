"""Streamlit entry point for the HACCP compliance assistant."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.rag import rag

st.set_page_config(page_title="HACCP Compliance Assistant", page_icon="🥗")

st.title("HACCP Compliance Assistant")

question = st.text_input("Ask a food safety compliance question")

if question:
    with st.spinner("Searching regulations and generating answer..."):
        result = rag(question)

    st.write(result["answer"])
    st.caption(f"Model: {result['model_used']} · {result['response_time']:.1f}s · Relevance: {result['relevance']}")
