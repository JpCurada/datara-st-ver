# utils/applications.py - Enhanced version with better error handling
import requests
import pycountry
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional


def _find_code(chosen_country: str) -> Optional[str]:
    """Find country code for the given country name"""
    try:
        for country in pycountry.countries:
            if country.name == chosen_country:
                return country.alpha_2
        return None
    except Exception:
        return None


def get_countries() -> List[str]:
    """Get list of all countries"""
    try:
        countries = [country.name for country in pycountry.countries]
        # Sort alphabetically for better UX
        return sorted(countries)
    except Exception as e:
        st.error(f"Error loading countries: {e}")
        # Fallback list of major countries
        return [
            "Afghanistan", "Albania", "Algeria", "Argentina", "Australia", "Austria",
            "Bangladesh", "Belgium", "Brazil", "Canada", "China", "Denmark", "Egypt",
            "France", "Germany", "India", "Indonesia", "Italy", "Japan", "Kenya",
            "Mexico", "Netherlands", "Nigeria", "Norway", "Pakistan", "Philippines",
            "Russia", "Saudi Arabia", "South Africa", "Spain", "Sweden", "Thailand",
            "Turkey", "Ukraine", "United Kingdom", "United States", "Vietnam"
        ]


def get_provinces(selected_country: str) -> List[str]:
    """Get provinces/states for the selected country"""
    try:
        country_code = _find_code(selected_country)
        if not country_code:
            return ["N/A - Please enter manually"]
        
        provinces = [sub.name for sub in pycountry.subdivisions.get(country_code=country_code)]
        
        if not provinces:
            return ["N/A - Please enter manually"]
        
        # Sort alphabetically
        return sorted(provinces)
        
    except Exception as e:
        st.warning(f"Could not load provinces for {selected_country}: {e}")
        return ["N/A - Please enter manually"]


def get_universities_by_country(selected_country: str) -> List[str]:
    """Fetch universities from API with improved error handling"""
    try:
        # Clean the country name for the API
        country_query = selected_country.strip()
        
        # Make request with timeout
        response = requests.get(
            f"http://universities.hipolabs.com/search?country={country_query}",
            timeout=10
        )
        
        if response.status_code == 200:
            universities = response.json()
            
            if not universities:
                return [f"No universities found for {selected_country} - Please type manually"]
            
            # Extract university names and sort them
            uni_names = [uni.get('name', 'Unknown University') for uni in universities if uni.get('name')]
            
            if not uni_names:
                return [f"No valid university data for {selected_country} - Please type manually"]
            
            # Remove duplicates and sort
            unique_unis = sorted(list(set(uni_names)))
            
            # Add manual entry option at the top
            return ["Type manually..."] + unique_unis
            
        else:
            return [f"University data unavailable (HTTP {response.status_code}) - Please type manually"]
            
    except requests.exceptions.Timeout:
        return ["University lookup timed out - Please type manually"]
    except requests.exceptions.ConnectionError:
        return ["No internet connection - Please type manually"]
    except Exception as e:
        st.warning(f"Error fetching universities: {e}")
        return ["API error - Please type manually"]


def send_otp_email(email: str, otp: str) -> bool:
    """
    Send OTP email to the applicant
    In production, this should use a proper email service like SendGrid, AWS SES, etc.
    """
    try:
        # For now, we'll simulate sending email and store OTP in session state
        # In production, you would implement actual email sending here
        
        st.session_state.sent_otp = otp
        
        # Log the OTP for development (remove in production)
        st.info(f"🔧 **Development Mode**: OTP sent to {email}")
        st.code(f"Your OTP: {otp}")
        
        return True
        
    except Exception as e:
        st.error(f"Failed to send OTP email: {e}")
        return False


def send_application_confirmation_email(email: str, applicant_name: str, partner_org: str) -> bool:
    """
    Send application confirmation email
    """
    try:
        # In production, implement actual email sending
        # For now, just return True to simulate success
        
        st.success(f"📧 Confirmation email sent to {email}")
        st.info(f"""
        **Email Preview:**
        
        Subject: Application Received - {partner_org} Scholarship
        
        Dear {applicant_name},
        
        Thank you for applying to the {partner_org} Data Science Scholarship program!
        
        Your application has been received and is under review. You will receive 
        an email notification within 2-3 business days regarding the status of 
        your application.
        
        Application ID: APP-{email.split('@')[0].upper()}
        
        Best regards,
        The DaTARA Team
        """)
        
        return True
        
    except Exception as e:
        st.error(f"Failed to send confirmation email: {e}")
        return False


def send_approval_email(email: str, applicant_name: str, partner_org: str, application_id: str) -> bool:
    """
    Send application approval email with login instructions
    """
    try:
        # In production, implement actual email sending
        # For now, simulate the email
        
        st.success(f"📧 Approval email sent to {email}")
        st.info(f"""
        **Approval Email Preview:**
        
        Subject: 🎉 Congratulations! Your {partner_org} Application is Approved
        
        Dear {applicant_name},
        
        Congratulations! Your application for the {partner_org} Data Science 
        Scholarship has been APPROVED!
        
        **Next Steps:**
        1. Log into the platform using:
           - Email: {email}
           - Temporary Password: {application_id}
        
        2. Change your password on first login
        3. Download and submit your signed MoA document
        4. Wait for MoA approval to become an active scholar
        
        Welcome to the DaTARA community!
        
        Best regards,
        The DaTARA Team
        """)
        
        return True
        
    except Exception as e:
        st.error(f"Failed to send approval email: {e}")
        return False


