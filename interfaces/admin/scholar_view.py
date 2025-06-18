# interfaces/admin/scholar_view.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.auth import require_auth, get_current_user
from utils.queries import get_scholars_for_admin


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
        st.write("Scholars will appear here when:")
        st.write("1. Applications are approved")
        st.write("2. MoA documents are submitted and approved")
        st.write("3. Scholar accounts are activated")
        return
    
    # Scholar Statistics
    st.header("Scholar Statistics")
    
    # Calculate stats
    total_scholars = len(scholars)
    active_scholars = len([s for s in scholars if s['is_active']])
    inactive_scholars = total_scholars - active_scholars
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Scholars", total_scholars)
    
    with col2:
        st.metric("Active Scholars", active_scholars)
    
    with col3:
        st.metric("Inactive Scholars", inactive_scholars)
    
    # Search and Filter Controls
    st.header("🔍 Search & Filter")
    
    search_col, filter_col, sort_col = st.columns([2, 1, 1])
    
    with search_col:
        search_term = st.text_input("Search scholars", placeholder="Enter name, email, or Scholar ID...")
    
    with filter_col:
        status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
    
    with sort_col:
        sort_option = st.selectbox("Sort by", ["Newest First", "Oldest First", "Name A-Z", "Name Z-A"])
    
    # Apply filters
    filtered_scholars = scholars.copy()
    
    # Status filter
    if status_filter == "Active":
        filtered_scholars = [s for s in filtered_scholars if s['is_active']]
    elif status_filter == "Inactive":
        filtered_scholars = [s for s in filtered_scholars if not s['is_active']]
    
    # Search filter
    if search_term:
        search_term_lower = search_term.lower()
        filtered_scholars = [
            s for s in filtered_scholars 
            if (search_term_lower in f"{s['applications']['first_name']} {s['applications']['last_name']}".lower() or
                search_term_lower in s['applications']['email'].lower() or
                search_term_lower in s['scholar_id'].lower())
        ]
    
    # Apply sorting
    if sort_option == "Newest First":
        filtered_scholars.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_option == "Oldest First":
        filtered_scholars.sort(key=lambda x: x['created_at'])
    elif sort_option == "Name A-Z":
        filtered_scholars.sort(key=lambda x: f"{x['applications']['first_name']} {x['applications']['last_name']}")
    elif sort_option == "Name Z-A":
        filtered_scholars.sort(key=lambda x: f"{x['applications']['first_name']} {x['applications']['last_name']}", reverse=True)
    
    # Display Results
    st.header(f"👥 Scholars ({len(filtered_scholars)} found)")
    
    if not filtered_scholars:
        st.info("No scholars match your search criteria.")
        return
    
    # Scholars Table/Cards
    for scholar in filtered_scholars:
        with st.container():
            # Create scholar card
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                # Scholar name and basic info
                st.write(f"**{scholar['applications']['first_name']} {scholar['applications']['last_name']}**")
                st.caption(f"{scholar['scholar_id']}")
            
            with col2:
                # Status badge
                status_icon = "Active" if scholar['is_active'] else "Inactive"
                status_color = "normal" if scholar['is_active'] else "off"
                st.write(f"Status: {status_icon}")
                
                # Program info
                st.caption(f"Program: {scholar['partner_organizations']['display_name']}")
                created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
                st.caption(f"Joined: {created_date.strftime('%Y-%m-%d')}")
            
            with col3:
                st.caption("Quick Stats:")
                st.caption("Certifications: 0")  # Placeholder
                st.caption("Jobs: Coming soon")
            
            with col4:
                # Action buttons
                if st.button("View Profile", key=f"view_profile_{scholar['scholar_id']}", use_container_width=True):
                    st.session_state[f"show_scholar_details_{scholar['scholar_id']}"] = True
            
            # Expandable scholar details
            if st.session_state.get(f"show_scholar_details_{scholar['scholar_id']}", False):
                with st.expander(f"Scholar Profile - {scholar['applications']['first_name']} {scholar['applications']['last_name']}", expanded=True):
                    display_scholar_profile(scholar)
            
            st.divider()
    
    # Export functionality
    st.divider()
    
    if st.button("Export to CSV", use_container_width=True):
        # Create export data
        export_data = []
        for scholar in scholars:
            export_data.append({
                'Scholar ID': scholar['scholar_id'],
                'First Name': scholar['applications']['first_name'],
                'Last Name': scholar['applications']['last_name'],
                'Email': scholar['applications']['email'],
                'Status': 'Active' if scholar['is_active'] else 'Inactive',
                'Country': scholar['applications']['country'],
                'Partner Organization': scholar['partner_organizations']['display_name'],
                'Created At': scholar['created_at']
            })
        
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"scholars_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )


def display_scholar_profile(scholar):
    """Display detailed scholar profile information"""
    
    # Display scholar information in a detailed format
    st.subheader("Basic Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write(f"**Full Name:** {scholar['applications']['first_name']} {scholar['applications']['last_name']}")
        st.write(f"**Email:** {scholar['applications']['email']}")
        st.write(f"**Scholar ID:** {scholar['scholar_id']}")
    
    with info_col2:
        # Status with color coding
        status_icon = "Active" if scholar['is_active'] else "Inactive"
        if scholar['is_active']:
            st.success(f"Status: {status_icon}")
        else:
            st.error(f"Status: {status_icon}")
        
        created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
        st.write(f"**Member Since:** {created_date.strftime('%Y-%m-%d')}")
        st.write(f"**Country:** {scholar['applications']['country']}")
    
    # Academic progress (placeholder for future implementation)
    st.subheader("Academic Progress")
    
    progress_col1, progress_col2 = st.columns(2)
    
    with progress_col1:
        st.info("**Certifications**\n\nCertification tracking coming soon!")
    
    with progress_col2:
        st.info("**Course Progress**\n\nCourse completion tracking coming soon!")
    
    # Career information (placeholder for future implementation)
    st.subheader("Career Development")
    
    career_col1, career_col2 = st.columns(2)
    
    with career_col1:
        st.info("Feature coming soon - Track employment status and career progress")
    
    with career_col2:
        st.info("Feature coming soon - Certifications and achievements")
    
    # Account management options
    st.subheader("Account Management")
    
    # Close profile button
    if st.button("Close Profile", key=f"close_profile_{scholar['scholar_id']}", use_container_width=True):
        if f"show_scholar_details_{scholar['scholar_id']}" in st.session_state:
            del st.session_state[f"show_scholar_details_{scholar['scholar_id']}"]
        st.rerun()