# interfaces/public/scholar_login.py
import streamlit as st
from utils.auth import scholar_login_auth, is_authenticated, is_scholar

def public_scholar_login_page():
    # Redirect if already authenticated as scholar
    if is_authenticated() and is_scholar():
        st.success("Already logged in as scholar!")
        return

    st.title("Scholar Login")

    login_col, _, info_col = st.columns([2, 1, 2])
    
    with login_col:
        with st.form("scholar_login_form", clear_on_submit=False):
            scholar_id = st.text_input(
                "DaTARA Scholar ID", 
                placeholder="SCH12345678",
                help="Your unique scholar ID (starts with SCH followed by 8 digits)"
            )
            email = st.text_input(
                "Email", 
                placeholder="your.email@example.com",
                help="The email address you used in your application"
            )
            birth_date = st.date_input(
                "Birth Date",
                help="Your birth date as provided in your application"
            )

            submit_button = st.form_submit_button("Login", use_container_width=True)

            if submit_button:
                if not scholar_id or not email or not birth_date:
                    st.error("Please fill in all fields")
                elif not scholar_id.startswith("SCH") or len(scholar_id) != 11:
                    st.error("Please enter a valid Scholar ID (format: SCH12345678)")
                else:
                    with st.spinner("Verifying credentials..."):
                        if scholar_login_auth(scholar_id, email, str(birth_date)):
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please check your Scholar ID, email, and birth date.")

    with info_col:
        st.info("ℹ️ **Scholar Login**")
        st.write("""
        **To access your scholar account:**
        1. Enter your DaTARA Scholar ID
        2. Use the same email from your application
        3. Enter your birth date
        
        **Don't have a Scholar ID?**
        - Only approved applicants receive Scholar IDs
        - Check your email for your Scholar ID
        - Apply through the Applications page if you haven't yet
        """)
        
        with st.expander("Forgot your Scholar ID?"):
            st.write("""
            **If you can't find your Scholar ID:**
            - Check your email inbox for "DaTARA Scholar Approval"
            - Look for emails from your partner organization
            - Contact support with your application email
            
            **Scholar ID Format:** SCH followed by 8 digits
            """)