# utils/auth.py - Fixed authentication with correct table relationships
import streamlit as st
from utils.db import get_supabase_client
from typing import Optional, Dict, Any, Literal
import json
import time


def init_auth_state():
    """Initialize authentication state if not exists"""
    if 'auth_initialized' not in st.session_state:
        st.session_state.auth_initialized = True
        st.session_state.user_data = None
        st.session_state.auth_timestamp = None
        
        # Try to restore session from Supabase session
        restore_supabase_session()


def save_auth_session(user_data: Dict[str, Any]):
    """Save authentication session"""
    st.session_state.user_data = user_data
    st.session_state.auth_timestamp = time.time()


def clear_auth_session():
    """Clear authentication session"""
    keys_to_clear = [
        'user_data', 'auth_timestamp', 'auth_session_token', 
        'scholar_id', 'authenticated', 'auth_initialized'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def restore_supabase_session():
    """Attempt to restore authentication session from Supabase"""
    try:
        supabase = get_supabase_client()
        session = supabase.auth.get_session()
        
        if session and session.user:
            user_email = session.user.email
            user_role_data = get_user_role_and_data(user_email)
            
            if user_role_data:
                session_data = {
                    'auth_user': session.user,
                    'role': user_role_data['role'],
                    'data': user_role_data['data'],
                    'partner_org_id': user_role_data['partner_org_id'],
                    'permissions': user_role_data['permissions'],
                    'email': user_email
                }
                
                st.session_state.user_data = session_data
                st.session_state.auth_timestamp = time.time()
                return True
    
    except Exception:
        pass
    
    return False


def get_user_role_and_data(user_email: str) -> Optional[Dict[str, Any]]:
    """
    Check if user is admin or scholar and return role with data
    """
    supabase = get_supabase_client()
    
    try:
        # Check if user is an admin
        admin_response = supabase.table("admins").select(
            "admin_id, partner_org_id, email, first_name, last_name, is_active, "
            "partner_organizations(display_name, is_active)"
        ).eq("email", user_email).eq("is_active", True).execute()
        
        if admin_response.data and len(admin_response.data) > 0:
            admin_data = admin_response.data[0]
            partner_org = admin_data.get('partner_organizations')
            if partner_org and partner_org.get('is_active'):
                return {
                    'role': 'admin',
                    'data': admin_data,
                    'partner_org_id': admin_data['partner_org_id'],
                    'permissions': ['view_applications', 'review_applications', 'view_scholars', 'view_moa']
                }
        
        # Check if user is a scholar
        scholar_response = supabase.table("scholars").select(
            "scholar_id, partner_org_id, is_active, created_at, "
            "applications(email, first_name, last_name, birthdate), "
            "partner_organizations(display_name, is_active)"
        ).eq("is_active", True).execute()
        
        if scholar_response.data:
            for scholar in scholar_response.data:
                applications = scholar.get('applications')
                if applications and applications.get('email') == user_email:
                    partner_org = scholar.get('partner_organizations')
                    if partner_org and partner_org.get('is_active'):
                        return {
                            'role': 'scholar',
                            'data': scholar,
                            'partner_org_id': scholar['partner_org_id'],
                            'permissions': ['view_profile', 'update_profile', 'submit_moa', 'view_certifications']
                        }
        
        return None
        
    except Exception as e:
        st.error(f"Error checking user role: {e}")
        return None


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user and return user data with role
    """
    supabase = get_supabase_client()
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        
        if response.user:
            user_role_data = get_user_role_and_data(email)
            
            if user_role_data:
                session_data = {
                    'auth_user': response.user,
                    'role': user_role_data['role'],
                    'data': user_role_data['data'],
                    'partner_org_id': user_role_data['partner_org_id'],
                    'permissions': user_role_data['permissions'],
                    'email': email
                }
                
                st.session_state.user_data = session_data
                st.session_state.auth_timestamp = time.time()
                
                return session_data
            else:
                supabase.auth.sign_out()
                return None
                
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None


def unified_scholar_login(identifier: str, email: str, birth_date: str) -> bool:
    """
    Unified login for both scholars and approved applicants
    """
    supabase = get_supabase_client()
    
    try:
        # First check if it's a scholar ID (starts with SCH)
        if identifier.startswith("SCH"):
            return scholar_login_auth(identifier, email, birth_date)
        
        # Otherwise check if it's an approved applicant ID (starts with APP)
        elif identifier.startswith("APP"):
            return approved_applicant_login_auth(identifier, email, birth_date)
        
        else:
            st.error("Invalid ID format. Use Scholar ID (SCH...) or Approved Applicant ID (APP...)")
            return False
            
    except Exception as e:
        st.error(f"Login failed: {e}")
        return False


def scholar_login_auth(scholar_id: str, email: str, birth_date: str) -> bool:
    """
    Authentication for scholars using ID, email, and birth date
    """
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("scholars").select(
            "scholar_id, partner_org_id, is_active, created_at, "
            "applications!inner(email, birthdate, first_name, last_name, country, education_status, institution_name, institution_country, state_region_province, city, postal_code), "  # Add empty fields in needed
            "partner_organizations!inner(display_name)"
        ).eq("scholar_id", scholar_id).eq("is_active", True).execute()
        
        if response.data:
            scholar_data = response.data[0]
            application_data = scholar_data['applications']
            
            # Verify email and birth date
            if (application_data['email'].lower() == email.lower() and 
                str(application_data['birthdate']) == str(birth_date)):
                
                session_data = {
                    'auth_user': None,
                    'role': 'scholar',
                    'data': scholar_data,
                    'partner_org_id': scholar_data['partner_org_id'],
                    'permissions': ['view_profile', 'update_profile', 'submit_moa', 'view_certifications'],
                    'email': email,
                    'scholar_id': scholar_id
                }
                
                st.session_state.user_data = session_data
                st.session_state.auth_timestamp = time.time()
                
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Scholar login failed: {e}")
        return False


def approved_applicant_login_auth(approved_applicant_id: str, email: str, birth_date: str) -> bool:
    """
    Authentication for approved applicants using ID, email, and birth date
    FIXED: Correct table relationships
    """
    supabase = get_supabase_client()
    
    try:
        # Fixed query: Use proper table relationships
        response = supabase.table("approved_applicants").select(
            """
            approved_applicant_id, application_id, created_at,
            applications!inner(
                email, birthdate, first_name, last_name, country, education_status, institution_name, institution_country, state_region_province, city, postal_code,
                partner_org_id,
                partner_organizations!inner(display_name)
            )
            """
        ).eq("approved_applicant_id", approved_applicant_id).execute()
        
        if response.data:
            applicant_data = response.data[0]
            application_data = applicant_data['applications']
            
            # Verify email and birth date
            if (application_data['email'].lower() == email.lower() and 
                str(application_data['birthdate']) == str(birth_date)):
                
                # Check if they haven't become a scholar yet
                scholar_check = supabase.table("scholars").select("scholar_id").eq("application_id", applicant_data['application_id']).execute()
                
                if scholar_check.data:
                    # They're already a scholar, redirect them
                    st.error("You are already a scholar! Please use Scholar Login instead.")
                    st.info(f"Your Scholar ID: {scholar_check.data[0]['scholar_id']}")
                    return False
                
                # Create session data with correct structure
                session_data = {
                    'auth_user': None,
                    'role': 'approved_applicant',
                    'data': {
                        'approved_applicant_id': applicant_data['approved_applicant_id'],
                        'application_id': applicant_data['application_id'],
                        'created_at': applicant_data['created_at'],
                        'applications': application_data,
                        'partner_organizations': application_data['partner_organizations']
                    },
                    'partner_org_id': application_data['partner_org_id'],
                    'permissions': ['submit_moa', 'view_moa_status'],
                    'email': email,
                    'approved_applicant_id': approved_applicant_id
                }
                
                st.session_state.user_data = session_data
                st.session_state.auth_timestamp = time.time()
                
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Approved applicant login failed: {e}")
        return False


# Authentication state checks
def is_authenticated() -> bool:
    """Check if user is authenticated"""
    init_auth_state()
    
    if st.session_state.user_data and st.session_state.auth_timestamp:
        if time.time() - st.session_state.auth_timestamp < 86400:
            return True
        else:
            clear_auth_session()
    
    if restore_supabase_session():
        return True
    
    return False


def is_admin() -> bool:
    """Check if current user is an admin"""
    return (is_authenticated() and 
            st.session_state.user_data.get('role') == 'admin')


def is_scholar() -> bool:
    """Check if current user is a scholar"""
    return (is_authenticated() and 
            st.session_state.user_data.get('role') == 'scholar')


def is_approved_applicant() -> bool:
    """Check if current user is an approved applicant"""
    return (is_authenticated() and 
            st.session_state.user_data.get('role') == 'approved_applicant')


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user data"""
    if is_authenticated():
        return st.session_state.user_data
    return None


def logout():
    """Log out current user"""
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
    except:
        pass
    
    clear_auth_session()


def require_auth(role: Optional[Literal['admin', 'scholar', 'approved_applicant']] = None):
    """
    Require authentication with optional role check
    """
    init_auth_state()
    
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.info("Use the navigation menu to access the login page.")
        st.stop()
    
    if role and get_current_user().get('role') != role:
        st.error(f"Access denied. {role.replace('_', ' ').title()} role required.")
        st.info("You don't have permission to access this page.")
        st.stop()


# Auto-initialize auth state when module is imported
init_auth_state()