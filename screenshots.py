
import asyncio
import os.path
import tomllib
import urllib.parse

from datetime             import datetime
from playwright.async_api import async_playwright, expect, Playwright, Page
from typing               import Literal



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



async def screenshot_post(
    
    page:       Page, 
    url:        str, 
    path:       str                            = ".", 
    wait_until: Literal["load", "networkidle"] = "load"
    
) -> str:
    
    """
    Using the Playwright page `page`, navigates to and screenshots a Tumblr post at `url`.
    
    This screenshot is then saved to disk at `path/filename.png`.
    
    :param Page page:     
        A Playwright page object.
    
    :param str url:
        The URL of the Tumblr post to save.
    
    :param str path:
        Directory to save the screenshot to
    .
    :param Literal["load", "networkidle"] wait_until:
        The state Playwright will load the page to. (Must at least be `"load"` to disable image lazy-loading.) 
        If the post contains a lot of images that aren't loading, try setting to `"networkidle"`, otherwise keep on `"load"`.
        However, *this will add a lot (at least 500ms) of latency*. Only change if necessary. 
    
    :returns str: The path to the screenshot.
    """
    
    # Ensure types.
    
    if type(page) != Page:
        raise TypeError(f"screenshot_post() expected Playwright Page, received {type(page).__name__}.")
    
    if type(url) != str:
        raise TypeError(f"screenshot_post() expected a string, received {type(url).__name__}")
    
    # Generate screenshot filename.
    
    url_path = urllib.parse.urlparse(url).path.split("/") # split the URL path into blocks
    
    username = url_path[1]                                # index 0 will always be ""
    post_id  = [i for i in url_path if i.isnumeric()][0]  # it'll always be the numerical one
    date     = datetime.today().strftime("%Y%m%d")        # Get today's date in YYYYMMDD format.
    
    img_path = os.path.join(path, f"{username}-{post_id}-{date}.png") # path/USERNAME-EXAMPLE_ID-YYYYMMDD.png
    
    # Go to url. 
    
    await page.goto(url, wait_until="domcontentloaded", timeout=0)
    
    # Click any "Keep reading" button.
    
    keep_reading_locator = page.locator('article:first-of-type button[aria-label="Keep reading"]')
    
    if await keep_reading_locator.count():
        await keep_reading_locator.click()
    
    # Inject JS to force the loading of all lazy-loaded images, and disable the gradient boxes.
    
    await page.evaluate("""
                        
    let div_nodes = document.querySelectorAll("article > div:nth-of-type(1) div[style]:has(> img[loading])"),
        img_nodes = document.querySelectorAll("article > div:nth-of-type(1) div[style] > img[loading]");
    
    div_nodes.forEach( n => n.setAttribute("style", "padding-bottom: 44.837%;") );
    img_nodes.forEach( n => n.setAttribute("loading", "eager") );
    
    """)
    
    # Load page
    
    await page.wait_for_load_state(wait_until, timeout=0)
    
    # Ensure page hasn't redirected to login-required page.
    
    if "login_required" in page.url:
        raise ValueError("Blog requires Tumblr login -- cannot bypass without SID cookie.")
    
    # Check for content warnings, and abort if found. (Cannot bypass mature content wall without cookie.)
    
    cw_button = page.locator("div[data-testid=community-label-cover] button").get_by_text("View post")
    
    if await cw_button.count():
        
        await cw_button.click()
        
        await page.screenshot(
            path = "error.png"
        )
        
        raise RuntimeError("Mature content wall detected -- cannot bypass without SID cookie.")
    
    # Grab the post body. (finds the first article)
    
    article_locator = page.locator('article')
    posts_num       = await article_locator.count()
    
    # Ensure there's at least one post.
    
    if posts_num == 0:
        
        await page.screenshot(
            path = "error.png"
        )
        
        raise ValueError("Could not find posts on page; either wrong URL passed or Tumblr's formatting has changed drastically.")

    # Get the target post (will always be first object hit by the locator) and screenshot it.
    
    post = article_locator.first
    
    await post.screenshot(
        animations = "disabled",      # Disables all CSS animations
        style      = POST_INJECT_CSS, # Hides all unnecessary popups etc. -- see constant at top of page for what's hidden.
        path       = img_path         
    )
    
    # Return path to image
    
    return path



async def main():
    
    POST_URL     = "https://www.tumblr.com/stimday/771348500066746368/do-you-love-the-color-of-the-sky-stimboard?source=share"
    SECRETS_PATH = "./secrets.toml"
    
    # Get secrets, and determine whether cookies will be injected.
    
    secrets        = {}
    inject_cookies = True
    
    if not os.path.exists(SECRETS_PATH):
        inject_cookies = False
    
    else:
    
        with open(SECRETS_PATH) as f:
            
            secrets = tomllib.loads(f.read())
            
            # If we've one and not the other, abort.
            
            if ("SID" not in secrets) or ("SID_EXPIRES" not in secrets):
                inject_cookies = False
                
            else:
                sid     = secrets["SID"]     # Session ID cookie value
                expires = datetime.strptime( # Session ID expiry date
                    secrets["SID_EXPIRES"],
                    "%a, %-d %b %Y %X %Z"
                ).timestamp()
    
    # Load playwright
    
    async with async_playwright() as playwright:
        
        # Launch headless Firefox.
        
        browser = await playwright.firefox.launch()
        context = await browser.new_context()
        
        # Inject session cookies into the browser context
        
        if inject_cookies:
        
            await context.add_cookies([
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
            ])
        
        # Create page (done this way to allow batch async downloads)
        
        page = await context.new_page()
        
        # Screenshot post!
        
        await screenshot_post(page, POST_URL, path="./screenshots")
        
        # (careful, I think there's a memory leak somewhere -- maybe don't do this /too/ many times in one terminal?)
        


if __name__ == "__main__":
    
    asyncio.run(main())