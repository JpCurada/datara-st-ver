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
    
    # Get applications data
    applications = get_applications_for_admin(partner_org_id)
    
    if not applications:
        st.info("No applications found for your organization.")
        return

    # Filter Controls
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "PENDING", "APPROVED", "REJECTED"],
            index=1
        )
    
    with col2:
        search_term = st.text_input("Search", placeholder="Name, email, or country...")
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["Applied Date (Newest)", "Applied Date (Oldest)", "Name A-Z", "Name Z-A"]
        )
    
    with col4:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    # Apply filters
    filtered_apps = filter_applications(applications, status_filter, search_term, sort_by)
    
    # Statistics Dashboard
    display_application_statistics(filtered_apps, applications)
    
    # Applications CRUD Table
    st.header("Applications Table")
    display_applications_table(filtered_apps, admin_id)


def filter_applications(applications, status_filter, search_term, sort_by):
    """Filter and sort applications based on criteria"""
    filtered = applications.copy()
    
    # Status filter
    if status_filter != "All":
        filtered = [app for app in filtered if app['status'] == status_filter]
    
    # Search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            app for app in filtered 
            if (search_lower in f"{app['first_name']} {app['last_name']}".lower() or
                search_lower in app['email'].lower() or
                search_lower in app['country'].lower())
        ]
    
    # Sorting
    if sort_by == "Applied Date (Newest)":
        filtered.sort(key=lambda x: x['applied_at'], reverse=True)
    elif sort_by == "Applied Date (Oldest)":
        filtered.sort(key=lambda x: x['applied_at'])
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda x: f"{x['first_name']} {x['last_name']}")
    elif sort_by == "Name Z-A":
        filtered.sort(key=lambda x: f"{x['first_name']} {x['last_name']}", reverse=True)
    
    return filtered


