from langchain_core.language_models.chat_models import BaseChatModel
from core.config import settings

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    class WrappedChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
        def _generate(self, *args, **kwargs):
            chat_result = super()._generate(*args, **kwargs)
            for generation in chat_result.generations:
                msg = generation.message
                if hasattr(msg, "content") and isinstance(msg.content, list):
                    text_parts = []
                    for part in msg.content:
                        if isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                        elif isinstance(part, str):
                            text_parts.append(part)
                    msg.content = "".join(text_parts)
            return chat_result

        async def _agenerate(self, *args, **kwargs):
            chat_result = await super()._agenerate(*args, **kwargs)
            for generation in chat_result.generations:
                msg = generation.message
                if hasattr(msg, "content") and isinstance(msg.content, list):
                    text_parts = []
                    for part in msg.content:
                        if isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                        elif isinstance(part, str):
                            text_parts.append(part)
                    msg.content = "".join(text_parts)
            return chat_result
except ImportError:
    WrappedChatGoogleGenerativeAI = None

def get_llm(model_name: str, temperature: float = 0.7, format: str = None) -> BaseChatModel:
    if "gemini" in model_name.lower():
        if WrappedChatGoogleGenerativeAI is None:
            raise ImportError("Please install langchain-google-genai to use Gemini models.")
        kwargs = {
            "model": model_name,
            "temperature": temperature,
            "google_api_key": settings.GEMINI_API_KEY
        }
        if format == "json":
             kwargs["model_kwargs"] = {"response_mime_type": "application/json"}
        return WrappedChatGoogleGenerativeAI(**kwargs)
    else:
        from langchain_ollama import ChatOllama
        kwargs = {
            "model": model_name,
            "base_url": settings.OLLAMA_BASE_URL,
            "temperature": temperature
        }
        if format:
            kwargs["format"] = format
        return ChatOllama(**kwargs)
