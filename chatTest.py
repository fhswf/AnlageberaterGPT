from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

load_dotenv()

api_version = "2024-02-01"
deployment_name = "GPT-4o"

azure_openai_llm = AzureChatOpenAI(
    azure_deployment=deployment_name,
    temperature=0,
    openai_api_version=api_version,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

prompt = "Bitte sag mir, wie die Hauptstadt von Frankreich lautet."

response = azure_openai_llm.invoke(prompt)

print(response)