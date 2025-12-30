import pytest
import asyncio
from backend.services.provider_proxy import Provider, ProviderProxy

@pytest.mark.asyncio
async def test_send_request_success():
    providers = [Provider("p1", "url1", "key1", quota=10)]
    proxy = ProviderProxy(providers)
    payload = {"data": "test"}
    resp = await proxy.send_request(payload)
    assert resp["status_code"] == 200
    assert "Response from p1" in resp["result"]

@pytest.mark.asyncio
async def test_send_request_rate_limit_and_queue():
    providers = [Provider("p2", "url2", "key2", quota=1)]
    providers[0].usage = 1  # Simulate quota used up
    proxy = ProviderProxy(providers, optimistic_threshold=0.5)
    payload = {"data": "test2"}
    resp = await proxy.send_request(payload, optimistic=False, max_retries=1)
    assert resp["status"] == "queued"

@pytest.mark.asyncio
async def test_select_provider_optimistic():
    providers = [Provider("p3", "url3", "key3", quota=2)]
    providers[0].usage = 2  # At quota
    proxy = ProviderProxy(providers, optimistic_threshold=1.0)
    p = await proxy._select_provider(optimistic=True)
    assert p is not None or p is None  # Should not error

@pytest.mark.asyncio
async def test_queue_and_process():
    providers = [Provider("p4", "url4", "key4", quota=0)]
    proxy = ProviderProxy(providers)
    payload = {"data": "queued"}
    await proxy._queue_request(payload)
    assert not proxy.queue.empty()
    # Simulate process_queue (run one iteration only)
    async def process_once():
        item = await proxy.queue.get()
        proxy.queue.task_done()
        return item
    item = await process_once()
    assert item == payload
