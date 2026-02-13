# skills/weather_skill.py

import requests
import time


OPENWEATHER_API_KEY = "PUT YOUR OPENWEATHERMAP API HERE"


def get_weather(city: str) -> str:
    city = city.strip()
    if not city:
        return "Please tell me the city name for the weather."

    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
        return "Weather API key is not configured."

    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&appid={OPENWEATHER_API_KEY}"
        )
        w_data = requests.get(url, timeout=10).json()

        if w_data.get("cod") != 200:
            return f"I could not get weather information for {city}."

        weather = w_data["weather"][0]["main"]
        temp = int(w_data["main"]["temp"] - 273.15)
        temp_min = int(w_data["main"]["temp_min"] - 273.15)
        temp_max = int(w_data["main"]["temp_max"] - 273.15)
        humidity = w_data["main"]["humidity"]
        wind = w_data["wind"]["speed"]
        # Convert sunrise/sunset to local time (assuming IST +5:30 as example)
        sunrise = time.strftime("%H:%M:%S", time.gmtime(w_data["sys"]["sunrise"] + 19800))
        sunset = time.strftime("%H:%M:%S", time.gmtime(w_data["sys"]["sunset"] + 19800))

        part1 = f"Weather in {city}: {weather}, temperature {temp} degrees Celsius."
        part2 = (
            f"Minimum {temp_min}, maximum {temp_max}, humidity {humidity} percent, "
            f"wind speed {wind} kilometers per hour. "
            f"Sunrise at {sunrise}, sunset at {sunset}."
        )
        return part1 + " " + part2
    except Exception as e:
        return f"I could not fetch weather information: {e}"
