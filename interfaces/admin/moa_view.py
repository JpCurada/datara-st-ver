# interfaces/admin/moa_view.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.auth import require_auth, get_current_user
from utils.queries import (
    get_moa_submissions_for_admin, 
    approve_moa_submission, 
    request_moa_revision, 
    get_moa_review_history
)
from utils.db import get_supabase_client


def admin_moa_page():
    require_auth('admin')
    user = get_current_user()
    partner_org_id = user['partner_org_id']
    partner_org_name = user['data']['partner_organizations']['display_name']
    admin_id = user['data']['admin_id']
    
    st.title(f"MoA Management - {partner_org_name}")
    
    # Get MoA submissions
    moa_submissions = get_moa_submissions_for_admin(partner_org_id)
    
    if not moa_submissions:
        st.info("No MoA submissions found.")
        st.write("MoA submissions will appear here after applications are approved and MoA documents are submitted.")
        return
    
    # Filter Controls
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "PENDING", "SUBMITTED", "APPROVED"]
        )
    
    with col2:
        search_term = st.text_input("Search", placeholder="Name or email...")
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["Submitted Date (Newest)", "Submitted Date (Oldest)", "Name A-Z", "Status"]
        )
    
    with col4:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    
    # Apply filters
    filtered_moas = filter_moa_submissions(moa_submissions, status_filter, search_term, sort_by)
    
    # Statistics Dashboard
    display_moa_statistics(filtered_moas, moa_submissions)
    
    # MoA CRUD Table
    st.header("MoA Submissions Table")
    display_moa_table(filtered_moas, admin_id)


def filter_moa_submissions(moa_submissions, status_filter, search_term, sort_by):
    """Filter and sort MoA submissions based on criteria"""
    filtered = moa_submissions.copy()
    
    # Status filter
    if status_filter != "All":
        filtered = [moa for moa in filtered if moa['status'] == status_filter]
    
    # Search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            moa for moa in filtered
            if (search_lower in f"{moa['approved_applicants']['applications']['first_name']} {moa['approved_applicants']['applications']['last_name']}".lower() or
                search_lower in moa['approved_applicants']['applications']['email'].lower())
        ]
    
    # Sorting
    if sort_by == "Submitted Date (Newest)":
        filtered.sort(key=lambda x: x['submitted_at'], reverse=True)
    elif sort_by == "Submitted Date (Oldest)":
        filtered.sort(key=lambda x: x['submitted_at'])
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda x: f"{x['approved_applicants']['applications']['first_name']} {x['approved_applicants']['applications']['last_name']}")
    elif sort_by == "Status":
        filtered.sort(key=lambda x: x['status'])
    
    return filtered


