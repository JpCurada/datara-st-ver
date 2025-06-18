# interfaces/scholar/home.py
import streamlit as st
from datetime import datetime
from utils.auth import require_auth, get_current_user
from utils.db import get_supabase_client


def scholar_dashboard_page():
    require_auth('scholar')
    user = get_current_user()
    
    # Get scholar and application data
    scholar_data = user['data']
    application_data = scholar_data['applications']
    scholar_id = user['scholar_id']
    partner_org = scholar_data['partner_organizations']['display_name']
    
    # Welcome header
    st.title(f"Welcome, {application_data['first_name']}!")
    st.subheader(f"DaTARA Scholar • {partner_org}")
    
    # Scholar ID and status
    id_col, status_col = st.columns([2, 1])
    
    with id_col:
        st.info(f"**Your Scholar ID:** `{scholar_id}`")
    
    with status_col:
        if scholar_data['is_active']:
            st.success("Active Scholar")
        else:
            st.error("Inactive")
    
    # Quick Stats Dashboard
    st.header("Your Progress Overview")
    
    # Get scholar stats (placeholder for now)
    stats = get_scholar_stats(scholar_id)
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric(
            label="Certifications",
            value=stats.get('certifications', 0),
            help="Certifications earned through the program"
        )
    
    with stat_col2:
        st.metric(
            label="Courses Completed",
            value=stats.get('courses_completed', 0),
            help="Number of courses completed"
        )
    
    with stat_col3:
        st.metric(
            label="Days as Scholar",
            value=stats.get('days_as_scholar', 0),
            help="Days since becoming a scholar"
        )
    
    with stat_col4:
        st.metric(
            label="Job Status",
            value=stats.get('employment_status', 'Seeking'),
            help="Current employment status"
        )
    
    # Main Dashboard Sections
    dashboard_tab1, dashboard_tab2, dashboard_tab3, dashboard_tab4 = st.tabs([
        "Home", "Learning", "Achievements", "Career"
    ])
    
    with dashboard_tab1:
        display_home_section(scholar_data, application_data, partner_org)
    
    with dashboard_tab2:
        display_learning_section(scholar_id, partner_org)
    
    with dashboard_tab3:
        display_achievements_section(scholar_id)
    
    with dashboard_tab4:
        display_career_section(scholar_id)


def display_home_section(scholar_data, application_data, partner_org):
    """Display the home/overview section"""
    
    # Welcome message and program info
    st.subheader("Welcome to the DaTARA Program!")
    
    st.write(f"""
    Congratulations on becoming a **{partner_org}** scholar! You are now part of an exclusive 
    community of data science learners committed to making a positive impact through data.
    """)
    
    # Scholar Profile Summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Your Profile")
        
        profile_info = f"""
        **Full Name:** {application_data['first_name']} {application_data['last_name']}
        **Email:** {application_data['email']}
        **Program:** {partner_org} Data Science Scholarship
        **Scholar Since:** {datetime.fromisoformat(scholar_data['created_at'].replace('Z', '+00:00')).strftime('%B %Y')}
        """
        st.markdown(profile_info)
        
        # Program benefits
        st.subheader("Your Program Benefits")
        benefits = [
            "Free access to premium courses and learning materials",
            "Industry-recognized certifications upon completion",
            "Access to exclusive scholar community and networking",
            "Career support and job placement assistance",
            "Progress tracking and personalized learning paths",
            "Mentorship opportunities with industry professionals"
        ]
        
        for benefit in benefits:
            st.write(benefit)
    
    with col2:
        st.subheader("Quick Actions")
        
        # Quick action buttons
        if st.button("Start Learning", use_container_width=True, type="primary"):
            st.switch_page("interfaces/scholar/learning.py")
        
        if st.button("View Achievements", use_container_width=True):
            st.info("Navigate to the Achievements tab above!")
        
        if st.button("Update Career Info", use_container_width=True):
            st.info("Navigate to the Career tab above!")
        
        if st.button("Edit Profile", use_container_width=True):
            st.info("Profile editing coming soon!")
        
        # Important announcements
        st.subheader("Announcements")
        st.info("""
        **Welcome to DaTARA!**
        
        Start your learning journey today. 
        Complete your first course to unlock additional features!
        """)


