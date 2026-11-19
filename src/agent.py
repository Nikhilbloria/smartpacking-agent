import os
import sys
# pyrefly: ignore [missing-import]

# Ensure the parent directory is in sys.path to allow running this script directly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from ollama import Client
from src.tools import check_weather, add_item, forgot_something, clear_packing_list
from src.memory import Memory

class PackingAgent:

    def __init__(self):
        self.memory = Memory()
        load_dotenv()
        self.token = os.getenv("OLLAMA_API_KEY")
        self.use_llm = False
        self.model_name = "gpt-oss:20b-cloud"
        
        # We check if a real token is provided, not the default placeholders
        if self.token and self.token.strip() and self.token not in ["your_key_here", "your_actual_token_here", "your_openai_api_key_here"]:
            try:
                # Initialize Ollama client pointing to the hosted Ollama Cloud endpoint
                self.client = Client(host="https://ollama.com")
                print("[Info] Initialized Ollama Cloud client.")
                self.use_llm = True
            except Exception as e:
                # API key is never included in the log output or exception prints for safety
                print(f"[Warning] Failed to initialize Ollama Cloud client: {type(e).__name__}. Falling back to deterministic agent.")
                self.use_llm = False
        else:
            print("[Error] OLLAMA_API_KEY environment variable is missing. Please configure it in your .env file or environment.")
            self.use_llm = False

    def run(self, destination, trip_type, duration):
        # Reset the global tools state before a new agent run
        clear_packing_list()

        print("\n=== STEP 1: Understanding User Goal & Saving to Memory ===")
        self.memory.save_trip(trip_type, destination, duration)
        print(f"Destination: {destination}")
        print(f"Trip type: {trip_type}")
        print(f"Duration: {duration} days")

        print("\n=== STEP 2: Invoking Tool: check_weather() ===")
        weather = check_weather(destination)
        self.current_weather = weather
        print(f"Tool check_weather('{destination}') returned: {weather}")

        if "error" in weather:
            print(f"[Error] Weather information for '{destination}' could not be retrieved. Agent aborting.")
            return {
                "error": f"Weather data not found for destination '{destination}'."
            }

        print("\n=== STEP 3: Deciding Packing List (Reasoning & LLM Prompting) ===")
        items = []
        if self.use_llm:
            try:
                print(f"[AI Logic] Sending context (Goal + Weather + Memory) to Ollama Cloud LLM ({self.model_name})...")
                
                prompt = f"""
You are a Smart Packing Agent. Your task is to decide what items a user needs to pack for their trip.

TRIP DETAILS:
- Destination: {destination}
- Trip Type: {trip_type}
- Duration: {duration} days

WEATHER AT DESTINATION (Retrieved from Tool):
{json.dumps(weather, indent=2)}

CURRENT PACKING LIST (From Memory):
{json.dumps(self.memory.get_memory()["items"], indent=2)}

INSTRUCTIONS:
1. Analyze the destination weather: If cold (< 15°C) suggest warm clothing. If hot (> 25°C) suggest light clothes. If rainy, suggest umbrella/raincoat.
2. Analyze the trip type: Suggest items relevant to '{trip_type}' (e.g. trekking shoes for trekking, swimwear/sunscreen/sunglasses for beach, formal clothes/laptop/charger for business).
3. Analyze the duration: If it is 5 or more days, suggest 'Extra clothes'.
4. Respond ONLY with a valid JSON array of strings containing the item names (e.g., ["Jacket", "Trekking shoes", "Water bottle"]). Do not output markdown code blocks (like ```json), do not write conversational filler or reasoning, just return the raw JSON array.
"""
                response = self.client.chat(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise packing assistant. Always respond with raw JSON arrays of strings."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    options={
                        "temperature": 0.1
                    }
                )
                
                response_text = response['message']['content'].strip()
                
                # Strip standard markdown wrappers if the model generated them
                if response_text.startswith("```"):
                    lines = response_text.splitlines()
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        lines = lines[1:-1]
                    response_text = "\n".join(lines).strip()
                
                items = json.loads(response_text)
                print(f"[AI Logic] LLM reasoning decided these items: {items}")
                
            except Exception as e:
                # Ensure exception string is filtered/truncated to never expose API key if included in trace
                clean_err_msg = str(e)[:250]
                print(f"[Warning] LLM call failed with error: {type(e).__name__} - {clean_err_msg}. Falling back to deterministic rules.")
                items = self._deterministic_packing(destination, trip_type, duration, weather)
        else:
            print("[Local Logic] Computing decisions locally using deterministic rules...")
            items = self._deterministic_packing(destination, trip_type, duration, weather)
            print(f"[Local Logic] Decided these items: {items}")

        print("\n=== STEP 4: Invoking Tool: add_item() for Decided Items ===")
        for item in items:
            tool_res = add_item(item)
            self.memory.add_item(item)
            print(f"Called add_item('{item}') -> Tool response: {tool_res}")

        print("\n=== STEP 5: Running Safety Check: forgot_something() (Group-of-3 Feature) ===")
        current_items = self.memory.get_memory()["items"]
        missing = forgot_something(trip_type, current_items)
        
        if missing:
            print(f"[Safety Check] Detected missing items for a '{trip_type}' trip: {missing}")
            print("Automatically adding missing items to make the trip safe...")
            for m_item in missing:
                tool_res = add_item(m_item)
                self.memory.add_item(m_item)
                print(f"Called add_item('{m_item}') -> Tool response: {tool_res}")
        else:
            print("[Safety Check] No required items missing. The list is safe!")

        print("\n=== STEP 6: Reading Memory and Compiling Final Recommendation ===")
        final_memory = self.memory.get_memory()
        print("Final Memory State:")
        print(json.dumps(final_memory, indent=4))
        return final_memory

    def _deterministic_packing(self, destination, trip_type, duration, weather):
        """Standard backup reasoning logic if LLM is unavailable."""
        items = []
        temp = weather.get("temperature", 20)
        is_rainy = weather.get("rain", False)
        
        # Weather rules
        if temp < 15:
            items.extend(["Jacket", "Warm clothes"])
        else:
            items.extend(["T-shirts", "Shorts"])
            
        if is_rainy:
            items.extend(["Raincoat", "Umbrella"])
            
        # Trip type rules
        t_type = trip_type.lower().strip()
        if t_type == "trekking":
            items.extend(["Trekking shoes", "Water bottle"])
        elif t_type == "beach":
            items.extend(["Swimwear", "Sunglasses", "Sunscreen"])
        elif t_type == "business":
            items.extend(["Formal clothes", "Laptop", "Charger"])
            
        # Duration rules
        if duration >= 5:
            items.append("Extra clothes")
            
        # Return list with duplicates removed but order preserved
        seen = set()
        unique_items = []
        for x in items:
            if x not in seen:
                seen.add(x)
                unique_items.append(x)
        return unique_items

if __name__ == "__main__":
    import sys
    import os
    # Add parent directory to sys.path to resolve 'src' imports
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    # Run the agent for a sample destination
    agent = PackingAgent()
    agent.run(destination="Manali", trip_type="trekking", duration=4)

