import streamlit as st
from css import apply_css
from tabs.add_agent import add_agent_tab
from tabs.list_agents import list_agents_tab


# Define FastAPI URL
FASTAPI_URL = "http://127.0.0.1:8000"

# Page Configuration
st.set_page_config(page_title="Voice-Bot Manager", layout="wide", initial_sidebar_state="expanded")

# Apply custom CSS
st.markdown(apply_css(), unsafe_allow_html=True)

# Tabs for the application
tab1, tab2 = st.tabs(["Add Agent", "List of Agents"])

# Add Agent Tab
with tab1:
    add_agent_tab(FASTAPI_URL)

# List of Agents Tab
with tab2:
    list_agents_tab(FASTAPI_URL)
