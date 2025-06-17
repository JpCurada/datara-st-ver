import streamlit as st

def admin_dashboard_page():
    st.title("Admin Dashboard")
    st.write(st.session_state)
    