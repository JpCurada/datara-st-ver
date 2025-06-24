import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, Optional
from utils.auth import require_auth, get_current_user
from utils.db import get_supabase_client
from utils.applications import get_countries, get_provinces, get_universities_by_country  # Add university function

def scholar_profile_page():
    """Main profile page function with side-by-side layout"""
    require_auth('scholar')
    user = get_current_user()
    
    scholar_data = user['data']
    application_data = scholar_data['applications']
    scholar_id = user['scholar_id']
    
    st.title("My Profile")
    
    # Two-column layout: Profile on left, Certifications on right
    _, profile_col, _, cert_col, _ = st.columns([0.03, 1.2, 0.05, 0.8, 0.07])
    
    with profile_col:
        display_profile_section(scholar_data, application_data, scholar_id)
    
    with cert_col:
        display_certifications_section(scholar_id)

def display_profile_section(scholar_data, application_data, scholar_id):
    """Display profile information and editing on the left side"""
    
    # Initialize edit mode in session state if not exists
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    # Calculate derived fields
    scholar_since = scholar_data['created_at'][:10]
    duration = calculate_scholarship_duration(scholar_data['created_at'])
    age = calculate_age(application_data['birthdate'])
    
    # Header with toggle button - adjusted proportions for far right positioning
    header_col1, header_col2, header_col3 = st.columns([3, 0.5, 1])
    
    with header_col1:
        st.subheader("Profile Information")
    
    with header_col2:
        # Empty column for spacing
        pass
    
    with header_col3:
        # Toggle button for edit mode - positioned far right
        edit_mode_toggle = st.toggle(
            "Edit Mode", 
            value=st.session_state.edit_mode,
            help="Toggle to enable/disable profile editing"
        )
        
        # Update session state when toggle changes
        if edit_mode_toggle != st.session_state.edit_mode:
            st.session_state.edit_mode = edit_mode_toggle
            st.rerun()
    
    # Show edit mode status
    if st.session_state.edit_mode:
        st.success("**Edit Mode Active** - Only editable fields are shown below for easier editing.")
        # Show only editable fields when in edit mode
        display_editable_fields_only(scholar_data, application_data, scholar_id)
    else:
        st.info("**View Mode** - All profile information is displayed below.")
        # Show all fields in read-only mode
        display_all_profile_fields(scholar_data, application_data, age, scholar_since, duration)

