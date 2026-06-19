from langchain_core.language_models.chat_models import BaseChatModel
from core.config import settings

def get_llm(model_name: str, temperature: float = 0.7, format: str = None) -> BaseChatModel:
    if "gemini" in model_name.lower():
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            kwargs = {
                "model": model_name,
                "temperature": temperature,
                "google_api_key": settings.GEMINI_API_KEY
            }
            if format == "json":
                 kwargs["model_kwargs"] = {"response_mime_type": "application/json"}
            return ChatGoogleGenerativeAI(**kwargs)
        except ImportError:
            raise ImportError("Please install langchain-google-genai to use Gemini models.")
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
