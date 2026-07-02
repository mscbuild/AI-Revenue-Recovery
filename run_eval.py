import json
from google import genai
from google.adk import Agent
from app.agent import CustomerSupportAgent

agent = CustomerSupportAgent()

with open("eval_dataset.json", encoding="utf-8") as f:
    dataset = json.load(f)

for i, case in enumerate(dataset, 1):

    response = agent.run(case["input"]).lower()

    missing = [
        word for word in case["keywords"]
        if word.lower() not in response
    ]

    if missing:
        print(f"Test {i}: FAIL")
        print("Missing:", missing)
    else:
        print(f"Test {i}: PASS")
