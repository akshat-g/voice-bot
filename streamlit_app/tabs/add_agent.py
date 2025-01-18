import streamlit as st
import requests

def add_agent_tab(fastapi_url):
    """Render the Add Agent tab."""
    st.header("Add an Agent")
    st.subheader("Create a new agent with its configuration.")

    # Input fields for agent details
    name = st.text_input("Name", placeholder="Enter agent name")
    config = st.text_area("Configuration (JSON format)", placeholder='{ "key": "value" }')

    # Validate JSON configuration
    try:
        valid_json = eval(config)  # You may replace this with `json.loads` for stricter parsing
        st.success("Valid JSON configuration")
    except Exception:
        valid_json = None
        st.error("Invalid JSON configuration. Please correct it.")

    # Button to add agent
    if st.button("Add Agent") and valid_json:
        try:
            response = requests.post(f"{fastapi_url}/agent", json={"name": name, "config": valid_json})
            if response.status_code == 200:
                st.success("Agent added successfully!")
            else:
                st.error(f"Error: {response.json()}")
        except Exception as e:
            st.error(f"Exception: {e}")