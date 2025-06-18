# interfaces/admin/dashboard.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from utils.auth import require_auth, get_current_user
from utils.queries import (
    get_admin_dashboard_metrics, 
    get_scholars_for_admin,
    get_application_analytics,
    get_partner_organization_stats,
    get_applications_for_admin
)


def admin_dashboard_page():
    require_auth('admin')
    user = get_current_user()
    partner_org_id = user['partner_org_id']
    partner_org_name = user['data']['partner_organizations']['display_name']
    admin_name = f"{user['data']['first_name']} {user['data']['last_name']}"
    
    st.title(f"Admin Dashboard - {partner_org_name}")
    st.caption(f"Welcome back, {admin_name}")
    
    # Get comprehensive data
    metrics = get_admin_dashboard_metrics(partner_org_id)
    analytics = get_application_analytics(partner_org_id)
    org_stats = get_partner_organization_stats(partner_org_id)
    recent_applications = get_applications_for_admin(partner_org_id)[:10]  # Last 10
    scholars = get_scholars_for_admin(partner_org_id)
    
    # Key Metrics Dashboard
    display_key_metrics(metrics, org_stats)
    
    # Charts and Analytics
    col1, col2 = st.columns(2)
    
    with col1:
        display_application_trends(analytics, recent_applications)
        display_country_distribution(analytics)
    
    with col2:
        display_status_overview(analytics)
        display_scholar_timeline(scholars)
    
    # Recent Activity and Quick Actions
    display_recent_activity(recent_applications, scholars)
    
    # Quick Navigation
    display_quick_actions()


def display_key_metrics(metrics, org_stats):
    """Display key performance metrics"""
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_apps = metrics.get('total_applications', 0)
        pending_apps = org_stats.get('applications', {}).get('pending', 0)
        st.metric(
            label="Total Applications",
            value=total_apps,
            delta=f"{pending_apps} pending"
        )
    
    with col2:
        approved_apps = metrics.get('approved_applications', 0)
        approval_rate = (approved_apps / total_apps * 100) if total_apps > 0 else 0
        st.metric(
            label="Approved Applications",
            value=approved_apps,
            delta=f"{approval_rate:.1f}% rate"
        )
    
    with col3:
        active_scholars = metrics.get('active_scholars', 0)
        total_scholars = org_stats.get('scholars', {}).get('total', 0)
        st.metric(
            label="Active Scholars",
            value=active_scholars,
            delta=f"{total_scholars} total"
        )
    
    with col4:
        moa_submissions = metrics.get('moa_submissions', 0)
        st.metric(
            label="MoA Submissions",
            value=moa_submissions,
            delta="awaiting review" if moa_submissions > 0 else "none pending"
        )
    
    with col5:
        certifications = org_stats.get('certifications', {}).get('total', 0)
        avg_certs = (certifications / active_scholars) if active_scholars > 0 else 0
        st.metric(
            label="Certifications Earned",
            value=certifications,
            delta=f"{avg_certs:.1f} avg/scholar"
        )


