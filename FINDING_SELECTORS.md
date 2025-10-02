# Finding Google Review Selectors (Your "Eyes" Guide)

This guide will help you identify the HTML selectors we need to complete the scraper.

## Step 1: Find a Target Google Business Profile

1. Go to Google Maps
2. Search for any car dealership (preferably one with lots of reviews for testing)
3. Click on the business to open its profile
4. Copy the full URL from your browser's address bar

**Example URL format:**
```
https://www.google.com/maps/place/Business+Name/@40.7589,-73.9851,17z/data=...
```

## Step 2: Open Developer Tools

1. **In Chrome/Edge:** Press `F12` or right-click → "Inspect"
2. **In Firefox:** Press `F12` or right-click → "Inspect Element"
3. **In Safari:** Enable developer tools first (Preferences → Advanced → "Show Develop menu"), then press `Cmd+Option+I`

You should see a panel appear with HTML code.

## Step 3: Find the Reviews Section

1. In the Google Business Profile, scroll down to the reviews section
2. Click on "Reviews" if there's a tab
3. You should see a list of customer reviews

## Step 4: Inspect Review Elements

Now we need to find the "CSS selectors" for different parts of a review. Here's how:

### Finding Individual Review Containers

1. Right-click on **any review** → "Inspect"
2. The Developer Tools will highlight the HTML element for that review
3. Look for a repeating pattern - usually a `<div>` with a specific class name that contains an entire review
4. Right-click the element → "Copy" → "Copy selector"

**What to look for:**
- Each review is usually wrapped in a container with a class like:
  - `class="review-item"` 
  - `class="jftiEf fontBodyMedium"`
  - `data-review-id="..."`
- Write down this selector!

### Finding the Reviewer Name

1. Within a review, find the reviewer's name
2. Right-click it → "Inspect"
3. Copy the selector for this element
4. Note: It might be in a `<span>`, `<div>`, or `<a>` tag

### Finding the Star Rating

This is usually tricky. Star ratings can be represented as:
- An `aria-label` attribute (e.g., `aria-label="Rated 1 out of 5 stars"`)
- Multiple filled/empty star icons
- A number in a specific element

**Inspect a 1-star review's rating area and look for:**
- Any attribute that says "1" or "1 star" or "Rated 1"
- Note the element and attribute name

### Finding the Review Text

1. Find the actual text content of the review
2. Right-click the text → "Inspect"
3. Copy the selector
4. This is usually in a `<span>` or `<div>` with a specific class

### Finding the Review Date

1. Find where it says "3 days ago", "2 weeks ago", etc.
2. Right-click → "Inspect"
3. Copy the selector

## Step 5: Document Your Findings

Create a document or note with this format:

```
TARGET URL:
https://www.google.com/maps/place/[your test dealership]

REVIEW CONTAINER SELECTOR:
[paste the CSS selector for the individual review wrapper]

REVIEWER NAME SELECTOR (within review container):
[paste selector]

STAR RATING:
Element: [paste selector]
Attribute to read: [e.g., aria-label, innerText, etc.]
Example value: [e.g., "Rated 1 out of 5 stars"]

REVIEW TEXT SELECTOR:
[paste selector]

REVIEW DATE SELECTOR:
[paste selector]
```

## Tips for Success

1. **Look for patterns:** Google uses consistent class names for all reviews on the page
2. **Test multiple reviews:** Make sure your selector works for different reviews, not just one
3. **Avoid overly specific selectors:** Sometimes the "Copy selector" tool gives you a very long, fragile selector. We want something simpler if possible.
4. **Check for dynamic content:** Some elements might load after scrolling

## Example (Hypothetical - Google changes frequently)

```
REVIEW CONTAINER: 
div[data-review-id]

REVIEWER NAME:
div.d4r55 

STAR RATING:
span[aria-label*="star"]
Attribute: aria-label
Value: "Rated 1 out of 5 stars"

REVIEW TEXT:
span.wiI7pd

REVIEW DATE:
span.rsqaWe
```

## What to Send Me

Once you have all the selectors, just paste them in the chat, and I'll update the scraper code with the real values!

## Alternative: Share a Screenshot

If you're unsure, you can also:
1. Take screenshots of the Developer Tools showing the HTML structure
2. Share those, and I can guide you through finding the right selectors
