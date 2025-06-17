# utils/queries.py
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import uuid
from utils.db import get_supabase_client


def check_email_in_scholars(email: str, partner_org: str) -> bool:
    """Check if email already exists as an active scholar for the given partner org"""
    supabase = get_supabase_client()
    try:
        # Get partner org ID first
        org_response = supabase.table("partner_organizations").select("partner_org_id").eq("display_name", partner_org).execute()
        if not org_response.data:
            return False
        
        partner_org_id = org_response.data[0]["partner_org_id"]
        
        # Check if email exists in scholars through applications
        scholar_response = supabase.table("scholars").select(
            "scholar_id, applications!inner(email)"
        ).eq("partner_org_id", partner_org_id).eq("is_active", True).execute()
        
        if scholar_response.data:
            for scholar in scholar_response.data:
                if scholar["applications"]["email"].lower() == email.lower():
                    return True
        return False
    except Exception as e:
        st.error(f"Error checking scholar email: {e}")
        return False


def check_email_in_applications(email: str, partner_org: str) -> Optional[str]:
    """Check if email already has an application for the given partner org"""
    supabase = get_supabase_client()
    try:
        # Get partner org ID first
        org_response = supabase.table("partner_organizations").select("partner_org_id").eq("display_name", partner_org).execute()
        if not org_response.data:
            return None
        
        partner_org_id = org_response.data[0]["partner_org_id"]
        
        # Check existing application
        app_response = supabase.table("applications").select("status").eq("email", email).eq("partner_org_id", partner_org_id).execute()
        
        if app_response.data:
            return app_response.data[0]["status"]
        return None
    except Exception as e:
        st.error(f"Error checking application email: {e}")
        return None


def get_active_partner_organizations() -> List[str]:
    """Get list of active partner organizations accepting applications"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("partner_organizations").select("display_name").eq("is_active", True).eq("is_accepting", True).execute()
        return [org["display_name"] for org in response.data]
    except Exception as e:
        st.error(f"Error fetching partner organizations: {e}")
        return ["DataCamp", "Coursera", "Udacity", "edX"]  # Fallback


def save_application_to_database(form_data: Dict[str, Any]) -> bool:
    """Save complete application to database"""
    supabase = get_supabase_client()
    
    try:
        # Get partner org ID
        org_response = supabase.table("partner_organizations").select("partner_org_id").eq(
            "display_name", form_data["Partner Organization & Data Privacy"]["partner_org"]
        ).execute()
        
        if not org_response.data:
            st.error("Partner organization not found")
            return False
        
        partner_org_id = org_response.data[0]["partner_org_id"]
        
        # Prepare application data
        step_data = form_data
        basic_info = step_data["Basic Information"]
        geo_details = step_data["Geographic Details"]
        edu_details = step_data["Education Details"]
        interest_details = step_data["Interest Details"]
        demo_details = step_data["Demographic and Connectivity"]
        
        # Insert main application
        application_data = {
            "partner_org_id": partner_org_id,
            "email": step_data["Partner Organization & Data Privacy"]["email"],
            "first_name": basic_info["first_name"],
            "middle_name": basic_info.get("middle_name"),
            "last_name": basic_info["last_name"],
            "birthdate": str(basic_info["birthdate"]),
            "gender": basic_info["gender"],
            "country": geo_details["country"],
            "state_region_province": geo_details["state"],
            "city": geo_details["city"],
            "postal_code": str(geo_details["postal"]),
            "education_status": edu_details["education_status"],
            "institution_country": edu_details["institution_country"],
            "institution_name": edu_details["institution_name"],
            "programming_experience": interest_details["programming_experience"],
            "data_science_experience": interest_details["data_science_experience"],
            "weekly_time_commitment": interest_details["time_commitment"],
            "scholarship_reason": interest_details["why_scholarship"],
            "career_goals": interest_details["career_goals"],
            "status": "PENDING"
        }
        
        app_response = supabase.table("applications").insert(application_data).execute()
        
        if not app_response.data:
            return False
        
        application_id = app_response.data[0]["application_id"]
        
        # Insert demographics
        for demo in demo_details["demographic"]:
            supabase.table("application_demographics").insert({
                "application_id": application_id,
                "demographic_group": demo
            }).execute()
        
        # Insert devices
        for device in demo_details["devices"]:
            supabase.table("application_devices").insert({
                "application_id": application_id,
                "device_type": device
            }).execute()
        
        # Insert connectivity
        for conn in demo_details["connectivity"]:
            supabase.table("application_connectivity").insert({
                "application_id": application_id,
                "connectivity_type": conn
            }).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error saving application: {e}")
        return False


def get_applications_for_admin(partner_org_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get applications for admin review"""
    supabase = get_supabase_client()
    try:
        query = supabase.table("applications").select(
            "application_id, email, first_name, last_name, status, applied_at, "
            "country, education_status, programming_experience, data_science_experience"
        ).eq("partner_org_id", partner_org_id)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        response = query.order("applied_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching applications: {e}")
        return []


