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
        st.info("📚 No scholars found for your organization yet.")
        st.write("Scholars will appear here after:")
        st.write("1. ✅ Applications are approved")
        st.write("2. 📄 MoA documents are submitted and approved")
        st.write("3. 🎓 Scholar accounts are activated")
        return
    
    # Summary Statistics
    st.header("📊 Scholar Statistics")
    
    total_scholars = len(scholars)
    active_scholars = len([s for s in scholars if s['is_active']])
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("👥 Total Scholars", total_scholars)
    
    with stat_col2:
        st.metric("🟢 Active Scholars", active_scholars)
    
    with stat_col3:
        inactive_scholars = total_scholars - active_scholars
        st.metric("🔴 Inactive Scholars", inactive_scholars)
    
    with stat_col4:
        if total_scholars > 0:
            activity_rate = (active_scholars / total_scholars) * 100
            st.metric("📈 Activity Rate", f"{activity_rate:.1f}%")
    
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
                full_name = f"{scholar['applications']['first_name']} {scholar['applications']['last_name']}"
                st.write(f"**{full_name}**")
                st.caption(f"📧 {scholar['applications']['email']}")
                st.caption(f"🆔 {scholar['scholar_id']}")
            
            with col2:
                # Status indicator
                status_icon = "🟢" if scholar['is_active'] else "🔴"
                status_text = "Active" if scholar['is_active'] else "Inactive"
                st.write(f"{status_icon} {status_text}")
                
                # Scholar since date
                created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
                st.caption(f"📅 Scholar since: {created_date.strftime('%Y-%m-%d')}")
            
            with col3:
                # Quick stats (placeholder for future features)
                st.caption("📊 Quick Stats:")
                st.caption("🏆 Certifications: Coming soon")
                st.caption("💼 Jobs: Coming soon")
            
            with col4:
                # Action buttons
                if st.button("👁️ View Profile", key=f"view_profile_{scholar['scholar_id']}", use_container_width=True):
                    st.session_state[f"show_scholar_details_{scholar['scholar_id']}"] = True
            
            # Expandable scholar details
            if st.session_state.get(f"show_scholar_details_{scholar['scholar_id']}", False):
                with st.expander(f"Scholar Profile - {full_name}", expanded=True):
                    display_scholar_profile(scholar)
            
            st.divider()
    
    # Export functionality
    st.header("📤 Export Data")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        if st.button("📊 Export to CSV", use_container_width=True):
            # Create DataFrame for export
            export_data = []
            for scholar in filtered_scholars:
                export_data.append({
                    'Scholar ID': scholar['scholar_id'],
                    'First Name': scholar['applications']['first_name'],
                    'Last Name': scholar['applications']['last_name'],
                    'Email': scholar['applications']['email'],
                    'Status': 'Active' if scholar['is_active'] else 'Inactive',
                    'Created Date': scholar['created_at']
                })
            
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"scholars_{partner_org_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with export_col2:
        st.info("💡 **Export Features**\n\nDownload scholar data for:\n- Reporting\n- Analysis\n- Record keeping")


def display_scholar_profile(scholar):
    """Display detailed scholar profile information"""
    
    # Basic Information
    st.subheader("👤 Basic Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write(f"**Scholar ID:** {scholar['scholar_id']}")
        st.write(f"**Full Name:** {scholar['applications']['first_name']} {scholar['applications']['last_name']}")
        st.write(f"**Email:** {scholar['applications']['email']}")
    
    with info_col2:
        status_icon = "🟢" if scholar['is_active'] else "🔴"
        status_text = "Active" if scholar['is_active'] else "Inactive"
        st.write(f"**Status:** {status_icon} {status_text}")
        
        created_date = datetime.fromisoformat(scholar['created_at'].replace('Z', '+00:00'))
        st.write(f"**Scholar Since:** {created_date.strftime('%B %d, %Y')}")
        
        # Calculate tenure
        days_as_scholar = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days
        st.write(f"**Tenure:** {days_as_scholar} days")
    
    # Academic Progress Section (Placeholder)
    st.subheader("📚 Academic Progress")
    
    progress_col1, progress_col2 = st.columns(2)
    
    with progress_col1:
        st.info("🚧 **Certifications**\n\nCertification tracking coming soon!")
    
    with progress_col2:
        st.info("🚧 **Course Progress**\n\nCourse completion tracking coming soon!")
    
    # Career Development Section (Placeholder)
    st.subheader("💼 Career Development")
    
    career_col1, career_col2 = st.columns(2)
    
    with career_col1:
        st.info("🚧 **Job Placements**\n\nJob tracking coming soon!")
    
    with career_col2:
        st.info("🚧 **Success Stories**\n\nTestimonial management coming soon!")
    
    # Account Management
    st.subheader("⚙️ Account Management")
    
    # Close button
    if st.button("❌ Close Profile", key=f"close_profile_{scholar['scholar_id']}", use_container_width=True):
        if f"show_scholar_details_{scholar['scholar_id']}" in st.session_state:
            del st.session_state[f"show_scholar_details_{scholar['scholar_id']}"]
        st.rerun()