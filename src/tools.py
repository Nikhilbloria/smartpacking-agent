import os
import requests
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()


packing_list = []


def clear_packing_list():
    """Resets the global packing list state."""
    global packing_list
    packing_list.clear()


def check_weather(city):
    """Retrieves real-time weather information for a given city via OpenWeather API."""
    city = city.strip()
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or api_key.strip() in ["", "your_openweather_api_key_here"]:
        return {
            "error": "OPENWEATHER_API_KEY environment variable is missing. Please configure it."
        }
        
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 404:
            return {
                "error": f"City '{city}' not found by OpenWeather API."
            }
        elif response.status_code == 401:
            return {
                "error": "Invalid OpenWeather API Key. Please verify your billing/key details."
            }
        elif response.status_code != 200:
            return {
                "error": f"OpenWeather API returned status code {response.status_code}."
            }
            
        data = response.json()
        
        # Extract parsing details
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        
        weather_list = data.get("weather", [{}])
        main_condition = weather_list[0].get("main", "Clear")
        description = weather_list[0].get("description", "")
        
        # Determine if it is rainy or snowy
        condition_lower = main_condition.lower()
        is_rainy = any(x in condition_lower for x in ["rain", "drizzle", "thunderstorm", "snow"])
        
        # Also double check if 'rain' or 'snow' dictionaries exist in the response
        if "rain" in data or "snow" in data:
            is_rainy = True
            
        condition = "cold" if temp < 15 else "hot" if temp > 25 else "moderate"
        
        return {
            "city": data.get("name", city),
            "temperature": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "description": description,
            "wind_speed": wind_speed,
            "condition": condition,
            "rain": is_rainy,
            "main_condition": main_condition
        }
        
    except requests.exceptions.Timeout:
        return {
            "error": "Connection to OpenWeather API timed out."
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Network error during weather check: {type(e).__name__}."
        }
    except Exception as e:
        return {
            "error": f"Unexpected error parsing weather data: {type(e).__name__}."
        }


def add_item(item):
    """Adds a item to the packing list if not already present."""
    if item not in packing_list:
        packing_list.append(item)

    return {
        "item": item,
        "packing_list": list(packing_list)
    }


def forgot_something(trip_type, items):
    """Compares current items against a list of required items per trip type."""
    required_items = {
        "trekking": [
            "Trekking shoes",
            "Water bottle",
            "Jacket"
        ],
        "beach": [
            "Sunglasses",
            "Sunscreen",
            "Swimwear"
        ],
        "business": [
            "Formal clothes",
            "Laptop",
            "Charger"
        ]
    }

    missing = []
    # Convert all items to lowercase for case-insensitive comparison
    lower_packed = [i.lower() for i in items]

    for item in required_items.get(trip_type.lower(), []):
        if item.lower() not in lower_packed:
            missing.append(item)

    return missing
