
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


async def screenshot_post(page: Page, url: str, screenshot_all: bool = False, path=".") -> str:
    
    """
    Using the Playwright page `page`, navigates to and screenshots a Tumblr post at `url`.
    
    This screenshot is then saved to disk at `path/filename.png`.
    
    :param Page page:           A Playwright page object.
    :param str url:             The URL of the Tumblr post to save
    :param bool screenshot_all: Description
    
    :returns str: The path to the screenshot.
    """
    
    # Ensure types.
    
    if type(page) != Page:
        raise TypeError(f"screenshot_post() expected Playwright Page, received {type(page).__name__}.")
    
    if type(url) != str:
        raise TypeError(f"screenshot_post() expected a string, received {type(url).__name__}")
    
    if type(screenshot_all) != bool:
        raise TypeError(f"screenshot_post() expected a bool, received {type(screenshot_all).__name__}")
    
    # Go to URL. 
    
    await page.goto(url, wait_until="domcontentloaded")
    
    # Check for content warnings, and abort if found. (Cannot bypass mature content wall.)
    
    cw_button = page.locator('button[class="VmbqY r21y5 Li_00 zn53i EF4A5"]')
    
    if await cw_button.count():
        raise ValueError("Cannot get past Tumblr auth on mature posts currently.")
    
    # Grab the div that contains the post body. (uses data-testID: "timelinePosts"; change if no longer working)
    
    locator   = page.locator('article div[class="eA_DC"]')
    posts_num = await locator.count()
    
    # Ensure there's at least one post.
    
    if posts_num <= 0:
        raise ValueError("Could not find posts on page; either wrong URL passed or Tumblr format has changed.")
    
    # Generate screenshot filename.
    
    post_id  = [i for i in urllib.parse.urlparse(url).path.split("/") if i.isnumeric()][0]
    
    date     = datetime.today().strftime("%Y%m%d")            # Get the date in YYYYMMDD format.
    img_path = os.path.join(path, f"{post_id}-{date}.png")    # Saves screenshot at path/EXAMPLE_ID-YYYYMMDD-N.png
        
    # Get the target post (will always be first object hit by the locator) and screenshot it.
    
    post = locator.first
        
    await post.screenshot(
        animations = "disabled",                          # Disables all CSS animations
        style      = POST_INJECT_CSS, # ".IvzMP.VC_rY.hgN9e" catches the login banner and hides it (through Firefox inspect)
        path       = img_path         
    )
    
    # Return path to image
    
    return path



def load_secrets(path: str) -> dict[str, str]:
    
    with open(path) as f:
        
        data = tomllib.loads(f.read())
        
        if "CONSUMER_KEY" not in data:
            raise ValueError("CONSUMER_KEY not found within secrets file!")
        
        if "SECRET_KEY" not in data:
            raise ValueError("SECRET_KEY not found within secrets file!")

        return data



async def main():
    
    POST_URL     = "[YOUR POST HERE]"
    SECRETS_PATH = "./secrets.toml"
    
    # Load secrets
    
    secrets = load_secrets(SECRETS_PATH)
    
    print(secrets)
    
    """
    
    # Load playwright
    
    async with async_playwright() as playwright:
        
        # Launch headless Firefox.
        
        browser = await playwright.firefox.launch()
        
        # Create page (done this way to allow batch async downloads)
        
        page = await browser.new_page()
        
        # Screenshot post!
        
        await screenshot_post(page, POST_URL, screenshot_all=True)
    
    """
        


if __name__ == "__main__":
    
    asyncio.run(main())