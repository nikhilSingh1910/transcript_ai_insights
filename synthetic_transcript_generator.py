import asyncio
import json
from datetime import datetime, timedelta
from faker import Faker
import random
import openai
import os
from threading import Lock

fake = Faker()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Simulated agent IDs (lets pretend these are our real call center agents)
AGENT_IDS = ["A1", "A2", "A3", "A4", "A5"]
SAVE_FILE = "transcripts.jsonl"

# Thread lock to ensure only one thread writes to the file at a time
file_lock = Lock()

def generate_customer_query():
    """
    Randomly pick a customer query type and return a sentence for it.
    """
    query_type = random.choice(["order_status", "billing", "account", "technical_issue"])
    if query_type == "order_status":
        return f"Can you update me on the status of my order #ORD{fake.random_number(digits=6)}?"
    elif query_type == "billing":
        return f"I received a wrong charge on my bill, can you review it for me?"
    elif query_type == "account":
        return f"I'm unable to log into my account. Could you help me with a password reset?"
    elif query_type == "technical_issue":
        return f"I'm experiencing issues with the {fake.word()} feature. It’s not working correctly."

async def generate_transcript_with_llm(call_id: str, customer_id: str, agent_id: str):
    language = "English"
    start_time = datetime.now() - timedelta(minutes=random.randint(1, 120))
    duration_seconds = random.randint(60, 1200)
    customer_query = generate_customer_query()

    prompt = f"Generate a customer service conversation between an agent and a customer. The customer says: {customer_query}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1,
        )
        cleaned_response = response["choices"][0]["message"]["content"]

        result = {
            "call_id": call_id,
            "agent_id": agent_id,
            "customer_id": customer_id,
            "language": language,
            "start_time": start_time.isoformat(),
            "duration_seconds": duration_seconds,
            "transcript": cleaned_response
        }

        # Write to file asynchronously
        await asyncio.to_thread(write_line_to_file, result)

    except Exception as e:
        print(f"Error generating transcript for call_id={call_id}: {e}")

def write_line_to_file(transcript):
    """
    Write a single transcript as JSON to the transcripts file.
    Uses a file lock to avoid write collisions.
    """
    line = json.dumps(transcript)
    with file_lock:
        with open(SAVE_FILE, 'a') as f:
            f.write(line + "\n")
            f.flush()
    print(f"Saved transcript for call_id={transcript['call_id']}")

async def generate_synthetic_transcripts(num_transcripts=200):
    """
    Create N synthetic call transcripts in parallel.
    Each call gets a random agent, customer, and call ID.
    """
    tasks = []
    for _ in range(num_transcripts):
        call_id = fake.uuid4()
        customer_id = fake.uuid4()
        agent_id = random.choice(AGENT_IDS)
        tasks.append(generate_transcript_with_llm(call_id, customer_id, agent_id))
    await asyncio.gather(*tasks)

async def main():
    await generate_synthetic_transcripts()

if __name__ == "__main__":
    asyncio.run(main())
