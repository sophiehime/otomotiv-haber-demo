from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', title='Otomotiv Haber')

@app.route('/api/haberler')
def haberler():
    haberler = [
        {"id": 1, "baslik": "Elektrikli Araç Piyasası Büyüyor", "kaynak": "Motor Trend"},
        {"id": 2, "baslik": "2024'ün En Beklenen SUV'ları", "kaynak": "Car and Driver"}
    ]
    return jsonify(haberler)

@app.route('/health')
def health():
    return jsonify({"status": "OK", "message": "Otomotiv Haber API çalışıyor"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
