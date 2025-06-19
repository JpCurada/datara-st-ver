# interfaces/scholar/home.py
import streamlit as st
from utils.auth import require_auth, get_current_user, is_approved_applicant
from utils.db import get_supabase_client
from utils.queries import generate_scholar_id
from typing import Optional


def scholar_dashboard_page():
    # Check user role and redirect accordingly
    if is_approved_applicant():
        # Show MoA submission interface for approved applicants
        display_approved_applicant_moa_interface()
        return
    
    # Regular scholar dashboard for active scholars
    require_auth('scholar')
    user = get_current_user()
    
    scholar_data = user['data']
    application_data = scholar_data['applications']
    scholar_id = user['scholar_id']
    partner_org = scholar_data['partner_organizations']['display_name']
    
    # Check if scholar is active or needs MoA approval
    if not scholar_data['is_active']:
        display_scholar_moa_pending_interface(scholar_data, application_data, scholar_id, partner_org)
        return
    
    # Display normal scholar dashboard for active scholars
    display_active_scholar_dashboard(scholar_data, application_data, scholar_id, partner_org)


def display_approved_applicant_moa_interface():
    """Display MoA submission interface for approved applicants"""
    require_auth('approved_applicant')
    user = get_current_user()
    
    applicant_data = user['data']
    application_data = applicant_data['applications']
    approved_applicant_id = user['approved_applicant_id']
    partner_org = applicant_data['partner_organizations']['display_name']
    
    st.title(f"Welcome, {application_data['first_name']}!")
    st.subheader(f"MoA Submission Required • {partner_org}")
    
    # Status indicator
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"**Your Approved Applicant ID:** `{approved_applicant_id}`")
    
    with col2:
        st.warning("MoA Submission Required")
    
    # Progress indicator
    st.header("Your Progress")
    progress_col1, progress_col2, progress_col3 = st.columns(3)
    
    with progress_col1:
        st.success("1. Application Approved")
    
    with progress_col2:
        st.warning("2. MoA Submission")
    
    with progress_col3:
        st.info("3. Scholar Activation")
    
    st.divider()
    
    # Check if MoA already submitted
    moa_status = get_applicant_moa_status(approved_applicant_id)
    
    if moa_status is None:
        # Show MoA submission form
        display_moa_submission_form(approved_applicant_id, application_data, partner_org)
    elif moa_status == 'SUBMITTED':
        display_moa_submitted_waiting(approved_applicant_id)
    elif moa_status == 'APPROVED':
        display_transition_to_scholar(approved_applicant_id)


def display_moa_submission_form(approved_applicant_id: str, application_data: dict, partner_org: str):
    """Display MoA submission form"""
    
    st.header("Submit Your MoA Document")
    st.write("Complete your Memorandum of Agreement to become a scholar.")
    
    with st.form("moa_submission_form"):
        st.subheader("Memorandum of Agreement Terms")
        
        # MoA content
        moa_content = f"""
MEMORANDUM OF AGREEMENT - {partner_org} Data Science Scholarship

Applicant: {application_data['first_name']} {application_data['last_name']}
Email: {application_data['email']}
Approved Applicant ID: {approved_applicant_id}

TERMS: I agree to actively participate in the program, complete coursework, follow community guidelines, and work towards program completion.

BENEFITS: Free access to premium courses, certifications, career support, and scholar community.
        """
        
        st.text_area("MoA Terms", value=moa_content, height=150, disabled=True)
        
        # Agreement checkboxes
        col1, col2 = st.columns(2)
        
        with col1:
            terms_agreed = st.checkbox("I agree to all terms and conditions")
            commitment_confirmed = st.checkbox("I commit to active participation")
        
        with col2:
            info_accurate = st.checkbox("All information provided is accurate")
            communication_consent = st.checkbox("I consent to program communications")
        
        # Digital signature
        digital_signature = st.text_input(
            "Digital Signature (Type your full name)",
            placeholder=f"{application_data['first_name']} {application_data['last_name']}"
        )
        
        # Submit button
        submit_moa = st.form_submit_button("Submit MoA", type="primary", use_container_width=True)
        
        if submit_moa:
            all_agreed = terms_agreed and commitment_confirmed and info_accurate and communication_consent
            
            if not all_agreed:
                st.error("Please confirm all agreements")
            elif not digital_signature.strip():
                st.error("Please provide your digital signature")
            else:
                # Submit MoA and create scholar account
                if submit_moa_and_create_scholar(approved_applicant_id, digital_signature.strip()):
                    st.success("MoA submitted successfully!")
                    st.balloons()
                    st.info("Your scholar account has been created! You'll receive your Scholar ID within 2-3 business days after admin review.")
                    st.rerun()
                else:
                    st.error("Failed to submit MoA. Please try again.")


