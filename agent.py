import json
from openai import OpenAI
from tools import (
    get_head_to_head,
    get_recent_form,
    get_tournament_history,
    get_goals_stats
)
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("URL")
)

# --- Tool registry ---
TOOLS_MAP = {
    "get_head_to_head": get_head_to_head,
    "get_recent_form": get_recent_form,
    "get_tournament_history": get_tournament_history,
    "get_goals_stats": get_goals_stats,
}

# --- Tool schemas for LLM ---
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_head_to_head",
            "description": "Get historical head to head results between two national teams",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_a": {"type": "string", "description": "First team name"},
                    "team_b": {"type": "string", "description": "Second team name"},
                    "last_n": {"type": "integer", "description": "Number of recent matches to return", "default": 10}
                },
                "required": ["team_a", "team_b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_form",
            "description": "Get a team's recent match results and form",
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {"type": "string"},
                    "last_n": {"type": "integer", "default": 10}
                },
                "required": ["team"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tournament_history",
            "description": "Get a team's historical performance in a tournament like FIFA World Cup",
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {"type": "string"},
                    "tournament": {"type": "string", "default": "FIFA World Cup"}
                },
                "required": ["team"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals_stats",
            "description": "Get attacking and defensive goal statistics for a team",
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {"type": "string"},
                    "last_n": {"type": "integer", "default": 20}
                },
                "required": ["team"]
            }
        }
    },
]

SYSTEM_PROMPT = """
You are a football analyst AI specializing in World Cup predictions.
When asked to predict a match:
1. Always fetch head-to-head history
2. Always fetch recent form for both teams
3. Fetch tournament history and goals stats if relevant
4. Reason step by step over the data
5. Give a predicted score with confidence level (low/medium/high)
6. Explain your reasoning clearly
Use only data from the tools — do not invent statistics.
"""

def run_agent(user_question: str, verbose: bool = True) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question}
    ]

    while True:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            tools=TOOLS_SCHEMA
        )

        choice = response.choices[0]

        # LLM wants to call a tool
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                if verbose:
                    print(f"🔧 Calling tool: {fn_name}({fn_args})")

                result = TOOLS_MAP[fn_name](**fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        # LLM has final answer
        else:
            return choice.message.content