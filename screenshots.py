
import asyncio
import os.path
import tomllib
import urllib.parse

from datetime             import datetime
from playwright.async_api import async_playwright, Playwright, Page


POST_INJECT_CSS = """

/* Hides the login prompt banner. */

.IvzMP.VC_rY.hgN9e {
    display: none;
}

""" 



async def screenshot_post(page: Page, url: str, path: str = ".") -> str:
    
    """
    Using the Playwright page `page`, navigates to and screenshots a Tumblr post at `url`.
    
    This screenshot is then saved to disk at `path/filename.png`.
    
    :param Page page: A Playwright page object.
    :param str url:   The URL of the Tumblr post to save
    :param str path:  Directory to save the screenshot to.
    
    :returns str: The path to the screenshot.
    """
    
    # Ensure types.
    
    if type(page) != Page:
        raise TypeError(f"screenshot_post() expected Playwright Page, received {type(page).__name__}.")
    
    if type(url) != str:
        raise TypeError(f"screenshot_post() expected a string, received {type(url).__name__}")
    
    # Generate screenshot filename.
    
    url_path = urllib.parse.urlparse(url).path.split("/")
    
    username = url_path[1]
    post_id  = [i for i in url_path if i.isnumeric()][0]
    
    print(username, post_id)
    
    date     = datetime.today().strftime("%Y%m%d")                    # Get the date in YYYYMMDD format.
    img_path = os.path.join(path, f"{username}-{post_id}-{date}.png") # Screenshot path -- will be saved to path/USERNAME-EXAMPLE_ID-YYYYMMDD.png
    
    # Go to URL. 
    
    await page.goto(url, wait_until="domcontentloaded")
    
    # Ensure page hasn't redirected to login-required page.
    
    if "login_required" in page.url:
        raise ValueError("Blog requires Tumblr login.")
    
    # Check for content warnings, and abort if found. (Cannot bypass mature content wall.)
    
    cw_button = page.locator('button[class="VmbqY r21y5 Li_00 zn53i EF4A5"]').get_by_text("View post")
    
    if await cw_button.count():
        await cw_button.click()
    
    # Grab the div that contains the post body. (uses class eA_DC; change if no longer working)
    
    locator   = page.locator('article').locator('div[class="eA_DC"]')
    posts_num = await locator.count()
    
    # Ensure there's at least one post.
    
    if posts_num == 0:
        raise ValueError("Could not find posts on page; either wrong URL passed or Tumblr format has changed.")
        
    # Get the target post (will always be first object hit by the locator) and screenshot it.
    
    post = locator.first
        
    await post.screenshot(
        animations = "disabled",      # Disables all CSS animations
        style      = POST_INJECT_CSS, # ".IvzMP.VC_rY.hgN9e" catches the login banner and hides it (through Firefox inspect)
        path       = img_path         
    )
    
    # Return path to image
    
    return path



async def main():
    
    POST_URL     = "https://www.tumblr.com/briefoxx/804158067301335040"
    SECRETS_PATH = "./secrets.toml"
    
    # Load playwright
    
    async with async_playwright() as playwright:
        
        # Launch headless Firefox.
        
        browser = await playwright.firefox.launch()
        context = await browser.new_context()
        
        # await context.add_cookies([
        #     {
        #         "name": "sid",
        #         "value": "...",
        #         "domain": "https://tumblr.com",
        #         "path": "/"
        #     }
        # ])
        
        # Create page (done this way to allow batch async downloads)
        
        page = await context.new_page()
        
        # Screenshot post!
        
        await screenshot_post(page, POST_URL, path="./screenshots")
        
        
        import pprint
        
        pprint.pprint(await context.cookies())
        


if __name__ == "__main__":
    
    asyncio.run(main())