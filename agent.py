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