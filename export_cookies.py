import asyncio
from playwright.async_api import async_playwright

async def main():
    p = await async_playwright().start()
    b = await p.firefox.launch(headless=False)
    c = await b.new_context()
    page = await c.new_page()
    await page.goto("https://facebook.com")
    input("Log in to Facebook and press Enter here...")
    await c.storage_state(path=r"C:\Users\R5 5600 GT\fb_cookies_playwright.json")
    print("Cookies saved.")
    await b.close()

asyncio.run(main())