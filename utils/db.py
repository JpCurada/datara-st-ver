import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_connection():
    url = st.secrets.connections.supabase["SUPABASE_URL"]
    key = st.secrets.connections.supabase["SUPABASE_KEY"]
    return create_client(url, key)

def get_supabase_client():
    return init_connection()
