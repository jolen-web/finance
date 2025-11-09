# BDO Deals Scraper

Python scripts to scrape credit card deals and promotions from BDO Philippines.

## Overview

Three scraping approaches:

1. **BeautifulSoup** (`bdo_scraper.py`) - Fast, static HTML parsing
2. **Selenium** (`bdo_scraper_selenium.py`) - JavaScript rendering
3. **Test Suite** (`test_bdo_scraper.py`) - Compare both approaches

## Quick Start

### Installation

```bash
# Install dependencies
pip install requests beautifulsoup4

# Optional: For Selenium support
pip install selenium webdriver-manager
```

### Basic Usage

#### BeautifulSoup (Static HTML)
```bash
# Print deals to console
python bdo_scraper.py

# Save to JSON
python bdo_scraper.py --output json --filepath deals.json

# Save to CSV
python bdo_scraper.py --output csv --filepath deals.csv
```

#### Selenium (JavaScript)
```bash
# Run with headless browser
python bdo_scraper_selenium.py

# Run with visible browser (debug)
python bdo_scraper_selenium.py --debug

# Save results
python bdo_scraper_selenium.py --output json --filepath deals.json
```

#### Test Both
```bash
# Test BeautifulSoup only
python test_bdo_scraper.py --mode static

# Test Selenium only
python test_bdo_scraper.py --mode js

# Test both and compare
python test_bdo_scraper.py --mode all
```

## How It Works

### BeautifulSoup Scraper

**Process**:
1. Fetch HTML from website
2. Parse with BeautifulSoup
3. Try multiple CSS selectors to find deal elements
4. Extract title, description, cashback, etc.
5. Calculate data quality score
6. Save to JSON/CSV

**Best For**:
- Static HTML pages
- Fast scraping (< 2 seconds)
- Simple structure
- Low resource usage

**Limitations**:
- Won't work if content is JavaScript-rendered
- Breaks if website structure changes

### Selenium Scraper

**Process**:
1. Initialize Chrome browser
2. Navigate to website
3. Wait for page to load
4. Scroll to trigger lazy-loading
5. Extract deals from rendered DOM
6. Calculate quality scores
7. Save results

**Best For**:
- JavaScript-heavy pages
- Dynamic content loading
- Single-page applications
- Complex interactions

**Limitations**:
- Slower (10-20 seconds per page)
- Higher resource usage
- Requires Chrome browser

## Data Structure

Each deal is extracted with these fields:

```json
{
  "source": "bdo_website",
  "scraped_at": "2025-11-09T10:30:00",
  "card_issuer": "BDO",
  "title": "BDO Gold MasterCard",
  "description": "5% cashback on dining",
  "cashback_percent": 5.0,
  "reward_points": null,
  "discount_amount": null,
  "discount_percent": null,
  "card_type": "Gold MasterCard",
  "promotion_start_date": "11/09/2025",
  "promotion_end_date": "12/31/2025",
  "url": "https://deals.bdo.com.ph/...",
  "data_quality_score": 0.85
}
```

## Error Handling

### Common Issues

**"No deals found"**
- Check if website structure changed
- Try visiting in browser to verify deals exist
- Check if content is JavaScript-rendered (use Selenium)

**"Request timeout"**
- Website may be slow or down
- Try with `--timeout 30` flag
- Increase retries with `--retries 5`

**"Connection refused"**
- Network issue or VPN needed
- Check if Philippines VPN required
- Verify `https://deals.bdo.com.ph` is accessible

**"Chrome not found" (Selenium)**
- Install Chrome: `brew install google-chrome`
- Or install Chromium: `pip install chromium`

## Customization

### Change Website URL
```python
scraper = BDOScraper(base_url="https://custom-deals.bdo.com.ph")
```

### Adjust Timeouts
```python
scraper = BDOScraper(timeout=20, retries=5)
```

### Custom Selectors
Edit the `selectors` list in `_extract_deal_info()`:

```python
selectors = [
    ('div.my-deal-class', 'my custom selector'),
    ('article.promotion', 'article with promotion class'),
]
```

### Custom Field Extraction
Override `_extract_deal_info()` to add more fields:

```python
def _extract_deal_info(self, element, index):
    deal = super()._extract_deal_info(element, index)
    deal['custom_field'] = element.find('span.custom').text
    return deal
```

## Output Formats

### JSON
```json
[
  {
    "source": "bdo_website",
    "title": "BDO Gold MasterCard",
    ...
  },
  ...
]
```

### CSV
```csv
source,scraped_at,card_issuer,title,description,...
bdo_website,2025-11-09T10:30:00,BDO,BDO Gold MasterCard,...
```

### Console
```
================================================================================
BDO CREDIT CARD DEALS - 15 Total
================================================================================

DEAL #1
────────────────────────────────────────────────────────────────────────────────
  title............................. BDO Gold MasterCard
  description....................... 5% cashback on dining
  cashback_percent.................. 5.0
  ...
```

## Performance

### BeautifulSoup
- **Speed**: < 2 seconds per page
- **Memory**: ~20-50 MB
- **CPU**: Minimal
- **Good for**: High-frequency scraping, many pages

### Selenium
- **Speed**: 10-20 seconds per page
- **Memory**: 200-500 MB
- **CPU**: Significant
- **Good for**: Complex pages, one-time scrapes

## Legal & Ethical

### Terms of Service
- Always check website's robots.txt and ToS
- BDO may prohibit scraping in their ToS
- Publicly available data is generally legal to scrape
- PDPA (Philippine Data Privacy Act) applies to personal data

### Rate Limiting
- Don't hammer the website with rapid requests
- Use delays between requests (1-2 seconds minimum)
- Respect robots.txt Crawl-Delay directives
- Monitor server responses for 429 (Too Many Requests)

### Best Practices
- Add realistic User-Agent headers ✅
- Implement retry logic with exponential backoff ✅
- Cache results to avoid redundant scrapes ✅
- Contact BDO about official API access ✅

## Troubleshooting

### Debug Mode

**BeautifulSoup**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Selenium**:
```bash
python bdo_scraper_selenium.py --debug  # Shows browser
```

### Inspect Page Structure

```bash
# Download HTML for inspection
curl https://deals.bdo.com.ph > page.html

# Open in browser to inspect manually
open page.html
```

### Log Details

```bash
# Capture full log output
python bdo_scraper.py 2>&1 | tee scraper.log
```

## Integration with Finance Tracker

This scraper is designed for Phase 2 of the Deals Service:

1. **Phase 2: Scraper Implementation** - Currently here
2. **Phase 3: API Integration** - Cache and API clients
3. **Phase 4: UI Integration** - Display deals to users
4. **Phase 5: Testing** - Full test coverage

See `../../PHASE_0_EXECUTION.md` for full project timeline.

## Future Enhancements

- [ ] Multi-threaded scraping for faster extraction
- [ ] Proxy rotation to avoid blocking
- [ ] ML-based deal categorization
- [ ] Real-time deals notification system
- [ ] Historical deal tracking (price/offer changes)
- [ ] Integration with user credit cards
- [ ] BDO official API integration (if available)

## Support

For issues:

1. Check `ERROR` messages in logs
2. Try both scraper versions to identify JavaScript dependency
3. Verify website is accessible and contains deals
4. Check network connectivity and VPN requirements
5. Review scrapers' source code for custom extraction logic

## License

Part of Finance Tracker project. See main LICENSE file.

---

**Last Updated**: 2025-11-09
**Status**: Ready for Phase 2 Implementation
**Tested**: BeautifulSoup ✅, Selenium ⏳
