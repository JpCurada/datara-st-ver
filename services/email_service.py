# services/email_service.py - Complete email service with all functions
import streamlit as st
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Gmail SMTP email service"""
    
    def __init__(self):
        self.smtp_server = st.secrets.email["smtp_server"]
        self.smtp_port = st.secrets.email["smtp_port"]
        self.sender_email = st.secrets.email["sender_email"]
        self.sender_password = st.secrets.email["sender_password"]
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email using Gmail SMTP"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = message.as_string()
                server.sendmail(self.sender_email, to_email, text)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False


class EmailTemplates:
    """HTML email templates for different scenarios"""
    
    @staticmethod
    def get_base_template() -> str:
        """Base HTML template for all emails"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DaTARA Platform</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #4CAF50;
                }}
                .header h1 {{
                    color: #4CAF50;
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .otp-box {{
                    background-color: #f8f9fa;
                    border: 2px dashed #4CAF50;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                    border-radius: 8px;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4CAF50;
                    letter-spacing: 8px;
                    font-family: 'Courier New', monospace;
                }}
                .credentials-box {{
                    background-color: #e8f5e8;
                    border-left: 4px solid #4CAF50;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .success {{
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>DaTARA Platform</h1>
                    <p>Data Science Education for All</p>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>&copy; 2024 DaTARA Platform. All rights reserved.</p>
                    <p>This email was sent from an automated system. Please do not reply to this email.</p>
                    <p>If you have questions, contact us at <a href="mailto:support@datara.org">support@datara.org</a></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def otp_verification_email(otp_code: str, applicant_name: str) -> tuple[str, str, str]:
        """Email template for OTP verification"""
        subject = "Verify Your DaTARA Application - OTP Code"
        
        html_content = f"""
        <h2>Hello {applicant_name},</h2>
        
        <p>Thank you for applying to the DaTARA Data Science Scholarship program!</p>
        
        <p>To complete your application submission, please verify your email address using the One-Time Password (OTP) below:</p>
        
        <div class="otp-box">
            <p><strong>Your OTP Code:</strong></p>
            <div class="otp-code">{otp_code}</div>
            <p><em>This code will expire in 10 minutes</em></p>
        </div>
        
        <div class="warning">
            <strong>Important:</strong>
            <ul>
                <li>Enter this code in the application form to proceed</li>
                <li>Do not share this code with anyone</li>
                <li>If you didn't request this code, please ignore this email</li>
            </ul>
        </div>
        
        <p>Once verified, your application will be submitted for review by our partner organization.</p>
        
        <p>Best regards,<br>
        <strong>The DaTARA Team</strong></p>
        """
        
        text_content = f"""
        Hello {applicant_name},
        
        Thank you for applying to the DaTARA Data Science Scholarship program!
        
        Your OTP Code: {otp_code}
        
        This code will expire in 10 minutes. Enter this code in the application form to complete your submission.
        
        Best regards,
        The DaTARA Team
        """
        
        full_html = EmailTemplates.get_base_template().format(content=html_content)
        return subject, full_html, text_content
    
    @staticmethod
    def application_approval_email(applicant_name: str, partner_org: str, approved_applicant_id: str, 
                                 email: str, birthdate: str, login_url: str) -> tuple[str, str, str]:
        """Email template for application approval with approved applicant credentials"""
        subject = f"Congratulations! Your {partner_org} Application is APPROVED"
        
        html_content = f"""
        <h2>Congratulations, {applicant_name}!</h2>
        
        <div class="success">
            <h3>Your application for the {partner_org} Data Science Scholarship has been <strong>APPROVED</strong>!</h3>
        </div>
        
        <p>Welcome to the DaTARA community! You are now one step closer to becoming an active scholar.</p>
        
        <h3>Your Login Credentials</h3>
        
        <div class="credentials-box">
            <h4>Use these credentials to access the platform:</h4>
            <ul>
                <li><strong>Approved Applicant ID:</strong> {approved_applicant_id}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Birth Date:</strong> {birthdate}</li>
            </ul>
        </div>
        
        <div class="warning">
            <h4>Required Next Steps:</h4>
            <ol>
                <li><strong>Login to Platform:</strong> Use the "Scholar & Approved Applicant Login" page</li>
                <li><strong>Submit MoA:</strong> Complete and submit your Memorandum of Agreement</li>
                <li><strong>Wait for Approval:</strong> 2-3 business days for MoA review</li>
                <li><strong>Receive Scholar ID:</strong> Get your final Scholar ID via email</li>
                <li><strong>Access Full Program:</strong> Begin your learning journey!</li>
            </ol>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{login_url}" class="button">Login to Platform</a>
        </div>
        
        <h3>About the MoA (Memorandum of Agreement)</h3>
        <p>The MoA is a formal agreement that outlines:</p>
        <ul>
            <li>Program expectations and requirements</li>
            <li>Your commitments as a scholar</li>
            <li>Code of conduct and community guidelines</li>
            <li>Benefits and support you'll receive</li>
        </ul>
        
        <p><strong>Important:</strong> You must complete the MoA submission within 7 days to maintain your approved status.</p>
        
        <p>If you have any questions during this process, please don't hesitate to contact our support team.</p>
        
        <p>Congratulations again, and welcome to your data science journey!</p>
        
        <p>Best regards,<br>
        <strong>The DaTARA Team</strong><br>
        <em>on behalf of {partner_org}</em></p>
        """
        
        text_content = f"""
        Congratulations, {applicant_name}!
        
        Your application for the {partner_org} Data Science Scholarship has been APPROVED!
        
        Your Login Credentials:
        - Approved Applicant ID: {approved_applicant_id}
        - Email: {email}
        - Birth Date: {birthdate}
        
        Next Steps:
        1. Login to the platform using the Scholar & Approved Applicant Login page
        2. Submit your MoA (Memorandum of Agreement)
        3. Wait 2-3 business days for MoA approval
        4. Receive your Scholar ID and full program access
        
        Login URL: {login_url}
        
        Welcome to the DaTARA community!
        
        Best regards,
        The DaTARA Team
        """
        
        full_html = EmailTemplates.get_base_template().format(content=html_content)
        return subject, full_html, text_content
    
    @staticmethod
    def scholar_activation_email(scholar_name: str, partner_org: str, scholar_id: str, 
                               platform_url: str) -> tuple[str, str, str]:
        """Email template for final scholar activation after MoA approval"""
        subject = f"Welcome to {partner_org}! You're Now an Active Scholar"
        
        html_content = f"""
        <h2>Welcome to the Program, {scholar_name}!</h2>
        
        <div class="success">
            <h3>Your MoA has been approved! You are now an <strong>ACTIVE SCHOLAR</strong> in the {partner_org} program!</h3>
        </div>
        
        <p>This is an exciting milestone in your data science journey. You now have full access to all program benefits and resources.</p>
        
        <div class="credentials-box">
            <h4>Your Scholar Information:</h4>
            <ul>
                <li><strong>Scholar ID:</strong> {scholar_id}</li>
                <li><strong>Partner Organization:</strong> {partner_org}</li>
                <li><strong>Status:</strong> Active Scholar</li>
                <li><strong>Program Start Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
            </ul>
        </div>
        
        <h3>What You Now Have Access To:</h3>
        <ul>
            <li><strong>Free Premium Courses:</strong> Full access to {partner_org} course library</li>
            <li><strong>Industry Certifications:</strong> Earn recognized credentials</li>
            <li><strong>Scholar Community:</strong> Connect with fellow learners worldwide</li>
            <li><strong>Career Support:</strong> Job placement assistance and career guidance</li>
            <li><strong>Progress Tracking:</strong> Monitor your learning advancement</li>
            <li><strong>Mentorship Program:</strong> Connect with industry professionals</li>
        </ul>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{platform_url}" class="button">Access Scholar Dashboard</a>
        </div>
        
        <div class="warning">
            <h4>Important Timeline:</h4>
            <p><strong>{partner_org} Platform Access:</strong> You will receive your {partner_org} course platform invitation within <strong>1-2 business days</strong>. This will give you direct access to the learning platform.</p>
        </div>
        
        <h3>Recommended Next Steps:</h3>
        <ol>
            <li><strong>Complete Your Profile:</strong> Add a profile picture and bio in your dashboard</li>
            <li><strong>Explore Available Courses:</strong> Browse the {partner_org} course catalog</li>
            <li><strong>Join the Community:</strong> Introduce yourself in the scholar forums</li>
            <li><strong>Set Learning Goals:</strong> Define your 3-month and 6-month objectives</li>
            <li><strong>Start Your First Course:</strong> Begin with foundational data science topics</li>
        </ol>
        
        <h3>Support & Resources:</h3>
        <ul>
            <li><strong>Technical Support:</strong> support@datara.org</li>
            <li><strong>Academic Guidance:</strong> Available through your scholar dashboard</li>
            <li><strong>Community Forums:</strong> Access via your scholar portal</li>
            <li><strong>Live Support:</strong> Regular Q&A sessions (details in platform)</li>
        </ul>
        
        <p>We're incredibly excited to have you as part of our community. Your dedication to learning and growth inspires us, and we're here to support you every step of the way.</p>
        
        <p>Remember, this is not just about learning data science – it's about transforming your career and making a positive impact in your community through data-driven solutions.</p>
        
        <p><strong>Welcome to the DaTARA family!</strong></p>
        
        <p>Best regards,<br>
        <strong>The DaTARA Team</strong><br>
        <em>in partnership with {partner_org}</em></p>
        """
        
        text_content = f"""
        Welcome to the Program, {scholar_name}!
        
        Congratulations! Your MoA has been approved and you are now an ACTIVE SCHOLAR in the {partner_org} program!
        
        Scholar Information:
        - Scholar ID: {scholar_id}
        - Partner Organization: {partner_org}
        - Status: Active Scholar
        - Program Start Date: {datetime.now().strftime('%B %d, %Y')}
        
        What you now have access to:
        - Free premium courses from {partner_org}
        - Industry-recognized certifications
        - Scholar community and networking
        - Career support and job placement assistance
        - Progress tracking and personalized learning
        - Mentorship opportunities
        
        Important: You will receive your {partner_org} platform invitation within 1-2 business days.
        
        Access your scholar dashboard: {platform_url}
        
        Welcome to the DaTARA family!
        
        Best regards,
        The DaTARA Team
        """
        
        full_html = EmailTemplates.get_base_template().format(content=html_content)
        return subject, full_html, text_content


# Main Email Functions
def send_otp_email(email: str, otp: str, applicant_name: str) -> bool:
    """Send OTP verification email"""
    try:
        email_service = EmailService()
        subject, html_content, text_content = EmailTemplates.otp_verification_email(otp, applicant_name)
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if success:
            logger.info(f"OTP email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send OTP email to {email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending OTP email: {str(e)}")
        return False


def send_approval_email(email: str, applicant_name: str, partner_org: str, 
                       scholar_id: str, birthdate: str) -> bool:
    """Send application approval email with approved applicant credentials"""
    try:
        email_service = EmailService()
        login_url = st.secrets.general.get("platform_url", "https://your-datara-platform.streamlit.app")
        
        subject, html_content, text_content = EmailTemplates.application_approval_email(
            applicant_name, partner_org, scholar_id, email, birthdate, login_url
        )
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if success:
            logger.info(f"Approval email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send approval email to {email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending approval email: {str(e)}")
        return False


def send_scholar_activation_email(email: str, scholar_name: str, partner_org: str, scholar_id: str) -> bool:
    """Send scholar activation email after MoA approval"""
    try:
        email_service = EmailService()
        platform_url = st.secrets.general.get("platform_url", "https://your-datara-platform.streamlit.app")
        
        subject, html_content, text_content = EmailTemplates.scholar_activation_email(
            scholar_name, partner_org, scholar_id, platform_url
        )
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if success:
            logger.info(f"Scholar activation email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send scholar activation email to {email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending scholar activation email: {str(e)}")
        return False


def send_application_confirmation_email(email: str, applicant_name: str, partner_org: str) -> bool:
    """Send application confirmation email"""
    try:
        email_service = EmailService()
        
        subject = f"Application Received - {partner_org} Scholarship"
        
        html_content = f"""
        <h2>Dear {applicant_name},</h2>
        
        <div class="success">
            <h3>Thank you for applying to the {partner_org} Data Science Scholarship program!</h3>
        </div>
        
        <p>Your application has been received and is under review. You will receive an email notification within 2-3 business days regarding the status of your application.</p>
        
        <div class="credentials-box">
            <h4>Application Details:</h4>
            <ul>
                <li><strong>Applicant:</strong> {applicant_name}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Partner Organization:</strong> {partner_org}</li>
                <li><strong>Submitted:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</li>
            </ul>
        </div>
        
        <p>What happens next:</p>
        <ol>
            <li>Our partner organization will review your application</li>
            <li>You'll receive an email with the decision within 2-3 business days</li>
            <li>If approved, you'll receive login credentials to access the platform</li>
            <li>You'll then complete the MoA submission process</li>
        </ol>
        
        <p>Thank you for your interest in advancing your data science skills with DaTARA!</p>
        
        <p>Best regards,<br>
        <strong>The DaTARA Team</strong></p>
        """
        
        text_content = f"""
        Dear {applicant_name},
        
        Thank you for applying to the {partner_org} Data Science Scholarship program!
        
        Your application has been received and is under review. You will receive an email notification within 2-3 business days regarding the status of your application.
        
        Application Details:
        - Applicant: {applicant_name}
        - Email: {email}
        - Partner Organization: {partner_org}
        - Submitted: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        
        What happens next:
        1. Our partner organization will review your application
        2. You'll receive an email with the decision within 2-3 business days
        3. If approved, you'll receive login credentials to access the platform
        4. You'll then complete the MoA submission process
        
        Thank you for your interest in advancing your data science skills with DaTARA!
        
        Best regards,
        The DaTARA Team
        """
        
        full_html = EmailTemplates.get_base_template().format(content=html_content)
        
        success = email_service.send_email(email, subject, full_html, text_content)
        
        if success:
            logger.info(f"Confirmation email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send confirmation email to {email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending confirmation email: {str(e)}")
        return False