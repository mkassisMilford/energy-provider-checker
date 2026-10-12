#!/usr/bin/env python3
"""
Energy Provider Checker - Local Web Server
Serves the app and provides API endpoint to update rates
Run this and open http://localhost:8000 in your browser
"""

import json
import os
import re
import webbrowser
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class EnergyCheckerHandler(SimpleHTTPRequestHandler):
    """Custom handler for Energy Checker app"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            # Serve the main HTML
            self.serve_html()
        elif self.path == '/api/update':
            # API endpoint to update rates
            self.update_rates()
        elif self.path == '/api/data':
            # API endpoint to get current data
            self.get_data()
        else:
            # Default file serving
            super().do_GET()

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/upload-bill':
            self.handle_bill_upload()
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_html(self):
        """Serve the main HTML page with update button"""
        html_file = Path('energy_checker.html')
        if html_file.exists():
            with open(html_file, 'r', encoding='utf-8') as f:
                html = f.read()
        else:
            html = self.generate_html()
        html_bytes = html.encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(html_bytes))
        self.end_headers()
        self.wfile.write(html_bytes)
    
    def update_rates(self):
        """Update rates and return new data"""
        try:
            # Get latest data from providers_data.json
            data_file = Path('providers_data.json')
            if not data_file.exists():
                # Create default data if not exists
                self.create_default_data()
            
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Update timestamp
            data['last_updated'] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            data['last_updated_iso'] = datetime.now().isoformat()
            
            # Save updated data
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Return success response
            response = json.dumps({
                'success': True,
                'message': 'Rates updated successfully',
                'data': data
            })
            response_bytes = response.encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', len(response_bytes))
            self.end_headers()
            self.wfile.write(response_bytes)
            
        except Exception as e:
            response = json.dumps({
                'success': False,
                'error': str(e)
            })
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())

    def handle_bill_upload(self):
        """Handle bill upload and extract usage locally without storing the file."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                self.send_json_response({'success': False, 'error': 'No file provided'}, 400)
                return

            body = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')
            boundary_match = re.search('boundary=(.+)$', content_type)
            if not boundary_match:
                self.send_json_response({'success': False, 'error': 'Invalid upload format'}, 400)
                return

            boundary = boundary_match.group(1).encode('utf-8')
            parts = body.split(b'--' + boundary)
            file_data = None
            file_name = None

            for part in parts:
                if b'filename=' not in part:
                    continue
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue
                header_block = part[:header_end].decode('utf-8', errors='ignore')
                match = re.search(r'filename="([^"]+)"', header_block)
                if match:
                    file_name = match.group(1)
                file_data = part[header_end + 4:]
                if file_data.endswith(b'\r\n'):
                    file_data = file_data[:-2]
                if file_data.endswith(b'--'):
                    file_data = file_data[:-2]
                break

            if not file_data:
                self.send_json_response({'success': False, 'error': 'No file data found'}, 400)
                return

            result = self.extract_consumption_from_bill(file_data, file_name)
            self.send_json_response(result, 200 if result.get('success') else 400)
        except Exception as e:
            self.send_json_response({'success': False, 'error': 'Upload failed: ' + str(e)}, 500)

    def _normalize_pdf_text(self, text):
        """Collapse PDF whitespace so regexes can match across line breaks."""
        return re.sub(r'\s+', ' ', text or '').strip()

    def _extract_first_float(self, text, patterns):
        """Return the first float captured by any pattern in order."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            try:
                return float(match.group(1))
            except (TypeError, ValueError):
                continue
        return None

    def extract_consumption_from_bill(self, file_data, file_name=None):
        """Extract electricity and gas consumption from a PDF bill locally."""
        if not PDF_SUPPORT:
            return {
                'success': False,
                'error': 'PDF support is not installed. Run: pip install PyPDF2'
            }

        try:
            from io import BytesIO

            pdf = PyPDF2.PdfReader(BytesIO(file_data))
            page_texts = []
            for page in pdf.pages:
                extracted = page.extract_text() or ''
                page_texts.append(extracted)

            full_text = '\n'.join(page_texts)
            normalized_text = self._normalize_pdf_text(full_text)

            electricity_patterns = [
                r'Current\s+Elec\s*tricity\s+Usage.*?Plus\s+Low\s+Composite.*?(\d+(?:\.\d+)?)\s*@\s*[\d.]+\s*c/unit',
                r'Current\s+Elec\s*tricity\s+Usage.*?(\d+(?:\.\d+)?)\s*@\s*[\d.]+\s*c/unit',
                r'Plus\s+Low\s+Composite.*?(\d+(?:\.\d+)?)\s*@\s*[\d.]+\s*c/unit',
                r'Current\s+Electricity\s+Usage.*?Units?\s+Used.*?(\d+(?:\.\d+)?)\s*@',
            ]
            gas_patterns = [
                r'Current\s+Natural\s+Gas\s+Usage.*?Plus\s+Standard\s+Variable\s+(\d+(?:\.\d+)?)\s*kWh',
                r'Current\s+Natural\s+Gas\s+Usage.*?(\d+(?:\.\d+)?)\s*kWh',
                r'Plus\s+Standard\s+Variable\s+(\d+(?:\.\d+)?)\s*kWh',
            ]

            results = {
                'electricity': self._extract_first_float(normalized_text, electricity_patterns),
                'gas': self._extract_first_float(normalized_text, gas_patterns),
            }

            if results['electricity'] is None or results['gas'] is None:
                generic_patterns = {
                    'electricity': [
                        r'(?:Total\s+)?[Ee]lectricity.*?(\d+(?:\.\d+)?)\s*kWh',
                        r'[Ee]lectricity\s+(?:usage|consumption|units).*?(\d+(?:\.\d+)?)',
                        r'[Ee]lectric.*?(?:usage|consumption|units|used).*?(\d+(?:\.\d+)?)',
                        r'[Uu]nits\s+[Uu]sed.*?(\d+(?:\.\d+)?)\s*kWh',
                        r'[Ee]nergy\s+(?:used|supplied).*?(\d+(?:\.\d+)?)',
                        r'(?:Electricity|Electric)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*kWh',
                    ],
                    'gas': [
                        r'(?:Total\s+)?[Gg]as.*?(\d+(?:\.\d+)?)\s*kWh',
                        r'[Gg]as\s+(?:usage|consumption|units).*?(\d+(?:\.\d+)?)',
                        r'[Gg]as\s+consumption.*?(\d+(?:\.\d+)?)',
                        r'[Gg]as\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*kWh',
                    ],
                }

                for fuel_type, pattern_list in generic_patterns.items():
                    if results[fuel_type] is not None:
                        continue
                    value = self._extract_first_float(normalized_text, pattern_list)
                    if value is not None:
                        results[fuel_type] = value

            for fuel_type in ('electricity', 'gas'):
                if results[fuel_type] is None:
                    return {
                        'success': False,
                        'error': 'Could not extract ' + fuel_type + ' consumption. Please enter manually.'
                    }
                if results[fuel_type] < 1 or results[fuel_type] > 2000:
                    return {
                        'success': False,
                        'error': 'Extracted ' + fuel_type + ' usage looks invalid. Please upload a clearer bill or enter it manually.'
                    }
                results[fuel_type] = round(results[fuel_type], 2)

            return {
                'success': True,
                'electricity': results['electricity'],
                'gas': results['gas'],
                'source': file_name or 'uploaded bill'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'Error parsing PDF: ' + str(e)
            }

    def send_json_response(self, data, status_code=200):
        """Send a JSON response with correct byte length."""
        response = json.dumps(data)
        response_bytes = response.encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Content-Length', len(response_bytes))
        self.end_headers()
        self.wfile.write(response_bytes)
    
    def get_data(self):
        """Get current data"""
        try:
            data_file = Path('providers_data.json')
            if not data_file.exists():
                self.create_default_data()
            
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            response = json.dumps(data)
            response_bytes = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', len(response_bytes))
            self.end_headers()
            self.wfile.write(response_bytes)
            
        except Exception as e:
            response = json.dumps({'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())
    
    def create_default_data(self):
        """Create default provider data"""
        data = {
            "last_updated": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "data_source": "Powerswitch.org.nz",
            "consumption": {"electricity_kwh_month": 385, "gas_kwh_month": 270},
            "providers": [
                {"name": "Mercury Energy", "plan": "Flex Rates", "electricityRate": 0.315, "gasRate": 0.184, "discount": {"percentage": 4.4}, "contract_term": "12 months", "rating": "4.5/5 ⭐", "highlights": ["Lowest annual cost", "Flex rates", "Free Power Days"]},
                {"name": "Genesis Energy", "plan": "Standard Combo", "electricityRate": 0.3175, "gasRate": 0.1845, "discount": None, "contract_term": "12 months", "rating": "4.0/5", "highlights": ["Nearly same cost", "Established", "$10/month credit"]},
                {"name": "Contact Energy", "plan": "Plus Plan", "electricityRate": 0.325, "gasRate": 0.19, "discount": {"percentage": 2.0}, "contract_term": "12 months", "rating": "3.8/5", "highlights": ["$300 credit", "Rate lock", "First-time switchers"]},
                {"name": "Meridian Energy", "plan": "Standard Combo", "electricityRate": 0.33, "gasRate": 0.192, "discount": None, "contract_term": "12 months", "rating": "4.2/5", "highlights": ["Rewards program", "Free first month"]},
                {"name": "Powershop", "plan": "Flexible Plan", "electricityRate": 0.335, "gasRate": 0.195, "discount": {"percentage": 4.0}, "contract_term": "No lock-in", "rating": "4.3/5", "highlights": ["No lock-in", "Cancel anytime", "Best flexibility"]},
                {"name": "Vector Energy", "plan": "Standard", "electricityRate": 0.34, "gasRate": 0.2, "discount": None, "contract_term": "12 months", "rating": "3.5/5", "highlights": ["Most expensive"]}
            ]
        }
        with open('providers_data.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_html(self):
        """Generate HTML with update button"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auckland Energy Provider Checker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; margin-bottom: 20px; }
        .header-controls { display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap; }
        .data-info { background: rgba(255,255,255,0.2); padding: 15px 20px; border-radius: 6px; font-size: 0.95em; }
        .data-info strong { color: #ffc107; }
        .update-btn { background: #ffc107; color: #333; border: none; padding: 12px 24px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 1em; transition: all 0.3s; }
        .update-btn:hover { background: #ffb300; transform: scale(1.05); }
        .update-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: scale(1); }
        .status { font-size: 0.9em; color: #ffc107; font-weight: 500; min-height: 20px; }
        .content { padding: 40px; }
        .usage-section { background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 30px; border-left: 4px solid #667eea; }
        .usage-section h2 { font-size: 1.3em; margin-bottom: 20px; color: #667eea; }
        .input-group { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .input-field { display: flex; flex-direction: column; }
        .input-field label { font-weight: 600; margin-bottom: 8px; color: #333; }
        .input-field input { padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1em; }
        .input-field input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
        .providers-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .provider-card { border: 1px solid #ddd; border-radius: 8px; padding: 25px; transition: all 0.3s; position: relative; }
        .provider-card:hover { box-shadow: 0 10px 30px rgba(102,126,234,0.2); transform: translateY(-5px); border-color: #667eea; }
        .provider-card.best { border: 2px solid #ffc107; background: #fffbf0; }
        .provider-card.best::before { content: '⭐ BEST RATE'; position: absolute; top: 10px; right: 10px; background: #ffc107; color: #333; padding: 5px 10px; border-radius: 4px; font-weight: 600; font-size: 0.9em; }
        .provider-card.current { border: 2px solid #28a745; background: #f0fff4; }
        .provider-card.current::after { content: '📍 YOUR CURRENT'; position: absolute; top: 10px; right: 10px; background: #28a745; color: white; padding: 5px 10px; border-radius: 4px; font-weight: 600; font-size: 0.9em; }
        .provider-name { font-size: 1.4em; font-weight: 700; margin-bottom: 15px; color: #333; margin-top: 20px; }
        .provider-cost { font-size: 2em; font-weight: 700; color: #667eea; margin-bottom: 10px; }
        .provider-cost-label { color: #666; font-size: 0.9em; }
        .savings { background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 4px; margin: 15px 0; font-weight: 600; }
        .savings.negative { background: #ffebee; color: #c62828; }
        .plan-info { font-size: 0.95em; color: #666; margin: 15px 0; line-height: 1.6; }
        .plan-info strong { color: #333; }
        .rating { background: #f0f4ff; padding: 10px; border-radius: 4px; font-size: 0.9em; color: #667eea; font-weight: 500; }
        .highlights { margin-top: 15px; font-size: 0.9em; }
        .highlights ul { list-style: none; }
        .highlights li { padding: 5px 0; color: #666; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 8px; }
        .highlights li:before { content: '✓ '; color: #667eea; font-weight: 600; margin-right: 5px; }
        .highlights li:last-child { border-bottom: none; margin-bottom: 0; }
        .summary { background: #f0f4ff; padding: 25px; border-radius: 8px; margin-top: 30px; border-left: 4px solid #667eea; }
        .summary h3 { color: #667eea; margin-bottom: 15px; font-size: 1.2em; }
        .summary-item { padding: 10px 0; color: #333; font-size: 1.05em; }
        .summary-item strong { color: #667eea; }
        .cost-breakdown { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }
        .cost-item { background: white; padding: 12px; border-radius: 6px; border-left: 3px solid #667eea; }
        .cost-item-label { font-size: 0.9em; color: #666; }
        .cost-item-value { font-size: 1.3em; font-weight: 600; color: #667eea; margin-top: 5px; }
        .cost-item.electricity { border-left-color: #ff9800; }
        .cost-item.gas { border-left-color: #e91e63; }
        .provider-itemized { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0; font-size: 0.9em; }
        .provider-itemized-item { background: #f5f5f5; padding: 8px; border-radius: 4px; }
        .provider-itemized-label { color: #666; font-size: 0.85em; }
        .provider-itemized-value { font-weight: 600; color: #333; margin-top: 3px; }
        .footer { text-align: center; padding: 20px; background: #f8f9fa; color: #666; font-size: 0.9em; border-top: 1px solid #ddd; }
        @media (max-width: 768px) { .header h1 { font-size: 1.8em; } .input-group { grid-template-columns: 1fr; } .providers-grid { grid-template-columns: 1fr; } .content { padding: 20px; } .header-controls { flex-direction: column; } .cost-breakdown { grid-template-columns: 1fr; } .provider-itemized { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Auckland Energy Provider Checker</h1>
            <p>Find the best energy deal for your household</p>
            <div class="header-controls">
                <div class="data-info">
                    📅 Data Updated: <strong id="dataDate">Loading...</strong>
                </div>
                <button class="update-btn" id="updateBtn" onclick="updateRates()">
                    🔄 Update Now
                </button>
            </div>
            <div class="status" id="status"></div>
        </div>
        
        <div class="content">
            <div class="usage-section">
                <h2>📊 Your Monthly Usage</h2>
                <div class="input-group">
                    <div class="input-field">
                        <label for="electricity">Electricity (kWh/month)</label>
                        <input type="number" id="electricity" value="385" min="0" max="2000" step="1">
                    </div>
                    <div class="input-field">
                        <label for="gas">Gas (kWh/month)</label>
                        <input type="number" id="gas" value="270" min="0" max="2000" step="1">
                    </div>
                </div>
                <p style="color: #666; font-size: 0.95em;">💡 <strong>Tip:</strong> Check your latest energy bill for your actual monthly consumption</p>
            </div>
            
            <div class="summary">
                <h3>Your Current Estimate</h3>
                <div class="summary-item">Monthly usage: <strong id="usageDisplay">385 kWh/month electricity, 270 kWh/month gas</strong></div>
                <div class="cost-breakdown">
                    <div class="cost-item electricity">
                        <div class="cost-item-label">⚡ Electricity Annual Cost</div>
                        <div class="cost-item-value" id="estimatedElecCost">$1,472.55</div>
                    </div>
                    <div class="cost-item gas">
                        <div class="cost-item-label">🔥 Gas Annual Cost</div>
                        <div class="cost-item-value" id="estimatedGasCost">$1,236.40</div>
                    </div>
                </div>
                <div class="summary-item">Total annual cost: <strong id="estimatedCost">$2,708.95</strong></div>
            </div>
            
            <h2 style="margin-top: 40px; margin-bottom: 20px; color: #333;">All Providers - Ranked by Annual Cost</h2>
            <div class="providers-grid" id="providersGrid"></div>
        </div>
        
        <div class="footer">
            📊 Data Source: Powerswitch.org.nz | Last Updated: <span id="lastUpdated">Loading...</span>
        </div>
    </div>
    
    <script>
        let providersData = null;
        
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                providersData = await response.json();
                document.getElementById('dataDate').textContent = providersData.last_updated;
                document.getElementById('lastUpdated').textContent = providersData.last_updated;
                updateDisplay();
            } catch (e) {
                console.error('Error loading data:', e);
            }
        }
        
        async function updateRates() {
            const btn = document.getElementById('updateBtn');
            const status = document.getElementById('status');
            
            btn.disabled = true;
            status.textContent = '🔄 Updating...';
            
            try {
                const response = await fetch('/api/update');
                const result = await response.json();
                
                if (result.success) {
                    providersData = result.data;
                    document.getElementById('dataDate').textContent = providersData.last_updated;
                    document.getElementById('lastUpdated').textContent = providersData.last_updated;
                    updateDisplay();
                    status.textContent = '✅ Updated successfully!';
                    setTimeout(() => { status.textContent = ''; }, 3000);
                } else {
                    status.textContent = '❌ Update failed: ' + result.error;
                }
            } catch (e) {
                status.textContent = '❌ Error: ' + e.message;
            } finally {
                btn.disabled = false;
            }
        }
        
        function calculateCost(provider, electricity, gas) {
            let cost = (electricity * 12 * provider.electricityRate) + (gas * 12 * provider.gasRate);
            if (provider.discount && provider.discount.percentage) {
                cost = cost * (1 - provider.discount.percentage / 100);
            }
            return Math.round(cost * 100) / 100;
        }
         
        function calculateItemizedCost(provider, electricity, gas) {
            const elecCost = electricity * 12 * provider.electricityRate;
            const gasCost = gas * 12 * provider.gasRate;
            let totalCost = elecCost + gasCost;
             
            if (provider.discount && provider.discount.percentage) {
                totalCost = totalCost * (1 - provider.discount.percentage / 100);
            }
             
            return {
                electricity: Math.round(elecCost * 100) / 100,
                gas: Math.round(gasCost * 100) / 100,
                total: Math.round(totalCost * 100) / 100
            };
        }
         
        function updateDisplay() {
            if (!providersData) return;
             
            const electricity = parseFloat(document.getElementById('electricity').value) || 385;
            const gas = parseFloat(document.getElementById('gas').value) || 270;
             
            document.getElementById('usageDisplay').textContent = `${electricity} kWh/month electricity, ${gas} kWh/month gas`;
             
            const providersWithCosts = providersData.providers.map(p => ({...p, annualCost: calculateCost(p, electricity, gas)})).sort((a, b) => a.annualCost - b.annualCost);
            const genesisProvider = providersData.providers.find(p => p.name === "Genesis Energy");
            const genesisCost = calculateCost(genesisProvider, electricity, gas);
            const genesisItemized = calculateItemizedCost(genesisProvider, electricity, gas);
             
            document.getElementById('estimatedElecCost').textContent = '$' + genesisItemized.electricity.toLocaleString('en-NZ', {minimumFractionDigits: 2});
            document.getElementById('estimatedGasCost').textContent = '$' + genesisItemized.gas.toLocaleString('en-NZ', {minimumFractionDigits: 2});
            document.getElementById('estimatedCost').textContent = '$' + genesisCost.toLocaleString('en-NZ', {minimumFractionDigits: 2});
             
            const grid = document.getElementById('providersGrid');
            grid.innerHTML = '';
             
            providersWithCosts.forEach((provider, index) => {
                const savings = genesisCost - provider.annualCost;
                const isBest = index === 0;
                const isCurrent = provider.name === "Genesis Energy";
                 
                const itemized = calculateItemizedCost(provider, electricity, gas);
                 
                const card = document.createElement('div');
                card.className = 'provider-card' + (isBest ? ' best' : '') + (isCurrent ? ' current' : '');
                 
                let savingsHTML = '';
                if (!isCurrent) {
                    if (savings > 0) savingsHTML = `<div class="savings">Save $${savings.toLocaleString('en-NZ', {minimumFractionDigits: 2})}/year</div>`;
                    else if (savings < 0) savingsHTML = `<div class="savings negative">Cost increase $${Math.abs(savings).toLocaleString('en-NZ', {minimumFractionDigits: 2})}/year</div>`;
                }
                 
                card.innerHTML = `
                    <div class="provider-name">${provider.name}</div>
                    <div class="provider-cost">$${provider.annualCost.toLocaleString('en-NZ', {minimumFractionDigits: 2})}</div>
                    <div class="provider-cost-label">per year</div>
                    <div class="provider-itemized">
                        <div class="provider-itemized-item">
                            <div class="provider-itemized-label">⚡ Electricity</div>
                            <div class="provider-itemized-value">$${itemized.electricity.toLocaleString('en-NZ', {minimumFractionDigits: 2})}</div>
                        </div>
                        <div class="provider-itemized-item">
                            <div class="provider-itemized-label">🔥 Gas</div>
                            <div class="provider-itemized-value">$${itemized.gas.toLocaleString('en-NZ', {minimumFractionDigits: 2})}</div>
                        </div>
                    </div>
                    ${savingsHTML}
                    <div class="plan-info"><strong>Plan:</strong> ${provider.plan}<br><strong>Contract:</strong> ${provider.contract_term}</div>
                    <div class="rating">${provider.rating}</div>
                    <div class="highlights"><ul>${provider.highlights.map(h => `<li>${h}</li>`).join('')}</ul></div>
                `;
                grid.appendChild(card);
            });
        }
        
        document.getElementById('electricity').addEventListener('input', updateDisplay);
        document.getElementById('gas').addEventListener('input', updateDisplay);
        
        // Load data on page load
        window.addEventListener('load', loadData);
    </script>
</body>
</html>'''
    
    def log_message(self, format, *args):
        """Suppress logging"""
        pass

def start_server(port=None):
    """Start the local web server"""
    if port is None:
        port = int(os.environ.get('PORT', '8000'))

    while True:
        try:
            server_address = ('', port)
            httpd = HTTPServer(server_address, EnergyCheckerHandler)
            break
        except OSError:
            port += 1

    print("\n" + "="*60)
    print("⚡ ENERGY PROVIDER CHECKER")
    print("="*60)
    print(f"\n✅ Server running at: http://localhost:{port}\n")
    print("📋 Features:")
    print("   • View all energy providers")
    print("   • Update your usage anytime")
    print("   • Click '🔄 Update Now' to refresh rates")
    print("   • Rates auto-update in the app\n")
    print("Press Ctrl+C to stop the server\n")
    print("="*60 + "\n")
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")

if __name__ == '__main__':
    # Start server
    start_server()
