import os
import logging
# Suppress gRPC/ALTS warnings
os.environ["GRPC_VERBOSITY"] = "NONE"
logging.getLogger("absl").setLevel(logging.ERROR)

import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import matplotlib.pyplot as plt
import requests
from deep_translator import GoogleTranslator

# ---------------------------
# 🔑 Configure Google Gemini API
# ---------------------------
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ---------------------------
# 🌦 Weather Forecast Function
# ---------------------------
def get_weather_forecast(destination, days):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return ["⚠️ No weather API key configured."]

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={destination}&units=metric&appid={api_key}"
    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200 or "list" not in data:
            return [f"⚠️ Weather not available for {destination}"]

        forecasts = []
        for i in range(days):
            forecast = data["list"][i * 8]  # every 24 hours (8 intervals of 3h)
            temp = forecast["main"]["temp"]
            desc = forecast["weather"][0]["description"].capitalize()
            forecasts.append(f"Day {i+1}: {desc}, {temp}°C")
        return forecasts
    except Exception as e:
        return [f"⚠️ Error fetching weather: {str(e)}"]

# ---------------------------
# 🌟 Smart Suggestions
# ---------------------------
def smart_suggestion(weather_desc):
    if "rain" in weather_desc.lower() or "storm" in weather_desc.lower():
        return "🌧 Suggested: Indoor activities (museums, cafes, shopping)."
    elif "clear" in weather_desc.lower() or "sun" in weather_desc.lower():
        return "☀️ Suggested: Outdoor sightseeing, beaches, local tours."
    else:
        return "✨ Suggested: Flexible activities depending on mood!"

# ---------------------------
# 📍 Google Places API Recommendations
# ---------------------------
def get_places_recommendations(destination):
    maps_key = os.getenv("GOOGLE_MAPS_KEY")
    if not maps_key:
        return ["⚠️ No Google Maps API key configured."]

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=top+attractions+in+{destination}&key={maps_key}"
    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200 or "results" not in data:
            return ["⚠️ Places not available"]

        places = []
        for place in data["results"][:5]:
            name = place.get("name", "Unknown Place")
            addr = place.get("formatted_address", "")
            places.append(f"🏛 {name} - {addr}")
        return places
    except Exception as e:
        return [f"⚠️ Error fetching places: {str(e)}"]

# ---------------------------
# 📄 PDF Export Function
# ---------------------------
def export_pdf(itinerary_text):
    pdf = FPDF()
    pdf.add_page()
    font_path = "DejaVuSans.ttf"
    pdf.add_font("DejaVu", "", font_path)
    pdf.set_font("DejaVu", size=12)
    safe_text = str(itinerary_text)
    pdf.multi_cell(0, 10, safe_text)
    pdf_file = "itinerary.pdf"
    pdf.output(pdf_file)
    return pdf_file

# ---------------------------
# 🌍 Streamlit App Setup
# ---------------------------
st.set_page_config(page_title="AI Trip Planner", layout="wide")
st.title("✈️ AI Trip Planner")

# Session state
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "booking_done" not in st.session_state:
    st.session_state.booking_done = False

# ---------------------------
# 📝 Trip Input
# ---------------------------
st.sidebar.header("📝 Trip Details")
destination = st.sidebar.text_input("Destination", "Goa")
days = st.sidebar.number_input("Number of Days", min_value=1, max_value=30, value=3)
budget = st.sidebar.number_input("Budget (INR)", min_value=1000, value=20000)
language = st.sidebar.selectbox("Translate Itinerary To", ["English", "Hindi", "Telugu", "French", "Spanish", "German"])

# ---------------------------
# 🚀 Generate Itinerary
# ---------------------------
if st.button("✨ Generate Itinerary"):
    with st.spinner("✍️ Creating your personalized trip plan..."):
        prompt = f"Plan a {days}-day trip to {destination} for {budget} INR. Give it in day-wise format."
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        itinerary = response.text

        # 🌦 Weather forecast
        weather_forecast = get_weather_forecast(destination, days)

        # Merge weather + smart suggestions
        itinerary_with_weather = ""
        weather_index = 0
        for line in itinerary.split("\n"):
            if line.strip().lower().startswith("day") and weather_index < len(weather_forecast):
                itinerary_with_weather += f"{line}\n"
                weather_line = weather_forecast[weather_index]
                itinerary_with_weather += f"   🌦 Weather: {weather_line}\n"
                itinerary_with_weather += f"   💡 {smart_suggestion(weather_line)}\n"
                weather_index += 1
            else:
                itinerary_with_weather += line + "\n"

        # Google Places recommendations
        places = get_places_recommendations(destination)
        itinerary_with_weather += "\n\n🏙 Recommended Places to Visit:\n" + "\n".join(places)

        # Translate if not English
        if language != "English":
            try:
                translator = GoogleTranslator(source="auto", target=language.lower())
                itinerary_with_weather = translator.translate(itinerary_with_weather)
            except Exception:
                itinerary_with_weather += "\n⚠️ Translation failed."

        # Save in session state
        st.session_state.itinerary = itinerary_with_weather.strip()
        st.session_state.booking_done = False

    st.success("✅ Your itinerary is ready with live weather, smart tips & recommendations!")

# ---------------------------
# 📋 Show Itinerary
# ---------------------------
if st.session_state.itinerary:
    st.divider()
    st.subheader("🗺 Your AI Trip Itinerary")
    st.write(st.session_state.itinerary)

    # 📥 Download PDF
    pdf_file = export_pdf(st.session_state.itinerary)
    with open(pdf_file, "rb") as f:
        st.download_button("📥 Download Itinerary as PDF", f, file_name="itinerary.pdf")

    st.divider()
    # 📊 Budget Chart
    st.subheader("💰 Budget Overview")
    labels = ["Travel", "Stay", "Food", "Activities", "Misc"]
    values = [budget * 0.3, budget * 0.25, budget * 0.2, budget * 0.15, budget * 0.1]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%")
    st.pyplot(fig)

    st.divider()
    # 📍 Google Maps Embed
    st.subheader("📍 Destination Map")
    maps_key = os.getenv("GOOGLE_MAPS_KEY")
    if maps_key:
        maps_url = f"https://www.google.com/maps/embed/v1/place?key={maps_key}&q={destination}"
        st.components.v1.iframe(maps_url, width=700, height=400)
    else:
        st.warning("⚠️ Google Maps API key not set.")

    st.divider()
    # 🛎 Book My Trip
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
