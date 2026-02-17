
import asyncio
import os.path
import tomllib
import urllib.parse

from datetime             import datetime
from playwright.async_api import async_playwright, expect, Page
from typing               import Any


POST_INJECT_CSS = """

/* Hides the "You need clearance" popup. */

div[aria-modal=true] {
    display: none;
}

/* Hides comments */

article div[aria-label="Post Activity"] {
    display: none;
}

/* Hide login banner */

div[data-testid=scroll-container] div div:has(footer[role=contentinfo]) { /* wow that's long?!?!? */
    display: none;
}

/* Hide communities popup */

div[role=group] div:has(div) {
    display: none;
}

""" 


async def screenshot_post(page: Page, url: str, path: str = ".") -> str:
    
    """
    Using the Playwright page `page`, navigates to and screenshots a Tumblr post at `url`.
    
    This screenshot is then saved to disk at `path/filename.png`.
    
    :param Page page:     
        A Playwright page object.
    
    :param str url:
        The URL of the Tumblr post to save.
    
    :param str path:
        Directory to save the screenshot to.
    
    :returns str: The path to the screenshot.
    """
    
    # Ensure types.
    
    if type(page) != Page:
        raise TypeError(f"screenshot_post() expected Playwright Page, received {type(page).__name__}.")
    
    if type(url) != str:
        raise TypeError(f"screenshot_post() expected a string, received {type(url).__name__}")
    
    # Set to default theme if blog has custom theme (can't reliably handle all themes) 
    
    url_parse = urllib.parse.urlparse(url)   # parse the URL
    url_path  = url_parse.path.split("/")    # split the URL path into blocks
    
    if not url_parse.netloc.startswith("www.tumblr"):
        username = url_parse.netloc.split(".")[0]
        url_path = ["", username] + url_path[2:] # removes "" and "post"
        url      = f"{url_parse.scheme}://www.tumblr.com{'/'.join(url_path)}"
    
    else:
        username = url_path[1] # index 0 will always be ""
    
    # Generate screenshot filename.
    
    post_id  = [i for i in url_path if i.isnumeric()][0]               # it'll always be the numerical one
    date     = datetime.today().strftime("%Y%m%d")                     # Get today's date in YYYYMMDD format.
    img_path = os.path.join(path, f"{username}-{post_id}-{date}.png")  # path/USERNAME-EXAMPLE_ID-YYYYMMDD.png
    
    # Go to url. 
    
    await page.goto(url, wait_until="domcontentloaded", timeout=0)
    
    # Ensure page hasn't redirected to login-required page.
    
    if "login_required" in page.url:
        raise ValueError("Blog requires Tumblr login -- cannot bypass without SID cookie.")
    
    # Check for content warnings, and abort if found. (Cannot bypass mature content wall without cookie.)
    
    cw_button = page.locator("div[data-testid=community-label-cover] button").get_by_text("View post")
    
    if await cw_button.count():
        raise RuntimeError("Mature content wall detected -- cannot bypass without SID cookie.")
    
    # Click any "Keep reading" button.
    
    keep_reading_locator = page.locator('article button[aria-label="Keep reading"]').first
    
    if await keep_reading_locator.count():
        await keep_reading_locator.click()
    
    # Cheat the system and change page size to get loading to work -- no JS required.
    
    # TODO: I suspect one of our problems lies in here.
    # TODO: Figure out why we're not loading the entire page consistently.
    
    dimensions = await page.locator("article").first.bounding_box()
    
    if dimensions is None:
        raise RuntimeError("Somehow, the first article has no dimensions. Something weird's happened.")
    
    await page.set_viewport_size({
        "height": int(dimensions["height"]) + 100, 
        "width": int(dimensions["width"])
    })
    
    # Load page
    
    await page.wait_for_load_state("load", timeout=0)
    
    # Click on the "see all tags" button.
    
    see_all_button = page.locator("article div:has(footer[aria-label='Post footer']) button").get_by_text("See all")
    
    if await see_all_button.count():
        await see_all_button.click()
    
    # Grab the post body. (finds the first article)
    
    article_locator = page.locator('article')
    posts_num       = await article_locator.count()
    
    # Ensure there's at least one post.
    
    if posts_num == 0:
        
        await page.screenshot(
            path = "error.png"
        )
        
        raise ValueError("Could not find posts on page; either wrong URL passed or Tumblr's formatting has changed drastically.")
    
    # Ensure all lazy-loaded images have, well, loaded.
    
    lazy_images = await page.locator("article > div:nth-of-type(1) div[style] > img[loading=lazy]:visible").all()
    
    for image in lazy_images:
        await expect(image).to_have_js_property("complete", True, timeout=0)
    
    # Get the target post (will always be first object hit by the locator) and screenshot it.
    
    post = article_locator.first
    
    await post.screenshot(
        animations = "disabled",      # Disables all CSS animations
        style      = POST_INJECT_CSS, # Hides all unnecessary popups etc. -- see constant at top of page for what's hidden.
        path       = img_path         
    )
    
    # Return path to image
    
    return path


def get_secrets(path: str) -> tuple[str, float] | None:
    
    # If there's no secrets file, no secrets.
    
    if not os.path.exists(path):
        return None
    
    with open(path) as f:
            
        secrets = tomllib.loads(f.read())
            
        # If we've one and not the other, no secrets.
            
        if ("SID" not in secrets) or ("SID_EXPIRES" not in secrets):
            return None
        
        sid     = secrets["SID"]     # Session ID cookie value
        expires = datetime.strptime( # Session ID expiry date
            secrets["SID_EXPIRES"],
            "%a, %-d %b %Y %X %Z"
        ).timestamp()
        
    return (sid, expires)


def generate_cookies(sid: str, expires: float) -> list[dict[str, Any]]:
    
    """
    Generates the SID and logged_in cookies to simulate being logged in.
    """
    
    return [
        {
            "name": "sid",
            "value": sid,
            "domain": ".www.tumblr.com",
            "path": "/",
            "expires": expires
        },
        {
            "name": "logged_in",
            "value": "1",
            "domain": ".www.tumblr.com",
            "path": "/",
            "expires": expires
        }
    ]


async def main():
    
    POST_URL     = "https://www.tumblr.com/0w0tsuki/808750900793540608?source=share"
    SECRETS_PATH = "./secrets.toml"
    
    # Get secrets, and determine whether cookies will be injected.
    
    secrets        = get_secrets(SECRETS_PATH)
    inject_cookies = secrets is not None
    
    if secrets:
        sid, expires = secrets 
    
    # Load playwright
    
    async with async_playwright() as playwright:
        
        # Launch headless Firefox.
        
        browser = await playwright.firefox.launch()
        context = await browser.new_context()
        
        # Inject session cookies into the browser context
        
        if inject_cookies:
            await context.add_cookies(generate_cookies(sid, expires)) # type:ignore
        
        # Create page (done this way to allow batch async downloads)
        
        page = await context.new_page()
        
        # Screenshot post!
        
        await screenshot_post(page, POST_URL, path="./screenshots")


if __name__ == "__main__":
    asyncio.run(main())