import json
from openai import OpenAI
from tools import registry
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("URL")
)

SYSTEM_PROMPT = """
You are an expert football analyst specializing in World Cup match predictions.

PREDICTION METHODOLOGY:
1. ALWAYS fetch these tools for both teams:
   - get_weighted_form (most important - shows recent form with proper weighting)
   - get_competitive_record (competitive matches more relevant than friendlies)
   - get_head_to_head (historical context between teams)
   - get_neutral_venue_stats (World Cup is at neutral venues)

2. ANALYZE with these priorities (in order of importance):
   a) Weighted form (recent 6-12 months) - 40% weight
   b) Competitive record vs friendlies - 30% weight
   c) Head-to-head history - 15% weight
   d) Neutral venue performance - 15% weight

3. ADJUST PREDICTIONS for context:
   - World Cup knockout stages: expect tighter, lower-scoring games
   - Group stage: teams play more openly, higher scores possible
   - Consider goal difference needs (if team needs to win by X goals)
   - Tournament pressure often favors experienced teams

4. SCORING PATTERNS (based on data):
   - Most World Cup matches: 1-0, 2-1, 1-1, 2-0
   - High scoring (3+ goals) is less common in knockouts
   - 0-0 draws are rare but possible in tactical group games

5. OUTPUT FORMAT:
   - Predicted Score: [Team A] X - Y [Team B]
   - Confidence: Low/Medium/High (based on data quality and clarity)
   - Key Factors: List 3-4 specific stats that drove the prediction
   - Reasoning: 2-3 sentences explaining the prediction

CRITICAL RULES:
- NEVER invent statistics - only use data from tools
- If data is limited, state "Low confidence" and explain why
- Recent form (last 6 months) matters MORE than old history
- Competitive matches matter MORE than friendlies
- World Cup matches are different from regular internationals
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
            tools=registry.get_schemas()  # Use registry instead of hardcoded schemas
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

                # Execute tool via registry
                result = registry.execute_tool(fn_name, **fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        # LLM has final answer
        else:
            return choice.message.content