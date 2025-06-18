# interfaces/admin/moa_view.py
import streamlit as st
from datetime import datetime
from utils.auth import require_auth, get_current_user
from utils.queries import get_moa_submissions_for_admin


def admin_moa_page():
    require_auth('admin')
    user = get_current_user()
    partner_org_id = user['partner_org_id']
    partner_org_name = user['data']['partner_organizations']['display_name']
    
    st.title(f"MoA Management - {partner_org_name}")
    
    # Introduction and explanation
    with st.expander("About Memorandum of Agreement (MoA)", expanded=False):
        st.markdown("""
        **What is a Memorandum of Agreement (MoA)?**
        
        The MoA is a formal agreement between approved scholarship applicants and our organization. 
        It outlines the terms, conditions, and expectations for participation in the data science scholarship program.
        
        **Key Components:**
        - Program participation requirements
        - Learning objectives and milestones
        - Code of conduct and community guidelines
        - Certification and completion criteria
        - Mutual responsibilities and commitments
        """)
    
    # Overview of MoA Process
    st.subheader("MoA Submission Process")
    st.write("Understanding the workflow:")
    st.write("1. Applications are approved")
    st.write("2. Approved applicants submit their signed MoA documents")
    st.write("3. Admin reviews and verifies MoA submissions")
    st.write("4. Approved MoAs activate scholar accounts")
    
    # Get MoA submissions
    moa_submissions = get_moa_submissions_for_admin(partner_org_id)
    
    if not moa_submissions:
        st.info("No MoA submissions found.")
        st.write("MoA submissions will appear here after:")
        st.write("1. Applications are approved")
        st.write("2. Approved applicants submit their signed MoA documents")
        return
    
    # Statistics Section
    st.header("MoA Statistics")
    
    # Calculate statistics
    total_submissions = len(moa_submissions) if moa_submissions else 0
    pending_submissions = len([m for m in moa_submissions if m['status'] == 'PENDING']) if moa_submissions else 0
    approved_submissions = len([m for m in moa_submissions if m['status'] == 'APPROVED']) if moa_submissions else 0
    
    # Display metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("Total Submissions", total_submissions)
    
    with metric_col2:
        st.metric("Pending Review", pending_submissions)
    
    with metric_col3:
        st.metric("Approved", approved_submissions)
    
    with metric_col4:
        if total_submissions > 0:
            approval_rate = (approved_submissions / total_submissions) * 100
            st.metric("Approval Rate", f"{approval_rate:.1f}%")
        else:
            st.metric("Approval Rate", "0%")
    
    # Filter and refresh controls
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "PENDING", "APPROVED", "REJECTED"],
            index=0
        )
    
    with filter_col2:
        search_term = st.text_input("Search by name or email", placeholder="Enter name or email...")
    
    with filter_col3:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    
    # Apply filters
    filtered_submissions = moa_submissions.copy()
    
    # Status filter
    if status_filter != "All":
        filtered_submissions = [m for m in filtered_submissions if m['status'] == status_filter]
    
    # Search filter
    if search_term:
        search_term_lower = search_term.lower()
        filtered_submissions = [
            m for m in filtered_submissions 
            if (search_term_lower in f"{m['approved_applicants']['applications']['first_name']} {m['approved_applicants']['applications']['last_name']}".lower() or
                search_term_lower in m['approved_applicants']['applications']['email'].lower())
        ]
    
    # Sort by submission date (newest first)
    filtered_submissions.sort(key=lambda x: x['submitted_at'], reverse=True)
    
    # Display MoA submissions
    st.header(f"MoA Submissions ({len(filtered_submissions)} found)")
    
    if not filtered_submissions:
        st.info("No MoA submissions match your current filters.")
        return
    
    # Display each submission
    for submission in filtered_submissions:
        with st.container():
            # Submission header
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                applicant_name = f"{submission['approved_applicants']['applications']['first_name']} {submission['approved_applicants']['applications']['last_name']}"
                st.write(f"**{applicant_name}**")
                st.caption(f"{submission['approved_applicants']['applications']['email']}")
            
            with col2:
                # Status badge
                status_colors = {
                    'PENDING': 'Orange',
                    'APPROVED': 'Green'
                }
                status_color = status_colors.get(submission['status'], 'Gray')
                st.write(f"Status: {status_color} {submission['status']}")
            
            with col3:
                # Submission date
                submitted_date = datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00'))
                st.write(f"{submitted_date.strftime('%Y-%m-%d %H:%M')}")
                
                # Time ago calculation
                now = datetime.now().replace(tzinfo=submitted_date.tzinfo)
                days_ago = (now - submitted_date).days
                
                if days_ago == 0:
                    st.caption("Today")
                elif days_ago == 1:
                    st.caption("Yesterday")
                else:
                    st.caption(f"{days_ago} days ago")
            
            with col4:
                if st.button("Review", key=f"review_{submission['moa_id']}", use_container_width=True):
                    st.session_state[f"show_moa_review_{submission['moa_id']}"] = True
            
            # Expandable MoA details
            if st.session_state.get(f"show_moa_review_{submission['moa_id']}", False):
                with st.expander(f"MoA Review - {applicant_name}", expanded=True):
                    display_moa_details(submission)
            
            st.divider()


