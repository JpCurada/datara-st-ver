import streamlit as st
from utils.db import get_supabase_client

def check_email_in_scholars(email, partner_org):
    return False

def check_email_in_applications(email, partner_org):
    return False

def get_active_partner_organizations():
    return ["DataCamp", "Coursera", "Udacity", "edX"]

def save_application_to_database(form_data):
    return True