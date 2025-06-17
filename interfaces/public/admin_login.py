# interfaces/public/admin_login.py
import streamlit as st
from utils.auth import authenticate_user, is_authenticated, is_admin

def org_admin_login():
    # Redirect if already authenticated as admin
    if is_authenticated() and is_admin():
        st.success("Already logged in as admin!")
        return

    st.title("Admin Login")

    _, login_col, _ = st.columns([1, 3, 1])
    with login_col:
        with st.form("admin_login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please fill in all fields")
                    return
                
                with st.spinner("Authenticating..."):
                    user_data = authenticate_user(email, password)
                
                if user_data and user_data['role'] == 'admin':
                    st.success("Login successful!")
                    st.rerun()
                elif user_data and user_data['role'] == 'scholar':
                    st.error("This is a scholar account. Please use the scholar login.")
                else:
                    st.error("Invalid credentials or account not found in admin records.")

        st.divider()
        st.info("💡 **Admin accounts** are created by system administrators and linked to partner organizations.")
        
        with st.expander("Need help?"):
            st.write("""
            **Admin Login Issues:**
            - Contact your system administrator if you don't have admin credentials
            - Admin accounts must be pre-created and linked to a partner organization
            - If you're a scholar, use the Scholar Login instead
            """)