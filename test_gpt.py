from openai import OpenAI
import os

print("API key:", os.getenv("OPENAI_API_KEY"))

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Piši poetično v slovenščini."},
        {"role": "user", "content": "sanje, beg, jeza"},
    ],
)

print("\nGPT ODGOVOR:\n")
print(response.choices[0].message.content)
