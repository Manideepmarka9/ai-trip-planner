import os
import logging
# Suppress gRPC/ALTS warnings
os.environ["GRPC_VERBOSITY"] = "NONE"
logging.getLogger("absl").setLevel(logging.ERROR)

import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import matplotlib.pyplot as plt

# ---------------------------
# 🔑 Configure Google Gemini API
# ---------------------------
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ---------------------------
# 📄 PDF Export Function
# ---------------------------
def export_pdf(itinerary_text):
    pdf = FPDF()
    pdf.add_page()

    # Use Unicode font
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

# ---------------------------
# 🚀 Generate Itinerary
# ---------------------------
if st.button("✨ Generate Itinerary"):
    with st.spinner("✍️ Creating your personalized trip plan..."):
        prompt = f"Plan a {days}-day trip to {destination} for {budget} INR."
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        itinerary = response.text

        # Save in session state
        st.session_state.itinerary = itinerary
        st.session_state.booking_done = False  # reset booking

    st.success("✅ Your itinerary is ready!")

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
    # ---------------------------
    # 📊 Budget Chart
    # ---------------------------
    st.subheader("💰 Budget Overview")
    labels = ["Travel", "Stay", "Food", "Activities", "Misc"]
    values = [budget * 0.3, budget * 0.25, budget * 0.2, budget * 0.15, budget * 0.1]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%")
    st.pyplot(fig)

    st.divider()
    # ---------------------------
    # 🗺 Google Maps Embed
    # ---------------------------
    st.subheader("📍 Destination Map")
    maps_key = os.getenv("GOOGLE_MAPS_KEY")
    maps_url = f"https://www.google.com/maps/embed/v1/place?key={maps_key}&q={destination}"
    st.components.v1.iframe(maps_url, width=700, height=400)

    st.divider()
    # ---------------------------
    # 🛎 Book My Trip (ONLY once)
    # ---------------------------
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
                    st.success(
                        f"✅ Demo booking successful! 🎉\nReference: EMT-DEMO-{os.urandom(3).hex().upper()}"
                    )
                    st.balloons()
    else:
        st.success("🎉 Your trip is already booked in this demo session!")
