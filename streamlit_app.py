import streamlit as st
import os
import interfaces as pg
from utils.db import get_supabase_client


st.set_page_config(
    page_title="DaTARA",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Use forward slashes for paths to ensure compatibility with Docker
parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "assets", "images", "seekliyab-logo.png")
css_path = os.path.join(parent_dir, "assets", "styles.css")

# Load custom CSS
with open(css_path) as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

supabase = get_supabase_client()

# Public Pages
public_home = st.Page(page=pg.public_home_page, title='Home')
public_applications = st.Page(page=pg.public_applications_page, title='Applications')
public_scholar_login = st.Page(page=pg.public_scholar_login_page, title='Scholar Login')
public_admin_login = st.Page(page=pg.org_admin_login, title='Admin Login')

# Admin Pages
org_admin_dashboard = st.Page(page=pg.admin_dashboard_page, title='Admin Dashboard')
org_applications = st.Page(page=pg.admin_applications_page, title='Appliants')
org_scholars = st.Page(page=pg.admin_scholars_page, title='Scholars')
org_moa = st.Page(page=pg.admin_moa_page, title='MoA')

# Scholar Pages
scholar_dashboard = st.Page(page=pg.scholar_dashboard_page, title='Scholar Dashboard')

# Example: Use st.user.is_logged_in for authentication status
if supabase.auth.get_user() is None:
    # Hide the default navigation but make pages available
    pg = st.navigation([public_home, public_applications, public_scholar_login, 
                        public_admin_login, org_admin_dashboard, org_applications, 
                        org_scholars, org_moa, scholar_dashboard], position="hidden")
   
    # Create a top navigation bar with right alignment
    left_section, _, right_section = st.columns([2, 3, 3], gap='small', vertical_alignment='center')
    with right_section.container(border=True):
        nav_cols = st.columns(3)
        with nav_cols[0]:
            st.page_link(public_home, label="DaTARA")
        with nav_cols[1]:
            st.page_link(public_scholar_login, label="Scholar")
        with nav_cols[2]:
            st.page_link(public_applications, label="Apply")

elif supabase.auth.get_user() :
    # Show all pages if authenticated and authorized
    pg = st.navigation([org_admin_dashboard, org_applications, org_scholars, org_moa])

    st.write(supabase.auth.get_user())

    # Create a top navigation bar with right alignment
    left_section, _, right_section = st.columns([2, 3, 3], gap='small', vertical_alignment='center')
    with right_section.container(border=True):
        nav_cols = st.columns(5)
        with nav_cols[0]:
            st.page_link(org_admin_dashboard, label="Dashboard")
        with nav_cols[1]:
            st.page_link(org_applications, label="Applications")
        with nav_cols[2]:
            st.page_link(org_moa, label="MoA Records")
        with nav_cols[3]:
            st.page_link(org_scholars, label="Scholars")
        with nav_cols[4]:
            if st.button("Logout", type="secondary", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith("user_") or key in ["authenticated", "admin_user", "user_email"]:
                        del st.session_state[key]
                # Sign out from Supabase
                try:
                    supabase.auth.sign_out()
                    st.page_link(public_home, label="Home")
                except:
                    pass  # Ignore errors during sign out
                st.success("Logged out successfully!")
                st.rerun()
        






pg.run()