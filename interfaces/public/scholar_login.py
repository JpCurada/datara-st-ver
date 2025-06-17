import streamlit as st

def public_scholar_login_page():
    st.title("Scholar Login")

    login_col, _, _ = st.columns([1, 2, 2])
    with login_col.form("login_form", clear_on_submit=True, border=False):
        scholar_id = st.text_input("DaTARA ID")
        email = st.text_input("Email")
        birth_date = st.date_input("Birth Date")

        submit_button = st.form_submit_button("Login")

        if submit_button:
            if not scholar_id or not email or not birth_date:
                st.error("Please fill in all fields")
            else:
                st.success("Login successful")

        