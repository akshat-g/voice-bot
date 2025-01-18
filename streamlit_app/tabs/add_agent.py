import streamlit as st
import requests
import json  # Import for JSON validation

def add_agent_tab(fastapi_url):
    """Render the Add Agent tab."""
    st.header("Add an Agent")
    st.subheader("Create a new agent with its configuration.")

    # Input fields for agent details
    name = st.text_input("Name", placeholder="Enter agent name")
    config = st.text_area("Configuration (JSON format)", placeholder='{ "key": "value" }')

    # Validate JSON configuration only if the input is not empty
    valid_json = None  # Initialize as None
    if config.strip():  # Check if the user entered something
        try:
            valid_json = json.loads(config)  # Validate JSON input
            st.success("Valid JSON configuration")
        except json.JSONDecodeError:
            st.error("Invalid JSON configuration. Please correct it.")

    # Button to add agent
    if st.button("Add Agent"):
        if not name.strip():
            st.error("Name cannot be empty.")
        elif not valid_json:
            st.error("Please provide a valid JSON configuration.")
        else:
            try:
                response = requests.post(f"{fastapi_url}/agent", json={"name": name, "config": valid_json})
                if response.status_code == 200:
                    st.success("Agent added successfully!")
                else:
                    st.error(f"Error: {response.json()}")
            except Exception as e:
                st.error(f"Exception: {e}")
