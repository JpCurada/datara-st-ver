import streamlit as st

def display_footer():
    """
    Display a consistent footer across all pages for the DaTARA scholarship platform.
    """
    
    # Simplified footer structure with minimal divs
    st.markdown("""
    <div class="datara-footer-container">
        <div class="footer-content">
            <div class="footer-brand-section">
                <h3 class="footer-brand">DaTARA</h3>
                <p class="footer-tagline">Data Science Education for All</p>
                <p class="footer-description">Empowering underrepresented communities through free, high-quality data science education and certification programs.</p>
            </div>
            <div class="footer-links-section">
                <h4 class="footer-heading">Quick Links</h4>
                <a href="/" class="footer-link">Home</a>
                <a href="/applications" class="footer-link">Apply Now</a>
                <a href="/scholar_login" class="footer-link">Scholar Login</a>
                <a href="/admin_login" class="footer-link">Admin Login</a>
            </div>
            <div class="footer-scholars-section">
                <h4 class="footer-heading">For Scholars</h4>
                <a href="/scholar_home" class="footer-link">Dashboard</a>
                <a href="/help" class="footer-link">Help & Support</a>
                <a href="/scholar_profile" class="footer-link">Profile</a>
                <a href="/community" class="footer-link">Community</a>
            </div>
            <div class="footer-info-section">
                <h4 class="footer-heading">Program Info</h4>
                <a href="/about" class="footer-link">About DaTARA</a>
                <a href="/partners" class="footer-link">Partner Organizations</a>
                <a href="/success_stories" class="footer-link">Success Stories</a>
                <a href="/faq" class="footer-link">FAQ</a>
            </div>
            <div class="footer-contact-section">
                <h4 class="footer-heading">Contact & Support</h4>
                <p class="footer-contact">📧 support@datara.org</p>
                <p class="footer-contact">🌐 www.datara.org</p>
                <p class="footer-contact">📱 Follow us on social media</p>
                <p class="footer-contact">💬 Live chat support available</p>
            </div>
        </div>
        <div class="footer-bottom">
            <div class="footer-stats">
                <span class="stat-item">2,400+ Scholars Graduated • 8,200+ Certifications Earned • 75+ Countries Reached</span>
            </div>
            <div class="footer-copyright">© 2024 DaTARA Platform. Bridging the digital divide through education. All rights reserved.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)