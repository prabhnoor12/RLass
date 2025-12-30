import asyncio
import random
import time
from typing import List, Dict, Any, Callable, Optional

class Provider:
    def __init__(self, name: str, api_url: str, api_key: str, quota: int):
        self.name = name
        self.api_url = api_url
        self.api_key = api_key
        self.quota = quota
        self.usage = 0
        self.last_error = None

class ProviderProxy:
    def __init__(self, providers: List[Provider], optimistic_threshold: float = 0.9, max_queue_size: int = 100):
        self.providers = providers
        self.optimistic_threshold = optimistic_threshold
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.lock = asyncio.Lock()

    async def send_request(self, payload: Dict[str, Any], *, optimistic: bool = True, max_retries: int = 5) -> Any:
        # Main entry point: send a request, handle retries, backoff, and provider selection
        for attempt in range(max_retries):
            provider = await self._select_provider(optimistic=optimistic)
            if not provider:
                # If no provider is available, queue the request
                await self._queue_request(payload)
                return {"status": "queued"}
            try:
                response = await self._call_provider(provider, payload)
                if response.get("status_code") == 429:
                    await self._backoff(attempt)
                    continue
                provider.usage += 1
                return response
            except Exception as e:
                provider.last_error = str(e)
                await self._backoff(attempt)
        # If all retries fail, queue the request
        await self._queue_request(payload)
        return {"status": "queued"}

    async def _select_provider(self, optimistic: bool = True) -> Optional[Provider]:
        # Pooling/optimistic logic: select provider with quota left, or allow if < threshold
        async with self.lock:
            available = [p for p in self.providers if p.usage < p.quota]
            if available:
                return random.choice(available)
            if optimistic:
                optimistic_providers = [p for p in self.providers if p.usage < int(p.quota * self.optimistic_threshold)]
                if optimistic_providers:
                    return random.choice(optimistic_providers)
        return None

    async def _call_provider(self, provider: Provider, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder for actual HTTP call (to be implemented)
        # Simulate API call and random 429s
        await asyncio.sleep(0.05)  # Simulate network latency
        if random.random() < 0.1:
            return {"status_code": 429, "error": "Rate limit"}
        return {"status_code": 200, "result": f"Response from {provider.name}"}

    async def _backoff(self, attempt: int):
        # Exponential backoff with jitter
        base = 0.2 * (2 ** attempt)
        jitter = random.uniform(0, 0.2)
        await asyncio.sleep(base + jitter)

    async def _queue_request(self, payload: Dict[str, Any]):
        try:
            self.queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass  # Drop if queue is full (could log or handle differently)

    async def process_queue(self):
        # Background task to process queued requests
        while True:
            payload = await self.queue.get()
            await self.send_request(payload)
            self.queue.task_done()

# Example usage:
# providers = [Provider("openai", "https://api.openai.com", "sk-xxx", 1000)]
# proxy = ProviderProxy(providers)
# asyncio.create_task(proxy.process_queue())
# await proxy.send_request({"prompt": "hello"})