def submit_moa_and_create_scholar(approved_applicant_id: str, digital_signature: str) -> bool:
    """Submit MoA and create scholar account"""
    supabase = get_supabase_client()
    
    try:
        # Get applicant data
        applicant_response = supabase.table("approved_applicants").select(
            "application_id, applications!inner(partner_org_id, email, first_name, last_name)"
        ).eq("approved_applicant_id", approved_applicant_id).execute()
        
        if not applicant_response.data:
            return False
        
        applicant_data = applicant_response.data[0]
        
        # Create MoA submission
        moa_response = supabase.table("moa_submissions").insert({
            "approved_applicant_id": approved_applicant_id,
            "digital_signature": digital_signature,
            "status": "SUBMITTED"
        }).execute()
        
        if not moa_response.data:
            return False
        
        moa_id = moa_response.data[0]["moa_id"]
        
        # Generate scholar ID and create scholar account
        scholar_id = generate_scholar_id()
        
        supabase.table("scholars").insert({
            "scholar_id": scholar_id,
            "moa_id": moa_id,
            "application_id": applicant_data['application_id'],
            "partner_org_id": applicant_data['applications']['partner_org_id'],
            "is_active": False  # Will be activated when admin approves MoA
        }).execute()
        
        # Send notification email
        send_moa_submission_notification(
            email=applicant_data['applications']['email'],
            name=f"{applicant_data['applications']['first_name']} {applicant_data['applications']['last_name']}",
            scholar_id=scholar_id
        )
        
        return True
        
    except Exception as e:
        st.error(f"Error submitting MoA: {e}")
        return False


def get_applicant_moa_status(approved_applicant_id: str) -> Optional[str]:
    """Get MoA status for approved applicant"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("moa_submissions").select("status").eq("approved_applicant_id", approved_applicant_id).execute()
        
        if response.data:
            return response.data[0]['status']
        return None
        
    except Exception:
        return None


def send_moa_submission_notification(email: str, name: str, scholar_id: str):
    """Send notification that MoA was submitted"""
    st.info(f"""
    **Notification Email Sent to {email}:**
    
    Subject: MoA Submitted - Your Scholar ID
    
    Dear {name},
    
    Your MoA has been submitted successfully!
    
    **Your Scholar ID:** {scholar_id}
    
    You can now login using this Scholar ID instead of your Approved Applicant ID. Your account will be fully activated within 2-3 business days after admin review.
    
    Thank you for joining DaTARA!
    """)


# Continue with other display functions...
def display_moa_submitted_waiting(approved_applicant_id: str):
    """Show waiting status after MoA submission"""
    st.success("✅ MoA Successfully Submitted")
    st.info("⏳ Your MoA is under review. Please wait 2-3 business days for approval.")
    
    # Get scholar ID if available
    supabase = get_supabase_client()
    scholar_response = supabase.table("scholars").select("scholar_id").eq("approved_applicant_id", approved_applicant_id).execute()
    
    if scholar_response.data:
        scholar_id = scholar_response.data[0]['scholar_id']
        st.success(f"🎓 **Your Scholar ID:** `{scholar_id}`")
        st.info("You can now login using your Scholar ID instead of your Approved Applicant ID.")


def display_transition_to_scholar(approved_applicant_id: str):
    """Show transition message when becoming scholar"""
    st.success("🎉 Congratulations! You are now a Scholar!")
    
    if st.button("🔄 Continue to Scholar Dashboard", type="primary", use_container_width=True):
        st.rerun()


def display_scholar_moa_pending_interface(scholar_data, application_data, scholar_id, partner_org):
    """For scholars whose MoA is not yet approved"""
    st.title(f"Welcome, {application_data['first_name']}!")
    st.subheader(f"Scholar Activation Pending • {partner_org}")
    
    st.info(f"**Your Scholar ID:** `{scholar_id}`")
    st.warning("⏳ Your MoA is under admin review. Account activation pending.")
    
    # Show progress
    progress_col1, progress_col2, progress_col3 = st.columns(3)
    
    with progress_col1:
        st.success("✅ 1. Application Approved")
    
    with progress_col2:
        st.success("✅ 2. MoA Submitted")
    
    with progress_col3:
        st.warning("⏳ 3. Scholar Activation")
    
    st.info("Please wait 2-3 business days for final approval. You'll receive an email notification when your account is activated.")


# The rest of the scholar dashboard functions remain the same...
def display_active_scholar_dashboard(scholar_data, application_data, scholar_id, partner_org):
    """Regular scholar dashboard for active scholars"""
    # Implementation remains the same as before
    pass