import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "poll"  # Prevent inotify limit error

import streamlit as st
import google.generativeai as genai
import requests
from fpdf import FPDF
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator

# -------------------------------
# Streamlit Page Setup
# -------------------------------
st.set_page_config(page_title="AI Trip Planner", page_icon="🌍", layout="centered")

st.title("🌍 AI Trip Planner")
st.write("Plan your dream trip with Google Gemini 1.5 Pro ✈️")

# -------------------------------
# API Key Configuration
# -------------------------------
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Missing API key in Streamlit Secrets. Please add GOOGLE_API_KEY in your Streamlit Cloud settings.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# -------------------------------
# Input Fields
# -------------------------------
destination = st.text_input("Enter Destination", "Paris")
days = st.number_input("Number of Days", min_value=1, max_value=30, value=5)
budget = st.text_input("Enter Budget (e.g., $2000)", "$2000")
language = st.selectbox("Preferred Language", ["English", "Telugu", "Hindi", "French", "Spanish"])

if st.button("✨ Generate Trip Plan"):
    with st.spinner("Planning your trip... 🌍"):
        try:
            # Initialize Model (v1)
            model = genai.GenerativeModel("gemini-1.5-pro")

            # Step 1: Generate Itinerary
            prompt = f"Plan a detailed {days}-day travel itinerary for {destination} within {budget}. Include places, food, activities, and estimated costs."
            response = model.generate_content(prompt)
            itinerary = response.text

            # Step 2: Weather Data (optional example using Open-Meteo)
            weather_url = f"https://wttr.in/{destination}?format=3"
            weather_response = requests.get(weather_url)
            weather_info = weather_response.text if weather_response.status_code == 200 else "Weather info not available"

            # Step 3: Translation (if selected)
            if language != "English":
                itinerary = GoogleTranslator(source="auto", target=language.lower()).translate(itinerary)

            # Display
            st.subheader("🧭 Trip Itinerary")
            st.write(itinerary)

            st.subheader("🌦️ Weather Forecast")
            st.write(weather_info)

            # Step 4: PDF Download
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, f"Trip to {destination}\n\n{itinerary}\n\nWeather: {weather_info}")

            pdf_path = "/mount/src/ai-trip-planner/trip_plan.pdf"
            pdf.output(pdf_path)

            with open(pdf_path, "rb") as file:
                st.download_button("📄 Download Trip Plan PDF", file, file_name="TripPlan.pdf")

        except Exception as e:
            st.error(f"❌ Error: {e}")

# -------------------------------
# Footer
# -------------------------------
st.caption("Built with ❤️ using Google Gemini & Streamlit Cloud")
