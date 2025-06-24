# interfaces/admin/scholar_view.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.auth import require_auth, get_current_user
from utils.queries import (
    get_scholars_for_admin,
    toggle_scholar_status,
    get_scholar_certifications_count,
    get_scholar_employment_status,
    get_scholar_certifications,
    get_scholar_jobs,
    batch_fetch_demographics
)
from utils.db import get_supabase_client


def admin_scholars_page():
    require_auth('admin')
    user = get_current_user()
    partner_org_id = user['partner_org_id']
    partner_org_name = user['data']['partner_organizations']['display_name']
    
    st.title(f"Scholars Directory - {partner_org_name}")
    
    # Get scholars data
    scholars = get_scholars_for_admin(partner_org_id)
    
    if not scholars:
        st.info("No scholars found for your organization yet.")
        st.write("Scholars will appear here when applications are approved and MoA documents are processed.")
        return
    
    # After fetching scholars
    application_ids = [
        s['applications']['application_id']
        for s in scholars
        if s.get('applications') and s['applications'].get('application_id')
    ]
    supabase = get_supabase_client()
    demographics_lookup = batch_fetch_demographics(supabase, application_ids, batch_size=100)

    # Top bar: left for spacing, right for Refresh button
    _, top_right = st.columns([8, 1])
    with top_right:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    # Filter Controls
    with st.container(key="admin-filters"):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All", "Active", "Inactive"]
            )

        with col2:
            search_term = st.text_input("Search", placeholder="Name, email, or Scholar ID...")

        with col3:
            sort_by = st.selectbox(
                "Sort by",
                options=["Newest First", "Oldest First", "Name A-Z", "Name Z-A", "Scholar ID"]
            )

        with col4:
            all_demographics = sorted({d for v in demographics_lookup.values() for d in v})
            selected_demographics = st.multiselect(
                "Filter by Demographic Group(s)",
                options=all_demographics
            )
    
    # Apply filters
    filtered_scholars = filter_scholars(scholars, status_filter, search_term, sort_by, demographics_lookup, selected_demographics)
    
    # Statistics Dashboard
    with st.container(key="admin-metrics"):
        display_scholar_statistics(filtered_scholars, scholars)
    
    # Scholars CRUD Table
    with st.container(key="admin-table"):
        st.header("Scholars Directory Table")
        display_scholars_table(filtered_scholars, demographics_lookup)


def filter_scholars(scholars, status_filter, search_term, sort_by, demographics_lookup, selected_demographics):
    """Filter and sort scholars based on criteria"""
    filtered = scholars.copy()
    
    # Status filter
    if status_filter == "Active":
        filtered = [s for s in filtered if s['is_active']]
    elif status_filter == "Inactive":
        filtered = [s for s in filtered if not s['is_active']]
    
    # Search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            s for s in filtered
            if (search_lower in f"{s['applications']['first_name']} {s['applications']['last_name']}".lower() or
                search_lower in s['applications']['email'].lower() or
                search_lower in s['scholar_id'].lower())
        ]
    
    # Demographics filter
    if selected_demographics:
        filtered = [
            s for s in filtered
            if set(demographics_lookup.get(s['applications']['application_id'], [])) == set(selected_demographics)
        ]
    
    # Sorting
    if sort_by == "Newest First":
        filtered.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Oldest First":
        filtered.sort(key=lambda x: x['created_at'])
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda x: f"{x['applications']['first_name']} {x['applications']['last_name']}")
    elif sort_by == "Name Z-A":
        filtered.sort(key=lambda x: f"{x['applications']['first_name']} {x['applications']['last_name']}", reverse=True)
    elif sort_by == "Scholar ID":
        filtered.sort(key=lambda x: x['scholar_id'])
    
    return filtered


def display_scholar_statistics(filtered_scholars, all_scholars):
    """Display scholar statistics and charts"""
    st.subheader("Scholar Statistics")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scholars", len(all_scholars))
    
    with col2:
        active_count = len([s for s in all_scholars if s['is_active']])
        st.metric("Active Scholars", active_count)
    
    with col3:
        inactive_count = len(all_scholars) - active_count
        st.metric("Inactive Scholars", inactive_count)
    
    with col4:
        # Calculate average days as scholar
        if all_scholars:
            avg_days = sum([
                (datetime.now().replace(tzinfo=datetime.fromisoformat(s['created_at'].replace('Z', '+00:00')).tzinfo) - 
                 datetime.fromisoformat(s['created_at'].replace('Z', '+00:00'))).days
                for s in all_scholars
            ]) / len(all_scholars)
            st.metric("Avg. Days Active", int(avg_days))
    
    # Charts
    if len(all_scholars) > 0:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Scholar enrollment over time
            df = pd.DataFrame([
                {
                    'created_date': s['created_at'],
                    'scholar_id': s['scholar_id'],
                    'country': s['applications']['country']
                }
                for s in all_scholars
            ])
            
            df['created_date'] = pd.to_datetime(df['created_date'], format='ISO8601')
            df['enrollment_date'] = df['created_date'].dt.date
            daily_enrollments = df.groupby('enrollment_date').size().reset_index(name='count')
            
            fig_timeline = px.line(
                daily_enrollments,
                x='enrollment_date',
                y='count',
                title="Scholar Enrollment Over Time",
                labels={'enrollment_date': 'Date', 'count': 'New Scholars'}
            )
            fig_timeline.update_layout(
                font=dict(color='#041b2b'),
                paper_bgcolor='rgba(255,255,255,0.8)',
                plot_bgcolor='rgba(255,255,255,0.8)'
            )
            fig_timeline.update_traces(line_color='#07e966', line_width=3)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        with chart_col2:
            # Country distribution
            country_counts = df['country'].value_counts().head(10)
            fig_country = px.bar(
                x=country_counts.values,
                y=country_counts.index,
                orientation='h',
                title="Top 10 Countries by Scholar Count",
                labels={'x': 'Number of Scholars', 'y': 'Country'}
            )
            fig_country.update_layout(
                font=dict(color='#041b2b'),
                paper_bgcolor='rgba(255,255,255,0.8)',
                plot_bgcolor='rgba(255,255,255,0.8)'
            )
            fig_country.update_traces(marker_color='#07e966')
            st.plotly_chart(fig_country, use_container_width=True)


