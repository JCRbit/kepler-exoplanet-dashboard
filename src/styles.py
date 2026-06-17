"""
Corporate CSS styles and color palettes module for the Dashboard.
"""
import streamlit as st

# Reusable global color palettes for charts and layouts
SCATTER_COLORS = {
    "Falso Positivo": "rgba(55, 75, 95, 0.5)",   
    "Candidato": "rgba(242, 201, 76, 0.85)",     
    "Confirmado": "rgba(76, 195, 185, 0.95)"    
}

EXECUTIVE_COLORS = ["#4cc3b9", "#3da5c2", "#5c6bc0", "#ab47bc", "#ec407a"]

def inject_custom_css():
    """Injects custom CSS code into the Streamlit session."""
    st.markdown("""
        <style>
        .main { 
            background-color: #0d1624 !important; 
            color: #f0f6fc !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        }
        [data-testid="stAppViewContainer"] {
            background-color: #0d1624;
        }
        [data-testid="stSidebar"] {
            background-color: #090e18 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        /* Modifying filters (Multiselect) from red to blue/turquoise */
        div[data-baseweb="tag"] {
            background-color: rgba(76, 195, 185, 0.15) !important;
            border: 1px solid rgba(76, 195, 185, 0.4) !important;
            border-radius: 4px !important;
        }
        div[data-baseweb="tag"] span {
            color: #ffffff !important;
        }
        div[data-baseweb="tag"] svg {
            fill: #4cc3b9 !important;
        }
        div[data-baseweb="tag"] button:hover, 
        div[data-baseweb="tag"] [role="button"]:hover {
            background-color: rgba(76, 195, 185, 0.3) !important;
        }
        div[data-baseweb="tag"] button:hover svg, 
        div[data-baseweb="tag"] [role="button"]:hover svg {
            fill: #ffffff !important;
        }
        div[data-baseweb="select"] > div:focus-within {
            border-color: #4cc3b9 !important;
            box-shadow: 0 0 0 1px #4cc3b9 !important;
        }
        
        .executive-card {
            background-color: #1a263b !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px; 
            padding: 24px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            margin-bottom: 20px;
        }
        [data-testid="stSubcontainer"] {
            background-color: #1a263b !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            padding: 24px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
            margin-bottom: 20px !important;
        }
        .kpi-label { color: #8b949e; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .kpi-val { color: #ffffff; font-size: 36px; font-weight: 700; letter-spacing: -0.5px; }
        h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
        </style>
        """, unsafe_allow_html=True)