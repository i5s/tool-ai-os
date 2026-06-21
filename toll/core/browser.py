import asyncio
from . import config

class BrowserAI:
    def __init__(self):
        self.playwright = None

    async def _ensure(self):
        if self.playwright is None:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
        return self.playwright

    async def ask_free_ai(self, prompt: str, url: str = None) -> str:
        pw = await self._ensure()
        target = url or config.FREE_AI_URLS[0]
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(target, timeout=30000)
        await page.wait_for_timeout(2000)
        text = await page.inner_text("body")
        await browser.close()
        return text

    async def browse(self, url: str, wait_ms: int = 3000) -> str:
        pw = await self._ensure()
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(wait_ms)
        text = await page.inner_text("body")
        await browser.close()
        return text

    async def scrape(self, url: str, selector: str = None) -> str:
        pw = await self._ensure()
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(2000)
        if selector:
            el = await page.query_selector(selector)
            text = await el.inner_text() if el else ""
        else:
            text = await page.inner_text("body")
        await browser.close()
        return text

    def ask(self, prompt: str, url: str = None) -> str:
        return asyncio.run(self.ask_free_ai(prompt, url))

    def get(self, url: str) -> str:
        return asyncio.run(self.browse(url))
