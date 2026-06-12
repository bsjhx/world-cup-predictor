import json
from openai import OpenAI
from prompts import SYSTEM_PROMPT
from tools import registry
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("URL")
)

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