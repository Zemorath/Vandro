import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
GROK_API_KEY = os.getenv('GROK_API_KEY')

async def call_grok_api(system_prompt: str, user_message: str, model: str = "grok-3-mini-latest"):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.x.ai/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {GROK_API_KEY}'
            },
            json={
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                'model': model,
                'stream': False,
                'temperature': 0.7,
                'max_tokens': 200
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: Failed to connect to Grok API (status {resp.status})."