def display_application_trends(analytics, recent_applications):
    """Display application submission trends"""
    st.subheader("Application Trends")
    
    if not recent_applications:
        st.info("No application data available")
        return
    
    # Process data for trends
    df = pd.DataFrame(recent_applications)
    df['applied_at'] = pd.to_datetime(df['applied_at'])
    df['application_date'] = df['applied_at'].dt.date
    
    # Group by date
    daily_apps = df.groupby('application_date').size().reset_index(name='count')
    
    # Create line chart
    fig = px.line(
        daily_apps,
        x='application_date',
        y='count',
        title='Daily Application Submissions (Last 10)',
        labels={'application_date': 'Date', 'count': 'Applications'}
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def display_status_overview(analytics):
    """Display application status distribution"""
    st.subheader("Application Status Overview")
    
    status_data = analytics.get('status_breakdown', {})
    
    if not status_data:
        st.info("No status data available")
        return
    
    # Create pie chart
    fig = px.pie(
        values=list(status_data.values()),
        names=list(status_data.keys()),
        title="Application Status Distribution",
        color_discrete_map={
            'PENDING': '#ffc107',
            'APPROVED': '#28a745',
            'REJECTED': '#dc3545'
        }
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def display_country_distribution(analytics):
    """Display geographic distribution of applications"""
    st.subheader("Geographic Distribution")
    
    country_data = analytics.get('country_breakdown', {})
    
    if not country_data:
        st.info("No country data available")
        return
    
    # Get top 10 countries
    sorted_countries = sorted(country_data.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if sorted_countries:
        countries, counts = zip(*sorted_countries)
        
        fig = px.bar(
            x=list(counts),
            y=list(countries),
            orientation='h',
            title="Top 10 Countries by Applications",
            labels={'x': 'Number of Applications', 'y': 'Country'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def display_scholar_timeline(scholars):
    """Display scholar enrollment timeline"""
    st.subheader("Scholar Enrollment Timeline")
    
    if not scholars:
        st.info("No scholar data available")
        return
    
    # Process scholar data
    df = pd.DataFrame(scholars)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['enrollment_date'] = df['created_at'].dt.date
    
    # Group by date
    daily_enrollments = df.groupby('enrollment_date').size().reset_index(name='count')
    
    # Create area chart
    fig = px.area(
        daily_enrollments,
        x='enrollment_date',
        y='count',
        title='Scholar Enrollments Over Time',
        labels={'enrollment_date': 'Date', 'count': 'New Scholars'}
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def display_recent_activity(recent_applications, scholars):
    """Display recent activity and updates"""
    st.header("Recent Activity")
    
    activity_col1, activity_col2 = st.columns(2)
    
    with activity_col1:
        st.subheader("Recent Applications")
        
        if recent_applications:
            for app in recent_applications[:5]:  # Show last 5
                applied_date = datetime.fromisoformat(app['applied_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now().replace(tzinfo=applied_date.tzinfo) - applied_date).days
                
                status_color = {
                    'PENDING': '🟡',
                    'APPROVED': '🟢', 
                    'REJECTED': '🔴'
                }.get(app['status'], '⚪')
                
                st.write(f"{status_color} **{app['first_name']} {app['last_name']}**")
                st.caption(f"{app['email']} • {app['country']} • {days_ago} days ago")
                st.divider()
        else:
            st.info("No recent applications")
    
    with activity_col2:
        st.subheader("Recent Scholars")
        
        if scholars:
            recent_scholars = sorted(scholars, key=lambda x: x['created_at'], reverse=True)[:5]
            
            for scholar in recent_scholars:
                created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days
                
                status_icon = '🟢' if scholar['is_active'] else '🔴'
                
                st.write(f"{status_icon} **{scholar['applications']['first_name']} {scholar['applications']['last_name']}**")
                st.caption(f"ID: {scholar['scholar_id']} • {days_ago} days ago")
                st.divider()
        else:
            st.info("No scholars yet")


def display_quick_actions():
    """Display quick action buttons for navigation"""
    st.header("Quick Actions")
    
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("Review Applications", use_container_width=True, type="primary"):
            st.switch_page("interfaces/admin/applications_view.py")
        
        pending_apps = st.session_state.get('pending_applications', 0)
        if pending_apps > 0:
            st.caption(f"{pending_apps} pending review")
    
    with action_col2:
        if st.button("Check MoA Submissions", use_container_width=True):
            st.switch_page("interfaces/admin/moa_view.py")
        
        pending_moas = st.session_state.get('pending_moas', 0)
        if pending_moas > 0:
            st.caption(f"{pending_moas} pending review")
    
    with action_col3:
        if st.button("Manage Scholars", use_container_width=True):
            st.switch_page("interfaces/admin/scholar_view.py")
        
        total_scholars = st.session_state.get('total_scholars', 0)
        if total_scholars > 0:
            st.caption(f"{total_scholars} active scholars")
    
    with action_col4:
        if st.button("Export Reports", use_container_width=True):
            generate_export_options()


def generate_export_options():
    """Generate export options for reports"""
    st.subheader("Export Options")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.write("**Available Reports:**")
        
        if st.button("Applications Report", use_container_width=True):
            st.info("Exporting applications data...")
            # Implementation for exporting applications
        
        if st.button("Scholars Report", use_container_width=True):
            st.info("Exporting scholars data...")
            # Implementation for exporting scholars
        
        if st.button("Analytics Report", use_container_width=True):
            st.info("Exporting analytics data...")
            # Implementation for exporting analytics
    
    with export_col2:
        st.write("**Report Formats:**")
        
        report_format = st.selectbox(
            "Choose format",
            options=["CSV", "Excel", "PDF"]
        )
        
        date_range = st.selectbox(
            "Date range",
            options=["Last 30 days", "Last 90 days", "All time"]
        )
        
        if st.button("Generate Report", use_container_width=True, type="primary"):
            st.success(f"Generating {report_format} report for {date_range}...")


# Additional helper functions for enhanced dashboard

def get_performance_indicators():
    """Calculate key performance indicators"""
    # This woul