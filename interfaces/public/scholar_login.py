# interfaces/public/scholar_login.py - Enhanced with unified login
import streamlit as st
from utils.auth import unified_scholar_login, is_authenticated, is_scholar, is_approved_applicant
from datetime import date

def public_scholar_login_page():
    # Redirect if already authenticated
    if is_authenticated():
        user = st.session_state.user_data
        if is_scholar():
            st.success("Already logged in as scholar!")
            return
        elif is_approved_applicant():
            st.success("Already logged in as approved applicant!")
            return


    _,login_col, info_col, _ = st.columns([1,2, 3, 1], gap="medium")

    with login_col:
        with st.form("scholar_login_form", clear_on_submit=False, border=True):
            st.title("Scholar & Approved Applicant Login")

            scholar_id = st.text_input(
                "DaTARA ID", 
                placeholder="SCH12345678 or APP12345678",
                help="Your Scholar ID (SCH...) or Approved Applicant ID (APP...)"
            )
            email = st.text_input(
                "Email", 
                placeholder="your.email@example.com",
                help="The email address you used in your application"
            )

            min_date = date.today().replace(year=date.today().year - 16)
            birth_date = st.date_input(
                "Date of Birth", 
                min_value=date(1900, 1, 1), 
                max_value=min_date,
                help="Your birth date as provided in your application"
            )

            submit_button = st.form_submit_button("Login", use_container_width=True)

            if submit_button:
                if not scholar_id or not email or not birth_date:
                    st.error("Please fill in all fields")
                elif not (scholar_id.startswith("SCH") or scholar_id.startswith("APP")):
                    st.error("Please enter a valid ID (format: SCH12345678 or APP12345678)")
                elif len(scholar_id) != 11:
                    st.error("ID must be 11 characters (3 letters + 8 digits)")
                else:
                    with st.spinner("Verifying credentials..."):
                        if unified_scholar_login(scholar_id, email, str(birth_date)):
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please check your ID, email, and birth date.")

    with info_col.container(border=False):
        st.write("""
        **To access your account:**
        1. Enter your DaTARA ID (Scholar or Approved Applicant)
        2. Use the same email from your application
        3. Enter your birth date
        
        **Account Types:**
        - **Scholar ID (SCH...)**: Active scholars with full access
        - **Approved Applicant ID (APP...)**: Recently approved applicants who need to submit MoA
        
        **Don't have an ID?**
        - Only approved applicants receive IDs
        - Check your email for your ID
        - Apply through the Applications page if you haven't yet
        """)
        
        forget_col, need_help_col = st.columns([1, 1])

        with forget_col.expander("Forgot your ID?"):
            st.write("""
            **If you can't find your ID:**
            - Check your email inbox for "DaTARA Application Approved"
            - Look for emails from your partner organization
            - Contact support with your application email
            
            **ID Formats:**
            - Scholar ID: SCH followed by 8 digits
            - Approved Applicant ID: APP followed by 8 digits
            """)
        
        with need_help_col.expander("Need Help?"):
            st.write("""
            **Common Issues:**
            - Make sure to use the exact email from your application
            - Birth date must match your application exactly
            - IDs are case sensitive
            - Contact support if you continue having issues
            
            **Support:** support@datara.org
            """)