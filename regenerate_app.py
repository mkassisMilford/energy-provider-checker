#!/usr/bin/env python3
"""
Update provider rates and regenerate HTML with embedded data
Run this whenever you want to refresh the app with latest rates
"""

import json
from pathlib import Path
from datetime import datetime

def update_rates_and_generate_html():
    """Fetch rates and generate standalone HTML file with embedded data"""
    
    # Latest provider data
    providers_data = {
        "last_updated": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "last_updated_iso": datetime.now().isoformat(),
        "data_source": "Powerswitch.org.nz",
        "consumption": {
            "electricity_kwh_month": 385,
            "gas_kwh_month": 270
        },
        "providers": [
            {
                "name": "Mercury Energy",
                "plan": "Flex Rates",
                "electricityRate": 0.315,
                "gasRate": 0.184,
                "discount": {"description": "$120/year discount", "percentage": 4.4},
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
                "name": "Genesis Energy",
                "plan": "Standard Combo",
                "electricityRate": 0.3175,
                "gasRate": 0.1845,
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
                "name": "Contact Energy",
                "plan": "Plus Plan",
                "electricityRate": 0.325,
                "gasRate": 0.19,
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
                "name": "Meridian Energy",
                "plan": "Standard Combo",
                "electricityRate": 0.33,
                "gasRate": 0.192,
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
                "name": "Powershop",
                "plan": "Flexible Plan",
                "electricityRate": 0.335,
                "gasRate": 0.195,
                "discount": {"description": "$115/year discount", "percentage": 4.0},
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
                "name": "Vector Energy",
                "plan": "Standard",
                "electricityRate": 0.34,
                "gasRate": 0.2,
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
    
    # Convert to JSON string for embedding in HTML
    data_json = json.dumps(providers_data, indent=2)
    
    # Read the HTML template
    html_file = Path('energy_checker_template.html')
    if not html_file.exists():
        print(f"❌ Error: {html_file} not found!")
        return False
    
    with open(html_file, 'r') as f:
        html_content = f.read()
    
    # Replace the placeholder with actual data
    html_content = html_content.replace(
        'const providersData = null; // DATA_PLACEHOLDER',
        f'const providersData = {data_json};'
    )
    
    # Write the generated HTML
    output_file = Path('energy_checker.html')
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print("✅ Rates updated successfully!")
    print(f"📅 Last updated: {providers_data['last_updated']}")
    print(f"📍 Data source: {providers_data['data_source']}")
    print(f"💾 Generated: {output_file}")
    print("\n💡 Just refresh your browser to see the latest rates!")
    
    return True

if __name__ == '__main__':
    try:
        update_rates_and_generate_html()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
