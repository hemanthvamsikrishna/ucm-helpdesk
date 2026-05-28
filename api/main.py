from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import os
from fastapi.middleware.cors import CORSMiddleware
import re

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("ucm-helpdesk")
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

@tool
def search_ucm_knowledge(query: str) -> str:
    """Search UCM website content for information about admissions,
    financial aid, housing, registrar, transcripts, or IT support."""
    results = index.search(
        namespace="ucm",
        top_k=3,
        inputs={"text": query}
    )
    hits = results.result.hits
    print(f"DEBUG: Got {len(hits)} hits for query: {query}")
    if hits:
        print(f"DEBUG first hit: {hits[0].fields}")
    if not hits:
        return "No relevant information found."
    return "\n\n".join([hit.fields.get("text", "")[:500] for hit in hits])


@tool
def escalate_to_human(question: str, reason: str) -> str:
    """Use this when you cannot find a confident answer to the student's question.
    This flags the question for human review."""
    print(f"ESCALATION — Question: {question} | Reason: {reason}")
    return "I wasn't able to find a confident answer. Your question has been flagged for a UCM staff member to follow up with you."

agent = create_react_agent(llm, tools=[search_ucm_knowledge, escalate_to_human])

class Question(BaseModel):
    question: str

@app.post("/ask")
async def ask(q: Question):
    system_prompt = system_prompt = """You are a warm, helpful assistant for the University of Central Missouri (UCM) student services helpdesk.

Answer student questions about admissions, financial aid, housing, registrar, and IT support.

INSTRUCTIONS:
1. Always call search_ucm_knowledge first to find relevant information.
2. Use the search results to answer the question directly and confidently.
3. If search results contain relevant information, ALWAYS answer using that information. Do not escalate.
4. Only call escalate_to_human if the search returns absolutely no relevant information after searching twice.
5. Keep answers friendly, concise, and helpful. Include contact details from search results when relevant.

HANDLING UNKNOWN QUESTIONS:
If a student asks something outside your knowledge base, do not say you cannot help or give a blunt refusal. Instead, respond warmly like this: acknowledge what they asked, let them know this particular topic is not something you have details on right now, and gently redirect them to the most relevant UCM office or contact (registrar, financial aid office, housing office, or IT support at 660-543-4357 or tsc@ucmo.edu). Always end with an offer to help with something else.

HANDLING CASUAL MESSAGES:
If someone says hi, thanks, or makes small talk, respond naturally and briefly, then offer to help with their UCM questions. Do not search Pinecone for casual messages.

Never say things like "I was unable to find", "my knowledge base does not contain", or "I cannot answer that." Always stay warm and redirect gracefully."""

    result = agent.invoke({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": q.question}
        ]
    })
    answer = result["messages"][-1].content
    answer = re.sub(r'<function=.*?</function>', '', answer, flags=re.DOTALL).strip()
    return {"answer": answer}

@app.get("/health")
def health():
    return {"status": "ok"}