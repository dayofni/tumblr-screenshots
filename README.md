# screenshots.py

### About

Takes a screenshot of a Tumblr post given its URL.

To screenshot from blogs / posts requiring a login (e.g., mature / potentially-mature posts):
1. Make a `secrets.toml` file.
2. Inside, add keys `SID` and `SID_EXPIRES`.
3. Set `SID` to the value of Tumblr's `sid` token.
4. Set `SID_EXPIRES` to the expiry date of the Tumblr `sid` token.

(Note: uses Playwright's headless Firefox.)

### Possible future improvements
1. Using `aria-label` attributes to harden the locators better.
2. Not requiring a SID cookie to access mature accounts. (annoying process)
3. Ensure all images in the article are loaded before screenshotting.

### Dependencies

- playwright (>=1.57.0)