from playwright.async_api import async_playwright
import asyncio


async def scrape_job_url(url: str) -> dict:
    """
    Uses Playwright to scrape a job posting URL.
    Returns the title, body text, and success flag.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")

            title = await page.title()
            body_text = await page.evaluate("() => document.body.innerText")
            description = body_text[:3000] if body_text else ""

            return {
                "title": title or "Unknown",
                "description": description,
                "url": url,
                "success": True,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}
        finally:
            await browser.close()


def scrape_job_sync(url: str) -> dict:
    """Synchronous wrapper for LangChain tools."""
    return asyncio.run(scrape_job_url(url))