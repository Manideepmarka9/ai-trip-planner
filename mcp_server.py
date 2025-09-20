import os
import asyncio
import mcp.server

from app import get_weather_forecast, export_pdf  # reuse your existing functions
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

server = mcp.server.Server("ai-trip-planner-mcp")

# ---------------------------
# MCP Tools
# ---------------------------

@server.tool()
async def generate_itinerary(destination: str, days: int, budget: int) -> str:
    """Generate a day-wise trip itinerary using Gemini AI."""
    prompt = f"Plan a {days}-day trip to {destination} for {budget} INR. Give it in day-wise format."
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    return response.text

@server.tool()
async def weather_forecast(destination: str, days: int) -> list[str]:
    """Fetch weather forecast for given days using OpenWeather API."""
    return get_weather_forecast(destination, days)

@server.tool()
async def translate_itinerary(itinerary: str, language: str) -> str:
    """Translate itinerary into the target language using Gemini."""
    translate_prompt = f"Translate the following itinerary into {language}, keep format neat:\n\n{itinerary}"
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(translate_prompt)
    return response.text

@server.tool()
async def export_itinerary_pdf(itinerary: str) -> str:
    """Export itinerary to PDF and return the filename."""
    return export_pdf(itinerary)

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    asyncio.run(server.serve())
