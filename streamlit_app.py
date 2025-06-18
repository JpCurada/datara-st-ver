# streamlit_app.py - Enhanced version with complete functionality and persistent auth
import streamlit as st
import os
import interfaces as pg
from utils.auth import is_authenticated, is_admin, is_scholar, get_current_user, logout

st.set_page_config(
    page_title="DaTARA - Data Science Scholarship Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize authentication state on startup
from utils.auth import init_auth_state
init_auth_state()

# Load custom CSS
parent_dir = os.path.dirname(os.path.abspath(__file__))
css_path = os.path.join(parent_dir, "static", "styles.css")

try:
    with open(css_path) as css:
        st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    # Fallback if CSS file not found
    pass

# Define all pages with enhanced structure
public_home = st.Page(page=pg.public_home_page, title='Home')
public_applications = st.Page(page=pg.public_applications_page, title='Apply Now')
public_scholar_login = st.Page(page=pg.public_scholar_login_page, title='Scholar Login')
public_admin_login = st.Page(page=pg.org_admin_login, title='Admin Login')

# Admin Pages
admin_dashboard = st.Page(page=pg.admin_dashboard_page, title='Dashboard')
admin_applications = st.Page(page=pg.admin_applications_page, title='Applications')
admin_scholars = st.Page(page=pg.admin_scholars_page, title='Scholars')
admin_moa = st.Page(page=pg.admin_moa_page, title='MoA Records')

# Scholar Pages
scholar_dashboard = st.Page(page=pg.scholar_dashboard_page, title='Dashboard')

# Helper function to create navigation buttons
def create_nav_button(page, label, is_current=False):
    """Create a styled navigation button"""
    button_type = "primary" if is_current else "secondary"
    return st.button(label, key=f"nav_{label}", use_container_width=True, type=button_type)

# Main navigation logic
if not is_authenticated():
    # === PUBLIC NAVIGATION ===
    pg_nav = st.navigation({
        "Public Access": [public_home, public_applications, public_scholar_login, public_admin_login]
    }, position="hidden")
    
    # Create custom top navigation bar
    with st.container():
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 2])
        
        with nav_col1:
            st.markdown("### DaTARA")
            st.caption("Data Science Scholarship Platform")
        
        with nav_col3:
            # Navigation buttons container
            with st.container():
                nav_buttons = st.columns(4)
                
                with nav_buttons[0]:
                    if st.button("Home", use_container_width=True):
                        st.switch_page(public_home)
                
                with nav_buttons[1]:
                    if st.button("Admin", use_container_width=True):
                        st.switch_page(public_admin_login)

                with nav_buttons[2]:
                    if st.button("Scholar", use_container_width=True):
                        st.switch_page(public_scholar_login)
                
                with nav_buttons[3]:
                    if st.button("Apply", use_container_width=True, type="primary"):
                        st.switch_page(public_applications)
        
        st.divider()

elif is_admin():
    # === ADMIN NAVIGATION ===
    user = get_current_user()
    
    # Handle case where user data might be None after refresh
    if not user:
        st.error("Session expired. Please log in again.")
        logout()
        st.rerun()
    
    partner_org_name = user['data']['partner_organizations']['display_name']
    admin_name = user['data']['first_name']
    
    pg_nav = st.navigation({
        f"{partner_org_name} Admin": [admin_dashboard, admin_applications, admin_moa, admin_scholars]
    })
    
    # Admin header with user info and navigation
    with st.container():
        header_col1, header_col2, header_col3 = st.columns([2, 2, 3])
        
        with header_col1:
            st.markdown(f"### Welcome, **{admin_name}**")
            st.caption(f"{partner_org_name} Admin")
        
        with header_col2:
            # Quick stats or notifications can go here
            st.info("Dashboard • Real-time updates")
        
        with header_col3:
            # Admin navigation buttons
            with st.container():
                admin_nav = st.columns(5)
                
                with admin_nav[0]:
                    if st.button("Dashboard", use_container_width=True):
                        st.switch_page(admin_dashboard)
                
                with admin_nav[1]:
                    if st.button("Applications", use_container_width=True):
                        st.switch_page(admin_applications)
                
                with admin_nav[2]:
                    if st.button("MoA", use_container_width=True):
                        st.switch_page(admin_moa)
                
                with admin_nav[3]:
                    if st.button("Scholars", use_container_width=True):
                        st.switch_page(admin_scholars)
                
                with admin_nav[4]:
                    if st.button("Logout", use_container_width=True, type="secondary"):
                        logout()
                        st.success("Logged out successfully!")
                        st.rerun()
        
        st.divider()

elif is_scholar():
    # === SCHOLAR NAVIGATION ===
    user = get_current_user()
    
    # Handle case where user data might be None after refresh
    if not user:
        st.error("Session expired. Please log in again.")
        logout()
        st.rerun()
    
    scholar_data = user['data']
    application_data = scholar_data['applications']
    scholar_name = application_data['first_name']
    scholar_id = user['scholar_id']
    
    pg_nav = st.navigation({
        f"Scholar Portal": [scholar_dashboard]
    })
    
    # Scholar header with info and navigation
    with st.container():
        scholar_header_col1, scholar_header_col2, scholar_header_col3 = st.columns([2, 2, 2])
        
        with scholar_header_col1:
            st.markdown(f"### Welcome, **{scholar_name}**")
            st.caption(f"Scholar ID: {scholar_id}")
        
        with scholar_header_col2:
            # Scholar status and program info
            if scholar_data['is_active']:
                st.success("Active Scholar")
            else:
                st.error("Account Inactive")
            st.caption(f"{scholar_data['partner_organizations']['display_name']} Program")
        
        with scholar_header_col3:
            # Scholar navigation buttons
            with st.container():
                scholar_nav = st.columns(4)
                
                with scholar_nav[0]:
                    if st.button("Home", use_container_width=True):
                        st.switch_page(scholar_dashboard)
                
                with scholar_nav[1]:
                    if st.button("Profile", use_container_width=True):
                        st.info("Profile page coming soon!")
                
                with scholar_nav[2]:
                    if st.button("Learning", use_container_width=True):
                        st.info("Learning portal coming soon!")
                
                with scholar_nav[3]:
                    if st.button("Logout", use_container_width=True, type="secondary"):
                        logout()
                        st.success("Logged out successfully!")
                        st.rerun()
        
        st.divider()

# Add a footer with system information
def add_footer():
    """Add footer with system info"""
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
    
    with footer_col1:
        if is_authenticated():
            user = get_current_user()
            if user:
                role = user['role'].title()
                st.caption(f"Logged in as {role}")
            else:
                st.caption("Session loading...")
    
    with footer_col2:
        st.caption("DaTARA Platform • Data Science Education for All")
    
    with footer_col3:
        st.caption("System Status: Online")

# Run the navigation
try:
    pg_nav.run()
    
    # Add footer to all pages
    add_footer()
    
except Exception as e:
    st.error(f"Navigation Error: {e}")
    st.info("Please refresh the page or contact support if the issue persists.")
    
    # Show debug info in expander
    with st.expander("Debug Information"):
        st.write(f"Error: {str(e)}")
        st.write(f"Authenticated: {is_authenticated()}")
        st.write(f"Admin: {is_admin()}")
        st.write(f"Scholar: {is_scholar()}")
        if is_authenticated():
            user = get_current_user()
            if user:
                st.write(f"User role: {user.get('role')}")
                st.write(f"User email: {user.get('email')}")
