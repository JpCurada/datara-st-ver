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
    with st.container():
        _, progress_col, _ = st.columns([1, 2, 1])
        progress = (st.session_state.step + 1) / len(steps)
        progress_col.progress(progress, text=f"Step {st.session_state.step + 1} of {len(steps)}: {steps[st.session_state.step]}")
    
    _, step_col, _ = st.columns([1, 2, 1])
    with step_col.container(border=False, key=f"application-step-{st.session_state.step}"):
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

            # --- Institution Country Dropdown ---
            countries = get_countries()
            current_institution_country = data.get("institution_country", "")
            institution_country_index = countries.index(current_institution_country) if current_institution_country in countries else 0
            institution_country = st.selectbox(
                "Institution/University Country *",
                options=countries,
                index=institution_country_index,
                key="institution_country"
            )

            # --- University/Institution Dropdown or Manual Input ---
            institution_name = ""
            if institution_country:
                with st.spinner("Loading universities..."):
                    universities = get_universities_by_country(institution_country)
                # Check if API returned valid universities or error messages
                if (universities and len(universities) > 0 and
                    not any(error_msg in universities[0] for error_msg in [
                        "API unavailable", "University not found", "No universities found",
                        "Please type manually", "timed out", "No internet connection", "API error"
                    ])):
                    # Use dropdown when universities are available
                    current_institution = data.get("institution_name", "")
                    institution_index = universities.index(current_institution) if current_institution in universities else 0
                    selected_university = st.selectbox(
                        "Institution Name *",
                        options=universities,
                        index=institution_index,
                        key="institution_name_dropdown"
                    )
                    if selected_university == "Type manually...":
                        institution_name = st.text_input(
                            "Enter University Name",
                            value=current_institution if current_institution else "",
                            key="institution_name_manual"
                        )
                    else:
                        institution_name = selected_university
                else:
                    st.info("University lookup unavailable. Please enter manually.")
                    institution_name = st.text_input(
                        "Institution Name *",
                        value=data.get("institution_name", ""),
                        key="institution_name_text"
                    )
            else:
                st.info("Please select the institution/university country first to load available institutions.")
                institution_name = st.text_input(
                    "Institution Name *",
                    value="",
                    disabled=True,
                    key="institution_name_disabled"
                )

            # --- Navigation Buttons ---
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
            
            # Create tabs for Review and OTP Verification
            if not st.session_state.get("otp_step", False):
                # Review Tab
                st.subheader("Review Your Application")
                
                # Load existing data
                data_step0 = st.session_state.form_data.get(steps[0], {})
                data_step1 = st.session_state.form_data.get(steps[1], {})
                data_step2 = st.session_state.form_data.get(steps[2], {})
                data_step3 = st.session_state.form_data.get(steps[3], {})
                data_step4 = st.session_state.form_data.get(steps[4], {})
                data_step5 = st.session_state.form_data.get(steps[5], {})
                
                with st.form("review_form"):
                    # Partner Organization & Data Privacy (Email not editable)
                    st.write("**Partner Organization & Data Privacy**")
                    col1, col2 = st.columns(2)
                    with col1:
                        partner_org = st.text_input("Partner Organization", value=data_step0.get("partner_org", ""), disabled=True)
                    with col2:
                        email = st.text_input("Email Address", value=data_step0.get("email", ""), disabled=True)
                    
                    st.divider()
                    
                    # Basic Information
                    st.write("**Basic Information**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        first_name = st.text_input("First Name", value=data_step1.get("first_name", ""), key="review_fn")
                    with col2:
                        middle_name = st.text_input("Middle Name", value=data_step1.get("middle_name", ""), key="review_mn")
                    with col3:
                        last_name = st.text_input("Last Name", value=data_step1.get("last_name", ""), key="review_ln")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        gender_options = ["MALE", "FEMALE", "OTHER"]
                        gender_index = gender_options.index(data_step1.get("gender")) if data_step1.get("gender") in gender_options else 0
                        gender = st.selectbox("Gender", gender_options, index=gender_index, key="review_gender")
                    with col2:
                        birthdate = st.date_input("Date of Birth", value=data_step1.get("birthdate"), key="review_dob")
                    
                    st.divider()
                    
                    # Geographic Details
                    st.write("**Geographic Details**")
                    col1, col2 = st.columns(2)
                    with col1:
                        country = st.text_input("Country", value=data_step2.get("country", ""), key="review_country")
                    with col2:
                        state = st.text_input("State/Region/Province", value=data_step2.get("state", ""), key="review_state")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        city = st.text_input("City", value=data_step2.get("city", ""), key="review_city")
                    with col2:
                        postal = st.number_input("Postal/Zip Code", value=int(data_step2.get("postal", 0)), key="review_postal")
                    
                    st.divider()
                    
                    # Education Details
                    st.write("**Education Details**")
                    col1, col2 = st.columns(2)
                    with col1:
                        education_options = ["CURRENTLY_ENROLLED", "FRESH_GRADUATE", "GRADUATE", "GAP_YEAR"]
                        education_index = education_options.index(data_step3.get("education_status")) if data_step3.get("education_status") in education_options else 0
                        education_status = st.selectbox("Education Status", education_options, index=education_index, key="review_education")
                    with col2:
                        institution_country = st.text_input("Institution Country", value=data_step3.get("institution_country", ""), key="review_inst_country")
                    
                    institution_name = st.text_input("Institution Name", value=data_step3.get("institution_name", ""), key="review_institution")
                    
                    st.divider()
                    
                    # Interest Details
                    st.write("**Interest Details**")
                    col1, col2 = st.columns(2)
                    with col1:
                        prog_options = ["NONE", "BEGINNER", "INTERMEDIATE", "ADVANCED"]
                        prog_index = prog_options.index(data_step4.get("programming_experience")) if data_step4.get("programming_experience") in prog_options else 0
                        programming_experience = st.selectbox("Programming Experience", prog_options, index=prog_index, key="review_prog")
                    with col2:
                        ds_options = ["NONE", "BASIC", "INTERMEDIATE", "ADVANCED"]
                        ds_index = ds_options.index(data_step4.get("data_science_experience")) if data_step4.get("data_science_experience") in ds_options else 0
                        data_science_experience = st.selectbox("Data Science Experience", ds_options, index=ds_index, key="review_ds")
                    
                    time_options = ["1-2", "3-5", "6-10", "11-15", "16+"]
                    time_index = time_options.index(data_step4.get("time_commitment")) if data_step4.get("time_commitment") in time_options else 0
                    time_commitment = st.selectbox("Weekly Time Commitment", time_options, index=time_index, key="review_time")
                    
                    why_scholarship = st.text_area("Why do you want this scholarship?", value=data_step4.get("why_scholarship", ""), key="review_why", height=100)
                    career_goals = st.text_area("Career Goals", value=data_step4.get("career_goals", ""), key="review_goals", height=80)
                    
                    st.divider()
                    
                    # Demographic and Connectivity
                    st.write("**Demographic and Connectivity**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        demographic_options = ["UNEMPLOYED", "UNDEREMPLOYED", "BELOW_POVERTY", "REFUGEE", "DISABLED", "STUDENT", "WORKING_STUDENT", "NONPROFIT_SCIENTIST"]
                        demographic = st.multiselect("Demographic Group", demographic_options, default=data_step5.get("demographic", []), key="review_demographic")
                    with col2:
                        device_options = ["SMARTPHONE", "LAPTOP", "DESKTOP"]
                        devices = st.multiselect("Devices", device_options, default=data_step5.get("devices", []), key="review_devices")
                    with col3:
                        connectivity_options = ["MOBILE_DATA", "WIFI"]
                        connectivity = st.multiselect("Internet Connectivity", connectivity_options, default=data_step5.get("connectivity", []), key="review_connectivity")
                    
                    # Navigation buttons
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        prev_clicked = st.form_submit_button("Previous", use_container_width=True)
                    with col2:
                        can_proceed = (first_name and last_name and gender and birthdate and 
                                     country and state and city and postal and 
                                     education_status and institution_country and institution_name and
                                     programming_experience and data_science_experience and time_commitment and
                                     why_scholarship and career_goals and demographic and devices and connectivity)
                        submit_clicked = st.form_submit_button("Submit Application", disabled=not can_proceed, use_container_width=True, type="primary")
                    
                    if prev_clicked:
                        st.session_state.step -= 1
                        st.rerun()
                        
                    if submit_clicked:
                        # Update all form data with reviewed values
                        st.session_state.form_data[steps[1]] = {
                            "first_name": first_name,
                            "middle_name": middle_name,
                            "last_name": last_name,
                            "gender": gender,
                            "birthdate": birthdate
                        }
                        st.session_state.form_data[steps[2]] = {
                            "country": country,
                            "state": state,
                            "city": city,
                            "postal": postal
                        }
                        st.session_state.form_data[steps[3]] = {
                            "education_status": education_status,
                            "institution_country": institution_country,
                            "institution_name": institution_name
                        }
                        st.session_state.form_data[steps[4]] = {
                            "programming_experience": programming_experience,
                            "data_science_experience": data_science_experience,
                            "time_commitment": time_commitment,
                            "why_scholarship": why_scholarship,
                            "career_goals": career_goals
                        }
                        st.session_state.form_data[steps[5]] = {
                            "demographic": demographic,
                            "devices": devices,
                            "connectivity": connectivity
                        }
                        
                        # Generate and send OTP
                        applicant_name = st.session_state.form_data["Basic Information"]["first_name"]
                        email = st.session_state.form_data[steps[0]]["email"]
                        otp = str(random.randint(100000, 999999))
                        st.session_state.sent_otp = otp
                        
                        if send_otp_email(email, otp, applicant_name):
                            st.session_state.otp_step = True
                            st.session_state.otp_attempts = 0
                            st.success(f"A 6-digit OTP has been sent to {email}. Please check your email.")
                            st.rerun()
                        else:
                            st.error("Failed to send OTP. Please try again.")
            
            else:
                # OTP Verification Tab
                st.subheader("Email Verification")
                
                email = st.session_state.form_data[steps[0]]["email"]
                st.info(f"We've sent a 6-digit verification code to {email}")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    entered_otp = st.text_input(
                        "Enter verification code:",
                        key="otp_input",
                        max_chars=6,
                        placeholder="123456",
                        help="Check your email for the 6-digit code"
                    )
                    
                    verify_clicked = st.button("Verify Code", key="verify_otp", use_container_width=True, type="primary")
                    
                
                # Navigation buttons outside the column structure
                st.write("")  # Add some spacing
                
                col_back, col_resend = st.columns(2)
                with col_back:
                    if st.button("Back to Review", use_container_width=True):
                        st.session_state.otp_step = False
                        st.rerun()
                with col_resend:
                    if st.button("Resend Code", use_container_width=True):
                        applicant_name = st.session_state.form_data["Basic Information"]["first_name"]
                        otp = str(random.randint(100000, 999999))
                        st.session_state.sent_otp = otp
                        if send_otp_email(email, otp, applicant_name):
                            st.success("New code sent to your email!")
                        else:
                            st.error("Failed to send code. Please try again.")
                
                if verify_clicked:
                    stored_otp = st.session_state.get("sent_otp", "")
                    entered_clean = str(entered_otp).strip()
                    stored_clean = str(stored_otp).strip()
                    
                    if entered_clean == stored_clean and stored_clean:
                        st.session_state.otp_verified = True
                        
                        # Save application to database
                        if save_application_to_database(st.session_state.form_data):
                            partner_org = st.session_state.form_data[steps[0]]["partner_org"]
                            st.success(f"Application submitted successfully to {partner_org}!")
                            st.balloons()
                            st.info("You will receive an email confirmation shortly. We will review your application and contact you within 2-3 business days.")
                            
                            # Clear form data after successful submission - moved to session state
                            st.session_state.show_new_application_button = True
                        else:
                            st.error("Failed to save application. Please try again.")
                    else:
                        st.session_state.otp_attempts = st.session_state.get("otp_attempts", 0) + 1
                        if st.session_state.otp_attempts >= 3:
                            st.error("Too many failed attempts. Please restart the application process.")
                            st.session_state.show_restart_button = True
                        else:
                            remaining = 3 - st.session_state.otp_attempts
                            st.error(f"Invalid verification code. {remaining} attempts remaining.")
                            st.warning("Please check your email and enter the correct 6-digit code.")

                # Handle buttons outside of verification logic
                if st.session_state.get("show_new_application_button", False):
                    if st.button("Submit Another Application", use_container_width=True):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()
                
                if st.session_state.get("show_restart_button", False):
                    if st.button("Restart Application", use_container_width=True):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()