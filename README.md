# Smart Packing Agent

A python-based agentic workflow that plans, check weather conditions via tool calls, decides what to pack, logs items via tool calls, updates a stateful memory, and flags any missing required items for trekking, beach, or business trips.

## Architecture

```
                    USER
                      │
                      ▼
              ┌───────────────┐
              │   AI AGENT    │
              └───────┬───────┘
                      │
             ┌────────┴────────┐
             ▼                 ▼
     check_weather()      add_item()
             │                 │
             ▼                 ▼
       Weather data       Packing list
             │                 │
             └────────┬────────┘
                      ▼
                  MEMORY (and "Forgot Something?" check)
                      │
                      ▼
              Final recommendation
```

### Agentic Loop Details
1. **Understand Goal**: Record destination, trip type, and duration. Save trip context to `Memory`.
2. **Retrieve Context via Tools**: Execute `check_weather(city)` to inspect the current environment.
3. **Decide & Act**: Execute `add_item(item)` iteratively based on weather and trip type logic.
4. **Safety Check**: Perform a "forgot something" inspection comparing standard templates against packed items.
5. **Memory Retrieval**: Output the final stateful log of the trip.

---

## Directory Structure

```
SmartPackingAgent/
│
├── .env                  # Secrets configuration
├── .gitignore            # Git exclusion rules
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
│
├── src/
│   ├── tools.py          # Weather database, Packing list state, and Forgot check
│   ├── memory.py         # Memory class storing trip history
│   └── agent.py          # The core PackingAgent logic
│
├── data/                 # Data directory
└── notebooks/
    └── demo.ipynb        # Jupyter notebook demonstrating cold, hot, and rainy trips
```

---

## Getting Started

### 1. Set Up Virtual Environment
Initialize and activate your environment, then install dependencies:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure API Key
Create a GitHub Models API Token from your GitHub Settings under Developer Settings, then place it inside `.env`:
```env
GITHUB_TOKEN=your_actual_token_here
```
*Note: If no token is provided, the agent runs in a robust deterministic fallback mode to allow local testing and demonstration.*

### 3. Run the Demos
Run Jupyter Notebook to inspect the agent logs:
```powershell
jupyter notebook
```
Open `notebooks/demo.ipynb` to view the three demo scenarios: Cold trekking (Manali), Hot beach (Goa), and Cold rainy (Shimla).

---

## Viva Questions & Answers

### 1. Where is your first tool?
The first tool is `check_weather(city)` located in `src/tools.py`. It queries a mock weather database to obtain details such as temperature, weather condition (cold, hot, etc.), and if it is raining.

### 2. Where is your second tool?
The second tool is `add_item(item)` located in `src/tools.py`. It updates a global packing list and returns the state of the list.

### 3. Where is your memory?
The memory is implemented in the `Memory` class in `src/memory.py`. It stores the destination, trip type, duration, and the current list of items packed, allowing state to persist.

### 4. Why is this an agent and not a chatbot?
Unlike a chatbot that directly replies with a static list of suggestions in a single turn, this agent goes through a structured reasoning loop:
1. It analyzes the user's intent.
2. It calls the `check_weather` tool to fetch environment data.
3. It inspects the tool output to make reasoning decisions.
4. It calls `add_item` iteratively.
5. It runs verification scripts (the "forgot something" check).
6. It reviews its memory before outputting the final recommendation.

### 5. Show me the agentic loop.
```
  PLAN
   ↓
check_weather() (Tool Call)
   ↓
OBSERVE (Examine weather)
   ↓
DECIDE (Evaluate items & trip type)
   ↓
add_item() (Tool Call)
   ↓
MEMORY (Update state)
   ↓
FINAL RESULT
```
