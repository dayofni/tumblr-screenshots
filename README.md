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
1. Not requiring a SID cookie to access mature accounts. (annoying process)
2. Get long image-posts / posts with many images to load consistently -- it works most of the time, but not all of the time. ~~(hate hate hate hate hate hate)~~
3. Make this more useful as a library, maybe by including a class that handles Playwright and inserts cookies for you? (might be more useful if I make logins work off username / password instead of cookies)

### Dependencies
- playwright (>=1.57.0)