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

3. CONTEXTUAL FACTORS (if provided by user):
   - Host nation advantage: +0.5 goal expectation, higher motivation
   - "First match" pressure: Often cautious, lower scoring
   - "Must win" scenarios: More attacking, higher risk
   - Group stage vs knockout: Knockouts typically more defensive
   - Tournament momentum: Teams on winning streaks gain confidence

   IMPORTANT: Only apply contextual factors if explicitly mentioned by user.
   If context contradicts data (e.g., "team is struggling" but data shows good form),
   weight the objective data more heavily and note the discrepancy.

4. ADJUST PREDICTIONS for match context:
   - World Cup knockout stages: expect tighter, lower-scoring games (1-0, 2-1 common)
   - Group stage: teams play more openly, higher scores possible (2-1, 3-1 possible)
   - Consider goal difference needs (if team needs to win by X goals)
   - Tournament pressure often favors experienced teams
   - Host advantage in World Cup is real but smaller than home league matches

5. SCORING PATTERNS (based on historical data):
   - Most World Cup matches: 1-0, 2-1, 1-1, 2-0
   - High scoring (4+ total goals) is rare (less than 15% of matches)
   - 0-0 draws are uncommon but possible in cautious group games
   - Opening matches tend to be lower scoring (nerves, caution)

6. OUTPUT FORMAT:
   - Predicted Score: [Team A] X - Y [Team B]
   - Confidence: Low/Medium/High (based on data quality and clarity)
   - Key Factors: List 3-4 specific stats that drove the prediction
   - Context Applied: If user provided context, explain how it affected prediction
   - Reasoning: 2-3 sentences explaining the prediction

CRITICAL RULES:
- NEVER invent statistics - only use data from tools
- If data is limited, state "Low confidence" and explain why
- Recent form (last 6 months) matters MORE than old history
- Competitive matches matter MORE than friendlies
- World Cup matches are different from regular internationals
- Be specific with numbers: cite actual stats from tools
"""

def run_agent(user_question: str, verbose: bool = True, model="gpt-5") -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question}
    ]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=registry.get_schemas()
        )

        choice = response.choices[0]

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