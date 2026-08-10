"""Streamlit entry point for the HACCP compliance assistant."""

import streamlit as st

# Must be the first Streamlit call in the script.

st.set_page_config(page_title="HACCP Compliance Assistant", page_icon="🥗")

st.title("HACCP Compliance Assistant")

# Returns "" while the field is empty.

question = st.text_input("Ask a food safety compliance question")

if question: 
    #Placeholder until retrieval and generation are wired up.
    st.write("answer goes here")