def display_scholars_table(scholars, demographics_lookup):
    """Display scholars in an interactive table with CRUD operations"""
    if not scholars:
        st.info("No scholars match your criteria.")
        return
    
    # Create DataFrame for display
    table_data = []
    for scholar in scholars:
        created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
        days_active = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days
        
        # Get additional data
        certifications_count = get_scholar_certifications_count(scholar['scholar_id'])
        employment_status = get_scholar_employment_status(scholar['scholar_id'])
        
        # Demographics
        demographics = demographics_lookup.get(scholar['applications']['application_id'], [])
        
        table_data.append({
            'Scholar ID': scholar['scholar_id'],
            'Name': f"{scholar['applications']['first_name']} {scholar['applications']['last_name']}",
            'Email': scholar['applications']['email'],
            'Country': scholar['applications']['country'],
            'Status': 'Active' if scholar['is_active'] else 'Inactive',
            'Days Active': days_active,
            'Certifications': certifications_count,
            'Employment': employment_status,
            'Joined': created_date.strftime('%Y-%m-%d'),
            'Demographics': ", ".join(demographics) if demographics else "N/A",
            'Full Data': scholar  # Hidden column for operations
        })
    
    df = pd.DataFrame(table_data)
    
    # Display table with selection
    st.write(f"Showing {len(scholars)} scholars")
    
    # Use columns for table and actions
    table_col, actions_col = st.columns([3, 1])
    
    with table_col:
        # Display table (without the Full Data column)
        display_df = df.drop(columns=['Full Data'])
        
        # Color code the status column
        def highlight_status(val):
            if val == 'Active':
                return 'background-color: #d4edda'
            elif val == 'Inactive':
                return 'background-color: #f8d7da'
            return ''
        
        styled_df = display_df.style.applymap(highlight_status, subset=['Status'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with actions_col:
        st.subheader("Actions")
        
        # Scholar selection
        selected_name = st.selectbox(
            "Select Scholar",
            options=["None"] + [row['Name'] for _, row in df.iterrows()],
            key="selected_scholar"
        )
        
        if selected_name != "None":
            # Find selected scholar
            selected_row = df[df['Name'] == selected_name].iloc[0]
            selected_scholar = selected_row['Full Data']
            
            # Display selected scholar info
            st.write("**Selected:**")
            st.write(f"Name: {selected_row['Name']}")
            st.write(f"ID: {selected_row['Scholar ID']}")
            st.write(f"Status: {selected_row['Status']}")
            st.write(f"Certifications: {selected_row['Certifications']}")
            
            # Action buttons
            if st.button("View Profile", use_container_width=True):
                st.session_state[f"show_scholar_profile_{selected_scholar['scholar_id']}"] = True
                st.rerun()
            
            if st.button("View Certifications", use_container_width=True):
                st.session_state[f"show_certs_{selected_scholar['scholar_id']}"] = True
                st.rerun()
            
            if selected_scholar['is_active']:
                if st.button("Deactivate", use_container_width=True):
                    if toggle_scholar_status(selected_scholar['scholar_id'], False):
                        st.success("Scholar deactivated")
                        st.rerun()
            else:
                if st.button("Reactivate", use_container_width=True, type="primary"):
                    if toggle_scholar_status(selected_scholar['scholar_id'], True):
                        st.success("Scholar reactivated")
                        st.rerun()
        
        # Bulk actions
        st.divider()
        st.subheader("Bulk Actions")
        
        if st.button("Export CSV", use_container_width=True):
            csv = df.drop(columns=['Full Data']).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"scholars_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        if st.button("Send Bulk Email", use_container_width=True):
            st.info("Bulk email feature coming soon")
    
    # Show scholar profiles if requested
    for scholar in scholars:
        if st.session_state.get(f"show_scholar_profile_{scholar['scholar_id']}", False):
            with st.expander(f"Scholar Profile - {scholar['applications']['first_name']} {scholar['applications']['last_name']}", expanded=True):
                display_scholar_profile(scholar)
                
                if st.button("Close Profile", key=f"close_profile_{scholar['scholar_id']}"):
                    st.session_state[f"show_scholar_profile_{scholar['scholar_id']}"] = False
                    st.rerun()
        
        if st.session_state.get(f"show_certs_{scholar['scholar_id']}", False):
            with st.expander(f"Certifications - {scholar['applications']['first_name']} {scholar['applications']['last_name']}", expanded=True):
                display_scholar_certifications(scholar['scholar_id'])
                
                if st.button("Close Certifications", key=f"close_certs_{scholar['scholar_id']}"):
                    st.session_state[f"show_certs_{scholar['scholar_id']}"] = False
                    st.rerun()

    missing_app_id_count = sum(
        1 for s in scholars if not (s.get('applications') and s['applications'].get('application_id'))
    )
    if missing_app_id_count:
        st.warning(f"{missing_app_id_count} scholars have missing application IDs and are not shown in the directory.")


def display_scholar_profile(scholar):
    """Display detailed scholar profile information"""
    st.subheader("Scholar Profile")
    
    # Profile tabs
    profile_tabs = st.tabs(["Basic Info", "Academic Progress", "Career Status", "Account Management"])
    
    with profile_tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Full Name:** {scholar['applications']['first_name']} {scholar['applications']['last_name']}")
            st.write(f"**Email:** {scholar['applications']['email']}")
            st.write(f"**Scholar ID:** {scholar['scholar_id']}")
            st.write(f"**Country:** {scholar['applications']['country']}")
        
        with col2:
            created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
            days_active = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days
            
            status_func = st.success if scholar['is_active'] else st.error
            status_func(f"Status: {'Active' if scholar['is_active'] else 'Inactive'}")
            
            st.write(f"**Joined:** {created_date.strftime('%Y-%m-%d')}")
            st.write(f"**Days Active:** {days_active}")
            st.write(f"**Partner Org:** {scholar['partner_organizations']['display_name']}")
    
    with profile_tabs[1]:
        # Academic progress
        certifications = get_scholar_certifications(scholar['scholar_id'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Certifications")
            if certifications:
                for cert in certifications:
                    st.write(f"**{cert['name']}**")
                    st.caption(f"Issued by: {cert['issuing_organization']}")
                    st.caption(f"Date: {cert['issue_month']}/{cert['issue_year']}")
                    st.divider()
            else:
                st.info("No certifications yet")
        
        with col2:
            st.subheader("Learning Progress")
            st.info("Course progress tracking coming soon")
    
    with profile_tabs[2]:
        # Career status
        jobs = get_scholar_jobs(scholar['scholar_id'])
        
        if jobs:
            for job in jobs:
                st.subheader("Current Employment")
                st.write(f"**Position:** {job['job_title']}")
                st.write(f"**Company:** {job['company']}")
                if job.get('testimonial'):
                    st.write("**Testimonial:**")
                    st.info(job['testimonial'])
        else:
            st.info("No employment information available")
    
    with profile_tabs[3]:
        # Account management
        st.subheader("Account Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if scholar['is_active']:
                if st.button("Deactivate Scholar", key=f"deactivate_profile_{scholar['scholar_id']}"):
                    if toggle_scholar_status(scholar['scholar_id'], False):
                        st.success("Scholar deactivated")
                        st.rerun()
            else:
                if st.button("Reactivate Scholar", key=f"reactivate_profile_{scholar['scholar_id']}", type="primary"):
                    if toggle_scholar_status(scholar['scholar_id'], True):
                        st.success("Scholar reactivated")
                        st.rerun()
        
        with col2:
            if st.button("Send Email", key=f"email_scholar_{scholar['scholar_id']}"):
                st.info("Email feature coming soon")
            
            if st.button("Reset Password", key=f"reset_pwd_{scholar['scholar_id']}"):
                st.info("Password reset feature coming soon")


def display_scholar_certifications(scholar_id):
    """Display scholar's certifications in detail"""
    certifications = get_scholar_certifications(scholar_id)
    
    if not certifications:
        st.info("No certifications found for this scholar.")
        return
    
    st.subheader(f"Certifications ({len(certifications)} total)")
    
    # Create table of certifications
    cert_data = []
    for cert in certifications:
        cert_data.append({
            'Name': cert['name'],
            'Issuing Organization': cert['issuing_organization'],
            'Issue Date': f"{cert['issue_month']}/{cert['issue_year']}",
            'Expiration': f"{cert.get('expiration_month', 'N/A')}/{cert.get('expiration_year', 'N/A')}" if cert.get('expiration_month') else 'No Expiration',
            'Credential ID': cert.get('credential_id', 'N/A'),
            'URL': cert.get('credential_url', 'N/A')
        })
    
    df = pd.DataFrame(cert_data)
    st.dataframe(df, use_container_width=True, hide_index=True)