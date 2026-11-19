import os
import io
import sys
import contextlib
from flask import Flask, request, jsonify, render_template

# Ensure src/ folder is accessible
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.agent import PackingAgent

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/pack", methods=["POST"])
def pack():
    try:
        data = request.get_json() or {}
        destination = data.get("destination", "").strip()
        trip_type = data.get("trip_type", "").strip()
        duration = data.get("duration")

        if not destination or not trip_type or duration is None:
            return jsonify({"error": "Missing required fields (destination, trip_type, duration)"}), 400

        try:
            duration = int(duration)
        except ValueError:
            return jsonify({"error": "Duration must be a valid number of days"}), 400

        # Run the agent and redirect stdout to capture execution log trace
        log_buffer = io.StringIO()
        with contextlib.redirect_stdout(log_buffer):
            agent = PackingAgent()
            result = agent.run(
                destination=destination,
                trip_type=trip_type,
                duration=duration
            )
        
        logs = log_buffer.getvalue()

        # Extract weather if available from the agent
        weather_data = None
        if hasattr(agent, "current_weather"):
            raw_weather = agent.current_weather
            if raw_weather and "error" not in raw_weather:
                weather_data = {
                    "city": raw_weather.get("city"),
                    "temperature": raw_weather.get("temperature"),
                    "condition": raw_weather.get("main_condition") or raw_weather.get("description", "").title() or "N/A",
                    "humidity": raw_weather.get("humidity"),
                    "wind_speed": raw_weather.get("wind_speed")
                }
            elif raw_weather and "error" in raw_weather:
                weather_data = {
                    "error": raw_weather.get("error")
                }

        return jsonify({
            "success": True,
            "logs": logs,
            "weather": weather_data,
            "packing_list": result.get("items", []),
            "meta": {
                "destination": result.get("destination"),
                "trip_type": result.get("trip_type"),
                "duration": result.get("duration")
            }
        })

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(error_msg)
        return jsonify({"error": str(e), "trace": error_msg}), 500

if __name__ == "__main__":
    # Host on localhost:5000
    app.run(host="127.0.0.1", port=5000, debug=False)
