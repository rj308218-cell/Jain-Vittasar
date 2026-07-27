import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables (Streamlit secrets or .env)
load_dotenv()

# Fetch Supabase keys safely (supports Streamlit secrets if hosted online)
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("Jain Vittasar - Financial Intelligence & Billing (Cloud Edition)")

# Example Streamlit connection verification widget
try:
    response = supabase.table("inventory").select("id").limit(1).execute()
    st.success("Connected to Supabase cloud database successfully!")
except Exception as e:
    st.error(f"Supabase connection error: {e}")
