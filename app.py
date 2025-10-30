import os
import logging
import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import matplotlib.pyplot as plt
import requests
import pandas as pd

# ---------------------------------------------------
# 🧹 Silence unnecessary logs
# ---------------------------------------------------
os.environ["GRPC_VERBOSITY"] = "NONE"
logging.getLogger("absl").setLevel(logging.ERROR)

# ---------------------------------------------------
# 🔑 Configure Google Gemini API
# ---------------------------------------------------
# Streamlit Cloud: Add GOOGLE_API_KEY in your app Secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ---------------------------------------------------
# 🌦 Weather Forecast Function
# ---------------------------------------------------
def get_weather_forecast(destination, days):
    api_key = os.getenv("OPENWEATHER_API_KEY") or st.secrets.get("OPENWEATHER_API_KEY")
    if not api_key:
        return []

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={destination}&units=metric&appid={api_key}"
    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200 or "list" not in data:
            return []

        forecasts = []
        for i in range(days):
            forecast = data["list"][i * 8]  # 24-hour interval
            temp = forecast["main"]["temp"]
            desc = forecast["weather"][0]["description"].capitalize()
            icon = "☀️"
            if "rain" in desc.lower():
                icon = "🌧️"
            elif "cloud" in desc.lower():
                icon = "⛅"
            elif "clear" in desc.lower():
                icon = "☀️"

            forecasts.append({
                "Day": f"Day {i+1}",
                "Weather": f"{icon} {desc}",
                "Temp (°C)": f"{temp:.1f}"
            })
        return forecasts
    except Exception:
        return []

# ---------------------------------------------------
# 📄 PDF Export Function
# ---------------------------------------------------
def export_pdf(itinerary_text):
    pdf = FPDF()
    pdf.add_page()
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        pdf.set_font("Arial", size=12)
    else:
        pdf.add_font("DejaVu", "", font_path)
        pdf.set_font("DejaVu", size=12)

    safe_text = str(itinerary_text)
    pdf.multi_cell(0, 10, safe_text)
    pdf_file = "itinerary.pdf"
    pdf.output(pdf_file)
    return pdf_file

# ---------------------------------------------------
# 🌍 Streamlit UI Setup
# ---------------------------------------------------
st.set_page_config(page_title="AI Trip Planner", layout="wide")
st.title("✈️ AI Trip Planner")

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "booking_done" not in st.session_state:
    st.session_state.booking_done = False

# ---------------------------------------------------
# 📝 Trip Input Sidebar
# ---------------------------------------------------
st.sidebar.header("📝 Trip Details")
destination = st.sidebar.text_input("Destination", "Goa")
days = st.sidebar.number_input("Number of Days", min_value=1, max_value=30, value=3)
budget = st.sidebar.number_input("Budget (INR)", min_value=1000, value=20000)

st.sidebar.header("🌍 Language")
language = st.sidebar.selectbox(
    "Choose Itinerary Language",
    ["English", "Hindi", "Telugu", "Tamil", "French", "Spanish", "German"]
)

# ---------------------------------------------------
# 🚀 Generate Itinerary
# ---------------------------------------------------
if st.button("✨ Generate Itinerary"):
    with st.spinner("✍️ Creating your personalized trip plan..."):
        model = genai.GenerativeModel("gemini-1.5-pro")
        # Step 1: Generate base itinerary
        prompt = f"Plan a {days}-day trip to {destination} for {budget} INR. Give it in day-wise format."
        response = model.generate_content(prompt)
        itinerary = response.text

        # Step 2: Fetch weather forecast
        weather_forecast = get_weather_forecast(destination, days)

        # Step 3: Merge weather with itinerary
        itinerary_with_weather = ""
        day_counter = 0
        for line in itinerary.split("\n"):
            if line.strip().lower().startswith("day"):
                itinerary_with_weather += f"{line}\n"
                if day_counter < len(weather_forecast):
                    wf = weather_forecast[day_counter]
                    itinerary_with_weather += f"   🌦 Weather: {wf['Weather']}, {wf['Temp (°C)']}°C\n"
                day_counter += 1
            else:
                itinerary_with_weather += line + "\n"

        # Step 4: Translate (if needed)
        if language != "English":
            translate_prompt = (
                f"Translate the following itinerary into {language}, "
                f"keeping the same format and emojis:\n\n{itinerary_with_weather}"
            )
            translated_response = model.generate_content(translate_prompt)
            itinerary_with_weather = translated_response.text

        # Step 5: Save in session
        st.session_state.itinerary = itinerary_with_weather.strip()
        st.session_state.weather_forecast = weather_forecast
        st.session_state.booking_done = False

    st.success(f"✅ Your itinerary is ready with live weather updates in {language}!")

# ---------------------------------------------------
# 📋 Display Itinerary
# ---------------------------------------------------
if st.session_state.itinerary:
    st.divider()
    st.subheader("🗺 Your AI Trip Itinerary (with Weather)")
    st.write(st.session_state.itinerary)

    # 🌦 Weather Forecast Table
    if st.session_state.weather_forecast:
        st.subheader("🌦 Weather Forecast")
        st.table(pd.DataFrame(st.session_state.weather_forecast))

    # 📥 PDF Export Button
    pdf_file = export_pdf(st.session_state.itinerary)
    with open(pdf_file, "rb") as f:
        st.download_button("📥 Download Itinerary as PDF", f, file_name="itinerary.pdf")

    # 💰 Budget Overview Chart
    st.divider()
    st.subheader("💰 Budget Overview")
    labels = ["Travel", "Stay", "Food", "Activities", "Misc"]
    values = [budget * 0.3, budget * 0.25, budget * 0.2, budget * 0.15, budget * 0.1]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%")
    st.pyplot(fig)

    # 📍 Google Maps Embed
    st.divider()
    st.subheader("📍 Destination Map")
    maps_key = os.getenv("GOOGLE_MAPS_KEY") or st.secrets.get("GOOGLE_MAPS_KEY")
    if maps_key:
        maps_url = f"https://www.google.com/maps/embed/v1/place?key={maps_key}&q={destination}"
        st.components.v1.iframe(maps_url, width=700, height=400)
    else:
        st.info("🔑 Add GOOGLE_MAPS_KEY in Streamlit Secrets to enable map display.")

    # 🛎 Demo Booking Section
    st.divider()
    st.subheader("🛎 Book My Trip")
    if not st.session_state.booking_done:
        with st.form("booking_form_once"):
            name = st.text_input("Traveller Name")
            email = st.text_input("Email (optional)")
            submit_booking = st.form_submit_button("Confirm Booking")
            if submit_booking:
                if name.strip() == "":
                    st.error("⚠️ Please enter your name to confirm booking.")
                else:
                    st.session_state.booking_done = True
                    st.success(f"✅ Demo booking successful! 🎉\nReference: EMT-DEMO-{os.urandom(3).hex().upper()}")
                    st.balloons()
    else:
        st.success("🎉 Your trip is already booked in this demo session!")
