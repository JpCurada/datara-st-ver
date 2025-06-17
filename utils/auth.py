# utils/auth.py - Enhanced version with additional functionality
import streamlit as st
from utils.db import get_supabase_client
from typing import Optional, Dict, Any, Literal


def get_user_role_and_data(user_email: str) -> Optional[Dict[str, Any]]:
    """
    Check if user is admin or scholar and return role with data
    
    Returns:
        dict: {
            'role': 'admin' | 'scholar' | None,
            'data': user_specific_data,
            'partner_org_id': UUID (for both admin and scholar),
            'permissions': list of permissions
        }
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
            # Check if partner org is also active
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
        
        # Filter scholars by email since we need to join through applications
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
        # First authenticate with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        
        if response.user:
            # Get user role and data
            user_role_data = get_user_role_and_data(email)
            
            if user_role_data:
                # Store in session state
                st.session_state.user_data = {
                    'auth_user': response.user,
                    'role': user_role_data['role'],
                    'data': user_role_data['data'],
                    'partner_org_id': user_role_data['partner_org_id'],
                    'permissions': user_role_data['permissions'],
                    'email': email
                }
                return st.session_state.user_data
            else:
                # User exists in auth but not in admin/scholar tables
                supabase.auth.sign_out()
                return None
                
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return 'user_data' in st.session_state and st.session_state.user_data is not None


def is_admin() -> bool:
    """Check if current user is an admin"""
    return (is_authenticated() and 
            st.session_state.user_data.get('role') == 'admin')


def is_scholar() -> bool:
    """Check if current user is a scholar"""
    return (is_authenticated() and 
            st.session_state.user_data.get('role') == 'scholar')


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user data"""
    if is_authenticated():
        return st.session_state.user_data
    return None


def get_user_partner_org() -> Optional[str]:
    """Get current user's partner organization ID"""
    user = get_current_user()
    if user:
        return user.get('partner_org_id')
    return None


def has_permission(permission: str) -> bool:
    """Check if current user has specific permission"""
    user = get_current_user()
    if user:
        return permission in user.get('permissions', [])
    return False


def logout():
    """Log out current user"""
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
    except:
        pass  # Ignore errors during sign out
    
    # Clear session state
    for key in list(st.session_state.keys()):
        if key.startswith("user_") or key in ["authenticated", "user_data"]:
            del st.session_state[key]


def require_auth(role: Optional[Literal['admin', 'scholar']] = None):
    """
    Decorator/function to require authentication
    Optionally require specific role
    """
    if not is_authenticated():
        st.error("🔒 Please log in to access this page.")
        st.info("Use the navigation menu to access the login page.")
        st.stop()
    
    if role and get_current_user().get('role') != role:
        st.error(f"❌ Access denied. {role.title()} role required.")
        st.info("You don't have permission to access this page.")
        st.stop()


def scholar_login_auth(scholar_id: str, email: str, birth_date: str) -> bool:
    """
    Special authentication for scholars using ID, email, and birth date
    """
    supabase = get_supabase_client()
    
    try:
        # Query scholar with application data
        response = supabase.table("scholars").select(
            "scholar_id, partner_org_id, is_active, created_at, "
            "applications!inner(email, birthdate, first_name, last_name), "
            "partner_organizations!inner(display_name)"
        ).eq("scholar_id", scholar_id).eq("is_active", True).execute()
        
        if response.data:
            scholar_data = response.data[0]
            application_data = scholar_data['applications']
            
            # Verify email and birth date
            if (application_data['email'].lower() == email.lower() and 
                str(application_data['birthdate']) == str(birth_date)):
                
                # Store in session state
                st.session_state.user_data = {
                    'auth_user': None,  # No Supabase auth user for scholar login
                    'role': 'scholar',
                    'data': scholar_data,
                    'partner_org_id': scholar_data['partner_org_id'],
                    'permissions': ['view_profile', 'update_profile', 'submit_moa', 'view_certifications'],
                    'email': email,
                    'scholar_id': scholar_id
                }
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Scholar login failed: {e}")
        return False


def create_admin_user(email: str, password: str, first_name: str, last_name: str, partner_org_name: str) -> bool:
    """
    Create a new admin user (for system administration)
    This would typically be called by a super admin or during setup
    """
    supabase = get_supabase_client()
    
    try:
        # Get partner organization ID
        org_response = supabase.table("partner_organizations").select("partner_org_id").eq("display_name", partner_org_name).execute()
        
        if not org_response.data:
            st.error(f"Partner organization '{partner_org_name}' not found")
            return False
        
        partner_org_id = org_response.data[0]["partner_org_id"]
        
        # Create auth user with metadata
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "user_metadata": {
                "first_name": first_name,
                "last_name": last_name,
                "partner_org": partner_org_name
            }
        })
        
        if auth_response.user:
            st.success(f"✅ Admin user created successfully for {partner_org_name}")
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Error creating admin user: {e}")
        return False


def check_approved_applicant_status(email: str) -> Optional[Dict[str, Any]]:
    """
    Check if an email belongs to an approved applicant who needs to submit MoA
    Returns applicant data if found, None otherwise
    """
    supabase = get_supabase_client()
    
    try:
        # Check if email belongs to an approved applicant
        response = supabase.table("approved_applicants").select(
            "approved_applicant_id, application_id, "
            "applications!inner(email, first_name, last_name, partner_org_id, status), "
            "moa_submissions(moa_id, status)"
        ).eq("applications.email", email).eq("applications.status", "APPROVED").execute()
        
        if response.data:
            applicant_data = response.data[0]
            # Check if MoA has not been submitted yet
            if not applicant_data.get('moa_submissions'):
                return applicant_data
        
        return None
        
    except Exception as e:
        st.error(f"Error checking approved applicant status: {e}")
        return None


def get_scholar_moa_status(scholar_id: str) -> Optional[str]:
    """
    Get the MoA status for a scholar
    Returns: 'PENDING', 'SUBMITTED', 'APPROVED', or None
    """
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("scholars").select(
            "moa_submissions!inner(status)"
        ).eq("scholar_id", scholar_id).execute()
        
        if response.data and response.data[0].get('moa_submissions'):
            return response.data[0]['moa_submissions']['status']
        
        return None
        
    except Exception as e:
        st.error(f"Error getting MoA status: {e}")
        return None