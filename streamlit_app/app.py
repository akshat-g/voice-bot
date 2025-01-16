import streamlit as st
import requests
import json

# Define FastAPI URL (update as per your environment)
FASTAPI_URL = "http://127.0.0.1:8000"

st.title("Voice-Bot")

# Add an agent
st.header("Add an Agent")
name = st.text_input("Name")

try:
    # Create a text area for JSON input
    config = st.text_area("Configuration (JSON format)", height=200)
    
    if config:
        # Try to parse the JSON to validate it
        parsed_config = json.loads(config)
        
        # Display the beautified JSON
        st.code(json.dumps(parsed_config, indent=2), language="json")
        
        # Optional: Add a success message
        st.success("Valid JSON configuration")
except json.JSONDecodeError:
    if config:  # Only show error if user has entered something
        st.error("Invalid JSON format. Please check your input.")

if st.button("Add Agent"):
    try:
        # Parse the config string into a JSON object
        config_dict = json.loads(config) if config else {}
        
        response = requests.post(
            f"{FASTAPI_URL}/agent",
            json={"name": name, "config": config_dict},
        )
        if response.status_code == 200:
            st.success("Agent added successfully!")
        else:
            st.error(f"Error: {response.json()}")
    except Exception as e:
        st.error(f"Exception: {e}")

# List all agents
st.header("List of Agents")
if st.button("Fetch Agents"):
    try:
        response = requests.get(f"{FASTAPI_URL}/agent")
        if response.status_code == 200:
            agents = response.json()
            for agent in agents:
                st.write(f"Name: {agent['name']}")
        else:
            st.error(f"Error: {response.json()}")
    except Exception as e:
        st.error(f"Exception: {e}")
