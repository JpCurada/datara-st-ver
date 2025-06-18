import streamlit as st
from datetime import date, timedelta
import requests
import re
import random
import time

from utils.applications import get_countries, get_provinces, get_universities_by_country
from utils.queries import check_email_in_scholars, check_email_in_applications, get_active_partner_organizations, save_application_to_database
from services.email_service import send_otp_email

@st.fragment
def public_applications_page():
    # Initialize session TTL (3 days)
    if "form_creation_time" not in st.session_state:
        st.session_state.form_creation_time = time.time()
    
    # Check if session has expired (3 days = 259200 seconds)
    if time.time() - st.session_state.form_creation_time > 259200:
        st.error("Your session has expired. Please start a new application.")
        if st.button("Start New Application"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return

    steps = [
        "Partner Organization & Data Privacy",
        "Basic Information", 
        "Geographic Details",
        "Education Details",
        "Interest Details",
        "Demographic and Connectivity",
        "Review and Submission"
    ]

    if "step" not in st.session_state:
        st.session_state.step = 0
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}
    if "otp_verified" not in st.session_state:
        st.session_state.otp_verified = False

    # Progress bar
    _, progress_col, _ = st.columns([1, 3, 1])
    progress = (st.session_state.step + 1) / len(steps)
    progress_col.progress(progress, text=f"Step {st.session_state.step + 1} of {len(steps)}: {steps[st.session_state.step]}")
    
    _, step_col, _ = st.columns([1, 3, 1])
    with step_col:
        step = st.session_state.step

        # --- Step 0: Partner Organization & Data Privacy ---
        if step == 0:
            data = st.session_state.form_data.get(steps[0], {})
            
            st.subheader(steps[0])
            
            # Get active partner organizations
            partner_orgs = get_active_partner_organizations()
            partner_org_choice = st.selectbox(
                "Partner Organization", 
                partner_orgs, 
                index=partner_orgs.index(data.get("partner_org")) if data.get("partner_org") in partner_orgs else None,
                key="partner_org"
            )
            
            agree = st.checkbox(
                "I agree to the data privacy policy", 
                value=data.get("privacy_agree", False),
                key="privacy_agree"
            )
            
            email = st.text_input(
                "Email Address", 
                value=data.get("email", ""),
                key="email", 
                disabled=(partner_org_choice is None or not agree)
            )
            
            # Email validation
            email_error = ""
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                email_error = "Please enter a valid email address"
            
            if email_error:
                st.error(email_error)
            
            col1, col2 = st.columns([1, 1])
            with col2:
                can_proceed = (partner_org_choice is not None and agree and email and not email_error)
                next_clicked = st.button(
                    "Next", 
                    key="next0", 
                    disabled=not can_proceed,
                    use_container_width=True
                )
                
            if next_clicked:
                # Check email validations
                if check_email_in_scholars(email, partner_org_choice):
                    st.error("This email is already registered as a scholar. You cannot apply again.")
                    return
                
                application_status = check_email_in_applications(email, partner_org_choice)
                if application_status in ['PENDING', 'APPROVED']:
                    st.error(f"You already have a {application_status.lower()} application for {partner_org_choice}.")
                    return
                
                st.session_state.form_data[steps[0]] = {
                    "partner_org": partner_org_choice,
                    "email": email,
                    "privacy_agree": agree
                }
                st.session_state.step += 1
                st.rerun()

        # --- Step 1: Basic Information ---
        elif step == 1:
            data = st.session_state.form_data.get(steps[1], {})
            
            st.subheader(steps[1])
            
            fn_col, mn_col, ln_col = st.columns([1, 1, 1])
            with fn_col:
                fn = st.text_input("First Name *", value=data.get("first_name", ""), key="fn", max_chars=100)
            with mn_col:
                mn = st.text_input("Middle Name", value=data.get("middle_name", ""), key="mn", max_chars=100)
            with ln_col:
                ln = st.text_input("Last Name *", value=data.get("last_name", ""), key="ln", max_chars=100)

            gender_col, dob_col, age_col = st.columns([1, 2, 1])
            with gender_col:
                gender_options = ["MALE", "FEMALE", "OTHER"]
                gender_index = gender_options.index(data.get("gender")) if data.get("gender") in gender_options else None
                gender = st.selectbox("Gender *", gender_options, index=gender_index, key="gender")
            
            with dob_col:
                min_date = date.today().replace(year=date.today().year - 16)
                dob = st.date_input(
                    "Date of Birth *", 
                    value=data.get("birthdate", min_date),
                    key="dob", 
                    min_value=date(1900, 1, 1), 
                    max_value=min_date,
                    help="You must be at least 16 years old"
                )

            with age_col:            # Calculate and display age
                if dob:
                    today = date.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    st.info(f"Age: {age} years")
            

            
            col1, col2 = st.columns([1, 1])
            with col1:
                prev_clicked = st.button("Previous", key="prev1", use_container_width=True)
            with col2:
                can_proceed = fn and ln and gender and dob
                next_clicked = st.button("Next", key="next1", disabled=not can_proceed, use_container_width=True)
                
            if prev_clicked:
                st.session_state.form_data[steps[1]] = {
                    "first_name": fn,
                    "middle_name": mn,
                    "last_name": ln,
                    "gender": gender,
                    "birthdate": dob
                }
                st.session_state.step -= 1
                st.rerun()
                
            if next_clicked:
                st.session_state.form_data[steps[1]] = {
                    "first_name": fn,
                    "middle_name": mn,
                    "last_name": ln,
                    "gender": gender,
                    "birthdate": dob
                }
                st.session_state.step += 1
                st.rerun()

        # --- Step 2: Geographic Details ---
        elif step == 2:
            data = st.session_state.form_data.get(steps[2], {})
            
            st.subheader(steps[2])
            
            country_col, state_col = st.columns([1, 1])
            with country_col:
                countries = get_countries()
                selected_country = st.selectbox("Country *", options=countries, index=0, key="country")
            with state_col:
                provinces = get_provinces(selected_country) if selected_country else [""]
                selected_state = st.selectbox("State/Region/Province *", options=provinces, index=0, key="state")

            city_col, postal_col = st.columns([1, 1])
            with city_col:
                city = st.text_input("City *", value=data.get("city", ""), key="city", max_chars=100)
            with postal_col:
                # Ensure the value is a number; default to 0 if not present
                postal = st.number_input("Postal/Zip Code *", value=int(data.get("postal", 0)), key="postal")

            col1, col2 = st.columns([1, 1])
            with col1:
                prev_clicked = st.button("Previous", key="prev2", use_container_width=True)
            with col2:
                can_proceed = bool(selected_country and selected_state and city and postal)
                next_clicked = st.button("Next", key="next2", disabled=not can_proceed, use_container_width=True)

            if prev_clicked:
                st.session_state.form_data[steps[2]] = {
                    "country": selected_country,
                    "state": selected_state,
                    "city": city,
                    "postal": postal
                }
                st.session_state.step -= 1
                st.rerun()

            if next_clicked:
                st.session_state.form_data[steps[2]] = {
                    "country": selected_country, "state": selected_state, "city": city, "postal": postal
                }
                st.session_state.step += 1  
                st.rerun()

        # --- Step 3: Education Details ---
        elif step == 3:
            data = st.session_state.form_data.get(steps[3], {})
            
            st.subheader(steps[3])
            
            education_status_options = ["CURRENTLY_ENROLLED", "FRESH_GRADUATE", "GRADUATE", "GAP_YEAR"]
            education_status_index = education_status_options.index(data.get("education_status")) if data.get("education_status") in education_status_options else None
            education_status = st.selectbox("Education Status *", education_status_options, index=education_status_index, key="education_status")
            
            institution_country = st.text_input("Institution/University Country *", value=data.get("institution_country", ""), key="institution_country", max_chars=100)
            
            # Fetch universities when country is provided
            institution_name = None
            if institution_country:
                with st.spinner("Loading universities..."):
                    universities = get_universities_by_country(institution_country)
                
                # Allow manual input if API fails
                if "API unavailable" in universities[0] or "University not found" in universities[0]:
                    institution_name = st.text_input("Institution Name *", value=data.get("institution_name", ""), key="institution_name")
                else:
                    institution_index = universities.index(data.get("institution_name")) if data.get("institution_name") in universities else None
                    institution_name = st.selectbox("Institution Name *", universities, index=institution_index, key="institution_name")
            else:
                st.info("Please enter the institution/university country first to load available institutions.")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                prev_clicked = st.button("Previous", key="prev3", use_container_width=True)
            with col2:
                can_proceed = education_status and institution_country and institution_name
                next_clicked = st.button("Next", key="next3", disabled=not can_proceed, use_container_width=True)
                
            if prev_clicked:
                st.session_state.form_data[steps[3]] = {
                    "education_status": education_status,
                    "institution_country": institution_country,
                    "institution_name": institution_name
                }
                st.session_state.step -= 1
                st.rerun()
                
            if next_clicked:
                st.session_state.form_data[steps[3]] = {
                    "education_status": education_status,
                    "institution_country": institution_country,
                    "institution_name": institution_name
                }
                st.session_state.step += 1
                st.rerun()

        # --- Step 4: Interest Details ---
        elif step == 4:
            data = st.session_state.form_data.get(steps[4], {})
            
            st.subheader(steps[4])
            
            prog_exp_col, ds_exp_col = st.columns([1, 1])
            with prog_exp_col:
                prog_exp_options = ["NONE", "BEGINNER", "INTERMEDIATE", "ADVANCED"]
                prog_exp_index = prog_exp_options.index(data.get("programming_experience")) if data.get("programming_experience") in prog_exp_options else None
                prog_exp = st.selectbox("Programming Experience Level *", prog_exp_options, index=prog_exp_index, key="programming_experience")
            
            with ds_exp_col:
                ds_exp_options = ["NONE", "BASIC", "INTERMEDIATE", "ADVANCED"]
                ds_exp_index = ds_exp_options.index(data.get("data_science_experience")) if data.get("data_science_experience") in ds_exp_options else None
                ds_exp = st.selectbox("Data Science Experience Level *", ds_exp_options, index=ds_exp_index, key="data_science_experience")
            
            time_commitment_options = ["1-2", "3-5", "6-10", "11-15", "16+"]
            time_commitment_index = time_commitment_options.index(data.get("time_commitment")) if data.get("time_commitment") in time_commitment_options else None
            time_commitment = st.selectbox("Weekly Time Commitment *", time_commitment_options, index=time_commitment_index, key="time_commitment")
            
            why_scholarship = st.text_area("Why do you want this scholarship? *", value=data.get("why_scholarship", ""), key="why_scholarship", max_chars=1000, height=100)
            
            career_goals = st.text_area("Career Goals *", value=data.get("career_goals", ""), key="career_goals", max_chars=500, height=80)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                prev_clicked = st.button("Previous", key="prev4", use_container_width=True)
            with col2:
                can_proceed = prog_exp and ds_exp and time_commitment and why_scholarship and career_goals
                next_clicked = st.button("Next", key="next4", disabled=not can_proceed, use_container_width=True)
                
            if prev_clicked:
                st.session_state.form_data[steps[4]] = {
                    "programming_experience": prog_exp,
                    "data_science_experience": ds_exp,
                    "time_commitment": time_commitment,
                    "why_scholarship": why_scholarship,
                    "career_goals": career_goals
                }
                st.session_state.step -= 1
                st.rerun()
                
            if next_clicked:
                st.session_state.form_data[steps[4]] = {
                    "programming_experience": prog_exp,
                    "data_science_experience": ds_exp,
                    "time_commitment": time_commitment,
                    "why_scholarship": why_scholarship,
                    "career_goals": career_goals
                }
                st.session_state.step += 1
                st.rerun()

        # --- Step 5: Demographic and Connectivity ---
        elif step == 5:
            data = st.session_state.form_data.get(steps[5], {})
            
            st.subheader(steps[5])
            
            demographic_options = ["UNEMPLOYED", "UNDEREMPLOYED", "BELOW_POVERTY", "REFUGEE", "DISABLED", "STUDENT", "WORKING_STUDENT", "NONPROFIT_SCIENTIST"]
            demographic = st.multiselect("Demographic Group *", demographic_options, default=data.get("demographic", []), key="demographic")
            
            device_options = ["SMARTPHONE", "LAPTOP", "DESKTOP"]
            devices = st.multiselect("Devices *", device_options, default=data.get("devices", []), key="devices")
            
            connectivity_options = ["MOBILE_DATA", "WIFI"]
            connectivity = st.multiselect("Internet Connectivity *", connectivity_options, default=data.get("connectivity", []), key="connectivity")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                prev_clicked = st.button("Previous", key="prev5", use_container_width=True)
            with col2:
                can_proceed = demographic and devices and connectivity
                next_clicked = st.button("Next", key="next5", disabled=not can_proceed, use_container_width=True)
                
            if prev_clicked:
                st.session_state.form_data[steps[5]] = {
                    "demographic": demographic,
                    "devices": devices,
                    "connectivity": connectivity
                }
                st.session_state.step -= 1
                st.rerun()
                
            if next_clicked:
                st.session_state.form_data[steps[5]] = {
                    "demographic": demographic,
                    "devices": devices,
                    "connectivity": connectivity
                }
                st.session_state.step += 1
                st.rerun()

        # --- Step 6: Review and Submission ---
        elif step == 6:
            st.subheader(steps[6])
            
            # Display all form data for review
            st.write("### Please review your application:")
            
            for i, step_name in enumerate(steps[:-1]):  # Exclude current step
                if step_name in st.session_state.form_data:
                    st.write(f"**{step_name}:**")
                    step_data = st.session_state.form_data[step_name]
                    for key, value in step_data.items():
                        if isinstance(value, list):
                            st.write(f"- {key.replace('_', ' ').title()}: {', '.join(value)}")
                        else:
                            st.write(f"- {key.replace('_', ' ').title()}: {value}")
                    st.write("")
            
            # Email is not editable in review
            email = st.session_state.form_data[steps[0]]["email"]
            st.info(f"Application will be submitted for: {email}")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                prev_clicked = st.button("Previous", key="prev6", use_container_width=True)
            with col2:
                submit_clicked = st.button("Submit Application", key="submit", use_container_width=True, type="primary")
                
            if prev_clicked:
                st.session_state.step -= 1
                st.rerun()
                
            if submit_clicked:
                # Get applicant name for email
                applicant_name = st.session_state.form_data["Basic Information"]["first_name"]
                
                # Generate and send OTP
                otp = str(random.randint(100000, 999999))
                st.session_state.sent_otp = otp
                
                if send_otp_email(email, otp, applicant_name):
                    st.session_state.otp_step = True
                    st.session_state.otp_attempts = 0
                    st.success(f"A 6-digit OTP has been sent to {email}. Please check your email.")
                    st.rerun()
                else:
                    st.error("Failed to send OTP. Please try again.")

        # OTP Verification
        if st.session_state.get("otp_step", False) and not st.session_state.otp_verified:
            st.subheader("OTP Verification")
            
            entered_otp = st.text_input("Enter the 6-digit OTP sent to your email:", key="otp_input", max_chars=6)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                verify_clicked = st.button("Verify OTP", key="verify_otp", use_container_width=True)
            
            if verify_clicked:
                stored_otp = st.session_state.get("sent_otp", "")
                
                # Debug information (remove in production)
                st.write(f"Debug - Entered OTP: '{entered_otp}'")
                st.write(f"Debug - Stored OTP: '{stored_otp}'")
                st.write(f"Debug - OTP Type: {type(stored_otp)}")
                
                # Ensure both are strings and strip whitespace
                entered_clean = str(entered_otp).strip()
                stored_clean = str(stored_otp).strip()
                
                if entered_clean == stored_clean and stored_clean:
                    st.session_state.otp_verified = True
                    
                    # Save application to database
                    if save_application_to_database(st.session_state.form_data):
                        partner_org = st.session_state.form_data[steps[0]]["partner_org"]
                        st.success(f"You successfully applied to {partner_org}!")
                        st.info("**Instructions:** Please wait for an email confirmation. We will review your application and get back to you soon.")
                        
                        # Clear form data after successful submission
                        if st.button("Start New Application"):
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            st.rerun()
                    else:
                        st.error("Failed to save application. Please try again.")
                else:
                    st.session_state.otp_attempts += 1
                    if st.session_state.otp_attempts >= 3:
                        st.error("Too many failed attempts. Please restart the application process.")
                        if st.button("Restart Application"):
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            st.rerun()
                    else:
                        remaining = 3 - st.session_state.otp_attempts
                        st.error(f"Invalid OTP. {remaining} attempts remaining.")
                        # Show what was compared for debugging
                        if stored_clean:
                            st.error(f"Expected: {stored_clean}, Got: {entered_clean}")
                        else:
                            st.error("No OTP found in session. Please request a new OTP.")