import os 

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
  base_url = os.getenv('BASE_URL'),
  api_key = os.getenv("MEMOTRON_3_5_LIGHTNING_30B_A3B_KEY")
)


completion = client.chat.completions.create(
  model= os.getenv('MODEL_NAME'),
  messages=[{"role":"user","content":"Write a limerick about the wonders of GPU computing."}],
  temperature=1,
  top_p=0.95,
  max_tokens=16384,
  extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
  stream=True
)

for chunk in completion:
  if not chunk.choices:
    continue
  reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
  if reasoning:
    print(reasoning, end="")
  if chunk.choices[0].delta.content is not None:
    print(chunk.choices[0].delta.content, end="")

    