def validate_email_format(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_scholar_id_format(scholar_id: str) -> bool:
    """Validate scholar ID format (SCH + 8 digits)"""
    import re
    pattern = r'^SCH\d{8}$'
    return bool(re.match(pattern, scholar_id))


def format_phone_number(phone: str) -> str:
    """Format phone number (basic formatting)"""
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone))
    
    # Basic formatting for common lengths
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only[0] == '1':
        return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
    else:
        return phone  # Return original if can't format


def calculate_age(birth_date) -> int:
    """Calculate age from birth date"""
    from datetime import date
    
    if not birth_date:
        return 0
        
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def get_application_status_color(status: str) -> str:
    """Get color code for application status"""
    status_colors = {
        'PENDING': '#ffc107',  # Yellow
        'APPROVED': '#28a745',  # Green
        'REJECTED': '#dc3545'   # Red
    }
    return status_colors.get(status, '#6c757d')  # Default gray


def get_application_status_emoji(status: str) -> str:
    """Get emoji for application status"""
    status_emojis = {
        'PENDING': '⏳',
        'APPROVED': '✅',
        'REJECTED': '❌'
    }
    return status_emojis.get(status, '⚫')


def format_date_display(date_string: str) -> str:
    """Format date string for display"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y')
    except Exception:
        return date_string


def format_datetime_display(datetime_string: str) -> str:
    """Format datetime string for display"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except Exception:
        return datetime_string


def clean_text_input(text: str, max_length: Optional[int] = None) -> str:
    """Clean and validate text input"""
    if not text:
        return ""
    
    # Strip whitespace and clean up
    cleaned = text.strip()
    
    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())
    
    # Truncate if max_length specified
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()
    
    return cleaned


def validate_postal_code(postal_code: str, country: str) -> bool:
    """Validate postal code format based on country"""
    # Basic validation - can be enhanced for specific country formats
    if not postal_code:
        return False
    
    # Remove spaces and convert to uppercase
    postal = postal_code.replace(" ", "").upper()
    
    # Basic length check (most postal codes are 3-10 characters)
    if not (3 <= len(postal) <= 10):
        return False
    
    # Country-specific validation can be added here
    # For now, just check if it contains alphanumeric characters
    return postal.replace("-", "").isalnum()


def get_experience_level_description(level: str) -> str:
    """Get description for experience levels"""
    descriptions = {
        'NONE': 'No prior experience',
        'BEGINNER': 'Basic understanding, some tutorials completed',
        'INTERMEDIATE': 'Can work on projects with guidance',
        'ADVANCED': 'Independent project experience',
        'BASIC': 'Familiar with concepts',
    }
    return descriptions.get(level, level)


def get_demographic_group_description(group: str) -> str:
    """Get user-friendly description for demographic groups"""
    descriptions = {
        'UNEMPLOYED': 'Currently unemployed',
        'UNDEREMPLOYED': 'Working part-time or below skill level',
        'BELOW_POVERTY': 'Income below poverty line',
        'REFUGEE': 'Refugee or displaced person',
        'DISABLED': 'Person with disability',
        'STUDENT': 'Full-time student',
        'WORKING_STUDENT': 'Working while studying',
        'NONPROFIT_SCIENTIST': 'Working in nonprofit/research sector'
    }
    return descriptions.get(group, group.replace('_', ' ').title())


def export_applications_to_csv(applications: List[dict], filename: str = "applications.csv") -> str:
    """Export applications data to CSV format"""
    import pandas as pd
    import io
    
    try:
        # Flatten the data for CSV export
        export_data = []
        for app in applications:
            row = {
                'Application ID': app.get('application_id', ''),
                'Email': app.get('email', ''),
                'First Name': app.get('first_name', ''),
                'Last Name': app.get('last_name', ''),
                'Status': app.get('status', ''),
                'Country': app.get('country', ''),
                'Education Status': app.get('education_status', ''),
                'Programming Experience': app.get('programming_experience', ''),
                'Data Science Experience': app.get('data_science_experience', ''),
                'Applied Date': format_date_display(app.get('applied_at', ''))
            }
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        return df.to_csv(index=False)
        
    except Exception as e:
        st.error(f"Error exporting to CSV: {e}")
        return ""


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Trim and ensure it's not empty
    sanitized = sanitized.strip('_')
    return sanitized if sanitized else "file"


def generate_application_reference(email: str, partner_org: str) -> str:
    """Generate a reference number for the application"""
    import hashlib
    from datetime import datetime
    
    # Create a unique reference based on email, org, and timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    email_hash = hashlib.md5(f"{email}{partner_org}".encode()).hexdigest()[:6].upper()
    
    return f"APP-{partner_org[:3].upper()}-{timestamp}-{email_hash}"