import pytest
from toll.adapters.search.duckduckgo import DuckDuckGoSearch

pytestmark = pytest.mark.network


@pytest.mark.skip(reason="Network-dependent; run manually with pytest -m network")
def test_duckduckgo_search_sync():
    search = DuckDuckGoSearch()
    results = search.search_sync("python programming", max_results=3)
    assert len(results) <= 3
    for r in results:
        assert r.title
        assert r.url


@pytest.mark.asyncio
@pytest.mark.skip(reason="Network-dependent; run manually with pytest -m network")
async def test_duckduckgo_search_async():
    search = DuckDuckGoSearch()
    results = await search.search("python programming", max_results=3)
    assert len(results) <= 3
    for r in results:
        assert r.title
        assert r.url
