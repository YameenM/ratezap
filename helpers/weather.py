import requests
from utils import hide_streamlit_ui
hide_streamlit_ui()


def get_user_city():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return data.get("city", "Unknown")
    except:
        return "Unknown"

def get_weather_for_city(city, api_key):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        data = requests.get(url).json()
        condition = data["current"]["condition"]["text"]
        temp_c = data["current"]["temp_c"]
        icon_url = "https:" + data["current"]["condition"]["icon"]
        return condition, temp_c, icon_url
    except:
        return "Unavailable", "", ""