def get_application_details(application_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed application information"""
    supabase = get_supabase_client()
    try:
        # Get main application data
        app_response = supabase.table("applications").select("*").eq("application_id", application_id).execute()
        
        if not app_response.data:
            return None
        
        application = app_response.data[0]
        
        # Get demographics
        demo_response = supabase.table("application_demographics").select("demographic_group").eq("application_id", application_id).execute()
        application["demographics"] = [d["demographic_group"] for d in demo_response.data]
        
        # Get devices
        device_response = supabase.table("application_devices").select("device_type").eq("application_id", application_id).execute()
        application["devices"] = [d["device_type"] for d in device_response.data]
        
        # Get connectivity
        conn_response = supabase.table("application_connectivity").select("connectivity_type").eq("application_id", application_id).execute()
        application["connectivity"] = [c["connectivity_type"] for c in conn_response.data]
        
        return application
    except Exception as e:
        st.error(f"Error fetching application details: {e}")
        return None


def approve_application(application_id: str, admin_id: str, reason: Optional[str] = None) -> bool:
    """Approve an application and create approved applicant record"""
    supabase = get_supabase_client()
    try:
        # Update application status
        supabase.table("applications").update({"status": "APPROVED"}).eq("application_id", application_id).execute()
        
        # Create application review record
        supabase.table("application_reviews").insert({
            "application_id": application_id,
            "admin_id": admin_id,
            "action": "APPROVED",
            "action_reason": reason
        }).execute()
        
        # Create approved applicant record
        supabase.table("approved_applicants").insert({
            "application_id": application_id
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Error approving application: {e}")
        return False


def reject_application(application_id: str, admin_id: str, reason: str) -> bool:
    """Reject an application"""
    supabase = get_supabase_client()
    try:
        # Update application status
        supabase.table("applications").update({"status": "REJECTED"}).eq("application_id", application_id).execute()
        
        # Create application review record
        supabase.table("application_reviews").insert({
            "application_id": application_id,
            "admin_id": admin_id,
            "action": "REJECTED",
            "action_reason": reason
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Error rejecting application: {e}")
        return False


def get_admin_dashboard_metrics(partner_org_id: str) -> Dict[str, int]:
    """Get dashboard metrics for admin"""
    supabase = get_supabase_client()
    try:
        # Total applications
        total_apps = supabase.table("applications").select("application_id", count="exact").eq("partner_org_id", partner_org_id).execute()
        
        # Approved applications
        approved_apps = supabase.table("applications").select("application_id", count="exact").eq("partner_org_id", partner_org_id).eq("status", "APPROVED").execute()
        
        # Active scholars
        active_scholars = supabase.table("scholars").select("scholar_id", count="exact").eq("partner_org_id", partner_org_id).eq("is_active", True).execute()
        
        # MoA submissions
        moa_count = supabase.table("moa_submissions").select(
            "moa_id", count="exact"
        ).execute()  # Filter by partner org through joins if needed
        
        return {
            "total_applications": total_apps.count or 0,
            "approved_applications": approved_apps.count or 0,
            "active_scholars": active_scholars.count or 0,
            "moa_submissions": moa_count.count or 0
        }
    except Exception as e:
        st.error(f"Error fetching dashboard metrics: {e}")
        return {"total_applications": 0, "approved_applications": 0, "active_scholars": 0, "moa_submissions": 0}


def get_scholars_for_admin(partner_org_id: str) -> List[Dict[str, Any]]:
    """Get scholars list for admin"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("scholars").select(
            "scholar_id, created_at, is_active, "
            "applications!inner(first_name, last_name, email)"
        ).eq("partner_org_id", partner_org_id).order("created_at", desc=True).execute()
        
        return response.data
    except Exception as e:
        st.error(f"Error fetching scholars: {e}")
        return []


def get_moa_submissions_for_admin(partner_org_id: str) -> List[Dict[str, Any]]:
    """Get MoA submissions for admin review"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("moa_submissions").select(
            "moa_id, submitted_at, status, "
            "approved_applicants!inner(applications!inner(first_name, last_name, email, partner_org_id))"
        ).execute()
        
        # Filter by partner org
        filtered_data = []
        for moa in response.data:
            if moa["approved_applicants"]["applications"]["partner_org_id"] == partner_org_id:
                filtered_data.append(moa)
        
        return filtered_data
    except Exception as e:
        st.error(f"Error fetching MoA submissions: {e}")
        return []


def generate_scholar_id() -> str:
    """Generate unique scholar ID in format SCH12345678"""
    import random
    while True:
        scholar_id = f"SCH{random.randint(10000000, 99999999)}"
        supabase = get_supabase_client()
        try:
            # Check if ID already exists
            existing = supabase.table("scholars").select("scholar_id").eq("scholar_id", scholar_id).execute()
            if not existing.data:
                return scholar_id
        except:
            return scholar_id