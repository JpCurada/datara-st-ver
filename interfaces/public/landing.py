# interfaces/public/landing.py - Enhanced landing page
import streamlit as st
from utils.queries import get_active_partner_organizations
import os

# Use forward slashes for paths to ensure compatibility with Docker
parent_dir = os.path.dirname(os.path.abspath(__file__))
application_page = os.path.join(parent_dir, "interfaces", "public", "applications.py")
scholar_login_page = os.path.join(parent_dir, "interfaces", "public", "scholar_login.py")

def public_home_page():
    """Enhanced landing page for DaTARA platform"""
    
    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3.5rem; font-weight: 600; margin-bottom: 1rem;">
            Welcome to DaTARA
        </h1>
        <h2 style="font-size: 1.8rem; color: #666; font-weight: 300; margin-bottom: 2rem;">
            Data Science Education for All
        </h2>
        <p style="font-size: 1.2rem; max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Empowering underrepresented communities through free, high-quality data science education 
            and certification programs from leading industry partners.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Call-to-Action Buttons
    cta_col1, cta_col2, cta_col3 = st.columns([1, 2, 1])
    
    with cta_col2:
        button_col1, button_col2 = st.columns(2)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Program Overview
    st.header("Program Overview")
    
    overview_col1, overview_col2, overview_col3 = st.columns(3)
    
    with overview_col1:
        st.markdown("""
        ### **Our Mission**
        
        To bridge the digital divide by providing free, world-class data science education 
        to underrepresented communities worldwide.
        
        **Who We Serve:**
        - Students and recent graduates
        - Unemployed and underemployed individuals  
        - People from developing regions
        - Disabled individuals
        - Refugees and displaced persons
        """)
    
    with overview_col2:
        st.markdown("""
        ### **What You Get**
        
        **Free Access To:**
        - Premium courses and learning materials
        - Industry-recognized certifications
        - Exclusive scholar community
        - Career support and job placement
        - Personalized learning paths
        - Mentorship opportunities
        """)
    
    with overview_col3:
        st.markdown("""
        ### **Success Path**
        
        **Your Journey:**
        1. **Apply** - Submit your application
        2. **Get Approved** - Wait for review
        3. **Sign MoA** - Complete agreement
        4. **Become Scholar** - Start learning
        5. **Learn & Grow** - Complete courses
        6. **Get Certified** - Earn credentials
        7. **Land Job** - Career success!
        """)
    
    # Partner Organizations Section
    st.header("Our Partner Organizations")
    
    try:
        partner_orgs = get_active_partner_organizations()
        
        if partner_orgs:
            st.write("We're proud to partner with leading organizations in data science education:")
            
            # Display partners in a grid
            partner_cols = st.columns(len(partner_orgs))
            
            for i, org in enumerate(partner_orgs):
                with partner_cols[i]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; border: 2px solid #e0e0e0; border-radius: 10px; margin: 0.5rem;">
                        <h3 style="color: #4CAF50;">{org}</h3>
                        <p>Premium Data Science Courses</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Partner organizations information will be displayed here.")
            
    except Exception as e:
        st.info("Loading partner organization information...")
    
    # Statistics Section
    st.header("Program Impact")
    
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    with stats_col1:
        st.metric(
            label="Scholars Graduated",
            value="2,500+",
            help="Total number of program graduates"
        )
    
    with stats_col2:
        st.metric(
            label="Certifications Earned",
            value="8,200+",
            help="Industry certifications completed"
        )
    
    with stats_col3:
        st.metric(
            label="Job Placements",
            value="1,800+",
            help="Scholars who found employment"
        )
    
    with stats_col4:
        st.metric(
            label="Countries Reached",
            value="75+",
            help="Global reach of the program"
        )
    
    # How It Works Section
    st.header("How It Works")
    
    process_tabs = st.tabs(["Application", "Review", "MoA", "Scholar Life"])
    
    with process_tabs[0]:
        st.subheader("Application Process")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Step-by-Step Application:**
            
            1. **Choose Partner Organization** - Select your preferred learning platform
            2. **Personal Information** - Tell us about yourself
            3. **Geographic Details** - Where you're located
            4. **Education Background** - Your academic journey
            5. **Goals & Motivation** - Why you want to join
            6. **Demographics** - Help us understand your situation
            7. **Email Verification** - Confirm your application
            
            **Requirements:**
            - Must be 16+ years old
            - Belong to an underrepresented group
            - Demonstrate motivation to learn
            - Have access to internet and device
            """)
        
        with col2:
            st.info("""
            **Pro Tips:**
            
            - Be honest and detailed
            - Explain your career goals
            - Show your commitment
            - Double-check all information
            """)
    
    with process_tabs[1]:
        st.subheader("Review Process")
        st.markdown("""
        **What Happens After You Apply:**
        
        - **Confirmation Email** - You'll receive immediate confirmation
        - **Admin Review** - Partner organization reviews your application
        - **Review Time** - Typically 2-3 business days
        - **Evaluation Criteria**:
          - Eligibility requirements met
          - Demonstrated need and motivation
          - Commitment to complete the program
          - Clear career goals in data science
        
        **Possible Outcomes:**
        - **Approved** - Move to MoA submission
        - **Not Selected** - Feedback provided, can reapply
        """)
    
    with process_tabs[2]:
        st.subheader("Memorandum of Agreement")
        st.markdown("""
        **If Approved, You'll Need To:**
        
        1. **Receive Approval Email** - Contains login credentials
        2. **Login to Platform** - Use email + application ID as password
        3. **Change Password** - Set your secure password
        4. **Download MoA Template** - Get the agreement document
        5. **Digital Signature** - Sign the agreement
        6. **Submit MoA** - Upload signed document
        7. **Wait for Approval** - 2-3 business days
        
        **The MoA Covers:**
        - Program expectations and requirements
        - Your commitments as a scholar
        - Code of conduct and community guidelines
        - Certification and completion requirements
        """)
    
    with process_tabs[3]:
        st.subheader("Life as a Scholar")
        st.markdown("""
        **Welcome to the Community!**
        
        **Your Scholar Benefits:**
        - **Free Course Access** - Premium content at no cost
        - **Learning Resources** - Videos, exercises, projects
        - **Community Access** - Connect with fellow scholars
        - **Certifications** - Industry-recognized credentials
        - **Career Support** - Job placement assistance
        - **Progress Tracking** - Monitor your advancement
        
        **Ongoing Requirements:**
        - Regular participation in courses
        - Complete assignments and projects
        - Maintain community guidelines
        - Share your success story
        - Help other scholars when possible
        
        **Career Outcomes:**
        - Data Analyst positions
        - Machine Learning Engineer roles
        - Business Intelligence specialists
        - Research and academia opportunities
        """)
    
    # Success Stories Section
    st.header("Success Stories")
    
    story_col1, story_col2 = st.columns(2)
    
    with story_col1:
        st.markdown("""
        ### **Maria Rodriguez - Data Analyst**
        *Philippines → Tech Company, Singapore*
        
        *"I went from unemployment to landing my dream job as a Data Analyst in just 8 months. 
        The program didn't just teach me technical skills - it gave me confidence and a community 
        that believed in my potential."*
        
        **Journey:**
        - Started: Unemployed fresh graduate
        - Completed: 6 courses, 3 certifications
        - Outcome: Data Analyst at major tech firm
        """)
    
    with story_col2:
        st.markdown("""
        ### **James Wilson - ML Engineer**
        *Kenya → Fintech Startup, Remote*
        
        *"Coming from a non-technical background, I never thought I could become a Machine Learning 
        Engineer. The structured learning path and mentorship made it possible."*
        
        **Journey:**
        - Started: Working in retail
        - Completed: 8 courses, 5 certifications  
        - Outcome: ML Engineer, remote position
        """)
    
    # FAQ Section
    st.header("Frequently Asked Questions")
    
    faq_tabs = st.tabs(["Application", "Cost", "Time", "Requirements"])
    
    with faq_tabs[0]:
        st.markdown("""
        **Q: Who is eligible to apply?**
        A: Individuals from underrepresented communities, including students, unemployed, underemployed, refugees, disabled persons, and those from developing regions.
        
        **Q: Can I study part-time?**
        A: Yes! The program is designed to be flexible around your schedule.
        
        **Q: What's the time commitment?**
        A: Most scholars dedicate 6-15 hours per week, but you can go at your own pace.
        
        **Q: Is there a deadline to complete?**
        A: No strict deadlines, but we encourage consistent progress for best results.
        """)
    
    with faq_tabs[3]:
        st.markdown("""
        **Q: Do I need prior programming experience?**
        A: No! We welcome complete beginners and provide foundational courses.
        
        **Q: What technical requirements do I need?**
        A: Internet connection and a device (computer, tablet, or smartphone).
        
        **Q: What if English isn't my first language?**
        A: Many courses include subtitles and we have multilingual community support.
        """)
    
    # Call-to-Action Footer
    st.markdown("---")
    
    cta_footer_col1, cta_footer_col2, cta_footer_col3 = st.columns([1, 2, 1])
    
    with cta_footer_col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
            <h2 style="color: white; margin-bottom: 1rem;">Ready to Start Your Data Science Journey?</h2>
            <p style="font-size: 1.1rem; margin-bottom: 2rem; color: #f0f0f0;">
                Join thousands of scholars who have transformed their careers through data science education.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
                
    # Contact Information
    st.markdown("---")
    
    contact_col1, contact_col2, contact_col3 = st.columns(3)
    
    with contact_col1:
        st.markdown("""
        ### **Contact Support**
        
        **Technical Issues:**
        - tech-support@datara.org
        - Live chat (coming soon)
        
        **Application Help:**
        - applications@datara.org
        - +1-800-DATARA1
        """)
    
    with contact_col2:
        st.markdown("""
        ### **Connect With Us**
        
        **Social Media:**
        - @DaTARA_Official
        - Facebook.com/DaTARA
        - LinkedIn.com/company/datara
        
        **Newsletter:**
        - Monthly updates
        - Success stories
        """)
    
    with contact_col3:
        st.markdown("""
        ### **Resources**
        
        **Learning Resources:**
        - Study guides
        - Tutorial videos
        - Career advice
        
        **Community:**
        - Scholar forums
        - Study groups
        - Mentorship program
        """)
    
