import streamlit as st
from utils.auth import require_auth, get_current_user

def scholar_help_page():
    """Help page with FAQs for scholars and approved applicants"""
    require_auth('scholar')
    user = get_current_user()
    
    # Determine user type for personalized content
    is_scholar = 'scholar_id' in user

    # FAQ Sections
    st.header("Frequently Asked Questions")
            
    # Scholar
    faq_tabs = st.tabs([
        "Learning & Courses", 
        "Certifications", 
        "Profile & Account", 
        "Technical Issues",
        "General"
    ])
        
    with faq_tabs[0]:
        display_learning_faqs()
        
    with faq_tabs[1]:
        display_certification_faqs()
    
    # Common tabs for both user types
    with faq_tabs[2]:  # Profile & Account
        display_profile_faqs()
    
    with faq_tabs[3]:  # Technical Issues
        display_technical_faqs()

    with faq_tabs[4]:  # General
        display_general_faqs()

    
    # Quick Links
    help_col1, help_col2 = st.columns(2)
    
    with help_col1:
        st.markdown("""
        ### **Contact Support**
        - **Email:** sample-email-ni-jeyps@datara.org
        - **Response time:** n hours
        - **Available:** Monday-Friday, 9 AM - 5 PM UTC+08:00
        """)
    
    with help_col2:
        st.markdown("""
        ### **Your Information**
        - **Your ID:** `{user_id}`
        - **Status:** {status}
        - **Organization:** {partner_org}
        """.format(
            user_id=user.get('scholar_id', user.get('approved_applicant_id', 'N/A')),
            status="Active Scholar" if is_scholar else "Approved Applicant",
            partner_org=user['data']['partner_organizations']['display_name']
        ))
            
    # Emergency Contact
    st.markdown("---")
    st.error("""
    ### **Emergency Contact**
    If you're experiencing urgent technical issues that prevent you from accessing your courses or submitting important documents, please contact us immediately:
    
    **Email:** sample-email-ni-jp@datara.org  
    **Subject:** URGENT - [Your Scholar/Applicant ID] - Brief description
    """)

def display_moa_faqs():
    """FAQ section for MoA process"""
    st.subheader("Memorandum of Agreement (MoA) Process")

    with st.expander("What is the MoA and why do I need to submit it?"):
        st.markdown("""
        **The Memorandum of Agreement (MoA) is your formal commitment to the scholarship program.**
        
        - **Purpose:** Establishes mutual expectations and commitments
        - **Required for:** Transitioning from Approved Applicant to Active Scholar
        - **Content:** Program terms, your responsibilities, benefits you'll receive
        - **Digital signature:** Confirms your agreement to all terms
        """)
    
    with st.expander("How do I submit my MoA?"):
        st.markdown("""
        **Step-by-step MoA submission:**
        
        1. **Login** to your dashboard with your Approved Applicant ID
        2. **Review** the MoA terms and conditions carefully
        3. **Check all agreement boxes** to confirm understanding
        4. **Type your full name** as digital signature
        5. **Click Submit** to complete the process
        6. **Wait for approval** (typically 2-3 business days)
        
        **Note:** Make sure all information is accurate before submitting.
        """)
    
    with st.expander("How long does MoA approval take?"):
        st.markdown("""
        **Typical timeline:**
        - **Submission:** Instant confirmation
        - **Review period:** 2-3 business days
        - **Approval notification:** Email confirmation
        - **Scholar activation:** Immediate after approval
        
        **If delayed:** Contact support after 5 business days.
        """)
    
    with st.expander("What if my MoA is rejected?"):
        st.markdown("""
        **Rare but possible reasons for rejection:**
        - Incomplete information
        - Terms not properly acknowledged
        - Technical submission errors
        
        **Next steps:**
        - You'll receive detailed feedback via email
        - Correct any issues mentioned
        - Resubmit the MoA
        - Contact support if you need clarification
        """)

def display_learning_faqs():
    """FAQ section for learning and courses"""
    st.subheader("Learning & Courses")

    with st.expander("Paano ako magstart kuya jeyps?"):
        st.markdown("""
        **sagot mo here:**
        
        \*sighs\*, ganito kasi yan
        
        """)
    
    with st.expander("Paano po kung di ako nakapag aral kuya jeyps?"):
        st.markdown("""
        **sagot mo here:**
        
        \*sighs\*, ganito kasi yan
        """)
    
    with st.expander("Ilang days po limit kuya jeyps?"):
        st.markdown("""
        ewan ko kasi eh, pero ganito kasi yan
        """)

def display_certification_faqs():
    """FAQ section for certifications"""
    st.subheader("Certifications")
    
    with st.expander("anong certifications kuya jeyps?"):
        st.markdown("""
        ganito kasi yan
        """)

def display_profile_faqs():
    """FAQ section for profile and account"""
    st.subheader("Profile & Account")
    
    with st.expander("How do I update my profile information?"):
        st.markdown("""
        punta ka sa profile mo, tas isaksak mo sa baga mo yung mga info mo
        """)

def display_technical_faqs():
    """FAQ section for technical issues"""
    st.subheader("Technical Issues")
    
    with st.expander("di ko maaccess"):
        st.markdown("""
        hanubayan
        """)

def display_general_faqs():
    """FAQ section for general questions"""
    st.subheader("General Questions")
    
    with st.expander("saan ako nagkulang?"):
        st.markdown("""
        "sa tulog" - kuya jeyps
        """)
