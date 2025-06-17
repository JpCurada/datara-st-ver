# streamlit_app.py
import streamlit as st
import os
import interfaces as pg
from utils.auth import is_authenticated, is_admin, is_scholar, get_current_user, logout

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

# Define all pages
public_home = st.Page(page=pg.public_home_page, title='Home')
public_applications = st.Page(page=pg.public_applications_page, title='Applications')
public_scholar_login = st.Page(page=pg.public_scholar_login_page, title='Scholar Login')
public_admin_login = st.Page(page=pg.org_admin_login, title='Admin Login')

# Admin Pages
org_admin_dashboard = st.Page(page=pg.admin_dashboard_page, title='Admin Dashboard')
org_applications = st.Page(page=pg.admin_applications_page, title='Applications')
org_scholars = st.Page(page=pg.admin_scholars_page, title='Scholars')
org_moa = st.Page(page=pg.admin_moa_page, title='MoA')

# Scholar Pages
scholar_dashboard = st.Page(page=pg.scholar_dashboard_page, title='Scholar Dashboard')

# Authentication-based navigation
if not is_authenticated():
    # Public navigation for non-authenticated users
    pg_nav = st.navigation({
        "Public": [public_home, public_applications, public_scholar_login, public_admin_login]
    }, position="hidden")
    
    # Create a top navigation bar
    left_section, _, right_section = st.columns([2, 3, 3], gap='small', vertical_alignment='center')
    with right_section.container(border=True):
        nav_cols = st.columns(4)
        with nav_cols[0]:
            st.page_link(public_home, label="DaTARA")
        with nav_cols[1]:
            st.page_link(public_applications, label="Apply")
        with nav_cols[2]:
            st.page_link(public_scholar_login, label="Scholar")
        with nav_cols[3]:
            st.page_link(public_admin_login, label="Admin")

elif is_admin():
    # Admin navigation
    user = get_current_user()
    pg_nav = st.navigation({
        "Admin": [org_admin_dashboard, org_applications, org_scholars, org_moa]
    })
    
    # Admin top navigation with user info
    left_section, middle_section, right_section = st.columns([2, 2, 4], gap='small', vertical_alignment='center')
    
    with left_section:
        st.write(f"👋 Welcome, **{user['data']['first_name']}**")
        st.caption(f"Admin • {user['data']['partner_organizations']['display_name']}")
    
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
                logout()
                st.success("Logged out successfully!")
                st.rerun()

elif is_scholar():
    # Scholar navigation
    user = get_current_user()
    pg_nav = st.navigation({
        "Scholar": [scholar_dashboard]
    })
    
    # Scholar top navigation with user info
    left_section, middle_section, right_section = st.columns([2, 2, 4], gap='small', vertical_alignment='center')
    
    with left_section:
        application_data = user['data']['applications']
        st.write(f"👋 Welcome, **{application_data['first_name']}**")
        st.caption(f"Scholar • ID: {user['scholar_id']}")
    
    with right_section.container(border=True):
        nav_cols = st.columns(3)
        with nav_cols[0]:
            st.page_link(scholar_dashboard, label="Dashboard")
        with nav_cols[1]:
            st.write("Profile")  # Placeholder for future profile page
        with nav_cols[2]:
            if st.button("Logout", type="secondary", use_container_width=True):
                logout()
                st.success("Logged out successfully!")
                st.rerun()

# Run the navigation
pg_nav.run()