def apply_css():
    """Apply custom CSS styling to the Streamlit app."""
    css = """
    <style>
    .css-18e3th9 {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        padding: 0.5rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .tab-container {
        background-color: #20232a;
        padding: 1rem;
        border-radius: 10px;
    }
    .agent-card {
        background-color: #282c34;
        border: 1px solid #4CAF50;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        color: white;
    }
    </style>
    """
    return css