from smolagents import (
    CodeAgent,
    GoogleSearchTool,
    # HfApiModel,
    LiteLLMModel,
    ToolCallingAgent,
    models,
    Tool,
HfApiModel,
AmazonBedrockServerModel
)
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from together import Together
from transformers import pipeline

load_dotenv()
from typing import List, Optional, Dict
import warnings
import litellm
import boto3

custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}


def bedrock_model():
    # "bedrock/us.meta.llama3-3-70b-instruct-v1:0"
    # meta-llama/Llama-4-Scout-17B-16E-Instruct
    model_params = {
        "model_id": "bedrock/us.meta.llama3-3-70b-instruct-v1:0",
        "custom_role_conversions": custom_role_conversions,
        "max_completion_tokens": 8192,
        "temperature": 0,
    }
    # model = LiteLLMModel(**model_params)
    model = AmazonBedrockServerModel(model_id="meta.llama3-3-70b-instruct-v1:0")
    return model


def openai_model():
    """
    model_id = "anthropic/claude-3-5-sonnet-latest"

    """
    model_params = {
        "model_id": "openai/gpt-4o",
        "custom_role_conversions": custom_role_conversions,
        "max_completion_tokens": 8192,
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
    model = LiteLLMModel(**model_params)
    return model


def groq_model():
    model_params = {
        "model_id": "groq/llama3-8b-8192",
        "custom_role_conversions": custom_role_conversions,
        "max_completion_tokens": 8192,
        "api_key": os.getenv("GROQ_API_KEY"),
    }
    model = LiteLLMModel(**model_params)
    return model

def huggingface_model(model="deepseek-ai/DeepSeek-V3-0324"):
    engine = HfApiModel(
        provider="novita",
        model_id=model,
        token=os.getenv("HF_TOKEN"),
        max_tokens=5000, )
    return engine

class WikiInputs(BaseModel):
    """Inputs to the wikipedia tool."""

    query: str = Field(description="query to look up in Wikipedia, should be 3 or less words")


class CreateModel(models.ApiModel):
    """Model to use [LiteLLM Python SDK](https://docs.litellm.ai/docs/#litellm-python-sdk) to access hundreds of LLMs.

    Parameters:
        model_id (`str`):
            The model identifier to use on the server (e.g. "gpt-3.5-turbo").
        api_base (`str`, *optional*):
            The base URL of the provider API to call the model.
        api_key (`str`, *optional*):
            The API key to use for authentication.
        custom_role_conversions (`dict[str, str]`, *optional*):
            Custom role conversion mapping to convert message roles in others.
            Useful for specific models that do not support specific message roles like "system".
        flatten_messages_as_text (`bool`, *optional*): Whether to flatten messages as text.
            Defaults to `True` for models that start with "ollama", "groq", "cerebras".
        **kwargs:
            Additional keyword arguments to pass to the OpenAI API.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        api_base=None,
        api_key=None,
        custom_role_conversions: Optional[Dict[str, str]] = None,
        flatten_messages_as_text: bool | None = None,
        **kwargs,
    ):
        if not model_id:
            warnings.warn(
                "The 'model_id' parameter will be required in version 2.0.0. "
                "Please update your code to pass this parameter to avoid future errors. "
                "For now, it defaults to 'anthropic/claude-3-5-sonnet-20240620'.",
                FutureWarning,
            )
            model_id = "anthropic/claude-3-5-sonnet-20240620"
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.custom_role_conversions = custom_role_conversions
        flatten_messages_as_text = (
            flatten_messages_as_text
            if flatten_messages_as_text is not None
            else self.model_id.startswith(("ollama", "groq", "cerebras"))
        )
        super().__init__(flatten_messages_as_text=flatten_messages_as_text, **kwargs)

    def __call__(
        self,
        messages: List[Dict[str, str]],
        stop_sequences: Optional[List[str]] = None,
        grammar: Optional[str] = None,
        tools_to_call_from: Optional[List[Tool]] = None,
        **kwargs,
    ) -> models.ChatMessage:
        try:
            import litellm
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Please install 'litellm' extra to use LiteLLMModel: `pip install 'smolagents[litellm]'`"
            )

        completion_kwargs = self._prepare_completion_kwargs(
            messages=messages,
            stop_sequences=stop_sequences,
            grammar=grammar,
            tools_to_call_from=tools_to_call_from,
            model=self.model_id,
            api_base=self.api_base,
            api_key=self.api_key,
            convert_images_to_image_urls=True,
            custom_role_conversions=self.custom_role_conversions,
            **kwargs,
        )

        response = litellm.completion(**completion_kwargs)

        self.last_input_token_count = response.usage.prompt_tokens
        self.last_output_token_count = response.usage.completion_tokens
        first_message = models.ChatMessage.from_dict(
            response.choices[0].message.model_dump(include={"role", "content", "tool_calls"})
        )
        first_message.raw = response
        return self.postprocess_message(first_message, tools_to_call_from)

def together_model():
    client = Together()
    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role": "user", "content": "who are you?"}]
    )
    print(response.choices[0].message.content)

def transformer_hugging_face():
    messages = [
        {"role": "user", "content": "Who are you?"},
    ]
    pipe = pipeline("text-generation", model="deepseek-ai/DeepSeek-V3-0324")
    print(pipe(messages))

def gemini_model():
    messages = [
        {"role": "user", "content": "Who are you?"},
    ]
    model = LiteLLMModel(
        model_id="gemini/gemini-1.5-pro",
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    response = model(messages)
    print(response.content)
if __name__ == '__main__':
    gemini_model()