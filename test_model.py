from litellm import completion
import os
import litellm
from dotenv import load_dotenv

load_dotenv()
litellm._turn_on_debug()
# Try a simple completion with DeepSeek Reasoner
messages = [
    {"role": "system", "content": "You are a helpful AI assistant that gives very concise answers like a pirate."},
    {"role": "user", "content": "Say hello!"},
]

try:
    response = completion(model="deepseek/deepseek-chat", messages=messages)
    print(response)
except Exception as e:
    print(f"Error: {str(e)}")
