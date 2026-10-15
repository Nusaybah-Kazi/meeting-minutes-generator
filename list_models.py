from src.llm import get_client

for m in sorted(get_client().models.list().data, key=lambda m: m.id):
    print(m.id)