def display_moa_details(submission):
    """Display detailed MoA information for review"""
    
    moa_id = submission['moa_id']
    applicant = submission['approved_applicants']['applications']
    
    # Applicant Information
    st.subheader("Applicant Information")
    
    applicant_col1, applicant_col2 = st.columns(2)
    
    with applicant_col1:
        st.write(f"**Name:** {applicant['first_name']} {applicant['last_name']}")
        st.write(f"**Email:** {applicant['email']}")
        st.write(f"**Country:** {applicant['country']}")
    
    with applicant_col2:
        submitted_date = datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00'))
        st.write(f"**Submitted:** {submitted_date.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Status:** {submission['status']}")
        st.write(f"**Application ID:** {applicant['application_id']}")
    
    # MoA Document Review
    st.subheader("MoA Document")
    
    # Digital Signature Display
    st.write("**Digital Signature:**")
    st.code(submission['digital_signature'], language=None)
    
    # Verification checklist
    st.subheader("Verification Checklist")
    
    checklist_col1, checklist_col2 = st.columns(2)
    
    with checklist_col1:
        st.write("**Document Requirements:**")
        st.checkbox("Document is properly signed", key=f"check_signed_{moa_id}")
        st.checkbox("All fields are completed", key=f"check_complete_{moa_id}")
        st.checkbox("Signature matches applicant name", key=f"check_signature_{moa_id}")
    
    with checklist_col2:
        st.write("**Content Verification:**")
        st.checkbox("Terms and conditions acknowledged", key=f"check_terms_{moa_id}")
        st.checkbox("Program requirements understood", key=f"check_requirements_{moa_id}")
        st.checkbox("Contact information verified", key=f"check_contact_{moa_id}")
    
    # Review Actions
    st.subheader("Review Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button(
            "Approve MoA",
            key=f"approve_moa_{moa_id}",
            type="primary",
            use_container_width=True,
            help="Approve this MoA and activate scholar account"
        ):
            # Approve the MoA
            if approve_moa_submission(moa_id):
                st.success("MoA approved successfully! Scholar account will be activated.")
                st.balloons()
                # Remove from session state to close the review
                if f"show_moa_review_{moa_id}" in st.session_state:
                    del st.session_state[f"show_moa_review_{moa_id}"]
                st.rerun()
            else:
                st.error("Failed to approve MoA.")
    
    with action_col2:
        if st.button("Request Revision", key=f"revise_moa_{moa_id}", use_container_width=True):
            # Request revision logic here
            revision_reason = st.text_area(
                "Reason for revision request:",
                key=f"revision_reason_{moa_id}",
                placeholder="Please specify what needs to be corrected..."
            )
            
            if revision_reason and st.button("Send Revision Request", key=f"send_revision_{moa_id}"):
                # Here you would implement the revision request logic
                st.info("Revision request sent to applicant.")
                if f"show_moa_review_{moa_id}" in st.session_state:
                    del st.session_state[f"show_moa_review_{moa_id}"]
                st.rerun()
    
    with action_col3:
        if st.button("Close Review", key=f"close_moa_{moa_id}", use_container_width=True):
            if f"show_moa_review_{moa_id}" in st.session_state:
                del st.session_state[f"show_moa_review_{moa_id}"]
            st.rerun()


def approve_moa_submission(moa_id: str) -> bool:
    """Approve MoA submission and activate scholar account"""
    from utils.db import get_supabase_client
    from utils.queries import generate_scholar_id
    
    supabase = get_supabase_client()
    
    try:
        # Update MoA status to approved
        supabase.table("moa_submissions").update({"status": "APPROVED"}).eq("moa_id", moa_id).execute()
        
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