def display_editable_fields_only(scholar_data, application_data, scholar_id):
    """Display only the editable fields when in edit mode"""
    
    st.markdown("### Editable Information")
    st.markdown("*Fill in the fields below and click 'Save Changes' when done.*")
    
    # Address Information - moved to top in edit mode
    st.markdown("**Address Information**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Country dropdown with predefined values
        countries = get_countries()
        current_country = application_data.get('country', '')
        
        # Find index of current country
        country_index = 0
        if current_country and current_country in countries:
            country_index = countries.index(current_country)
        
        country = st.selectbox(
            "Country", 
            options=countries, 
            index=country_index, 
            help="Select your country",
            key="edit_country"
        )
    
    with col2:
        # State/Province dropdown based on selected country
        provinces = get_provinces(country) if country else [""]
        current_state = application_data.get('state_region_province', '')
        
        # Find index of current state
        state_index = 0
        if current_state and current_state in provinces:
            state_index = provinces.index(current_state)
        
        state = st.selectbox(
            "State/Province", 
            options=provinces, 
            index=state_index, 
            help="Select your state/province",
            key="edit_state"
        )

    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City", value=application_data.get('city', ''), help="Enter your city")
    with col2:
        # Handle postal code properly
        postal_value = application_data.get('postal_code', '')
        if isinstance(postal_value, (int, float)):
            postal_value = str(int(postal_value)) if postal_value else ''
        else:
            postal_value = str(postal_value) if postal_value else ''
        
        postal = st.text_input("Postal Code", value=postal_value, help="Enter your postal code")
    
    st.divider()

    # Education Information - moved to top in edit mode
    st.markdown("**Education Information**")

    education_status = st.selectbox(
        "Education Status",
        options=["CURRENTLY_ENROLLED", "FRESH_GRADUATE", "GRADUATE", "GAP_YEAR"],
        index=["CURRENTLY_ENROLLED", "FRESH_GRADUATE", "GRADUATE", "GAP_YEAR"].index(application_data.get('education_status', 'CURRENTLY_ENROLLED')),
        help="Select your current education status"
    )
    
    # Institution Country - dropdown using get_countries()
    countries = get_countries()
    current_institution_country = application_data.get('institution_country', '')
    
    # Find index of current institution country
    institution_country_index = 0
    if current_institution_country and current_institution_country in countries:
        institution_country_index = countries.index(current_institution_country)
    
    institution_country = st.selectbox(
        "Institution Country", 
        options=countries, 
        index=institution_country_index, 
        help="Select country to load universities",
        key="edit_institution_country"
    )
    
    # Initialize institution_name to None at the start
    institution_name = None
    
    # Check if the institution country has changed
    if 'previous_institution_country' not in st.session_state:
        st.session_state.previous_institution_country = current_institution_country
    
    # Clear university cache and reset name if country changed
    if st.session_state.previous_institution_country != institution_country:
        # Clear the cache for the previous country to force fresh load
        if 'university_cache' in st.session_state and st.session_state.previous_institution_country in st.session_state.university_cache:
            # Keep cache but reset the university selection
            pass
        # Update the tracked country
        st.session_state.previous_institution_country = institution_country
        # Reset current institution when country changes
        current_institution = ""
    else:
        # Use the saved institution name if country hasn't changed
        current_institution = application_data.get('institution_name', '')
    
    # University/Institution Name - with dynamic loading
    if institution_country:
        # Initialize university cache in session state
        if 'university_cache' not in st.session_state:
            st.session_state.university_cache = {}
        
        # Check if we already have universities cached for this country
        if institution_country in st.session_state.university_cache:
            universities = st.session_state.university_cache[institution_country]
        else:
            # Only fetch universities if not cached
            with st.spinner("Loading universities..."):
                universities = get_universities_by_country(institution_country)
            # Cache the result
            st.session_state.university_cache[institution_country] = universities
        
        # Check if API returned valid universities or error messages
        if (universities and len(universities) > 0 and 
            not any(error_msg in universities[0] for error_msg in [
                "API unavailable", "University not found", "No universities found", 
                "Please type manually", "timed out", "No internet connection", "API error"
            ])):
            
            # Use dropdown when universities are available
            institution_index = 0
            if current_institution:
                # Check if current institution is in the list
                if current_institution in universities:
                    institution_index = universities.index(current_institution)
                elif "Type manually..." in universities:
                    # If "Type manually..." is available and current institution is not in list
                    institution_index = universities.index("Type manually...")
            
            selected_university = st.selectbox(
                "University/Institution", 
                options=universities, 
                index=institution_index, 
                help="Select your university",
                key="edit_institution_dropdown"
            )
            
            # If user selects "Type manually...", show text input
            if selected_university == "Type manually...":
                institution_name = st.text_input(
                    "Enter University Name", 
                    value=current_institution if current_institution else "",
                    help="Type your university name manually",
                    key="edit_institution_manual"
                )
            else:
                institution_name = selected_university
                
        else:
            # Fallback to manual input when API fails or no universities found
            st.info("University lookup unavailable. Please enter manually.")
            institution_name = st.text_input(
                "University/Institution", 
                value=current_institution if current_institution else "",
                help="Enter your university name",
                key="edit_institution_text"
            )
    else:
        st.info("Please select the institution country first to load available universities.")
        institution_name = st.text_input(
            "University/Institution", 
            value="",  # Always empty when no country selected
            disabled=True,
            help="Select institution country first"
        )
    
    st.divider()
    
    # Save and Cancel buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Changes", type="primary", use_container_width=True):
            # Validate required fields
            if not institution_country:
                st.error("Institution Country is required")
                return
            if not institution_name:
                st.error("University/Institution name is required")
                return
                
            # Update editable fields
            update_data = {
                'country': country,
                'state_region_province': state,
                'city': city,
                'postal_code': postal,
                'education_status': education_status,
                'institution_name': institution_name,
                'institution_country': institution_country
            }
            
            if update_scholar_profile(update_data, scholar_id):
                st.success("Profile updated successfully!")
                # Clear university cache and tracking after successful update
                if 'university_cache' in st.session_state:
                    del st.session_state.university_cache
                if 'previous_institution_country' in st.session_state:
                    del st.session_state.previous_institution_country
                st.session_state.edit_mode = False
                st.rerun()
            else:
                st.error("Failed to update profile")
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            # Clear tracking state on cancel
            if 'previous_institution_country' in st.session_state:
                del st.session_state.previous_institution_country
            st.session_state.edit_mode = False
            st.rerun()

def display_all_profile_fields(scholar_data, application_data, age, scholar_since, duration):
    """Display all profile fields in read-only mode"""
    
    # Identity & Basic Information
    st.markdown("**Identity & Basic Information**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Scholar ID", value=scholar_data['scholar_id'], disabled=True, help="Cannot be changed")
        st.text_input("Scholar Since", value=scholar_since, disabled=True, help="Cannot be changed")
        st.text_input("Email", value=application_data['email'], disabled=True, help="Cannot be changed")
    with col2:
        st.text_input("Partner Organization", value=scholar_data['partner_organizations']['display_name'], disabled=True, help="Cannot be changed")
        st.text_input("Duration", value=duration, disabled=True, help="Cannot be changed")
        st.text_input("Age", value=f"{age} years old", disabled=True, help="Cannot be changed")
    
    st.divider()
    
    # Personal Information
    st.markdown("**Personal Information**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("First Name", value=application_data.get('first_name', ''), disabled=True, help="Cannot be changed")
        st.text_input("Birthday", value=str(application_data.get('birthdate', '')), disabled=True, help="Cannot be changed")
    with col2:
        st.text_input("Last Name", value=application_data.get('last_name', ''), disabled=True, help="Cannot be changed")
        st.text_input("Gender", value=application_data.get('gender', ''), disabled=True, help="Cannot be changed")
    
    st.divider()
    
    # Address Information
    st.markdown("**Address Information** *(Editable - Toggle Edit Mode)*")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Country", value=application_data.get('country', ''), disabled=True, help="Toggle 'Edit Mode' to change")
        st.text_input("City", value=application_data.get('city', ''), disabled=True, help="Toggle 'Edit Mode' to change")
    with col2:
        st.text_input("State/Province", value=application_data.get('state_region_province', ''), disabled=True, help="Toggle 'Edit Mode' to change")
        
        # Handle postal code display
        postal_display = application_data.get('postal_code', '')
        if isinstance(postal_display, (int, float)):
            postal_display = str(int(postal_display)) if postal_display else ''
        else:
            postal_display = str(postal_display) if postal_display else ''
            
        st.text_input("Postal Code", value=postal_display, disabled=True, help="Toggle 'Edit Mode' to change")

    st.divider()
    
    # Education Information
    st.markdown("**Education Information** *(Editable - Toggle Edit Mode)*")
    
    st.selectbox(
        "Education Status",
        options=["CURRENTLY_ENROLLED", "FRESH_GRADUATE", "GRADUATE", "GAP_YEAR"],
        index=["CURRENTLY_ENROLLED", "FRESH_GRADUATE", "GRADUATE", "GAP_YEAR"].index(application_data.get('education_status', 'CURRENTLY_ENROLLED')),
        disabled=True,
        help="Toggle 'Edit Mode' to change"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Institution Country", value=application_data.get('institution_country', ''), disabled=True, help="Toggle 'Edit Mode' to change")
    with col2:
        st.text_input("University/Institution", value=application_data.get('institution_name', ''), disabled=True, help="Toggle 'Edit Mode' to change")

def display_certifications_section(scholar_id):
    """Display certifications section on the right side"""
    
    st.subheader("Certifications")
    
    # Display existing certifications - more compact
    display_existing_certifications_compact(scholar_id)

def display_existing_certifications_compact(scholar_id: str):
    """Display existing certifications in a compact format"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("certifications").select("*").eq("scholar_id", scholar_id).execute()
        certifications = response.data
        
        if certifications:
            st.markdown(f"**Your Certifications ({len(certifications)})**")
            
            for i, cert in enumerate(certifications):
                with st.container():
                    # Create a row: left for cert info, right for buttons
                    row_col1, row_col2 = st.columns([3, 1], gap="small", vertical_alignment="center")
                    
                    with row_col1:
                        st.markdown(f"**{cert['name']}**")
                        st.caption(f"Issued by: {cert['issuing_organization']}")
                        st.caption(f"Issued: {cert['issue_month']}/{cert['issue_year']}")
                        if cert.get('expiration_month'):
                            st.caption(f"Expires: {cert['expiration_month']}/{cert['expiration_year']}")
                        else:
                            st.caption("No expiration")
                
                    
                    with row_col2:
                        # Place buttons at the top right
                        if cert.get('credential_url'):
                            st.link_button("View", cert['credential_url'], use_container_width=True)
                        if st.button("Delete", key=f"delete_cert_{cert['certification_id']}", type="secondary", use_container_width=True):
                            if delete_certification(cert['certification_id']):
                                st.success("Deleted!")
                                st.rerun()
                st.divider()
        else:
            st.info("No certifications yet.")
            
    except Exception as e:
        st.error(f"Error loading certifications: {e}")

# Helper functions (keep all the existing helper functions)
def calculate_scholarship_duration(created_at: str) -> str:
    """Calculate how long someone has been a scholar"""
    try:
        start_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(start_date.tzinfo) if start_date.tzinfo else datetime.now()
        
        delta = now - start_date
        days = delta.days
        
        if days < 30:
            return f"{days} days"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''}"
        else:
            years = days // 365
            months = (days % 365) // 30
            if months > 0:
                return f"{years} year{'s' if years > 1 else ''}, {months} month{'s' if months > 1 else ''}"
            else:
                return f"{years} year{'s' if years > 1 else ''}"
    except Exception:
        return "Unknown"

def calculate_age(birth_date) -> int:
    """Calculate age from birth date"""
    try:
        if isinstance(birth_date, str):
            birth_date = datetime.fromisoformat(birth_date).date()
        
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except Exception:
        return 0

def update_scholar_profile(profile_data: Dict[str, Any], scholar_id: str) -> bool:
    """Update scholar profile information"""
    supabase = get_supabase_client()
    
    try:
        # Get application_id for this scholar
        application_id = get_application_id_by_scholar_id(scholar_id)
        if not application_id:
            return False
        
        # Update the applications table (where profile data is stored)
        response = supabase.table("applications").update(profile_data).eq(
            "application_id", application_id
        ).execute()
        
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Error updating profile: {e}")
        return False

def get_application_id_by_scholar_id(scholar_id: str) -> Optional[str]:
    """Get application_id for a scholar"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("scholars").select("application_id").eq("scholar_id", scholar_id).execute()
        
        if response.data:
            return response.data[0]["application_id"]
        return None
    except Exception as e:
        st.error(f"Error fetching application ID: {e}")
        return None

def delete_certification(certification_id: str) -> bool:
    """Delete a certification"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("certifications").delete().eq("certification_id", certification_id).execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Error deleting certification: {e}")
        return False

