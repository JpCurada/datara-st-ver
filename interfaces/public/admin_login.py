import streamlit as st
import time
from utils.db import get_supabase_client

supabase = get_supabase_client()

def org_admin_login():

    # Check if authentication is required first
    if "auth_required" in st.session_state and st.session_state.auth_required:
        # Clear the flag to prevent infinite loops
        st.session_state.pop("auth_required")


    st.title("Admin Login")

    _, login_col, _ = st.columns([1, 3, 1])
    with login_col:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.success("Login successful")
                    st.write(response)
                    # Optionally, store login state in session_state
                    st.user.is_logged_in = True
                    st.session_state["user_email"] = email
                except Exception as e:
                    st.error(f"Error: {e}")