def display_learning_section(scholar_id, partner_org):
    """Display learning progress and available courses"""
    
    st.subheader("Your Learning Journey")
    
    # Learning progress overview
    progress_col1, progress_col2 = st.columns([2, 1])
    
    with progress_col1:
        st.subheader("Learning Progress")
        
        # Progress bars (placeholder data)
        st.write("**Overall Program Progress**")
        st.progress(0.25, text="25% Complete - Keep going!")
        
        st.write("**Current Course: Introduction to Data Science**")
        st.progress(0.60, text="60% Complete - 4 of 10 modules")
        
        # Recent activity
        st.subheader("Recent Activity")
        recent_activities = [
            "Completed: Python Basics Module",
            "Started: Data Visualization with Matplotlib", 
            "Earned: Python Fundamentals Badge",
            "Joined: Study Group Discussion"
        ]
        
        for activity in recent_activities:
            st.write(activity)
    
    with progress_col2:
        st.subheader(f"{partner_org} Curriculum")
        
        # Course recommendations
        st.write("**Recommended Courses:**")
        courses = [
            "Python for Data Science",
            "Data Analysis with Pandas", 
            "Data Visualization",
            "Machine Learning Basics",
            "SQL for Data Analysis"
        ]
        
        for course in courses:
            if st.button(course, use_container_width=True):
                st.info(f"Course access coming soon!\n\nYou selected: {course}")
        
        # Study resources
        st.subheader("Study Resources")
        st.write("• Course Materials")
        st.write("• Practice Datasets") 
        st.write("• Video Tutorials")
        st.write("• Interactive Exercises")
        st.write("• Community Forums")


def display_achievements_section(scholar_id):
    """Display certifications and achievements"""
    
    st.subheader("Your Achievements")
    
    # Get certifications
    certifications = get_scholar_certifications(scholar_id)
    
    if certifications:
        st.success(f"You have earned {len(certifications)} certification(s)!")
        
        for cert in certifications:
            with st.container():
                cert_col1, cert_col2, cert_col3 = st.columns([2, 2, 1])
                
                with cert_col1:
                    st.write(f"**{cert['name']}**")
                    st.caption(f"Issued by: {cert['issuing_organization']}")
                
                with cert_col2:
                    issue_date = f"{cert['issue_month']}/{cert['issue_year']}"
                    st.write(f"Issued: {issue_date}")
                    
                    if cert.get('expiration_month'):
                        exp_date = f"{cert['expiration_month']}/{cert['expiration_year']}"
                        st.caption(f"Expires: {exp_date}")
                
                with cert_col3:
                    if cert.get('credential_url'):
                        st.link_button("View", cert['credential_url'])
                
                st.divider()
    else:
        st.info("No certifications yet. Complete your courses to earn certifications!")
    
    # Add new certification
    st.subheader("Add New Certification")
    
    with st.expander("Add a certification"):
        with st.form("add_certification"):
            cert_name = st.text_input("Certification Name")
            issuing_org = st.text_input("Issuing Organization")
            
            col1, col2 = st.columns(2)
            with col1:
                issue_month = st.selectbox("Issue Month", range(1, 13))
                issue_year = st.number_input("Issue Year", min_value=2000, max_value=2030, value=2024)
            
            with col2:
                has_expiration = st.checkbox("Has expiration date")
                if has_expiration:
                    exp_month = st.selectbox("Expiration Month", range(1, 13))
                    exp_year = st.number_input("Expiration Year", min_value=2000, max_value=2040, value=2025)
            
            credential_id = st.text_input("Credential ID (optional)")
            credential_url = st.text_input("Credential URL (optional)")
            
            if st.form_submit_button("Add Certification"):
                # Here you would save to database
                st.success("Certification added successfully!")


