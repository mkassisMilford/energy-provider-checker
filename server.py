#!/usr/bin/env python3
"""
Energy Provider Checker - Simple Local Web Server
No SSL warnings, no complications
Just run and access at http://localhost:8000
"""

import json
import webbrowser
import threading
import time
import re
import os
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class EnergyCheckerHandler(SimpleHTTPRequestHandler):
    """Simple HTTP handler for Energy Checker app"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.serve_html()
        elif self.path == '/api/update':
            self.update_rates()
        elif self.path == '/api/data':
            self.get_data()
        else:
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/upload-bill':
            self.handle_bill_upload()
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_html(self):
        """Serve main HTML"""
        html = self.generate_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html.encode()))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def update_rates(self):
        """Update rates from JSON file"""
        try:
            data_file = Path('providers_data.json')
            if not data_file.exists():
                data = self.get_default_data()
            else:
                with open(data_file, 'r') as f:
                    data = json.load(f)
            
            # Update timestamp
            data['last_updated'] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            data['last_updated_iso'] = datetime.now().isoformat()
            
            # Save
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Respond
            response = json.dumps({'success': True, 'message': 'Updated!', 'data': data})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', len(response.encode()))
            self.end_headers()
            self.wfile.write(response.encode())
        except Exception as e:
            response = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response.encode()))
            self.end_headers()
            self.wfile.write(response.encode())
    
    def get_data(self):
        """Get current data"""
        try:
            data_file = Path('providers_data.json')
            if not data_file.exists():
                data = self.get_default_data()
                with open(data_file, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                with open(data_file, 'r') as f:
                    data = json.load(f)
            
            response = json.dumps(data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', len(response.encode()))
            self.end_headers()
            self.wfile.write(response.encode())
        except Exception as e:
            response = json.dumps({'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())
     
    def handle_bill_upload(self):
        """Handle bill PDF upload and extract consumption data (no storage)"""
        try:
           content_length = int(self.headers.get('Content-Length', 0))
           if content_length == 0:
               self.send_json_response({'success': False, 'error': 'No file provided'}, 400)
               return
             
           # Read the multipart form data
           body = self.rfile.read(content_length)
             
           # Extract file from multipart
           try:
               boundary = self.headers.get('Content-Type').split('boundary=')[1].encode()
           except (IndexError, AttributeError):
               self.send_json_response({'success': False, 'error': 'Invalid upload format'}, 400)
               return
             
           # Split by boundary and find the file part
           parts = body.split(b'--' + boundary)
           file_data = None
             
           for part in parts:
               if b'filename=' in part:
                   # Extract file content
                   header_end = part.find(b'\r\n\r\n')
                   file_data = part[header_end+4:-2]  # Remove headers and trailing CRLF
                   break
             
           if not file_data:
               self.send_json_response({'success': False, 'error': 'No file data found'}, 400)
               return
             
           # Extract consumption from PDF (no storage)
           consumption = self.extract_consumption_from_bill(file_data)
             
           self.send_json_response(consumption)
                 
        except Exception as e:
           self.send_json_response({'success': False, 'error': f'Upload failed: {str(e)}'}, 500)
     
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

    def extract_consumption_from_bill(self, file_data):
        """Extract electricity and gas consumption from bill PDF (temporary, no storage)"""
        if not PDF_SUPPORT:
           return {
               'success': False,
               'error': 'PDF support not installed. Run: pip install PyPDF2'
           }
         
        try:
           from io import BytesIO
           pdf = PyPDF2.PdfReader(BytesIO(file_data))

           page_texts = []
           for page in pdf.pages:
               page_texts.append(page.extract_text() or '')

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
                       'error': f'Could not extract {fuel_type} consumption. Please enter manually.'
                   }
               if results[fuel_type] < 1 or results[fuel_type] > 2000:
                   return {
                       'success': False,
                       'error': f'Extracted {fuel_type} usage looks invalid. Please upload a clearer bill or enter it manually.'
                   }
               results[fuel_type] = round(results[fuel_type], 2)

           # Return extracted data (temporary, never stored)
           return {
               'success': True,
               'electricity': results.get('electricity'),
               'gas': results.get('gas')
           }
             
        except Exception as e:
           return {
               'success': False,
               'error': f'Error parsing PDF: {str(e)}'
           }
     
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        response = json.dumps(data)
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', len(response.encode()))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def get_default_data(self):
        """Default provider data - reads from providers_data.json"""
        data_file = Path('providers_data.json')
        if data_file.exists():
            with open(data_file, 'r') as f:
                return json.load(f)
        
        # Fallback to hardcoded data if file doesn't exist
        return {
            "last_updated": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "data_source": "Powerswitch.org.nz",
            "consumption": {"electricity_kwh_month": 385, "gas_kwh_month": 270},
            "providers": [
                {"name": "Mercury Energy", "plan": "Flex Rates", "electricityRate": 0.3265, "gasRate": 0.1875, "discount": {"percentage": 2.2}, "contract_term": "12 months", "rating": "4.5/5 ⭐", "highlights": ["Lowest cost", "Flex rates", "Power Days"]},
                {"name": "Genesis Energy", "plan": "Standard Combo", "electricityRate": 0.3290, "gasRate": 0.1905, "discount": None, "contract_term": "12 months", "rating": "4.0/5", "highlights": ["Competitive", "Reliable", "$10/month"]},
                {"name": "Contact Energy", "plan": "Plus Plan", "electricityRate": 0.3355, "gasRate": 0.1955, "discount": {"percentage": 2.0}, "contract_term": "12 months", "rating": "3.8/5", "highlights": ["$300 credit", "Lock-in", "New customers"]},
                {"name": "Meridian Energy", "plan": "Standard", "electricityRate": 0.3360, "gasRate": 0.1965, "discount": None, "contract_term": "12 months", "rating": "4.2/5", "highlights": ["Rewards", "Free first month"]},
                {"name": "Powershop", "plan": "Flexible", "electricityRate": 0.3395, "gasRate": 0.1985, "discount": {"percentage": 2.0}, "contract_term": "No lock-in", "rating": "4.3/5", "highlights": ["Flexible", "Cancel anytime"]},
                {"name": "Vector Energy", "plan": "Standard", "electricityRate": 0.3425, "gasRate": 0.2050, "discount": None, "contract_term": "12 months", "rating": "3.5/5", "highlights": ["Most expensive"]}
            ]
        }
    
    def generate_html(self):
        """Generate the HTML page with update button"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auckland Energy Provider Checker</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;color:#333}
        .container{max-width:1200px;margin:0 auto;background:white;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
        .header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:40px;text-align:center}
        .header h1{font-size:2.5em;margin-bottom:10px}
        .header p{font-size:1.1em;opacity:.9;margin-bottom:20px}
        .header-controls{display:flex;justify-content:center;align-items:center;gap:20px;flex-wrap:wrap}
        .data-info{background:rgba(255,255,255,.2);padding:15px 20px;border-radius:6px;font-size:.95em}
        .data-info strong{color:#ffc107}
        .update-btn{background:#ffc107;color:#333;border:none;padding:12px 24px;border-radius:6px;font-weight:600;cursor:pointer;font-size:1em;transition:all .3s}
        .update-btn:hover{background:#ffb300;transform:scale(1.05)}
        .update-btn:disabled{opacity:.6;cursor:not-allowed;transform:scale(1)}
        .status{font-size:.9em;color:#ffc107;font-weight:500;min-height:20px}
        .content{padding:40px}
        .usage-section{background:#f8f9fa;padding:25px;border-radius:8px;margin-bottom:30px;border-left:4px solid #667eea}
        .usage-section h2{font-size:1.3em;margin-bottom:20px;color:#667eea}
        .input-group{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}
        .input-field{display:flex;flex-direction:column}
        .input-field label{font-weight:600;margin-bottom:8px;color:#333}
        .input-field input{padding:10px;border:1px solid #ddd;border-radius:4px;font-size:1em}
        .input-field input:focus{outline:0;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.1)}
        .providers-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;margin-top:30px}
        .provider-card{border:1px solid #ddd;border-radius:8px;padding:25px;transition:all .3s;position:relative}
        .provider-card:hover{box-shadow:0 10px 30px rgba(102,126,234,.2);transform:translateY(-5px);border-color:#667eea}
        .provider-card.best{border:2px solid #ffc107;background:#fffbf0}
        .provider-card.best::before{content:'⭐ BEST RATE';position:absolute;top:10px;right:10px;background:#ffc107;color:#333;padding:5px 10px;border-radius:4px;font-weight:600;font-size:.9em}
        .provider-card.current{border:2px solid #28a745;background:#f0fff4}
        .provider-card.current::after{content:'📍 YOUR CURRENT';position:absolute;top:10px;right:10px;background:#28a745;color:white;padding:5px 10px;border-radius:4px;font-weight:600;font-size:.9em}
        .provider-name{font-size:1.4em;font-weight:700;margin-bottom:15px;color:#333;margin-top:20px}
        .provider-cost{font-size:2em;font-weight:700;color:#667eea;margin-bottom:10px}
        .provider-cost-label{color:#666;font-size:.9em}
        .savings{background:#e8f5e9;color:#2e7d32;padding:10px;border-radius:4px;margin:15px 0;font-weight:600}
        .savings.negative{background:#ffebee;color:#c62828}
        .plan-info{font-size:.95em;color:#666;margin:15px 0;line-height:1.6}
        .plan-info strong{color:#333}
        .rating{background:#f0f4ff;padding:10px;border-radius:4px;font-size:.9em;color:#667eea;font-weight:500}
        .highlights{margin-top:15px;font-size:.9em}
        .highlights ul{list-style:0}
        .highlights li{padding:5px 0;color:#666;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:8px}
        .highlights li:before{content:'✓ ';color:#667eea;font-weight:600;margin-right:5px}
        .highlights li:last-child{border:0;margin:0;padding:0}
        .summary{background:#f0f4ff;padding:25px;border-radius:8px;margin-top:30px;border-left:4px solid #667eea}
        .summary h3{color:#667eea;margin-bottom:15px;font-size:1.2em}
        .summary-item{padding:10px 0;color:#333;font-size:1.05em}
        .summary-item strong{color:#667eea}
        .footer{text-align:center;padding:20px;background:#f8f9fa;color:#666;font-size:.9em;border-top:1px solid #ddd}
        .view-toggle{display:flex;justify-content:center;gap:10px}
        .toggle-btn{background:#e0e0e0;color:#333;border:2px solid transparent;padding:10px 20px;border-radius:6px;font-weight:600;cursor:pointer;font-size:.95em;transition:all .3s}
        .toggle-btn:hover{background:#d0d0d0}
        .toggle-btn.active{background:#667eea;color:white;border-color:#667eea}
        .bill-upload{background:#f0fff4;padding:25px;border-radius:8px;margin-bottom:30px;border:2px dashed #28a745;border-left:4px solid #28a745}
        .bill-upload h3{color:#28a745;margin-bottom:15px;font-size:1.1em}
        .upload-area{border:2px dashed #999;border-radius:6px;padding:30px;text-align:center;cursor:pointer;transition:all .3s;background:#fafafa}
        .upload-area:hover{background:#f0f0f0;border-color:#667eea}
        .upload-area.dragover{background:#e8f5e9;border-color:#28a745}
        #billInput{display:none}
        .upload-status{margin-top:15px;padding:10px;border-radius:4px;display:none}
        .upload-status.success{background:#d4edda;color:#155724;display:block}
        .upload-status.error{background:#f8d7da;color:#721c24;display:block}
        @media (max-width:768px){.header h1{font-size:1.8em}.input-group{grid-template-columns:1fr}.providers-grid{grid-template-columns:1fr}.content{padding:20px}.header-controls{flex-direction:column}}
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
            <div class="bill-upload">
                <h3>📄 Quick Start: Upload Your Latest Bill</h3>
                <p style="color:#666;margin-bottom:15px;font-size:.95em">Upload your energy bill (PDF) to automatically extract your consumption figures</p>
                <div class="upload-area" id="uploadArea" onclick="document.getElementById('billInput').click()">
                    <div style="font-size:1.5em;margin-bottom:10px">📤</div>
                    <p><strong>Click to upload</strong> or drag & drop your bill PDF here</p>
                    <p style="color:#999;font-size:.9em;margin-top:8px">Supports Genesis, Mercury, Contact, Meridian, Powershop, Vector</p>
                </div>
                <input type="file" id="billInput" accept=".pdf" onchange="handleFileSelect(event)">
                <div class="upload-status" id="uploadStatus"></div>
            </div>
            
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
                <p style="color:#666;font-size:.95em">💡 <strong>Tip:</strong> Check your latest energy bill</p>
            </div>
            
            <div class="view-toggle" style="text-align:center;margin:20px 0">
                <button class="toggle-btn active" id="annualBtn" onclick="switchView('annual')">📅 Annual View</button>
                <button class="toggle-btn" id="monthlyBtn" onclick="switchView('monthly')">📆 Monthly View</button>
            </div>
            
            <div class="summary">
                <h3>Your Current Estimate</h3>
                <div class="summary-item">Monthly usage: <strong id="usageDisplay">385 kWh/month electricity, 270 kWh/month gas</strong></div>
                <div class="summary-item" id="costDisplay">Estimated annual cost: <strong id="estimatedCost">$2,708.95</strong></div>
                
                <div style="margin-top:20px;padding-top:20px;border-top:1px solid #ddd">
                    <h4 style="color:#667eea;margin-bottom:12px">vs Genesis Energy (Your Current Provider)</h4>
                    <div class="summary-item" style="background:#f9f9f9;padding:10px;border-radius:4px;margin:8px 0">
                        <strong>Total Advantage:</strong> <span id="totalAdvantage" style="color:#28a745;font-size:1.1em">+$2.95/year</span>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px">
                        <div class="summary-item" style="background:#f0fff4;padding:10px;border-radius:4px;border-left:3px solid #28a745">
                            <strong>Electricity:</strong> <span id="elecAdvantage" style="color:#28a745">+$X/year</span>
                        </div>
                        <div class="summary-item" style="background:#f0fff4;padding:10px;border-radius:4px;border-left:3px solid #28a745">
                            <strong>Gas:</strong> <span id="gasAdvantage" style="color:#28a745">+$X/year</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <h2 style="margin-top:40px;margin-bottom:20px;color:#333">All Providers - Ranked by Annual Cost</h2>
            <div class="providers-grid" id="providersGrid"></div>
        </div>
        
        <div class="footer">
            📊 Data Source: Powerswitch.org.nz | Last Updated: <span id="lastUpdated">Loading...</span>
        </div>
    </div>
    
    <script>
        let providersData=null;
        let currentView='annual';
        
        // Bill upload handlers
        const uploadArea=document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover',(e)=>{e.preventDefault();uploadArea.classList.add('dragover')});
        uploadArea.addEventListener('dragleave',()=>{uploadArea.classList.remove('dragover')});
        uploadArea.addEventListener('drop',(e)=>{e.preventDefault();uploadArea.classList.remove('dragover');handleFileSelect({dataTransfer:e.dataTransfer})});
        
        function handleFileSelect(event){
            const files=event.dataTransfer?event.dataTransfer.files:event.target.files;
            if(!files.length)return;
            const file=files[0];
            if(!file.name.endsWith('.pdf')){showUploadStatus('Only PDF files are supported','error');return}
            uploadBill(file)
        }
        
        async function uploadBill(file){
            const status=document.getElementById('uploadStatus');
            status.textContent='📤 Uploading and extracting...';
            status.classList.remove('error');status.classList.add('success');status.style.display='block';
            try{
                const formData=new FormData();
                formData.append('bill',file);
                const r=await fetch('/api/upload-bill',{method:'POST',body:formData});
                const result=await r.json();
                if(result.success){
                    document.getElementById('electricity').value=result.electricity;
                    document.getElementById('gas').value=result.gas;
                    showUploadStatus(`✅ ${result.message}. Usage updated!`,'success');
                    updateDisplay()
                }else{
                    showUploadStatus(`❌ ${result.error}`,'error')
                }
            }catch(e){
                showUploadStatus(`❌ Upload failed: ${e.message}`,'error')
            }
        }
        
        function showUploadStatus(message,type){
            const status=document.getElementById('uploadStatus');
            status.textContent=message;
            status.className=`upload-status ${type}`;
            status.style.display='block'
        }
        
        async function loadData(){
            try{const r=await fetch('/api/data');providersData=await r.json();document.getElementById('dataDate').textContent=providersData.last_updated;document.getElementById('lastUpdated').textContent=providersData.last_updated;updateDisplay()}catch(e){console.error(e)}}
        async function updateRates(){
            const btn=document.getElementById('updateBtn');const status=document.getElementById('status');btn.disabled=true;status.textContent='🔄 Updating...';
            try{const r=await fetch('/api/update');const result=await r.json();if(result.success){providersData=result.data;document.getElementById('dataDate').textContent=providersData.last_updated;document.getElementById('lastUpdated').textContent=providersData.last_updated;updateDisplay();status.textContent='✅ Updated!';setTimeout(()=>{status.textContent=''},3000)}else{status.textContent='❌ '+result.error}}catch(e){status.textContent='❌ '+e.message}finally{btn.disabled=false}}
        function switchView(view){
            currentView=view;
            document.getElementById('annualBtn').classList.toggle('active',view==='annual');
            document.getElementById('monthlyBtn').classList.toggle('active',view==='monthly');
            updateDisplay();
        }
        function calculateCost(p,e,g){
            let annual;
            if(p.annual_cost){annual=p.annual_cost}else{annual=(e*12*p.electricityRate)+(g*12*p.gasRate);if(p.discount&&p.discount.percentage)annual=annual*(1-p.discount.percentage/100)}
            annual=Math.round(annual*100)/100;
            return currentView==='monthly'?Math.round(annual/12*100)/100:annual;
        }
        function calculateCosts(p,e,g){
            let elecCost=(e*12*p.electricityRate);
            let gasCost=(g*12*p.gasRate);
            return {electricity:currentView==='monthly'?Math.round(elecCost/12*100)/100:Math.round(elecCost*100)/100,gas:currentView==='monthly'?Math.round(gasCost/12*100)/100:Math.round(gasCost*100)/100};
        }
        function updateDisplay(){
            if(!providersData)return;
            const e=parseFloat(document.getElementById('electricity').value)||385;
            const g=parseFloat(document.getElementById('gas').value)||270;
            document.getElementById('usageDisplay').textContent=`${e} kWh/month electricity, ${g} kWh/month gas`;
            
            const pw=providersData.providers.map(p=>({...p,cost:calculateCost(p,e,g)})).sort((a,b)=>a.cost-b.cost);
            const genesisProvider=pw.find(p=>p.name==="Genesis Energy");
            const bestProvider=pw[0];
            const genesisCost=genesisProvider.cost;
            const bestCost=bestProvider.cost;
            
            const costLabel=currentView==='monthly'?'monthly':'annual';
            document.getElementById('costDisplay').innerHTML=`Estimated ${costLabel} cost: <strong id="estimatedCost">$${genesisCost.toLocaleString('en-NZ',{minimumFractionDigits:2})}</strong>`;
            document.getElementById('estimatedCost').textContent='$'+genesisCost.toLocaleString('en-NZ',{minimumFractionDigits:2});
            
            // Calculate advantages
            const totalAdv=genesisCost-bestCost;
            const genesisCosts=calculateCosts(genesisProvider,e,g);
            const bestCosts=calculateCosts(bestProvider,e,g);
            const elecAdv=genesisCosts.electricity-bestCosts.electricity;
            const gasAdv=genesisCosts.gas-bestCosts.gas;
            
            const advLabel=currentView==='monthly'?'/month':'/year';
            document.getElementById('totalAdvantage').innerHTML=totalAdv>0?`✓ <strong>Save $${totalAdv.toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}</strong>`:`<strong>Cost increase $${Math.abs(totalAdv).toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}</strong>`;
            document.getElementById('elecAdvantage').innerHTML=elecAdv>0?`✓ $${elecAdv.toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}`:elecAdv<0?`- $${Math.abs(elecAdv).toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}`:'Neutral';
            document.getElementById('gasAdvantage').innerHTML=gasAdv>0?`✓ $${gasAdv.toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}`:gasAdv<0?`- $${Math.abs(gasAdv).toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}`:'Neutral';
            
            const grid=document.getElementById('providersGrid');grid.innerHTML='';
            pw.forEach((p,idx)=>{
                const s=genesisCost-p.cost;
                const ib=idx===0;
                const ic=p.name==="Genesis Energy";
                const card=document.createElement('div');
                card.className='provider-card'+(ib?' best':'')+(ic?' current':'');
                let sh='';
                if(!ic){if(s>0)sh=`<div class="savings">Save $${s.toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}</div>`;else if(s<0)sh=`<div class="savings negative">Cost increase $${Math.abs(s).toLocaleString('en-NZ',{minimumFractionDigits:2})}${advLabel}</div>`}
                card.innerHTML=`<div class="provider-name">${p.name}</div><div class="provider-cost">$${p.cost.toLocaleString('en-NZ',{minimumFractionDigits:2})}</div><div class="provider-cost-label">per ${costLabel}</div>${sh}<div class="plan-info"><strong>Plan:</strong> ${p.plan}<br><strong>Contract:</strong> ${p.contract_term}</div><div class="rating">${p.rating}</div><div class="highlights"><ul>${p.highlights.map(h=>`<li>${h}</li>`).join('')}</ul></div>`;
                grid.appendChild(card)
            });
        }
        document.getElementById('electricity').addEventListener('input',updateDisplay);
        document.getElementById('gas').addEventListener('input',updateDisplay);
        window.addEventListener('load',loadData);
    </script>
</body>
</html>'''
    
    def log_message(self, format, *args):
        pass

def run_server(port=8000):
    """Start HTTP server (no SSL warnings)"""
    server = HTTPServer(('127.0.0.1', port), EnergyCheckerHandler)
    print("\n" + "="*60)
    print("⚡ ENERGY PROVIDER CHECKER")
    print("="*60)
    print(f"\n✅ Running at: http://localhost:{port}\n")
    print("📋 Press Ctrl+C to stop\n" + "="*60 + "\n")
    
    try:
        # Auto-open browser
        threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{port}')).start()
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Stopped")
        server.server_close()

if __name__ == '__main__':
    run_server()
