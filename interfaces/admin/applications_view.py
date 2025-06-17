# interfaces/admin/applications_view.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.auth import require_auth, get_current_user
from utils.queries import (
    get_applications_for_admin, 
    get_application_details, 
    approve_application, 
    reject_application
)


def admin_applications_page():
    require_auth('admin')
    user = get_current_user()
    partner_org_id = user['partner_org_id']
    partner_org_name = user['data']['partner_organizations']['display_name']
    admin_id = user['data']['admin_id']
    
    st.title(f"Applications Management - {partner_org_name}")
    
    # Filter Controls
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "PENDING", "APPROVED", "REJECTED"],
            index=1  # Default to PENDING
        )
    
    with filter_col2:
        search_term = st.text_input("Search by name or email", placeholder="Enter name or email...")
    
    with filter_col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Get applications data
    filter_status = None if status_filter == "All" else status_filter
    applications = get_applications_for_admin(partner_org_id, filter_status)
    
    # Apply search filter
    if search_term:
        applications = [
            app for app in applications 
            if search_term.lower() in f"{app['first_name']} {app['last_name']} {app['email']}".lower()
        ]
    
    # Statistics Overview
    if applications:
        st.header("📊 Applications Overview")
        
        # Create DataFrame for analysis
        df = pd.DataFrame(applications)
        
        # Status distribution chart
        chart_col, stats_col = st.columns([2, 1])
        
        with chart_col:
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                fig = px.bar(
                    x=status_counts.index, 
                    y=status_counts.values,
                    labels={'x': 'Status', 'y': 'Count'},
                    title="Applications by Status",
                    color=status_counts.index,
                    color_discrete_map={
                        'PENDING': '#ffc107',
                        'APPROVED': '#28a745', 
                        'REJECTED': '#dc3545'
                    }
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with stats_col:
            st.metric("📋 Total Applications", len(applications))
            
            if 'status' in df.columns:
                pending_count = len(df[df['status'] == 'PENDING'])
                approved_count = len(df[df['status'] == 'APPROVED'])
                rejected_count = len(df[df['status'] == 'REJECTED'])
                
                st.metric("⏳ Pending", pending_count)
                st.metric("✅ Approved", approved_count)
                st.metric("❌ Rejected", rejected_count)
    
    # Applications Table
    st.header("📋 Applications List")
    
    if not applications:
        st.info("No applications found matching your criteria.")
        return
    
    # Display applications in an interactive table
    for i, app in enumerate(applications):
        with st.container():
            # Application header
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{app['first_name']} {app['last_name']}**")
                st.caption(f"📧 {app['email']}")
            
            with col2:
                st.write(f"🌍 {app['country']}")
                st.caption(f"🎓 {app['education_status']}")
            
            with col3:
                # Status badge
                status_color = {
                    'PENDING': '🟡',
                    'APPROVED': '🟢', 
                    'REJECTED': '🔴'
                }
                st.write(f"{status_color.get(app['status'], '⚫')} {app['status']}")
                
                # Format date
                applied_date = datetime.fromisoformat(app['applied_at'].replace('Z', '+00:00'))
                st.caption(f"📅 {applied_date.strftime('%Y-%m-%d')}")
            
            with col4:
                if st.button("👁️ View", key=f"view_{app['application_id']}", use_container_width=True):
                    st.session_state[f"show_details_{app['application_id']}"] = True
            
            # Expandable details section
            if st.session_state.get(f"show_details_{app['application_id']}", False):
                with st.expander(f"Application Details - {app['first_name']} {app['last_name']}", expanded=True):
                    display_application_details(app['application_id'], admin_id, app['status'])
            
            st.divider()


def display_application_details(application_id: str, admin_id: str, current_status: str):
    """Display detailed application information with review options"""
    
    # Get detailed application data
    application = get_application_details(application_id)
    
    if not application:
        st.error("Failed to load application details.")
        return
    
    # Basic Information
    st.subheader("👤 Personal Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write(f"**Full Name:** {application['first_name']} {application.get('middle_name', '')} {application['last_name']}")
        st.write(f"**Email:** {application['email']}")
        st.write(f"**Gender:** {application['gender']}")
        st.write(f"**Birth Date:** {application['birthdate']}")
    
    with info_col2:
        st.write(f"**Country:** {application['country']}")
        st.write(f"**State/Province:** {application['state_region_province']}")
        st.write(f"**City:** {application['city']}")
        st.write(f"**Postal Code:** {application['postal_code']}")
    
    # Education Details
    st.subheader("🎓 Education Information")
    
    edu_col1, edu_col2 = st.columns(2)
    
    with edu_col1:
        st.write(f"**Education Status:** {application['education_status']}")
        st.write(f"**Institution Country:** {application['institution_country']}")
    
    with edu_col2:
        st.write(f"**Institution Name:** {application['institution_name']}")
    
    # Experience and Skills
    st.subheader("💻 Experience & Skills")
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        st.write(f"**Programming Experience:** {application['programming_experience']}")
    
    with exp_col2:
        st.write(f"**Data Science Experience:** {application['data_science_experience']}")
    
    with exp_col3:
        st.write(f"**Weekly Commitment:** {application['weekly_time_commitment']} hours")
    
    # Demographics and Tech Access
    st.subheader("📊 Demographics & Technology")
    
    demo_col1, demo_col2, demo_col3 = st.columns(3)
    
    with demo_col1:
        st.write("**Demographic Groups:**")
        for demo in application.get('demographics', []):
            st.write(f"• {demo}")
    
    with demo_col2:
        st.write("**Available Devices:**")
        for device in application.get('devices', []):
            st.write(f"• {device}")
    
    with demo_col3:
        st.write("**Internet Connectivity:**")
        for conn in application.get('connectivity', []):
            st.write(f"• {conn}")
    
    # Essay Responses
    st.subheader("📝 Essay Responses")
    
    st.write("**Why do you want this scholarship?**")
    st.info(application['scholarship_reason'])
    
    st.write("**Career Goals:**")
    st.info(application['career_goals'])
    
    # Review Actions (only for pending applications)
    if current_status == 'PENDING':
        st.subheader("⚖️ Review Actions")
        
        review_col1, review_col2 = st.columns(2)
        
        with review_col1:
            if st.button("✅ Approve Application", key=f"approve_{application_id}", type="primary", use_container_width=True):
                reason = st.text_input("Approval reason (optional)", key=f"approve_reason_{application_id}")
                
                if approve_application(application_id, admin_id, reason):
                    st.success("✅ Application approved successfully!")
                    st.balloons()
                    # Remove the details from session state to hide the expanded view
                    if f"show_details_{application_id}" in st.session_state:
                        del st.session_state[f"show_details_{application_id}"]
                    st.rerun()
                else:
                    st.error("❌ Failed to approve application.")
        
        with review_col2:
            if st.button("❌ Reject Application", key=f"reject_{application_id}", use_container_width=True):
                reason = st.text_area("Rejection reason (required)", key=f"reject_reason_{application_id}")
                
                if reason and st.button("Confirm Rejection", key=f"confirm_reject_{application_id}", type="secondary"):
                    if reject_application(application_id, admin_id, reason):
                        st.error("❌ Application rejected.")
                        # Remove the details from session state to hide the expanded view
                        if f"show_details_{application_id}" in st.session_state:
                            del st.session_state[f"show_details_{application_id}"]
                        st.rerun()
                    else:
                        st.error("❌ Failed to reject application.")
                elif not reason:
                    st.warning("⚠️ Please provide a reason for rejection.")
    
    else:
        # Show current status for non-pending applications
        st.subheader("📋 Current Status")
        status_colors = {
            'APPROVED': '🟢',
            'REJECTED': '🔴'
        }
        st.info(f"{status_colors.get(current_status, '⚫')} This application has been **{current_status}**")