import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import uuid
import random
from utils.db import get_supabase_client
from services.email_service import send_approval_email


def check_email_in_scholars(email: str, partner_org: str) -> bool:
    """Check if email already exists as an active scholar for the given partner org"""
    supabase = get_supabase_client()
    try:
        org_response = supabase.table("partner_organizations").select("partner_org_id").eq("display_name", partner_org).execute()
        if not org_response.data:
            return False
        
        partner_org_id = org_response.data[0]["partner_org_id"]
        
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
        org_response = supabase.table("partner_organizations").select("partner_org_id").eq("display_name", partner_org).execute()
        if not org_response.data:
            return None
        
        partner_org_id = org_response.data[0]["partner_org_id"]
        
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
        return ["DataCamp", "Coursera", "Udacity", "edX"]


def save_application_to_database(form_data: Dict[str, Any]) -> bool:
    """Save complete application to database"""
    supabase = get_supabase_client()
    
    try:
        org_response = supabase.table("partner_organizations").select("partner_org_id").eq(
            "display_name", form_data["Partner Organization & Data Privacy"]["partner_org"]
        ).execute()
        
        if not org_response.data:
            st.error("Partner organization not found")
            return False
        
        partner_org_id = org_response.data[0]["partner_org_id"]
        
        step_data = form_data
        basic_info = step_data["Basic Information"]
        geo_details = step_data["Geographic Details"]
        edu_details = step_data["Education Details"]
        interest_details = step_data["Interest Details"]
        demo_details = step_data["Demographic and Connectivity"]
        
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
    """Get applications for admin review with enhanced filtering"""
    supabase = get_supabase_client()
    try:
        query = supabase.table("applications").select(
            "application_id, email, first_name, last_name, status, applied_at, "
            "country, education_status, programming_experience, data_science_experience, "
            "state_region_province, city, institution_name"
        ).eq("partner_org_id", partner_org_id)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        response = query.order("applied_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching applications: {e}")
        return []


def get_application_details(application_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed application information with all related data"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("applications").select(
            "*, partner_organizations!inner(display_name)"  # Add this line to include partner org data
        ).eq("application_id", application_id).execute()
        
        if not response.data:
            return None
        
        application = response.data[0]
        
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
        # Get application details first
        app_details = get_application_details(application_id)
        if not app_details:
            st.error("Application not found")
            return False
        
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
        
        # Generate scholar ID
        scholar_id = generate_scholar_id()
        
        # Send approval email
        applicant_name = f"{app_details['first_name']} {app_details['last_name']}"
        partner_org = app_details['partner_organizations']['display_name']
        
        email_sent = send_approval_email(
            email=app_details['email'],
            applicant_name=applicant_name,
            partner_org=partner_org,
            scholar_id=scholar_id,
            birthdate=str(app_details['birthdate'])
        )
        
        if email_sent:
            st.success(f"Application approved and email sent to {app_details['email']}")
        else:
            st.warning("Application approved but email failed to send")
        
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
        
        # MoA submissions for this partner org
        moa_count = supabase.table("moa_submissions").select(
            "moa_id", count="exact"
        ).in_("approved_applicant_id", [
            app["approved_applicant_id"] for app in 
            supabase.table("approved_applicants").select("approved_applicant_id, applications!inner(partner_org_id)").eq("applications.partner_org_id", partner_org_id).execute().data
        ]).execute()
        
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
    """Get scholars list for admin with enhanced data"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("scholars").select(
            "scholar_id, created_at, is_active, "
            "applications!inner(first_name, last_name, email, country), "
            "partner_organizations!inner(display_name)"
        ).eq("partner_org_id", partner_org_id).order("created_at", desc=True).execute()
        
        return response.data
    except Exception as e:
        st.error(f"Error fetching scholars: {e}")
        return []


def get_moa_submissions_for_admin(partner_org_id: str) -> List[Dict[str, Any]]:
    """Get MoA submissions for admin review with enhanced filtering"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("moa_submissions").select(
            "moa_id, submitted_at, status, digital_signature, "
            "approved_applicants!inner(application_id, applications!inner(first_name, last_name, email, partner_org_id, country))"
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
    supabase = get_supabase_client()
    
    while True:
        scholar_id = f"SCH{random.randint(10000000, 99999999)}"
        try:
            # Check if ID already exists
            existing = supabase.table("scholars").select("scholar_id").eq("scholar_id", scholar_id).execute()
            if not existing.data:
                return scholar_id
        except:
            return scholar_id


