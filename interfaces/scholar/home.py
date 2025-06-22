# interfaces/scholar/home.py - Enhanced scholar dashboard
import streamlit as st
from utils.auth import require_auth, get_current_user, is_approved_applicant
from utils.db import get_supabase_client
from utils.queries import generate_scholar_id
from typing import Optional


def scholar_dashboard_page():
    # Check user role and redirect accordingly
    if is_approved_applicant():
        display_approved_applicant_moa_interface()
        return
    
    # Regular scholar dashboard for active scholars
    require_auth('scholar')
    user = get_current_user()
    
    scholar_data = user['data']
    application_data = scholar_data['applications']
    scholar_id = user['scholar_id']
    partner_org = scholar_data['partner_organizations']['display_name']
    
    display_active_scholar_dashboard(scholar_data, application_data, scholar_id, partner_org)


def display_approved_applicant_moa_interface():
    """Display MoA submission interface for approved applicants"""
    require_auth('approved_applicant')
    user = get_current_user()
    
    applicant_data = user['data']
    application_data = applicant_data['applications']
    approved_applicant_id = user['approved_applicant_id']
    partner_org = applicant_data['partner_organizations']['display_name']
    
    with st.container(key="scholar-welcome"):
        st.title(f"Welcome, {application_data['first_name']}!")
        st.subheader(f"MoA Submission Required - {partner_org}")
    
    # Status indicator
    with st.container(key="scholar-progress"):
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
        display_moa_submission_form(approved_applicant_id, application_data, partner_org)
    elif moa_status == 'SUBMITTED':
        display_moa_submitted_waiting(approved_applicant_id)
    elif moa_status == 'APPROVED':
        display_transition_to_scholar()


def display_moa_submission_form(approved_applicant_id: str, application_data: dict, partner_org: str):
    """Display MoA submission form"""
    
    st.header("Submit Your MoA Document")
    st.write("Complete your Memorandum of Agreement to become a scholar.")
    
    with st.form("moa_submission_form"):
        st.subheader("Memorandum of Agreement Terms")
        
        # MoA content
        moa_content = f"""MEMORANDUM OF AGREEMENT - {partner_org} Data Science Scholarship

Applicant: {application_data['first_name']} {application_data['last_name']}
Email: {application_data['email']}
Approved Applicant ID: {approved_applicant_id}

TERMS AND CONDITIONS:
1. I agree to actively participate in the {partner_org} data science program
2. I commit to completing assigned coursework and projects
3. I will follow all community guidelines and code of conduct
4. I will work towards program completion within the designated timeframe
5. I understand that failure to participate may result in program termination

BENEFITS:
- Free access to premium {partner_org} courses
- Industry-recognized certifications
- Career support and job placement assistance
- Access to scholar community and networking opportunities
- Personalized learning paths and mentorship

RESPONSIBILITIES:
- Regular participation in courses and assignments
- Professional conduct in all program interactions
- Honest reporting of progress and challenges
- Active engagement with the scholar community
- Commitment to sharing success stories and helping future scholars

By signing below, I acknowledge that I have read, understood, and agree to all terms and conditions outlined in this Memorandum of Agreement."""
        
        st.text_area("MoA Terms", value=moa_content, height=300, disabled=True)
        
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
                # Submit MoA
                if submit_moa_document(approved_applicant_id, digital_signature.strip()):
                    st.success("MoA submitted successfully!")
                    st.balloons()
                    st.info("Your MoA is now under review. You'll receive an email notification within 2-3 business days.")
                    st.rerun()
                else:
                    st.error("Failed to submit MoA. Please try again.")


def submit_moa_document(approved_applicant_id: str, digital_signature: str) -> bool:
    """Submit MoA document to database"""
    supabase = get_supabase_client()
    
    try:
        # Create MoA submission
        moa_response = supabase.table("moa_submissions").insert({
            "approved_applicant_id": approved_applicant_id,
            "digital_signature": digital_signature,
            "status": "SUBMITTED"
        }).execute()
        
        if moa_response.data:
            return True
        return False
        
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


def display_moa_submitted_waiting(approved_applicant_id: str):
    """Show waiting status after MoA submission"""
    st.success("MoA Successfully Submitted")
    st.info("Your MoA is under review. Please wait 2-3 business days for approval.")
    
    st.write("**What happens next?**")
    st.write("1. Admin will review your MoA submission")
    st.write("2. You'll receive an email notification upon approval")
    st.write("3. Your Scholar ID will be provided in the approval email")
    st.write("4. You'll gain full access to the program")
    
    # Show current MoA details
    with st.expander("View Submitted MoA"):
        moa_details = get_moa_details(approved_applicant_id)
        if moa_details:
            st.write(f"**Submitted:** {moa_details['submitted_at']}")
            st.write(f"**Status:** {moa_details['status']}")
            st.write("**Digital Signature:**")
            st.code(moa_details['digital_signature'])