def display_career_section(scholar_id):
    """Display career development and job tracking"""
    
    st.subheader("Career Development")
    
    # Current employment status
    employment_status = get_scholar_employment_status(scholar_id)
    
    status_col1, status_col2 = st.columns([2, 1])
    
    with status_col1:
        st.subheader("Employment Status")
        
        if employment_status:
            st.success(f"Congratulations! Currently employed at **{employment_status['company']}**")
            st.write(f"**Position:** {employment_status['job_title']}")
        else:
            st.info("Currently seeking opportunities")
            
            # Job search resources
            st.subheader("Job Search Resources")
            resources = [
                "Resume building templates",
                "Interview preparation guides", 
                "Networking opportunities",
                "Salary negotiation tips",
                "Job matching services"
            ]
            
            for resource in resources:
                st.write(resource)
    
    with status_col2:
        st.subheader("Quick Actions")
        
        if st.button("Update Employment", use_container_width=True):
            st.session_state['show_employment_form'] = True
        
        if st.button("Job Resources", use_container_width=True):
            st.info("Job resources portal coming soon!")
        
        if st.button("Career Analytics", use_container_width=True):
            st.info("Career tracking analytics coming soon!")
    
    # Employment update form
    if st.session_state.get('show_employment_form', False):
        st.subheader("Update Employment Information")
        
        with st.form("employment_update"):
            job_title = st.text_input("Job Title")
            company = st.text_input("Company Name")
            employment_type = st.selectbox("Employment Type", 
                                         ["Full-time", "Part-time", "Contract", "Internship", "Freelance"])
            start_date = st.date_input("Start Date")
            
            testimonial = st.text_area("Share your success story (optional)", 
                                     placeholder="Tell us about your experience and how the program helped you...")
            
            if st.form_submit_button("Update Employment Status"):
                # Here you would save to database
                st.success("Employment information updated successfully!")
                st.session_state['show_employment_form'] = False
                st.rerun()
        
        if st.button("Cancel"):
            st.session_state['show_employment_form'] = False
            st.rerun()
    
    # Success stories from other scholars
    st.subheader("Success Stories from Fellow Scholars")
    
    success_stories = [
        {
            "name": "Maria R.",
            "position": "Data Analyst at Tech Corp",
            "story": "The program gave me the skills and confidence to transition into data science!"
        },
        {
            "name": "James W.", 
            "position": "ML Engineer at Startup Inc",
            "story": "From zero programming experience to machine learning engineer in 8 months!"
        }
    ]
    
    for story in success_stories:
        with st.container():
            st.write(f"**{story['name']}** - {story['position']}")
            st.write(f"*\"{story['story']}\"*")
            st.divider()


def get_scholar_stats(scholar_id: str) -> dict:
    """Get scholar statistics and progress"""
    supabase = get_supabase_client()
    
    try:
        # Get scholar creation date
        scholar_response = supabase.table("scholars").select("created_at").eq("scholar_id", scholar_id).execute()
        
        stats = {
            "certifications": 0,
            "courses_completed": 0, 
            "days_as_scholar": 0,
            "employment_status": "Seeking"
        }
        
        if scholar_response.data:
            created_date = datetime.fromisoformat(scholar_response.data[0]['created_at'].replace('Z', '+00:00'))
            days_as_scholar = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days
            stats["days_as_scholar"] = days_as_scholar
        
        # Get certifications count
        cert_response = supabase.table("certifications").select("certification_id", count="exact").eq("scholar_id", scholar_id).execute()
        stats["certifications"] = cert_response.count or 0
        
        # Get employment status
        job_response = supabase.table("jobs").select("job_title, company").eq("scholar_id", scholar_id).eq("is_published", True).execute()
        if job_response.data:
            stats["employment_status"] = "Employed"
        
        return stats
        
    except Exception as e:
        st.error(f"Error fetching scholar stats: {e}")
        return {
            "certifications": 0,
            "courses_completed": 0,
            "days_as_scholar": 0, 
            "employment_status": "Seeking"
        }


def get_scholar_certifications(scholar_id: str) -> list:
    """Get scholar's certifications"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("certifications").select("*").eq("scholar_id", scholar_id).order("issue_year", desc=True).order("issue_month", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching certifications: {e}")
        return []


def get_scholar_employment_status(scholar_id: str) -> dict:
    """Get scholar's current employment status"""
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("jobs").select("job_title, company, testimonial").eq("scholar_id", scholar_id).eq("is_published", True).order("created_at", desc=True).limit(1).execute()
        
        if response.data:
            return response.data[0]
        return None
        
    except Exception as e:
        st.error(f"Error fetching employment status: {e}")
        return None