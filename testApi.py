from openai import OpenAI

client = OpenAI(
  api_key="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"
)

response = client.responses.create(
  model="gpt-5-nano",
  input="write a haiku about ai",
  store=True,
)

print(response.output_text);