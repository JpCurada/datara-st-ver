# interfaces/admin/dashboard.py
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.auth import require_auth, get_current_user
from utils.queries import get_admin_dashboard_metrics, get_scholars_for_admin
from datetime import datetime, timedelta


def admin_dashboard_page():
    require_auth('admin')
    user = get_current_user()
    partner_org_id = user['partner_org_id']
    partner_org_name = user['data']['partner_organizations']['display_name']
    
    st.title(f"Admin Dashboard - {partner_org_name}")
    
    # Get dashboard metrics
    metrics = get_admin_dashboard_metrics(partner_org_id)
    
    # Metrics Cards Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Applications",
            value=metrics['total_applications'],
            help="Total number of applications received"
        )
    
    with col2:
        st.metric(
            label="Approved Applications", 
            value=metrics['approved_applications'],
            help="Number of applications approved"
        )
    
    with col3:
        st.metric(
            label="Active Scholars",
            value=metrics['active_scholars'],
            help="Current number of active scholars"
        )
    
    with col4:
        st.metric(
            label="MoA Submissions",
            value=metrics['moa_submissions'],
            help="Total MoA submissions received"
        )
    
    # Recent Activity Section
    st.header("Recent Activity")
    
    # Create two columns for charts and recent data
    chart_col, activity_col = st.columns([2, 1])
    
    with chart_col:
        st.subheader("Application Status Overview")
        
        # Create a simple status chart
        if metrics['total_applications'] > 0:
            pending = metrics['total_applications'] - metrics['approved_applications']
            status_data = pd.DataFrame({
                'Status': ['Approved', 'Pending/Rejected'],
                'Count': [metrics['approved_applications'], pending]
            })
            
            fig = px.pie(status_data, values='Count', names='Status', 
                        color_discrete_sequence=['#28a745', '#ffc107'])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No applications data available yet.")
    
    with activity_col:
        st.subheader("Quick Stats")
        
        # Approval rate
        if metrics['total_applications'] > 0:
            approval_rate = (metrics['approved_applications'] / metrics['total_applications']) * 100
            st.metric("Approval Rate", f"{approval_rate:.1f}%")
        
        # Recent scholars (last 5)
        recent_scholars = get_scholars_for_admin(partner_org_id)[:5]
        if recent_scholars:
            st.subheader("Recent Scholars")
            for scholar in recent_scholars:
                created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days
                
                st.write(f"**{scholar['applications']['first_name']} {scholar['applications']['last_name']}**")
                st.caption(f"ID: {scholar['scholar_id']} • {days_ago} days ago")
                st.divider()
        else:
            st.info("No scholars yet.")
    
    # Success Stories Section (placeholder for future implementation)
    st.header("Success Stories")
    
    success_col1, success_col2 = st.columns(2)
    
    with success_col1:
        st.subheader("Recent Certifications")
        st.info("Feature coming soon - Track scholar certifications and achievements")
    
    with success_col2:
        st.subheader("Job Placements")
        st.info("Feature coming soon - Monitor scholar career success")
    
    # Quick Actions
    st.header("Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("Review Applications", use_container_width=True):
            st.switch_page("interfaces/admin/applications_view.py")
    
    with action_col2:
        if st.button("Check MoA Submissions", use_container_width=True):
            st.switch_page("interfaces/admin/moa_view.py")
    
    with action_col3:
        if st.button("View Scholars", use_container_width=True):
            st.switch_page("interfaces/admin/scholar_view.py")
    
    # System Information
    st.header("System Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.subheader("Organization Details")
        st.write(f"**Organization:** {partner_org_name}")
        st.write(f"**Admin:** {user['data']['first_name']} {user['data']['last_name']}")
        st.write(f"**Email:** {user['data']['email']}")
    
    with info_col2:
        st.subheader("Platform Status")
        st.success("System Online")
        st.info("All metrics updated in real-time")
        st.info("Last updated: Just now")