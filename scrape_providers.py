#!/usr/bin/env python3
"""
Scrape live energy prices directly from provider websites.
Uses Playwright for browser automation to handle dynamic sites.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# User's baseline usage
ELECTRICITY_KWH = 385  # per month
GAS_KWH = 270  # per month

def scrape_mercury_energy():
    """Scrape Mercury Energy pricing"""
    print("🔍 Scraping Mercury Energy...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.mercury.co.nz/", timeout=15000)
            page.wait_for_load_state("networkidle")
            
            # Look for pricing information
            price_text = page.query_selector("text=/[\$].*per month|annual/i")
            if price_text:
                price = price_text.inner_text()
                print(f"  ✓ Mercury: {price}")
            
            browser.close()
            return {"name": "Mercury Energy", "annual_cost": None, "status": "pending"}
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"name": "Mercury Energy", "annual_cost": None, "status": "error"}

def scrape_genesis_energy():
    """Scrape Genesis Energy pricing"""
    print("🔍 Scraping Genesis Energy...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.genesisenergy.co.nz/", timeout=15000)
            page.wait_for_load_state("networkidle")
            
            # Genesis may have a quote tool
            price_text = page.query_selector("text=/[\$].*per month|annual/i")
            if price_text:
                price = price_text.inner_text()
                print(f"  ✓ Genesis: {price}")
            
            browser.close()
            return {"name": "Genesis Energy", "annual_cost": None, "status": "pending"}
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"name": "Genesis Energy", "annual_cost": None, "status": "error"}

def scrape_contact_energy():
    """Scrape Contact Energy pricing"""
    print("🔍 Scraping Contact Energy...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.contact.co.nz/", timeout=15000)
            page.wait_for_load_state("networkidle")
            
            price_text = page.query_selector("text=/[\$].*per month|annual/i")
            if price_text:
                price = price_text.inner_text()
                print(f"  ✓ Contact: {price}")
            
            browser.close()
            return {"name": "Contact Energy", "annual_cost": None, "status": "pending"}
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"name": "Contact Energy", "annual_cost": None, "status": "error"}

def scrape_meridian_energy():
    """Scrape Meridian Energy pricing"""
    print("🔍 Scraping Meridian Energy...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.meridianenergy.co.nz/", timeout=15000)
            page.wait_for_load_state("networkidle")
            
            price_text = page.query_selector("text=/[\$].*per month|annual/i")
            if price_text:
                price = price_text.inner_text()
                print(f"  ✓ Meridian: {price}")
            
            browser.close()
            return {"name": "Meridian Energy", "annual_cost": None, "status": "pending"}
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"name": "Meridian Energy", "annual_cost": None, "status": "error"}

def scrape_powershop():
    """Scrape Powershop pricing"""
    print("🔍 Scraping Powershop...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.powershop.co.nz/", timeout=15000)
            page.wait_for_load_state("networkidle")
            
            price_text = page.query_selector("text=/[\$].*per month|annual/i")
            if price_text:
                price = price_text.inner_text()
                print(f"  ✓ Powershop: {price}")
            
            browser.close()
            return {"name": "Powershop", "annual_cost": None, "status": "pending"}
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"name": "Powershop", "annual_cost": None, "status": "error"}

def scrape_vector_energy():
    """Scrape Vector Energy pricing"""
    print("🔍 Scraping Vector Energy...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.vector.co.nz/", timeout=15000)
            page.wait_for_load_state("networkidle")
            
            price_text = page.query_selector("text=/[\$].*per month|annual/i")
            if price_text:
                price = price_text.inner_text()
                print(f"  ✓ Vector: {price}")
            
            browser.close()
            return {"name": "Vector Energy", "annual_cost": None, "status": "pending"}
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"name": "Vector Energy", "annual_cost": None, "status": "error"}

def scrape_all_providers():
    """Scrape all providers"""
    print(f"\n{'='*60}")
    print(f"🔗 SCRAPING DIRECT FROM PROVIDER WEBSITES")
    print(f"{'='*60}")
    print(f"📊 Usage: {ELECTRICITY_KWH} kWh/month electricity, {GAS_KWH} kWh/month gas\n")
    
    results = [
        scrape_mercury_energy(),
        scrape_genesis_energy(),
        scrape_contact_energy(),
        scrape_meridian_energy(),
        scrape_powershop(),
        scrape_vector_energy(),
    ]
    
    print(f"\n{'='*60}")
    print("📝 RESULTS:")
    print(f"{'='*60}\n")
    
    for result in results:
        status = "✓" if result["annual_cost"] else "⚠"
        cost = f"${result['annual_cost']}/year" if result["annual_cost"] else "Manual entry needed"
        print(f"{status} {result['name']}: {cost}")
    
    print(f"\n⚠️  NOTE: Some providers may require manual entry on their websites.")
    print(f"   Open each site and enter usage: {ELECTRICITY_KWH} kWh/month electricity, {GAS_KWH} kWh/month gas")
    print(f"\n📍 Websites to check:")
    print(f"   • Mercury Energy: https://www.mercury.co.nz/")
    print(f"   • Genesis Energy: https://www.genesisenergy.co.nz/")
    print(f"   • Contact Energy: https://www.contact.co.nz/")
    print(f"   • Meridian Energy: https://www.meridianenergy.co.nz/")
    print(f"   • Powershop: https://www.powershop.co.nz/")
    print(f"   • Vector Energy: https://www.vector.co.nz/")
    
    return results

if __name__ == "__main__":
    try:
        results = scrape_all_providers()
        print(f"\n✅ Scraping complete!")
        print(f"💡 Tip: Copy the annual costs and update providers_data.json manually")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