def get_moa_details(approved_applicant_id: str) -> Optional[dict]:
    """Get MoA submission details"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("moa_submissions").select(
            "digital_signature, submitted_at, status"
        ).eq("approved_applicant_id", approved_applicant_id).execute()
        
        if response.data:
            return response.data[0]
        return None
        
    except Exception:
        return None


def display_transition_to_scholar():
    """Show transition message when becoming scholar"""
    st.success("Congratulations! You are now a Scholar!")
    st.info("Your MoA has been approved and you've been granted Scholar status.")
    
    if st.button("Continue to Scholar Dashboard", type="primary", use_container_width=True):
        st.rerun()


def display_active_scholar_dashboard(scholar_data, application_data, scholar_id, partner_org):
    """Regular scholar dashboard for active scholars - simplified version"""
    with st.container(key="scholar-welcome"):
        st.title(f"Welcome back, {application_data['first_name']}!")
        st.subheader(f"Active Scholar - {partner_org}")
    
    # Scholar status card
    with st.container(key="scholar-progress"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Scholar ID", scholar_id)
        
        with col2:
            st.metric("Status", "Active", delta="Enrolled")
    
    with col3:
        created_date = scholar_data['created_at']
        st.metric("Member Since", created_date[:10])
    
    st.divider()
    
    # Basic scholar benefits info
    st.subheader("Your Scholar Benefits")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"✅ Free access to {partner_org} premium courses")
        st.write("✅ Industry-recognized certifications")
        st.write("✅ Career support and job placement")
    
    with col2:
        st.write("✅ Scholar community access")
        st.write("✅ Personalized learning paths") 
        st.write("✅ Mentorship opportunities")
    
    # Contact info
    st.info(f"You will receive your {partner_org} platform invitation within 1-2 business days. For support, contact: support@datara.org")

    # Scholar certification feed
    st.divider()
    st.subheader("Recent Scholar Certifications")
    display_scholar_cert_feed(scholar_id)


def display_scholar_cert_feed(current_scholar_id):
    """Show a feed of recent certifications from all scholars except the current user, in 3 columns per row."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("certifications").select(
            """
            name, issuing_organization, issue_month, issue_year, credential_url, scholar_id,
            scholars!inner(
                application_id,
                applications!inner(first_name, last_name)
            )
            """
        ).order("created_at", desc=True).limit(30).execute()  # Fetch more for more rows
        certs = response.data

        if not certs:
            st.info("No recent certifications from other scholars yet.")
            return

        # Create margin and content columns (just like scholar_profile.py)
        _, left_col, _, right_col, _ = st.columns([0.03, 0.8, 0.08, 0.8, 0.03])

        # Use left_col and right_col for your two feed columns
        with left_col:
            # First column of certifications
            for i, cert in enumerate(certs):
                if i % 2 == 0 and cert["scholar_id"] != current_scholar_id:
                    scholar = cert.get("scholars", {})
                    application = scholar.get("applications", {})
                    full_name = f"{application.get('first_name', '')} {application.get('last_name', '')}".strip()
                    st.markdown(
                        f'<div class="cert-feed-post">'
                        f'<div class="cert-feed-header"><b>{full_name} just posted a new certification!</b></div>'
                        f'<div class="cert-feed-body">'
                        f'Certification: <b>{cert["name"]}</b><br>'
                        f'Issued by: {cert["issuing_organization"]}<br>'
                        f'Issued at: {cert["issue_month"]}/{cert["issue_year"]}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if cert.get("credential_url"):
                        st.link_button("View", cert["credential_url"], use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            # Second column of certifications
            for i, cert in enumerate(certs):
                if i % 2 == 1 and cert["scholar_id"] != current_scholar_id:
                    scholar = cert.get("scholars", {})
                    application = scholar.get("applications", {})
                    full_name = f"{application.get('first_name', '')} {application.get('last_name', '')}".strip()
                    st.markdown(
                        f'<div class="cert-feed-post">'
                        f'<div class="cert-feed-header"><b>{full_name} just posted a new certification!</b></div>'
                        f'<div class="cert-feed-body">'
                        f'Certification: <b>{cert["name"]}</b><br>'
                        f'Issued by: {cert["issuing_organization"]}<br>'
                        f'Issued at: {cert["issue_month"]}/{cert["issue_year"]}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if cert.get("credential_url"):
                        st.link_button("View", cert["credential_url"], use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading certification feed: {e}")