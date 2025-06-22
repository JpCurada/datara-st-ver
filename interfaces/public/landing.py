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
    
    # Hero Section with CTA
    with st.container(key="landing-hero"):
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0;">
            <h1 style="font-size: 3.2rem; font-weight: 700; margin-bottom: 0.8rem; color: white;">
                Welcome to DaTARA
            </h1>
            <h2 style="font-size: 1.4rem; color: rgba(255,255,255,0.9); font-weight: 400; margin-bottom: 1.5rem;">
                Data Science Education for All
            </h2>
            <p style="font-size: 1.1rem; max-width: 700px; margin: 0 auto 2rem auto; line-height: 1.5; color: rgba(255,255,255,0.8);">
                Empowering underrepresented communities through free, high-quality data science education and certification programs.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
            # Key Features Overview - Compact
    with st.container(key="landing-features"):
        feature_col1, feature_col2, feature_col3 = st.columns(3, gap="medium")
        
        with feature_col1:
            with st.container(key="feature-mission"):
                st.markdown("""
                <div style="text-align: center;">
                    <h3 style="color: #041b2b; font-weight: 700; margin-bottom: 1.5rem; font-size: 1.4rem;">Our Mission</h3>
                    <p style="font-size: 1rem; line-height: 1.6; color: #555; font-weight: 400;">
                        Bridge the digital divide through world-class data science education for underrepresented communities worldwide. We believe everyone deserves access to quality education.
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with feature_col2:
            with st.container(key="feature-benefits"):
                st.markdown("""
                <div style="text-align: center;">
                    <h3 style="color: #041b2b; font-weight: 700; margin-bottom: 1.5rem; font-size: 1.4rem;">What You Get</h3>
                    <p style="font-size: 1rem; line-height: 1.6; color: #555; font-weight: 400;">
                        Premium courses, industry certifications, mentorship, career support, and access to our global scholar community. Everything you need to succeed in data science.
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with feature_col3:
            with st.container(key="feature-journey"):
                st.markdown("""
                <div style="text-align: center;">
                    <h3 style="color: #041b2b; font-weight: 700; margin-bottom: 1.5rem; font-size: 1.4rem;">Your Journey</h3>
                    <p style="font-size: 1rem; line-height: 1.6; color: #555; font-weight: 400;">
                        Apply → Get Approved → Sign MoA → Learn & Grow → Get Certified → Land Your Dream Job. A clear path to success.
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # Impact Statistics
    with st.container(key="landing-stats"):
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0 1rem 0;">
            <h2 style="color: #041b2b; font-weight: 600; margin-bottom: 1.5rem;">Program Impact</h2>
        </div>
        """, unsafe_allow_html=True)
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            with st.container(key="stat-graduates"):
                st.metric(
                    label="Scholars Graduated",
                    value="2,400+",
                    help="Total program graduates"
                )
        
        with stats_col2:
            with st.container(key="stat-certifications"):
                st.metric(
                    label="Certifications",
                    value="8,200+",
                    help="Industry certifications earned"
                )
        
        with stats_col3:
            with st.container(key="stat-placements"):
                st.metric(
                    label="Job Placements",
                    value="1,800+",
                    help="Scholars employed"
                )
        
        with stats_col4:
            with st.container(key="stat-countries"):
                st.metric(
                    label="Countries",
                    value="75+",
                    help="Global reach"
                )
    
    # Partner Organizations with Images
    with st.container(key="landing-partners"):
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0 1rem 0;">
            <h2 style="color: #041b2b; font-weight: 600; margin-bottom: 0.5rem;">Our Partner Organizations</h2>
            <p style="color: #666; font-size: 1rem;">Leading organizations in data science education</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            partner_orgs = get_active_partner_organizations()
            
            if partner_orgs and len(partner_orgs) > 0:
                # Display partner logos in a grid
                partner_cols = st.columns(min(len(partner_orgs), 4), gap="medium")
                
                for i, org in enumerate(partner_orgs[:4]):  # Limit to 4 partners
                    with partner_cols[i]:
                        with st.container(key=f"partner-{i}"):
                            st.markdown(f"""
                            <div style="text-align: center;">
                                <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #07e966, #02ef61); border-radius: 50%; margin: 0 auto 1rem auto; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: white; font-size: 1.5rem; font-weight: bold;">{org[0]}</span>
                                </div>
                                <h4 style="color: #07e966; margin-bottom: 0.5rem; font-size: 1.1rem; font-weight: 600;">{org}</h4>
                                <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem; margin: 0;">Premium Data Science</p>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                # Placeholder partner logos
                placeholder_partners = ["DataCamp", "Coursera", "Kaggle", "EdX"]
                partner_cols = st.columns(4, gap="medium")
                
                for i, partner in enumerate(placeholder_partners):
                    with partner_cols[i]:
                        with st.container(key=f"partner-placeholder-{i}"):
                            st.markdown(f"""
                            <div style="text-align: center;">
                                <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #07e966, #02ef61); border-radius: 50%; margin: 0 auto 1rem auto; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: white; font-size: 1.5rem; font-weight: bold;">{partner[0]}</span>
                                </div>
                                <h4 style="color: #07e966; margin-bottom: 0.5rem; font-size: 1.1rem; font-weight: 600;">{partner}</h4>
                                <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem; margin: 0;">Premium Courses</p>
                            </div>
                            """, unsafe_allow_html=True)
                
        except Exception as e:
            st.info("Loading partner organization information...")
    
    # How It Works - Streamlined
    with st.container(key="landing-process"):
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0 1rem 0;">
            <h2 style="color: #041b2b; font-weight: 600; margin-bottom: 1.5rem;">How It Works</h2>
        </div>
        """, unsafe_allow_html=True)
        
        process_col1, process_col2, process_col3, process_col4 = st.columns(4)
        
        steps = [
            ("1", "Apply", "Submit your application with required information and eligibility details"),
            ("2", "Review", "Partner organization reviews your application within 2-3 business days"),
            ("3", "Agreement", "Sign the Memorandum of Agreement and become an approved scholar"),
            ("4", "Learn", "Start your learning journey with premium courses and certifications")
        ]
        
        for i, (step_num, title, desc) in enumerate(steps):
            with [process_col1, process_col2, process_col3, process_col4][i]:
                with st.container(key=f"process-step-{i}"):
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #07e966, #02ef61); color: white; border-radius: 50%; margin: 0 auto 1.5rem auto; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; font-weight: 700; box-shadow: 0 4px 15px rgba(7, 233, 102, 0.3);">
                            {step_num}
                        </div>
                        <h4 style="color: #041b2b; margin-bottom: 1rem; font-weight: 600; font-size: 1.2rem;">{title}</h4>
                        <p style="color: #666; font-size: 0.95rem; line-height: 1.5; margin: 0;">{desc}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Success Stories - Compact
    with st.container(key="landing-success"):
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0 1rem 0;">
            <h2 style="color: #041b2b; font-weight: 600; margin-bottom: 1.5rem;">Success Stories</h2>
        </div>
        """, unsafe_allow_html=True)
        
        story_col1, story_col2 = st.columns(2, gap="large")
        
        with story_col1:
            with st.container(key="success-story-1"):
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #f8fffe, #e8fdf7); border-radius: 10px; border-left: 4px solid #07e966;">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <div style="width: 50px; height: 50px; background: #07e966; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                            <span style="color: white; font-size: 1.2rem;">MR</span>
                        </div>
                        <div>
                            <h4 style="margin: 0; color: #041b2b;">Maria Rodriguez</h4>
                            <p style="margin: 0; color: #666; font-size: 0.9rem;">Data Analyst, Singapore</p>
                        </div>
                    </div>
                    <p style="font-style: italic; color: #555; font-size: 0.9rem; line-height: 1.4; margin: 0;">
                        "Went from unemployment to landing my dream job as a Data Analyst in 8 months. The program gave me confidence and a supportive community."
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with story_col2:
            with st.container(key="success-story-2"):
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #f8fffe, #e8fdf7); border-radius: 10px; border-left: 4px solid #07e966;">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <div style="width: 50px; height: 50px; background: #07e966; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                            <span style="color: white; font-size: 1.2rem;">JW</span>
                        </div>
                        <div>
                            <h4 style="margin: 0; color: #041b2b;">James Wilson</h4>
                            <p style="margin: 0; color: #666; font-size: 0.9rem;">ML Engineer, Kenya</p>
                        </div>
                    </div>
                    <p style="font-style: italic; color: #555; font-size: 0.9rem; line-height: 1.4; margin: 0;">
                        "From retail to Machine Learning Engineer! The structured learning path and mentorship made it possible despite my non-technical background."
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
                
