# Energy Provider Checker

A quick, lightweight Python app to check if your Auckland energy provider is the best deal.

**No setup. No registration. Just run it.**

## What It Does

✅ Compare your provider against all major Auckland energy suppliers  
✅ See annual cost for each provider based on your usage  
✅ Find potential savings instantly  
✅ Get top 3 cheaper alternatives  
✅ Works as a static site with browser-side bill upload

## Quick Start

Open the hosted site from the GitHub Pages URL after deployment.

## Example Output

```
⚡ AUCKLAND ENERGY PROVIDER CHECKER
=====================================

📊 ANNUAL COST COMPARISON (Based on: 385 kWh/month elec, 270 kWh/month gas)

Rank | Provider         | Annual Cost | vs Your Current | Status
-----|------------------|-------------|-----------------|--------
 1   | Mercury Energy   | $2,706      | -$2.95          | ✅ Better
 2   | Contact Energy   | $2,714      | +$5.05          | ⚠️  Slightly higher
 3   | Genesis Energy   | $2,708.95   | Your current    | ➡️ Current
 4   | Meridian Energy  | $2,749      | +$40.05         | ✗ Higher
 5   | Pulse Energy     | $2,759      | +$50.05         | ✗ Higher
 6   | Gentari          | $2,773      | +$64.05         | ✗ Higher

💡 RECOMMENDATION:
You're on a competitive plan! Mercury Energy could save you $2.95/year.
Consider checking quarterly for better deals.
```

## How It Works

- **Data**: Provider rates stored in `providers_data.json`
- **Consumption**: Based on actual Auckland household usage (385 kWh/month electricity, 270 kWh/month gas)
- **Rates**: Loaded from the static JSON file in the site
- **Uploads**: PDF bill parsing runs in the browser, so nothing is stored

## Providers Included

1. **Genesis Energy** ($2,708.95/year)
2. **Mercury Energy** ($2,706/year)
3. **Contact Energy** ($2,714/year)
4. **Meridian Energy** ($2,749/year)
5. **Pulse Energy** ($2,759/year)
6. **Gentari** ($2,773/year)

## Installation

1. Download or clone this repository
2. Publish `index.html`, `energy_checker.html`, and `providers_data.json` to GitHub Pages
3. Open the Pages URL

## License

MIT License - See LICENSE file

## Support

Run this app periodically (monthly/quarterly) to check if your provider is still competitive.

Rates change frequently—stay informed!
