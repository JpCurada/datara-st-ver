import requests
import pycountry

def _find_code(chosen_country):
  for country in pycountry.countries:
    if country.name == chosen_country:
      return country.alpha_2

def get_countries() -> list[str]:
    countries = [country.name for country in pycountry.countries]
    return countries

def get_provinces(selected_country) -> list[str]:
   provinces =[sub.name for sub in pycountry.subdivisions.get(country_code=_find_code(selected_country))]
   return provinces

def get_universities_by_country(selected_country):
    """Fetch universities from API"""
    try:
        response = requests.get(f"http://universities.hipolabs.com/search?country={selected_country}")
        if response.status_code == 200:
            universities = response.json()
            return [uni['name'] for uni in universities]
        else:
            return ["University not found - please type manually"]
    except:
        return ["API unavailable - please type manually"]

def send_otp_email(email, otp):
    return True