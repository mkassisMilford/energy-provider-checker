#!/usr/bin/env python3
"""
Energy Provider Checker - Auckland
Check if your current energy provider is the best available rate
"""

import json
import sys
from pathlib import Path
from datetime import datetime

class ProviderChecker:
    def __init__(self, data_file='providers_data.json'):
        self.data_file = Path(data_file)
        self.data = self.load_data()
        self.custom_elec = None
        self.custom_gas = None
    
    def load_data(self):
        """Load provider data from JSON file"""
        if not self.data_file.exists():
            print(f"❌ Error: {self.data_file} not found!")
            print("Make sure providers_data.json is in the same folder.")
            sys.exit(1)
        
        with open(self.data_file, 'r') as f:
            return json.load(f)
    
    def display_header(self):
        """Display app header"""
        print("\n" + "="*70)
        print("⚡ AUCKLAND ENERGY PROVIDER CHECKER")
        print("="*70)
        print(f"Data updated: {self.data['last_updated']}")
        
        # Use custom values if set, otherwise use defaults
        elec = self.custom_elec if self.custom_elec else self.data['consumption']['electricity_kwh_month']
        gas = self.custom_gas if self.custom_gas else self.data['consumption']['gas_kwh_month']
        
        print(f"Your consumption: {elec} kWh/month electricity")
        print(f"                  {gas} kWh/month gas")
        print("-"*70)
    
    def calculate_provider_cost(self, provider, elec_kwh=None, gas_kwh=None):
        """Calculate provider cost based on custom consumption"""
        if elec_kwh is None:
            elec_kwh = self.custom_elec if self.custom_elec else self.data['consumption']['electricity_kwh_month']
        if gas_kwh is None:
            gas_kwh = self.custom_gas if self.custom_gas else self.data['consumption']['gas_kwh_month']
        
        # Calculate annual cost based on rates
        elec_rate = provider['rates']['electricity_per_kwh']
        gas_rate = provider['rates']['gas_per_kwh']
        
        annual_elec = (elec_kwh * 12 * elec_rate)
        annual_gas = (gas_kwh * 12 * gas_rate)
        annual_cost = annual_elec + annual_gas
        
        # Apply discount if exists
        if provider['discount'] and 'percentage' in provider['discount']:
            discount_pct = provider['discount']['percentage']
            annual_cost = annual_cost * (1 - discount_pct / 100)
        
        return annual_cost
    
    def set_custom_usage(self):
        """Allow user to set custom usage"""
        print("\n" + "="*70)
        print("UPDATE YOUR MONTHLY USAGE")
        print("="*70)
        
        default_elec = self.data['consumption']['electricity_kwh_month']
        default_gas = self.data['consumption']['gas_kwh_month']
        
        print(f"Current default: {default_elec} kWh/month electricity, {default_gas} kWh/month gas")
        print("(Press Enter to keep defaults)\n")
        
        try:
            elec_input = input(f"Electricity (kWh/month) [{default_elec}]: ").strip()
            if elec_input:
                self.custom_elec = float(elec_input)
            
            gas_input = input(f"Gas (kWh/month) [{default_gas}]: ").strip()
            if gas_input:
                self.custom_gas = float(gas_input)
            
            if self.custom_elec or self.custom_gas:
                print("\n✅ Usage updated!")
            else:
                print("\n✓ Using default values")
        except ValueError:
            print("\n❌ Invalid input! Using defaults.")
            self.custom_elec = None
            self.custom_gas = None
        """Check if current provider is the best"""
        if provider_name is None:
            print("\nWhat's your current provider?")
            for i, p in enumerate(self.data['providers'], 1):
                status = " ← YOUR CURRENT" if "YOUR CURRENT" in p['highlights'] else ""
                print(f"  {i}. {p['name']}{status}")
            
            try:
                choice = int(input("\nEnter number: "))
                if choice < 1 or choice > len(self.data['providers']):
                    print("Invalid choice!")
                    return
                current_provider = self.data['providers'][choice - 1]
            except (ValueError, IndexError):
                print("Invalid input!")
                return
        else:
            # Find provider by name
            current_provider = None
            for p in self.data['providers']:
                if p['name'].lower() == provider_name.lower():
                    current_provider = p
                    break
            
            if not current_provider:
                print(f"❌ Provider '{provider_name}' not found!")
                return
        
        # Use provider's cost if not specified
        if current_cost is None:
            current_cost = current_provider['annual_cost']
        
        self.display_analysis(current_provider, current_cost)
    
    def display_analysis(self, current_provider, current_cost):
        """Display detailed analysis"""
        best_provider = self.data['providers'][0]  # Already sorted by cost
        
        print(f"\n📊 ANALYSIS FOR: {current_provider['name']}")
        print("-"*70)
        print(f"Your current annual cost: ${current_cost:.2f}")
        print(f"Plan: {current_provider['plan']}")
        if current_provider['discount']:
            print(f"Discount: {current_provider['discount']}")
        print(f"Contract: {current_provider['contract_term']}")
        if current_provider['rating']:
            print(f"Rating: {current_provider['rating']}")
        
        # Calculate savings
        print("\n" + "="*70)
        
        if best_provider['name'] == current_provider['name']:
            print("✅ GREAT NEWS! You're with the BEST provider!")
            print(f"   Annual cost: ${current_cost:.2f} (Lowest available)")
            print(f"   No action needed!")
        else:
            savings = current_cost - best_provider['annual_cost']
            savings_pct = (savings / current_cost * 100) if current_cost > 0 else 0
            
            if savings >= 50:
                print(f"⚠️  SIGNIFICANT SAVINGS AVAILABLE!")
                print(f"   Best provider: {best_provider['name']}")
                print(f"   Best annual cost: ${best_provider['annual_cost']:.2f}")
                print(f"   Your annual cost: ${current_cost:.2f}")
                print(f"   Potential savings: ${savings:.2f}/year ({savings_pct:.1f}%)")
                print(f"\n🎯 RECOMMENDATION: SWITCH to {best_provider['name']}")
                print(f"   Plan: {best_provider['plan']}")
                if best_provider['discount']:
                    print(f"   Offer: {best_provider['discount']}")
            else:
                print(f"✓ Your provider is COMPETITIVE")
                print(f"   Best available: {best_provider['name']} at ${best_provider['annual_cost']:.2f}/year")
                print(f"   Your cost: ${current_cost:.2f}/year")
                print(f"   Difference: ${abs(savings):.2f}/year ({abs(savings_pct):.1f}%)")
                print(f"\n🎯 RECOMMENDATION: Stay with {current_provider['name']}")
                print(f"   Switching cost (~1-2 weeks setup) likely outweighs savings")
        
        # Show highlights
        print("\n📌 About your provider:")
        for highlight in current_provider['highlights']:
            print(f"   • {highlight}")
        
        # Show top 3 alternatives
        print("\n💡 TOP 3 ALTERNATIVES:")
        for i, provider in enumerate(self.data['providers'][:3], 1):
            if provider['name'] != current_provider['name']:
                savings = current_cost - provider['annual_cost']
                print(f"\n{i}. {provider['name']}")
                print(f"   Cost: ${provider['annual_cost']:.2f}/year")
                if savings > 0:
                    print(f"   Savings: ${savings:.2f}/year")
                else:
                    print(f"   Cost increase: ${abs(savings):.2f}/year")
                if provider['discount']:
                    print(f"   Offer: {provider['discount']}")
                print(f"   Rating: {provider['rating']}")
    
    def show_all_providers(self):
        """Display all providers ranked by cost"""
        print("\n📊 ALL PROVIDERS - RANKED BY ANNUAL COST")
        print("="*70)
        
        for provider in self.data['providers']:
            marker = "📍 YOU ARE HERE" if "YOUR CURRENT" in provider['highlights'] else ""
            marker2 = "⭐ BEST RATE" if provider['rank'] == 1 else ""
            
            status = f"{marker} {marker2}".strip()
            if status:
                status = f" [{status}]"
            
            print(f"\n{provider['rank']}. {provider['name']}{status}")
            print(f"   Annual Cost: ${provider['annual_cost']:.2f}")
            print(f"   Plan: {provider['plan']}")
            print(f"   Contract: {provider['contract_term']}")
            if provider['discount']:
                print(f"   Discount: {provider['discount']}")
            print(f"   Rating: {provider['rating']}")
            
            if provider['rank'] > 1:
                vs_best = provider['annual_cost'] - self.data['providers'][0]['annual_cost']
                print(f"   vs Best: +${vs_best:.2f}/year")
    
    def main_menu(self):
        """Interactive menu"""
        while True:
            print("\n" + "="*70)
            print("MENU")
            print("="*70)
            print("1. Check my current provider")
            print("2. Compare all providers")
            print("3. See top alternatives")
            print("4. Update my usage (electricity & gas)")
            print("5. Exit")
            
            choice = input("\nSelect (1-5): ").strip()
            
            if choice == '1':
                self.check_provider()
            elif choice == '2':
                self.show_all_providers()
            elif choice == '3':
                self.show_top_alternatives()
            elif choice == '4':
                self.set_custom_usage()
            elif choice == '5':
                print("\n✓ Goodbye! ⚡\n")
                break
            else:
                print("Invalid choice!")
    
    def show_top_alternatives(self):
        """Show top 3 alternatives to current provider"""
        current = None
        for p in self.data['providers']:
            if "YOUR CURRENT" in p['highlights']:
                current = p
                break
        
        if not current:
            print("\nNo current provider identified.")
            return
        
        print("\n🏆 TOP 3 ALTERNATIVES FOR YOU")
        print("="*70)
        
        for i, provider in enumerate(self.data['providers'][:3], 1):
            if provider['name'] != current['name']:
                savings = current['annual_cost'] - provider['annual_cost']
                print(f"\n{i}. {provider['name']}")
                print(f"   Your savings: ${savings:.2f}/year")
                print(f"   Annual cost: ${provider['annual_cost']:.2f}")
                print(f"   Plan: {provider['plan']}")
                if provider['discount']:
                    print(f"   Offer: {provider['discount']}")
                print(f"   Rating: {provider['rating']}")
                print(f"   Website: https://{provider['name'].lower().replace(' ', '')}.co.nz")


def main():
    """Main entry point"""
    checker = ProviderChecker()
    
    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'all':
            # Show all providers
            checker.display_header()
            checker.show_all_providers()
        elif sys.argv[1].lower() == 'check':
            # Check specific provider
            if len(sys.argv) > 2:
                provider_name = ' '.join(sys.argv[2:])
                checker.display_header()
                checker.check_provider(provider_name)
            else:
                checker.display_header()
                checker.check_provider()
        else:
            # Assume it's a provider name
            checker.display_header()
            checker.check_provider(sys.argv[1])
    else:
        # Interactive menu
        checker.display_header()
        checker.main_menu()


if __name__ == '__main__':
    main()
