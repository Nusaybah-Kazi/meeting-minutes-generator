from src import config
from src.llm import chat

print("Model:", config.LLM_MODEL)
reply = chat("Reply with exactly: Groq connection OK")
print("Reply:", reply)