# Additional CRUD operations for enhanced functionality

def update_application_status(application_id: str, new_status: str, admin_id: str, reason: str = None) -> bool:
    """Update application status with audit trail"""
    supabase = get_supabase_client()
    try:
        # Update application
        supabase.table("applications").update({"status": new_status}).eq("application_id", application_id).execute()
        
        # Create review record
        supabase.table("application_reviews").insert({
            "application_id": application_id,
            "admin_id": admin_id,
            "action": new_status,
            "action_reason": reason
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Error updating application status: {e}")
        return False


def get_application_review_history(application_id: str) -> List[Dict[str, Any]]:
    """Get review history for an application"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("application_reviews").select(
            "action, action_reason, reviewed_at, "
            "admins!inner(first_name, last_name, email)"
        ).eq("application_id", application_id).order("reviewed_at", desc=True).execute()
        
        return response.data
    except Exception as e:
        st.error(f"Error fetching review history: {e}")
        return []


def search_applications(partner_org_id: str, search_query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Advanced search for applications"""
    supabase = get_supabase_client()
    try:
        query = supabase.table("applications").select(
            "application_id, email, first_name, last_name, status, applied_at, "
            "country, education_status, programming_experience, data_science_experience"
        ).eq("partner_org_id", partner_org_id)
        
        # Apply text search
        if search_query:
            # This is a simplified text search - in production, you might want to use full-text search
            query = query.or_(f"first_name.ilike.%{search_query}%,last_name.ilike.%{search_query}%,email.ilike.%{search_query}%")
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if value:
                    query = query.eq(key, value)
        
        response = query.order("applied_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error searching applications: {e}")
        return []


def get_application_analytics(partner_org_id: str) -> Dict[str, Any]:
    """Get analytics data for applications"""
    supabase = get_supabase_client()
    try:
        # Get all applications for analytics
        response = supabase.table("applications").select(
            "status, applied_at, country, education_status, programming_experience, "
            "data_science_experience, gender, weekly_time_commitment"
        ).eq("partner_org_id", partner_org_id).execute()
        
        applications = response.data
        
        # Calculate analytics
        analytics = {
            "total_count": len(applications),
            "status_breakdown": {},
            "country_breakdown": {},
            "education_breakdown": {},
            "experience_breakdown": {},
            "monthly_trends": {}
        }
        
        # Status breakdown
        for app in applications:
            status = app.get('status', 'UNKNOWN')
            analytics["status_breakdown"][status] = analytics["status_breakdown"].get(status, 0) + 1
        
        # Country breakdown
        for app in applications:
            country = app.get('country', 'Unknown')
            analytics["country_breakdown"][country] = analytics["country_breakdown"].get(country, 0) + 1
        
        # Education breakdown
        for app in applications:
            education = app.get('education_status', 'Unknown')
            analytics["education_breakdown"][education] = analytics["education_breakdown"].get(education, 0) + 1
        
        # Programming experience breakdown
        for app in applications:
            exp = app.get('programming_experience', 'Unknown')
            analytics["experience_breakdown"][exp] = analytics["experience_breakdown"].get(exp, 0) + 1
        
        return analytics
    except Exception as e:
        st.error(f"Error fetching analytics: {e}")
        return {}


def bulk_update_applications(application_ids: List[str], new_status: str, admin_id: str, reason: str = None) -> bool:
    """Bulk update multiple applications"""
    supabase = get_supabase_client()
    try:
        for app_id in application_ids:
            # Update application
            supabase.table("applications").update({"status": new_status}).eq("application_id", app_id).execute()
            
            # Create review record
            supabase.table("application_reviews").insert({
                "application_id": app_id,
                "admin_id": admin_id,
                "action": new_status,
                "action_reason": reason
            }).execute()
        
        return True
    except Exception as e:
        st.error(f"Error bulk updating applications: {e}")
        return False


def get_scholar_detailed_info(scholar_id: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive scholar information"""
    supabase = get_supabase_client()
    try:
        # Get scholar basic info
        scholar_response = supabase.table("scholars").select(
            "scholar_id, created_at, is_active, "
            "applications!inner(first_name, last_name, email, country, birthdate), "
            "partner_organizations!inner(display_name)"
        ).eq("scholar_id", scholar_id).execute()
        
        if not scholar_response.data:
            return None
        
        scholar = scholar_response.data[0]
        
        # Get certifications
        cert_response = supabase.table("certifications").select("*").eq("scholar_id", scholar_id).execute()
        scholar["certifications"] = cert_response.data
        
        # Get jobs
        job_response = supabase.table("jobs").select("*").eq("scholar_id", scholar_id).execute()
        scholar["jobs"] = job_response.data
        
        return scholar
    except Exception as e:
        st.error(f"Error fetching scholar details: {e}")
        return None


def create_certification(scholar_id: str, certification_data: Dict[str, Any]) -> bool:
    """Create a new certification for a scholar"""
    supabase = get_supabase_client()
    try:
        certification_data["scholar_id"] = scholar_id
        supabase.table("certifications").insert(certification_data).execute()
        return True
    except Exception as e:
        st.error(f"Error creating certification: {e}")
        return False


def update_certification(certification_id: str, certification_data: Dict[str, Any]) -> bool:
    """Update an existing certification"""
    supabase = get_supabase_client()
    try:
        certification_data["updated_at"] = datetime.now().isoformat()
        supabase.table("certifications").update(certification_data).eq("certification_id", certification_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating certification: {e}")
        return False


def delete_certification(certification_id: str) -> bool:
    """Delete a certification"""
    supabase = get_supabase_client()
    try:
        supabase.table("certifications").delete().eq("certification_id", certification_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting certification: {e}")
        return False


def create_job_record(scholar_id: str, job_data: Dict[str, Any]) -> bool:
    """Create a job record for a scholar"""
    supabase = get_supabase_client()
    try:
        job_data["scholar_id"] = scholar_id
        supabase.table("jobs").insert(job_data).execute()
        return True
    except Exception as e:
        st.error(f"Error creating job record: {e}")
        return False


def get_partner_organization_stats(partner_org_id: str) -> Dict[str, Any]:
    """Get comprehensive statistics for a partner organization"""
    supabase = get_supabase_client()
    try:
        stats = {}
        
        # Application stats
        app_response = supabase.table("applications").select("status").eq("partner_org_id", partner_org_id).execute()
        applications = app_response.data
        
        stats["applications"] = {
            "total": len(applications),
            "pending": len([a for a in applications if a["status"] == "PENDING"]),
            "approved": len([a for a in applications if a["status"] == "APPROVED"]),
            "rejected": len([a for a in applications if a["status"] == "REJECTED"])
        }
        
        # Scholar stats
        scholar_response = supabase.table("scholars").select("is_active, created_at").eq("partner_org_id", partner_org_id).execute()
        scholars = scholar_response.data
        
        stats["scholars"] = {
            "total": len(scholars),
            "active": len([s for s in scholars if s["is_active"]]),
            "inactive": len([s for s in scholars if not s["is_active"]])
        }
        
        # Certification stats (through scholars)
        if scholars:
            scholar_ids = [s["scholar_id"] for s in scholars if "scholar_id" in s]
            if scholar_ids:
                cert_response = supabase.table("certifications").select("certification_id").in_("scholar_id", scholar_ids).execute()
                stats["certifications"] = {"total": len(cert_response.data)}
        
        return stats
    except Exception as e:
        st.error(f"Error fetching organization stats: {e}")
        return {}


def approve_moa_submission(moa_id: str, admin_id: str = None, reason: str = None) -> bool:
    """Approve MoA submission and create scholar account"""
    supabase = get_supabase_client()
    
    try:
        # Update MoA status
        supabase.table("moa_submissions").update({"status": "APPROVED"}).eq("moa_id", moa_id).execute()
        
        # Create MoA review record if admin_id provided
        if admin_id:
            supabase.table("moa_reviews").insert({
                "moa_id": moa_id,
                "admin_id": admin_id,
                "action": "APPROVED",
                "action_reason": reason
            }).execute()
        
        # Get MoA details to create scholar record
        moa_response = supabase.table("moa_submissions").select(
            "approved_applicants!inner(application_id, applications!inner(partner_org_id))"
        ).eq("moa_id", moa_id).execute()
        
        if moa_response.data:
            application_id = moa_response.data[0]['approved_applicants']['application_id']
            partner_org_id = moa_response.data[0]['approved_applicants']['applications']['partner_org_id']
            
            # Generate scholar ID
            scholar_id = generate_scholar_id()
            
            # Create scholar record
            supabase.table("scholars").insert({
                "scholar_id": scholar_id,
                "moa_id": moa_id,
                "application_id": application_id,
                "partner_org_id": partner_org_id,
                "is_active": True
            }).execute()
            
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Error approving MoA: {e}")
        return False


def request_moa_revision(moa_id: str, admin_id: str = None, reason: str = None) -> bool:
    """Request revision for MoA submission"""
    supabase = get_supabase_client()
    
    try:
        # Update MoA status to pending for revision
        supabase.table("moa_submissions").update({"status": "PENDING"}).eq("moa_id", moa_id).execute()
        
        # Create MoA review record if admin_id provided
        if admin_id:
            supabase.table("moa_reviews").insert({
                "moa_id": moa_id,
                "admin_id": admin_id,
                "action": "REJECTED",  # Using REJECTED for revision requests
                "action_reason": reason or "Revision requested"
            }).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error requesting revision: {e}")
        return False


def get_moa_review_history(moa_id: str) -> List[Dict[str, Any]]:
    """Get review history for a MoA submission"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("moa_reviews").select(
            "action, action_reason, reviewed_at, admins!inner(first_name, last_name)"
        ).eq("moa_id", moa_id).order("reviewed_at", desc=True).execute()
        
        return response.data
        
    except Exception as e:
        st.error(f"Error fetching review history: {e}")
        return []


def toggle_scholar_status(scholar_id: str, is_active: bool) -> bool:
    """Toggle scholar active status"""
    supabase = get_supabase_client()
    try:
        supabase.table("scholars").update({"is_active": is_active}).eq("scholar_id", scholar_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating scholar status: {e}")
        return False


def get_scholar_certifications_count(scholar_id: str) -> int:
    """Get count of certifications for a scholar"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("certifications").select("certification_id", count="exact").eq("scholar_id", scholar_id).execute()
        return response.count or 0
    except:
        return 0


def get_scholar_employment_status(scholar_id: str) -> str:
    """Get employment status for a scholar"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("jobs").select("job_title").eq("scholar_id", scholar_id).eq("is_published", True).execute()
        return "Employed" if response.data else "Seeking"
    except:
        return "Unknown"


def get_scholar_certifications(scholar_id: str) -> List[Dict[str, Any]]:
    """Get detailed certifications for a scholar"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("certifications").select("*").eq("scholar_id", scholar_id).order("issue_year", desc=True).execute()
        return response.data
    except:
        return []


def get_scholar_jobs(scholar_id: str) -> List[Dict[str, Any]]:
    """Get jobs for a scholar"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("jobs").select("*").eq("scholar_id", scholar_id).eq("is_published", True).execute()
        return response.data
    except:
        return []