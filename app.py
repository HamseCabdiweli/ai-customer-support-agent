import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from tools import get_order

INSTRUCTIONS = (
    "You are a friendly customer support assistant. Keep replies short. "
    "Use get_order whenever you need order information. Never invent order details. "
    "If an order is missing, say you could not find it and ask the user to check the ID. "
    "If the user asks about an order without giving an ID, ask for it. "
    "Reply to greetings normally without looking up an order."
)
TOOLS = [{
    "type": "function",
    "name": "get_order",
    "description": "Look up an order by its order ID.",
    "parameters": {
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
        "additionalProperties": False,
    },
    "strict": True,
}]


def reply(client, messages, model):
    # The model chooses whether to call get_order.
    for _ in range(5):
        response = client.responses.create(
            model=model,
            instructions=INSTRUCTIONS,
            input=messages,
            tools=TOOLS,
            tool_choice="auto",
            store=False,
        )
        messages.extend(response.output)
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text or "Sorry, I could not get a reply. Please try again."

        for call in calls:
            try:
                if call.name != "get_order":
                    raise ValueError("Unknown tool")
                args = json.loads(call.arguments)
                order = get_order(args["order_id"])
                result = order if order is not None else {"error": "Order not found"}
            except (ValueError, KeyError, TypeError):
                result = {"error": "Could not read the order lookup request"}
            except OSError:
                result = {"error": "Order data is unavailable"}
            messages.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(result),
            })
    raise ValueError("Too many tool calls")


def main():
    load_dotenv(Path(__file__).with_name(".env"))
    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("Add OPENAI_API_KEY to your .env file first.")
        return

    client = OpenAI(timeout=30, max_retries=1)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    messages = []
    print("Customer support chat. Type quit to exit.")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if text.lower() in ("quit", "exit"):
            break
        if not text:
            continue
        # Keep the previous conversation if this request fails.
        turn = messages + [{"role": "user", "content": text}]
        try:
            answer = reply(client, turn, model)
        except OpenAIError:
            print("Support: Could not connect to OpenAI. Check your key and connection.")
        except ValueError:
            print("Support: Something went wrong. Please try again.")
        else:
            messages = turn
            print("Support:", answer)


if __name__ == "__main__":
    main()
