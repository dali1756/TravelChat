import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(autouse=True)
def _reset_throttle_cache():
    """
    每個測試前清空 DRF throttle 的 cache，避免 rate-limit 狀態跨測試累積
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
