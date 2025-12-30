# screenshots.py

### About

Takes a screenshot of a Tumblr post, given a URL.

To screenshot blogs / posts requiring a login (e.g., mature / potentially-mature posts):
1. Make a `secrets.toml` file.
2. Inside, add keys `SID` and `SID_EXPIRES`.
3. Set `SID` to the value of Tumblr's `sid` token.
4. Set `SID_EXPIRES` to the expiry date of the Tumblr `sid` token.

### Dependencies

- playwright (>=1.57.0)