def display_application_statistics(filtered_apps, all_apps):
    """Display application statistics and charts"""
    st.subheader("Application Statistics")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Applications", len(all_apps))
    
    with col2:
        pending_count = len([app for app in all_apps if app['status'] == 'PENDING'])
        st.metric("Pending", pending_count)
    
    with col3:
        approved_count = len([app for app in all_apps if app['status'] == 'APPROVED'])
        st.metric("Approved", approved_count)
    
    with col4:
        rejected_count = len([app for app in all_apps if app['status'] == 'REJECTED'])
        st.metric("Rejected", rejected_count)
    
    # Charts
    if len(all_apps) > 0:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Status distribution
            df = pd.DataFrame(all_apps)
            status_counts = df['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Application Status Distribution",
                color_discrete_map={
                    'PENDING': '#ffc107',
                    'APPROVED': '#28a745',
                    'REJECTED': '#dc3545'
                }
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with chart_col2:
            # Country distribution (top 10)
            country_counts = df['country'].value_counts().head(10)
            fig_country = px.bar(
                x=country_counts.values,
                y=country_counts.index,
                orientation='h',
                title="Top 10 Countries by Applications",
                labels={'x': 'Number of Applications', 'y': 'Country'}
            )
            st.plotly_chart(fig_country, use_container_width=True)


def display_applications_table(applications, admin_id):
    """Display applications in an interactive table with CRUD operations"""
    if not applications:
        st.info("No applications match your criteria.")
        return
    
    # Create DataFrame for display
    table_data = []
    for app in applications:
        applied_date = datetime.fromisoformat(app['applied_at'].replace('Z', '+00:00'))
        table_data.append({
            'ID': app['application_id'][:8] + '...',
            'Name': f"{app['first_name']} {app['last_name']}",
            'Email': app['email'],
            'Country': app['country'],
            'Education': app['education_status'],
            'Programming': app['programming_experience'],
            'Data Science': app['data_science_experience'],
            'Status': app['status'],
            'Applied': applied_date.strftime('%Y-%m-%d'),
            'Full ID': app['application_id']  # Hidden column for operations
        })
    
    df = pd.DataFrame(table_data)
    
    # Display table with selection
    st.write(f"Showing {len(applications)} applications")
    
    # Use columns for table and actions
    table_col, actions_col = st.columns([3, 1])
    
    with table_col:
        # Display table (without the Full ID column)
        display_df = df.drop(columns=['Full ID'])
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with actions_col:
        st.subheader("Actions")
        
        # Application selection
        selected_name = st.selectbox(
            "Select Application",
            options=["None"] + [row['Name'] for _, row in df.iterrows()],
            key="selected_application"
        )
        
        if selected_name != "None":
            # Find selected application
            selected_row = df[df['Name'] == selected_name].iloc[0]
            selected_id = selected_row['Full ID']
            
            # Display selected application info
            st.write("**Selected:**")
            st.write(f"Name: {selected_row['Name']}")
            st.write(f"Email: {selected_row['Email']}")
            st.write(f"Status: {selected_row['Status']}")
            
            # Action buttons
            if st.button("View Details", use_container_width=True):
                st.session_state[f"show_details_{selected_id}"] = True
                st.rerun()
            
            if selected_row['Status'] == 'PENDING':
                if st.button("Quick Approve", use_container_width=True, type="primary"):
                    if approve_application(selected_id, admin_id, "Quick approval via table"):
                        st.success("Application approved!")
                        st.rerun()
                
                if st.button("Quick Reject", use_container_width=True):
                    if reject_application(selected_id, admin_id, "Quick rejection via table"):
                        st.success("Application rejected!")
                        st.rerun()
        
        # Bulk actions
        st.divider()
        st.subheader("Bulk Actions")
        
        if st.button("Export CSV", use_container_width=True):
            csv = df.drop(columns=['Full ID']).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"applications_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Show application details if requested
    for app in applications:
        if st.session_state.get(f"show_details_{app['application_id']}", False):
            with st.expander(f"Application Details - {app['first_name']} {app['last_name']}", expanded=True):
                display_application_details(app['application_id'], admin_id, app['status'])
                
                if st.button("Close Details", key=f"close_{app['application_id']}"):
                    st.session_state[f"show_details_{app['application_id']}"] = False
                    st.rerun()


def display_application_details(application_id, admin_id, current_status):
    """Display detailed application information with review options"""
    application = get_application_details(application_id)
    
    if not application:
        st.error("Failed to load application details.")
        return
    
    # Application details in tabs
    detail_tabs = st.tabs(["Personal Info", "Education & Skills", "Demographics", "Essays", "Review Actions"])
    
    with detail_tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Full Name:** {application['first_name']} {application.get('middle_name', '')} {application['last_name']}")
            st.write(f"**Email:** {application['email']}")
            st.write(f"**Gender:** {application['gender']}")
            st.write(f"**Birth Date:** {application['birthdate']}")
        
        with col2:
            st.write(f"**Country:** {application['country']}")
            st.write(f"**State/Province:** {application['state_region_province']}")
            st.write(f"**City:** {application['city']}")
            st.write(f"**Postal Code:** {application['postal_code']}")
    
    with detail_tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Education Status:** {application['education_status']}")
            st.write(f"**Institution Country:** {application['institution_country']}")
            st.write(f"**Institution:** {application['institution_name']}")
        
        with col2:
            st.write(f"**Programming Experience:** {application['programming_experience']}")
            st.write(f"**Data Science Experience:** {application['data_science_experience']}")
            st.write(f"**Weekly Commitment:** {application['weekly_time_commitment']} hours")
    
    with detail_tabs[2]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Demographic Groups:**")
            for demo in application.get('demographics', []):
                st.write(f"• {demo}")
        
        with col2:
            st.write("**Available Devices:**")
            for device in application.get('devices', []):
                st.write(f"• {device}")
        
        with col3:
            st.write("**Internet Connectivity:**")
            for conn in application.get('connectivity', []):
                st.write(f"• {conn}")
    
    with detail_tabs[3]:
        st.write("**Why do you want this scholarship?**")
        st.info(application['scholarship_reason'])
        
        st.write("**Career Goals:**")
        st.info(application['career_goals'])
    
    with detail_tabs[4]:
        if current_status == 'PENDING':
            col1, col2 = st.columns(2)
            
            with col1:
                approval_reason = st.text_area(
                    "Approval reason (optional)",
                    key=f"approve_reason_{application_id}",
                    height=100
                )
                
                if st.button("Approve Application", key=f"approve_{application_id}", type="primary"):
                    if approve_application(application_id, admin_id, approval_reason):
                        st.success("Application approved successfully!")
                        st.balloons()
                        if f"show_details_{application_id}" in st.session_state:
                            del st.session_state[f"show_details_{application_id}"]
                        st.rerun()
                    else:
                        st.error("Failed to approve application.")
            
            with col2:
                rejection_reason = st.text_area(
                    "Rejection reason (required)",
                    key=f"reject_reason_{application_id}",
                    height=100,
                    placeholder="Please provide a detailed reason..."
                )
                
                if st.button("Reject Application", key=f"reject_{application_id}", use_container_width=True):
                    if not rejection_reason.strip():
                        st.warning("Please provide a reason for rejection.")
                    else:
                        if reject_application(application_id, admin_id, rejection_reason):
                            st.success("Application rejected.")
                            if f"show_details_{application_id}" in st.session_state:
                                del st.session_state[f"show_details_{application_id}"]
                            st.rerun()
                        else:
                            st.error("Failed to reject application.")
        else:
            status_colors = {'APPROVED': 'success', 'REJECTED': 'error'}
            status_func = getattr(st, status_colors.get(current_status, 'info'))
            status_func(f"Status: {current_status}")