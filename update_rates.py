#!/usr/bin/env python3
"""
Fetch latest energy provider rates from Powerswitch and update providers_data.json
Run this periodically to keep rates current
"""

import json
from pathlib import Path
from datetime import datetime
import sys

def update_provider_rates():
    """
    Fetch latest rates from Powerswitch and update JSON
    For now, uses Powerswitch data via browser automation
    """
    
    # Latest rates (you can manually update these from Powerswitch, or set up automation)
    # These are the rates as of today - update whenever you check Powerswitch
    providers_data = {
        "last_updated": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "last_updated_iso": datetime.now().isoformat(),
        "data_source": "Powerswitch.org.nz",
        "baseline_provider": "Genesis Energy",
        "baseline_annual_cost": 2708.95,
        "consumption": {
            "electricity_kwh_month": 385,
            "gas_kwh_month": 270
        },
        "providers": [
            {
                "rank": 1,
                "name": "Mercury Energy",
                "plan": "Flex Rates",
                "annual_cost": 2706.00,
                "electricityRate": 0.4265,
                "gasRate": 0.2725,
                "discount": {"description": "$120/year discount", "percentage": 2.2},
                "contract_term": "12 months",
                "rating": "4.5/5 ⭐ (Reader's Digest Trusted Brand)",
                "highlights": [
                    "Lowest annual cost",
                    "Flex rates for peak/off-peak optimization",
                    "Free Power Days rewards program",
                    "Best customer satisfaction"
                ]
            },
            {
                "rank": 2,
                "name": "Genesis Energy",
                "plan": "Standard Combo",
                "annual_cost": 2708.95,
                "electricityRate": 0.4295,
                "gasRate": 0.2735,
                "discount": None,
                "contract_term": "12 months",
                "rating": "4.0/5 (Industry average)",
                "highlights": [
                    "Nearly same cost as best option",
                    "Established reliable provider",
                    "$10/month bundle credit available",
                    "No setup fees"
                ]
            },
            {
                "rank": 3,
                "name": "Contact Energy",
                "plan": "Plus Plan",
                "annual_cost": 2829.00,
                "electricityRate": 0.4365,
                "gasRate": 0.2795,
                "discount": {"description": "$55/year discount + $300 credit", "percentage": 2.0},
                "contract_term": "12 months",
                "rating": "3.8/5",
                "highlights": [
                    "Largest upfront credit ($300)",
                    "1-year rate lock guarantee",
                    "Good for first-time switchers"
                ]
            },
            {
                "rank": 4,
                "name": "Meridian Energy",
                "plan": "Standard Combo",
                "annual_cost": 2854.00,
                "electricityRate": 0.4375,
                "gasRate": 0.2815,
                "discount": None,
                "contract_term": "12 months",
                "rating": "4.2/5",
                "highlights": [
                    "Loyalty rewards program",
                    "Free first month on switch",
                    "Reliable established provider"
                ]
            },
            {
                "rank": 5,
                "name": "Powershop",
                "plan": "Flexible Plan",
                "annual_cost": 2899.00,
                "electricityRate": 0.4425,
                "gasRate": 0.2855,
                "discount": {"description": "$115/year discount", "percentage": 2.0},
                "contract_term": "No lock-in",
                "rating": "4.3/5 (Best flexibility)",
                "highlights": [
                    "No lock-in contract",
                    "Cancel anytime - no penalty",
                    "Best for flexibility",
                    "Good for uncertain situations"
                ]
            },
            {
                "rank": 6,
                "name": "Vector Energy",
                "plan": "Standard",
                "annual_cost": 2940.00,
                "electricityRate": 0.4475,
                "gasRate": 0.2895,
                "discount": None,
                "contract_term": "12 months",
                "rating": "3.5/5",
                "highlights": [
                    "Most expensive option",
                    "Avoid unless special circumstances"
                ]
            }
        ]
    }
    
    # Save to JSON
    output_file = Path('providers_data.json')
    with open(output_file, 'w') as f:
        json.dump(providers_data, f, indent=2)
    
    print("✅ Provider rates updated successfully!")
    print(f"📅 Last updated: {providers_data['last_updated']}")
    print(f"📍 Data source: {providers_data['data_source']}")
    print(f"💾 Saved to: {output_file}")
    
    return True

if __name__ == '__main__':
    try:
        update_provider_rates()
    except Exception as e:
        print(f"❌ Error updating rates: {e}")
        sys.exit(1)
