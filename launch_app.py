#!/usr/bin/env python3
"""
Launch the Energy Provider Checker with latest data
Refreshes data from providers_data.json and opens in browser
Run this instead of opening the HTML directly
"""

import json
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

def update_html_with_latest_data():
    """Read latest data from JSON and regenerate HTML"""
    
    # Read the latest data from JSON
    json_file = Path('providers_data.json')
    if not json_file.exists():
        print(f"❌ Error: {json_file} not found!")
        print("Run 'python update_rates.py' first")
        return False
    
    with open(json_file, 'r') as f:
        providers_data = json.load(f)
    
    # Convert to JSON string (minified for embedding)
    data_json = json.dumps(providers_data)
    
    # Read HTML template
    template_file = Path('energy_checker_template.html')
    if not template_file.exists():
        # If no template, use the current HTML as template
        html_file = Path('energy_checker.html')
        if not html_file.exists():
            print(f"❌ Error: {html_file} not found!")
            return False
        with open(html_file, 'r') as f:
            html_content = f.read()
    else:
        with open(template_file, 'r') as f:
            html_content = f.read()
    
    # Find and replace the data placeholder
    start_marker = 'const providersData = {'
    end_marker = '};'
    
    # Find the data section and replace it
    if 'const providersData = {' in html_content:
        start_idx = html_content.find('const providersData = {')
        if start_idx != -1:
            # Find the closing brace
            end_idx = html_content.find('};', start_idx) + 2
            old_data = html_content[start_idx:end_idx]
            new_data = f'const providersData = {data_json};'
            html_content = html_content.replace(old_data, new_data)
    
    # Update the date display
    last_updated = providers_data.get('last_updated', 'Unknown')
    html_content = html_content.replace(
        'id="dataDate">October 12, 2026 at 11:35 PM<',
        f'id="dataDate">{last_updated}<'
    )
    html_content = html_content.replace(
        'id="lastUpdated">October 12, 2026 at 11:35 PM<',
        f'id="lastUpdated">{last_updated}<'
    )
    
    # Write the updated HTML
    output_file = Path('energy_checker.html')
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print("✅ Data refreshed with latest rates")
    print(f"📅 Updated: {last_updated}")
    
    return True

if __name__ == '__main__':
    print("🔄 Refreshing Energy Provider Checker with latest data...\n")
    
    if update_html_with_latest_data():
        print("\n🚀 Opening in browser...\n")
        # Open the HTML file in the default browser
        html_path = Path('energy_checker.html').resolve()
        webbrowser.open(f'file:///{html_path}')
        print(f"✅ App opened! View: {html_path}")
    else:
        print("\n❌ Failed to refresh data")
        exit(1)
