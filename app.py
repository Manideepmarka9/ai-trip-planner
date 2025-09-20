import streamlit as st
import google.generativeai as genai
import os
import requests
from fpdf import FPDF
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator  # ✅ Multi-language works

# ---------------------------
# 🔑 Configure Google Gemini API
# ---------------------------
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------------------
# 🌦 Weather API function
# ---------------------------
def get_weather_forecast(destination, days, api_key):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={destination}&appid={api_key}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return [f"Weather data not available for {destination}"]

    data = response.json()
    forecast_list = data.get("list", [])
    daily_forecast = {}

    for entry in forecast_list:
        date = entry["dt_txt"].split(" ")[0]
        temp = entry["main"]["temp"]
        description = entry["weather"][0]["description"]

        if date not in daily_forecast:
            daily_forecast[date] = {"temp": temp, "description": description}

        if len(daily_forecast) >= days:
            break

    return [f"Day {i+1}: {v['description']}, {v['temp']}°C"
            for i, (k, v) in enumerate(daily_forecast.items())]

# ---------------------------
# 📄 Generate Itinerary
# ---------------------------
def generate_itinerary(destination, days, budget, language="en"):
    weather_api_key = st.secrets["WEATHER_API_KEY"]
    weather_forecast = get_weather_forecast(destination, days, weather_api_key)

    prompt = f"""
    Create a {days}-day travel itinerary for {destination} within a budget of {budget} INR.
    Include accommodation, food, activities, and transport suggestions.
    Also, here’s the weather forecast for each day: {weather_forecast}.
    """

    response = model.generate_content(prompt)
    itinerary = response.text

    # 🌍 Translate if not English
    if language != "en":
        itinerary = GoogleTranslator(source="auto", target=language).translate(itinerary)

    return itinerary, weather_forecast

# ---------------------------
# 📊 Generate Budget Chart
# ---------------------------
def generate_budget_chart():
    categories = ["Accommodation", "Food", "Transport", "Activities", "Misc"]
    values = [5000, 3000, 2000, 2500, 1500]

    fig, ax = plt.subplots()
    ax.pie(values, labels=categories, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    return fig

# ---------------------------
# 📝 Streamlit UI
# ---------------------------
st.title("✈️ AI Trip Planner")

with st.form("trip_form"):
    destination = st.text_input("Destination", "Goa")
    days = st.number_input("Number of Days", 1, 10, 3)
    budget = st.number_input("Budget (INR)", 1000, 100000, 20000)
    language = st.selectbox("Translate Itinerary To", ["en", "hi", "te", "ta", "fr", "es"])
    submitted = st.form_submit_button("Generate Itinerary")

if submitted:
    with st.spinner("Generating your trip plan..."):
        itinerary, weather_forecast = generate_itinerary(destination, days, budget, language)

    st.success("✅ Your itinerary is ready with live weather updates!")

    st.subheader("🗺 Your AI Trip Itinerary")
    st.write(itinerary)

    st.subheader("🌦 Weather Forecast")
    for day in weather_forecast:
        st.write(day)

    st.subheader("💰 Budget Overview")
    chart = generate_budget_chart()
    st.pyplot(chart)

    st.subheader("📍 Destination Map")
    st.map()
