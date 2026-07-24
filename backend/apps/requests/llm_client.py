"""LLM client for material parsing using OpenAI-compatible API."""
import json, httpx, logging
from django.conf import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = getattr(settings, 'LLM_API_KEY', '')
        self.model = getattr(settings, 'LLM_MODEL', 'deepseek-chat')
        self.base_url = getattr(settings, 'LLM_BASE_URL', 'https://api.deepseek.com/v1')

    def chat(self, messages, response_format=None):
        payload = {'model': self.model, 'messages': messages, 'temperature': 0.1, 'max_tokens': 2000}
        if response_format:
            payload['response_format'] = response_format
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        response = httpx.post(f'{self.base_url}/chat/completions', json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

llm = LLMClient()
