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
    
    # Information about MoA process
    with st.expander("ℹ️ About Memorandum of Agreement (MoA)", expanded=False):
        st.write("""
        **MoA Process Overview:**
        
        1. **Application Approval**: After you approve an application, the applicant receives access to submit their MoA
        2. **MoA Submission**: Approved applicants download, sign, and submit their MoA documents
        3. **Admin Review**: You review and approve MoA submissions here
        4. **Scholar Activation**: Upon MoA approval, the applicant becomes an active scholar
        
        **Your Role:**
        - Review submitted MoA documents
        - Verify signatures and completeness
        - Approve or request revisions
        """)
    
    # Get MoA submissions
    moa_submissions = get_moa_submissions_for_admin(partner_org_id)
    
    if not moa_submissions:
        st.info("📄 No MoA submissions found.")
        st.write("MoA submissions will appear here after:")
        st.write("1. ✅ Applications are approved")
        st.write("2. 📝 Approved applicants submit their signed MoA documents")
        return
    
    # Summary Statistics
    st.header("📊 MoA Statistics")
    
    total_submissions = len(moa_submissions)
    pending_submissions = len([m for m in moa_submissions if m['status'] == 'SUBMITTED'])
    approved_submissions = len([m for m in moa_submissions if m['status'] == 'APPROVED'])
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("📄 Total Submissions", total_submissions)
    
    with stat_col2:
        st.metric("⏳ Pending Review", pending_submissions)
    
    with stat_col3:
        st.metric("✅ Approved", approved_submissions)
    
    with stat_col4:
        if total_submissions > 0:
            approval_rate = (approved_submissions / total_submissions) * 100
            st.metric("📈 Approval Rate", f"{approval_rate:.1f}%")
    
    # Filter Controls
    st.header("🔍 Filter & Search")
    
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "SUBMITTED", "APPROVED"],
            index=1  # Default to SUBMITTED (pending review)
        )
    
    with filter_col2:
        search_term = st.text_input("Search by name or email", placeholder="Enter name or email...")
    
    with filter_col3:
        if st.button("🔄 Refresh", use_container_width=True):
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
    
    # Display MoA Submissions
    st.header(f"📋 MoA Submissions ({len(filtered_submissions)} found)")
    
    if not filtered_submissions:
        st.info("No MoA submissions match your criteria.")
        return
    
    # Display submissions
    for submission in filtered_submissions:
        with st.container():
            # Submission header
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            applicant = submission['approved_applicants']['applications']
            
            with col1:
                st.write(f"**{applicant['first_name']} {applicant['last_name']}**")
                st.caption(f"📧 {applicant['email']}")
            
            with col2:
                # Status badge
                status_colors = {
                    'SUBMITTED': '🟡',
                    'APPROVED': '🟢'
                }
                st.write(f"{status_colors.get(submission['status'], '⚫')} {submission['status']}")
            
            with col3:
                # Submission date
                submitted_date = datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00'))
                st.write(f"📅 {submitted_date.strftime('%Y-%m-%d %H:%M')}")
                
                # Days since submission
                days_ago = (datetime.now().replace(tzinfo=submitted_date.tzinfo) - submitted_date).days
                if days_ago == 0:
                    st.caption("📅 Today")
                elif days_ago == 1:
                    st.caption("📅 Yesterday")
                else:
                    st.caption(f"📅 {days_ago} days ago")
            
            with col4:
                if st.button("👁️ Review", key=f"review_{submission['moa_id']}", use_container_width=True):
                    st.session_state[f"show_moa_details_{submission['moa_id']}"] = True
            
            # Expandable MoA details
            if st.session_state.get(f"show_moa_details_{submission['moa_id']}", False):
                with st.expander(f"MoA Review - {applicant['first_name']} {applicant['last_name']}", expanded=True):
                    display_moa_details(submission)
            
            st.divider()


def display_moa_details(submission):
    """Display detailed MoA submission for review"""
    
    applicant = submission['approved_applicants']['applications']
    moa_id = submission['moa_id']
    
    # Applicant Information
    st.subheader("👤 Applicant Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write(f"**Full Name:** {applicant['first_name']} {applicant['last_name']}")
        st.write(f"**Email:** {applicant['email']}")
    
    with info_col2:
        submitted_date = datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00'))
        st.write(f"**Submission Date:** {submitted_date.strftime('%B %d, %Y at %H:%M')}")
        st.write(f"**Current Status:** {submission['status']}")
    
    # MoA Document Section
    st.subheader("📄 MoA Document")
    
    # Digital Signature Display
    st.write("**Digital Signature:**")
    st.code(submission['digital_signature'], language=None)
    
    # Document verification checklist
    st.subheader("✅ Verification Checklist")
    
    checklist_col1, checklist_col2 = st.columns(2)
    
    with checklist_col1:
        signature_valid = st.checkbox("Digital signature is valid", key=f"sig_valid_{moa_id}")
        terms_accepted = st.checkbox("All terms and conditions acknowledged", key=f"terms_{moa_id}")
        contact_verified = st.checkbox("Contact information verified", key=f"contact_{moa_id}")
    
    with checklist_col2:
        document_complete = st.checkbox("Document is complete", key=f"complete_{moa_id}")
        no_modifications = st.checkbox("No unauthorized modifications", key=f"no_mod_{moa_id}")
        ready_to_approve = st.checkbox("Ready for approval", key=f"ready_{moa_id}")
    
    # Review Actions (only for SUBMITTED status)
    if submission['status'] == 'SUBMITTED':
        st.subheader("⚖️ Review Actions")
        
        # Approval requirements check
        all_checks_passed = all([
            signature_valid, terms_accepted, contact_verified,
            document_complete, no_modifications, ready_to_approve
        ])
        
        action_col1, action_col2 = st.columns(2)
        
        with action_col1:
            approve_disabled = not all_checks_passed
            
            if st.button(
                "✅ Approve MoA", 
                key=f"approve_moa_{moa_id}", 
                type="primary", 
                disabled=approve_disabled,
                use_container_width=True,
                help="Complete all checklist items to enable approval"
            ):
                if approve_moa_submission(moa_id):
                    st.success("✅ MoA approved successfully! Scholar account will be activated.")
                    st.balloons()
                    # Remove details from session state
                    if f"show_moa_details_{moa_id}" in st.session_state:
                        del st.session_state[f"show_moa_details_{moa_id}"]
                    st.rerun()
                else:
                    st.error("❌ Failed to approve MoA.")
        
        with action_col2:
            if st.button("📝 Request Revision", key=f"revise_moa_{moa_id}", use_container_width=True):
                revision_notes = st.text_area(
                    "Revision notes for applicant:",
                    key=f"revision_notes_{moa_id}",
                    placeholder="Explain what needs to be corrected or updated..."
                )
                
                if revision_notes and st.button("Send Revision Request", key=f"send_revision_{moa_id}"):
                    # Implement revision request functionality
                    st.info("🚧 Revision request functionality coming soon!")
                    st.write("For now, please contact the applicant directly:")
                    st.code(f"Email: {applicant['email']}\nNotes: {revision_notes}")
    
    else:
        # Show status for approved MoAs
        st.subheader("📋 Current Status")
        st.success("🟢 This MoA has been **APPROVED**")
    
    # Close button
    if st.button("❌ Close Review", key=f"close_moa_{moa_id}", use_container_width=True):
        if f"show_moa_details_{moa_id}" in st.session_state:
            del st.session_state[f"show_moa_details_{moa_id}"]
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