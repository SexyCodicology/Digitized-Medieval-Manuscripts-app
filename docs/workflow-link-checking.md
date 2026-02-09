# How we check for broken links

We automatically check every library website link each week to ensure they're still active. This keeps the dashboard reliable and helps you discover manuscripts without encountering dead links.

## What the link checking system does

Our link checker performs three key tasks:

1. **Tests every link**: We verify that each library's website loads successfully
2. **Reports broken links**: We create a GitHub Issue if any links fail or become unreachable
3. **Keeps your site running**: Issues are tracked separately—the link checker never stops your website

The system runs automatically and maintains data quality without requiring manual checks.

## When link checks run

Link checks happen on a predictable schedule:

- **Automatically**: Every Monday at 00:00 UTC (midnight)

## How the link checker works

We visit every URL in `data.json` and verify it responds correctly. Here's what we check:

- **Response time**: Links must respond within 10 seconds
- **HTTP status**: Websites must return a successful response (not error codes like 404 or 500)
- **Accessibility**: Sites must be reachable from GitHub's servers

!!! success "Example: Healthy link"

    ```
    ✓ https://example.library.edu/manuscripts
    Status: 200 OK
    ```
    
    The website loads successfully and is available to users.

!!! failure "Example: Broken link"

    ```
    ✗ https://old-library-site.com/collection
    Status: 404 Not Found
    ```
    
    The page no longer exists and needs to be updated or removed.

## What happens if a link breaks

When we find broken links, we automatically create a GitHub Issue with details about what failed.

**Here's what you'll see**:

- **Issue title**: "⚠️ Broken Links Detected in Database"
- **Labels**: `maintenance` and `automated-issue` for easy filtering
- **Details**: A report listing each broken link and why it failed

**What this means for you**:

- Your dashboard keeps running normally
- Broken links are flagged for review and correction
- You can prioritize fixes based on impact

## How to handle broken links

When you find a broken link, follow this decision tree to determine the best action:

### 1. Fix it

Try to find the new URL if the page moved.

- Search for the library name online to locate the current website
- Check if the library has a new domain or restructured URL
- Update the `website` field in `data.json` with the correct URL

### 2. Archive it

If the site is down, check [The Wayback Machine](https://web.archive.org/).

- Visit the Wayback Machine and enter the broken URL
- Look for a recent snapshot of the page and check if digitized manuscripts are visible
- If a snapshot exists, use that archived URL in `data.json`

### 3. Delete it

If the content is gone, remove the entry from `data.json`.

- Verify the library and collection no longer exist online
- Remove the entire record from the data file
- Document the reason in your pull request

!!! note "Deleted data is safe"

    Don't worry about losing data. Git keeps a permanent history of every deleted entry if we ever need to restore it.

!!! example "Example: URL changed"

    **Old entry**:
    ```json
    {
      "id": 42,
      "library": "Example Manuscript Library",
      "website": "https://old-domain.edu/manuscripts"
    }
    ```
    
    **Updated entry**:
    ```json
    {
      "id": 42,
      "library": "Example Manuscript Library",
      "website": "https://new-domain.edu/digital-collections"
    }
    ```

### Step 4: Submit your fixes

1. Edit `data.json` with the corrected information
2. Follow the [Update the Dashboard Data](./update-data.md) guide to submit changes
3. Create a pull request with a descriptive message: "Fix broken link for Example Library"

### Step 5: Close the GitHub Issue

After your changes are merged, close the GitHub Issue with a comment explaining what you fixed.

## Handling false positives

Occasionally, the link checker reports errors for links that actually work. This happens when:

- **Websites block automated tools**: Some servers reject requests from automated checkers
- **Geographic restrictions**: Sites may block access from certain regions
- **Rate limiting**: Too many requests in a short time trigger temporary blocks
- **Authentication required**: Some pages might now require login before showing content

### How to skip false positives

If you verify a link works but the checker keeps reporting it as broken, you can exclude it from future checks.

**edit the `.lycheeignore` file** in the root of the DMMapp repository:

```text
# Websites that block automated checkers
https://library-that-blocks-bots.com

# Geographic restrictions
https://region-locked-library.gov

# Authentication required
https://members-only-archive.org
```

**Here's how it works**:

- Add one URL per line
- Use `#` for comments to explain why each link is excluded
- We skip these URLs in future checks

!!! warning "Use this sparingly"

    Only exclude links you've manually verified are working. Don't use this to hide genuinely broken links—fix them instead.

## Prevent broken links

### Before adding new libraries

1. Visit the website in your browser to confirm it loads
2. Verify the URL points to the actual manuscript collection (not just the homepage)
3. Check that the link uses HTTPS when available
4. Test the link from different devices or networks if possible

### Best practices

- **Use official URLs**: Link to the library's official domain, not third-party aggregators
- **Link directly**: Point to the digitized manuscripts section rather than a generic homepage
- **Prefer HTTPS**: Secure links are more reliable
- **Avoid URL shorteners**: Use full URLs so users know where they're going
- **Check links regularly**: Visit the links you've added to catch problems early

## Understanding the link health report

When we find issues, our report provides detailed information for each problem.

!!! example "Connection timeout"

    ```
    ✗ https://slow-server.edu/manuscripts
    Error: Request timeout (exceeded 10 seconds)
    ```
    
    **What it means**: The server took too long to respond.  
    **How to fix**: Try the link in your browser. If it loads (even if slowly), this may be a temporary issue. Consider excluding this URL if the site is consistently slow but functional.

!!! example "404 Not Found"

    ```
    ✗ https://library.org/old-path
    Error: HTTP 404 Not Found
    ```
    
    **What it means**: The page doesn't exist at this URL.  
    **How to fix**: Search for the library's new website or contact them directly to find the correct URL.

!!! example "Domain expired"

    ```
    ✗ https://defunct-library.com
    Error: DNS resolution failed
    ```
    
    **What it means**: The domain no longer exists.  
    **How to fix**: Research if the library moved to a new domain or closed permanently. Update or remove the record accordingly.

!!! example "SSL/TLS error"

    ```
    ✗ https://outdated-security.edu
    Error: Certificate verification failed
    ```
    
    **What it means**: The website's security certificate is invalid or expired.  
    **How to fix**: Contact the library to let them know their certificate needs renewal. You may temporarily switch to HTTP if HTTPS is unavailable, but note this in the issue.

## Need help?

If you can't resolve a broken link:

1. Search online for the library's current website
2. Contact the library directly via email or social media
3. Check recent news to see if the library merged, closed, or relocated
4. Search for the collection in larger aggregators like Europeana or DPLA
5. [Open an issue on GitHub](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-App/issues) to ask the community for help

## Related documentation

- [Update the Dashboard Data](./update-data.md) — How to edit library information
- [Data Structure Guide](./schema.md) — Understanding the data fields
- [How we validate data](./workflow-validation.md) — Automated quality checks
