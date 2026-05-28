import json
import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("ucm-helpdesk")

with open("scraper/scraped_data.json", "r") as f:
    data = json.load(f)

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

records = []
for page in data:
    chunks = chunk_text(page["text"])
    for j, chunk in enumerate(chunks):
        records.append({
            "id": f"{page['url']}__chunk{j}",
            "text": chunk,
            "source": page["url"]
        })

print(f"Total chunks to embed: {len(records)}")

batch_size = 50
for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]
    index.upsert_records(
        namespace="ucm",
        records=[{"_id": r["id"], "text": r["text"], "source": r["source"]} for r in batch]
    )
    print(f"Upserted batch {i//batch_size + 1}")

print("Done. All chunks embedded into Pinecone.")