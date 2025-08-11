import os

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from transformers import pipeline

from app.db.session import SessionLocal
from app.models.call import Call

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 32


def compute_agent_talk_ratio(transcript: str) -> float:
    """
    Calculate the ratio of words spoken by the agent
    compared to the total number of words in the transcript.

    - Only counts lines starting with "**Customer Service Agent:**"
    - Returns a value between 0 and 1.
    """
    agent_lines = [
        line
        for line in transcript.splitlines()
        if line.startswith("**Customer Service Agent:**")
    ]
    words_agent = sum(len(line.split()) for line in agent_lines)
    total_words = len(transcript.split())

    return (words_agent / total_words) if total_words else 0.0


def normalize_sentiment(label_score):
    """
    Convert a Hugging Face sentiment output to a numeric score:
    - Positive → positive number
    - Negative → negative number
    - Magnitude = confidence score from the model
    """
    label = label_score["label"].lower()
    score = label_score["score"]
    if "neg" in label:
        return -score
    return score


def main():
    """
    1. Loads embeddings and sentiment models
    2. Retrieves calls without embeddings from the DB
    3. Calculates embeddings, sentiment, and talk ratio
    4. Saves updated records back to the DB
    """
    session: Session = SessionLocal()

    # Step 1: Load models
    model = SentenceTransformer("all-MiniLM-L6-v2")
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
        device=-1,
        truncation=True,
    )

    print("Processing calls for analytics...")

    # Srep 2: retreive calls from DB
    calls_to_process = session.query(Call).filter(Call.embedding.is_(None)).all()

    for i in range(0, len(calls_to_process), EMBEDDING_BATCH_SIZE):
        chunk = calls_to_process[i : i + EMBEDDING_BATCH_SIZE]
        transcripts = [c.transcript or "" for c in chunk]

        # Step 3: Create embeddings
        embeddings = model.encode(
            transcripts,
            batch_size=EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        for idx, call in enumerate(chunk):

            text_for_sent = call.transcript[:512] if call.transcript else ""
            sentiment = sentiment_pipeline(text_for_sent)[0]

            # Step 4: Update table data
            call.embedding = embeddings[idx].tolist()
            call.customer_sentiment_score = normalize_sentiment(sentiment)
            call.agent_talk_ratio = compute_agent_talk_ratio(call.transcript or "")
            session.add(call)

        session.commit()
        print(f"Updated {len(chunk)} calls.")

    session.close()
    print("Processing complete.")


if __name__ == "__main__":
    main()
