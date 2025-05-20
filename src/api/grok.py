import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
GROK_API_KEY = os.getenv('GROK_API_KEY')

async def call_grok_api(system_prompt: str, user_message: str, model: str = "grok-3-mini-latest", max_tokens: int = 300):
    # Log prompt length (approximate words)
    prompt_length = len(system_prompt.split()) + len(user_message.split())
    print(f"Prompt length: {prompt_length} words")
    
    async with aiohttp.ClientSession() as session:
        try:
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
                    'max_tokens': max_tokens
                }
            ) as resp:
                print(f"Grok API status: {resp.status}")
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Grok API error response: {error_text}")
                    return f"Error: Failed to connect to Grok API (status {resp.status})"
                
                result = await resp.json()
                print(f"Grok API raw response: {result}")
                
                # Log token usage
                usage = result.get('usage', {})
                print(f"Token usage: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}, total={usage.get('total_tokens', 0)}")
                
                # Check for valid response structure
                if not result.get('choices') or not isinstance(result['choices'], list) or not result['choices']:
                    print("Grok API response missing choices")
                    return "Error: Invalid API response format (no choices)"
                
                choice = result['choices'][0]
                if 'message' not in choice or 'content' not in choice['message']:
                    print("Grok API response missing message or content")
                    return "Error: Invalid API response format (no message/content)"
                
                content = choice['message']['content'].strip()
                if not content:
                    print("Grok API returned empty content")
                    return "Error: Grok API returned an empty response"
                
                return content
        except Exception as e:
            print(f"Grok API exception: {str(e)}")
            return f"Error: Failed to process Grok API request: {str(e)}"