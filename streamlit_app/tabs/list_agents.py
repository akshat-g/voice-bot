import streamlit as st
import requests


def list_agents_tab(fastapi_url):
    """Render the List of Agents tab."""
    st.header("List of Agents")
    st.subheader("View and interact with agents.")

    # Layout with two vertical columns
    col1, col2 = st.columns([1, 1])  # Left (agents) and right (chat interface)

    # Fetch agents and display in the left column
    with col1:
        st.subheader("Agents List")
        if st.button("Fetch Agents"):
            try:
                response = requests.get(f"{fastapi_url}/agent")
                if response.status_code == 200:
                    agents = response.json()
                    if agents:
                        st.markdown("<div class='tab-container'>", unsafe_allow_html=True)
                        for agent in agents:
                            st.markdown(
                                f"""
                                <div class='agent-card'>
                                    <b>Agent Name:</b> {agent['name']}<br>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("No agents found. Please add an agent first.")
                else:
                    st.error(f"Error: {response.json()}")
            except Exception as e:
                st.error(f"Exception: {e}")

    # Chat functionality in the right column
    with col2:
        st.subheader("Chat with Agent")
        chat_agent_name = st.text_input("Enter Agent Name", placeholder="Type agent name here")
        if st.button("Start Chat"):
            if chat_agent_name.strip():
                st.write(f"Chatting with agent: {chat_agent_name}")
            else:
                st.error("Please enter an agent name to chat.")
