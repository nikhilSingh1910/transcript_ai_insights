import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.call import Call

DATA_PATH = "data/transcripts.jsonl"  # the location of transcripts json 

def load_calls_into_db():
    session: Session = SessionLocal()
    try:
        with open(DATA_PATH, 'r') as f:
            for line in f:
                item = json.loads(line)
                call = Call(
                    call_id=item["call_id"],
                    agent_id=item["agent_id"],
                    customer_id=item["customer_id"],
                    language=item["language"],
                    start_time=datetime.fromisoformat(item["start_time"]),
                    duration_seconds=item["duration_seconds"],
                    transcript=item["transcript"]
                )
                session.merge(call)
        session.commit()
        print("All records imported successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    load_calls_into_db()