def display_moa_statistics(filtered_moas, all_moas):
    """Display MoA statistics and charts"""
    st.subheader("MoA Statistics")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Submissions", len(all_moas))
    
    with col2:
        pending_count = len([moa for moa in all_moas if moa['status'] == 'PENDING'])
        st.metric("Pending Review", pending_count)
    
    with col3:
        submitted_count = len([moa for moa in all_moas if moa['status'] == 'SUBMITTED'])
        st.metric("Submitted", submitted_count)
    
    with col4:
        approved_count = len([moa for moa in all_moas if moa['status'] == 'APPROVED'])
        st.metric("Approved", approved_count)
    
    # Charts
    if len(all_moas) > 0:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Status distribution
            df = pd.DataFrame([
                {
                    'status': moa['status'],
                    'submitted_date': moa['submitted_at']
                }
                for moa in all_moas
            ])
            
            status_counts = df['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="MoA Status Distribution",
                color_discrete_map={
                    'PENDING': '#ffc107',
                    'SUBMITTED': '#17a2b8',
                    'APPROVED': '#28a745'
                }
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with chart_col2:
            # Submissions over time
            df['submitted_date'] = pd.to_datetime(df['submitted_date'])
            df['submission_date'] = df['submitted_date'].dt.date
            daily_counts = df.groupby('submission_date').size().reset_index(name='count')
            
            fig_timeline = px.line(
                daily_counts,
                x='submission_date',
                y='count',
                title="MoA Submissions Over Time",
                labels={'submission_date': 'Date', 'count': 'Submissions'}
            )
            st.plotly_chart(fig_timeline, use_container_width=True)


def display_moa_table(moa_submissions, admin_id):
    """Display MoA submissions in an interactive table with CRUD operations"""
    if not moa_submissions:
        st.info("No MoA submissions match your criteria.")
        return
    
    # Create DataFrame for display
    table_data = []
    for moa in moa_submissions:
        applicant = moa['approved_applicants']['applications']
        submitted_date = datetime.fromisoformat(moa['submitted_at'].replace('Z', '+00:00'))
        
        table_data.append({
            'MoA ID': moa['moa_id'][:8] + '...',
            'Name': f"{applicant['first_name']} {applicant['last_name']}",
            'Email': applicant['email'],
            'Country': applicant['country'],
            'Status': moa['status'],
            'Submitted': submitted_date.strftime('%Y-%m-%d %H:%M'),
            'Days Ago': (datetime.now().replace(tzinfo=submitted_date.tzinfo) - submitted_date).days,
            'Full ID': moa['moa_id']  # Hidden column for operations
        })
    
    df = pd.DataFrame(table_data)
    
    # Display table with selection
    st.write(f"Showing {len(moa_submissions)} MoA submissions")
    
    # Use columns for table and actions
    table_col, actions_col = st.columns([3, 1])
    
    with table_col:
        # Display table (without the Full ID column)
        display_df = df.drop(columns=['Full ID'])
        
        # Color code the status column
        def highlight_status(val):
            color_map = {
                'PENDING': 'background-color: #fff3cd',
                'SUBMITTED': 'background-color: #d1ecf1', 
                'APPROVED': 'background-color: #d4edda'
            }
            return color_map.get(val, '')
        
        styled_df = display_df.style.applymap(highlight_status, subset=['Status'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with actions_col:
        st.subheader("Actions")
        
        # MoA selection
        selected_name = st.selectbox(
            "Select MoA Submission",
            options=["None"] + [row['Name'] for _, row in df.iterrows()],
            key="selected_moa"
        )
        
        if selected_name != "None":
            # Find selected MoA
            selected_row = df[df['Name'] == selected_name].iloc[0]
            selected_id = selected_row['Full ID']
            
            # Display selected MoA info
            st.write("**Selected:**")
            st.write(f"Name: {selected_row['Name']}")
            st.write(f"Email: {selected_row['Email']}")
            st.write(f"Status: {selected_row['Status']}")
            st.write(f"Submitted: {selected_row['Submitted']}")
            
            # Action buttons
            if st.button("View Details", use_container_width=True):
                st.session_state[f"show_moa_details_{selected_id}"] = True
                st.rerun()
            
            if selected_row['Status'] in ['PENDING', 'SUBMITTED']:
                if st.button("Quick Approve", use_container_width=True, type="primary"):
                    if approve_moa_submission(selected_id, admin_id):
                        st.success("MoA approved!")
                        st.rerun()
                
                if st.button("Request Revision", use_container_width=True):
                    if request_moa_revision(selected_id, admin_id, "Revision requested via table"):
                        st.success("Revision requested!")
                        st.rerun()
        
        # Bulk actions
        st.divider()
        st.subheader("Bulk Actions")
        
        if st.button("Export CSV", use_container_width=True):
            csv = df.drop(columns=['Full ID']).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"moa_submissions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Show MoA details if requested
    for moa in moa_submissions:
        if st.session_state.get(f"show_moa_details_{moa['moa_id']}", False):
            with st.expander(f"MoA Details - {moa['approved_applicants']['applications']['first_name']} {moa['approved_applicants']['applications']['last_name']}", expanded=True):
                display_moa_details(moa, admin_id)
                
                if st.button("Close Details", key=f"close_moa_{moa['moa_id']}"):
                    st.session_state[f"show_moa_details_{moa['moa_id']}"] = False
                    st.rerun()


def display_moa_details(moa, admin_id):
    """Display detailed MoA information with review options"""
    moa_id = moa['moa_id']
    applicant = moa['approved_applicants']['applications']
    
    # MoA details in tabs
    detail_tabs = st.tabs(["Applicant Info", "MoA Document", "Review History", "Actions"])
    
    with detail_tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {applicant['first_name']} {applicant['last_name']}")
            st.write(f"**Email:** {applicant['email']}")
            st.write(f"**Country:** {applicant['country']}")
            st.write(f"**Application ID:** {applicant['application_id']}")
        
        with col2:
            submitted_date = datetime.fromisoformat(moa['submitted_at'].replace('Z', '+00:00'))
            st.write(f"**Submitted:** {submitted_date.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Status:** {moa['status']}")
            st.write(f"**Days Ago:** {(datetime.now().replace(tzinfo=submitted_date.tzinfo) - submitted_date).days}")
    
    with detail_tabs[1]:
        st.subheader("Digital Signature")
        st.code(moa['digital_signature'], language=None)
        
        # Verification checklist
        st.subheader("Verification Checklist")
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Document properly signed", key=f"check_signed_{moa_id}")
            st.checkbox("All fields completed", key=f"check_complete_{moa_id}")
            st.checkbox("Signature matches name", key=f"check_signature_{moa_id}")
        
        with col2:
            st.checkbox("Terms acknowledged", key=f"check_terms_{moa_id}")
            st.checkbox("Requirements understood", key=f"check_requirements_{moa_id}")
            st.checkbox("Contact info verified", key=f"check_contact_{moa_id}")
    
    with detail_tabs[2]:
        # Get review history
        review_history = get_moa_review_history(moa_id)
        
        if review_history:
            for review in review_history:
                review_date = datetime.fromisoformat(review['reviewed_at'].replace('Z', '+00:00'))
                st.write(f"**{review['action']}** on {review_date.strftime('%Y-%m-%d %H:%M')}")
                if review.get('action_reason'):
                    st.write(f"Reason: {review['action_reason']}")
                st.divider()
        else:
            st.info("No review history available.")
    
    with detail_tabs[3]:
        if moa['status'] in ['PENDING', 'SUBMITTED']:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                approval_reason = st.text_area(
                    "Approval notes (optional)",
                    key=f"approve_notes_{moa_id}",
                    height=100
                )
                
                if st.button("Approve MoA", key=f"approve_moa_{moa_id}", type="primary", use_container_width=True):
                    if approve_moa_submission(moa_id, admin_id, approval_reason):
                        st.success("MoA approved successfully!")
                        st.balloons()
                        if f"show_moa_details_{moa_id}" in st.session_state:
                            del st.session_state[f"show_moa_details_{moa_id}"]
                        st.rerun()
                    else:
                        st.error("Failed to approve MoA.")
            
            with col2:
                revision_reason = st.text_area(
                    "Revision request reason",
                    key=f"revision_reason_{moa_id}",
                    height=100,
                    placeholder="Specify what needs correction..."
                )
                
                if st.button("Request Revision", key=f"revise_moa_{moa_id}", use_container_width=True):
                    if not revision_reason.strip():
                        st.warning("Please provide a reason for revision.")
                    else:
                        if request_moa_revision(moa_id, admin_id, revision_reason):
                            st.success("Revision request sent.")
                            if f"show_moa_details_{moa_id}" in st.session_state:
                                del st.session_state[f"show_moa_details_{moa_id}"]
                            st.rerun()
                        else:
                            st.error("Failed to request revision.")
            
            with col3:
                st.write("**Quick Actions:**")
                if st.button("Download MoA", use_container_width=True):
                    st.info("MoA download feature coming soon.")
                
                if st.button("Contact Applicant", use_container_width=True):
                    st.info("Email integration coming soon.")
        else:
            status_colors = {'APPROVED': 'success', 'REJECTED': 'error'}
            status_func = getattr(st, status_colors.get(moa['status'], 'info'))
            status_func(f"Status: {moa['status']}")