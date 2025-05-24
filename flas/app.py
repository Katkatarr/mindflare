from flask import Flask, render_template, request, jsonify
import dashscope
from dashscope import Generation
from dotenv import load_dotenv
import os
import re
import json

load_dotenv()

app = Flask(__name__)

# Set API Key
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'your-default-api-key')
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

# Product database
PRODUCTS = {
    "jambu-air": {
        "name": "Jambu Air",
        "price": "Rp17.000",
        "sold": "2.3k+ terjual",
        "reviews": "1.5k ulasan",
        "image": "/static/images/jambu-air.jpg",
        "description": "Jambu Air segar dengan kualitas terbaik. Dipetik langsung dari kebun untuk kesegaran maksimal.",
        "composition": ["Jambu air segar", "Air mineral", "Es batu"],
        "benefits": [
            "Meningkatkan sistem kekebalan tubuh",
            "Mengandung vitamin C tinggi",
            "Menjaga kesehatan kulit",
            "Membantu pencernaan"
        ]
    },
    "tepung-beras": {
        "name": "Tepung Beras",
        "price": "Rp15.000",
        "sold": "1.8k+ terjual",
        "reviews": "1.2k ulasan",
        "image": "/static/images/tepung-beras.jpg",
        "description": "Tepung beras premium untuk membuat berbagai macam kue tradisional.",
        "composition": ["Beras pilihan", "Tanpa pengawet"],
        "benefits": [
            "Bebas gluten",
            "Cocok untuk diet",
            "Tekstur lembut"
        ]
    },
    "gula-merah": {
        "name": "Gula Merah Aren",
        "price": "Rp25.000",
        "sold": "10K+ terjual",
        "reviews": "1.2k ulasan",
        "image": "/static/images/gula-merah.jpg",
        "description": "Gula merah alami dari aren asli, tanpa bahan pengawet.",
        "composition": ["Gula aren murni", "Tanpa pengawet"],
        "benefits": [
            "Lebih sehat dari gula putih",
            "Cocok untuk masakan tradisional",
            "Rasa lebih kaya"
        ]
    },
    "kacang-hijau": {
        "name": "Kacang Hijau Kupas",
        "price": "Rp18.000",
        "sold": "5K+ terjual", 
        "reviews": "800 ulasan",
        "image": "/static/images/kacang-hijau.jpg",
        "description": "Kacang hijau kupas kualitas premium untuk bubur dan olahan lainnya.",
        "composition": ["Kacang hijau kupas", "Tanpa campuran"],
        "benefits": [
            "Kaya protein",
            "Sumber serat tinggi",
            "Tanpa bahan pengawet"
        ]
    }
    # Tambahkan produk lainnya sesuai kebutuhan

}

# Initialize chat history
chat_history = [
    {
        'role': 'system', 
        'content': '''Kamu adalah chatbot resep makanan tradisional Indonesia. Berikan respon dengan format:

**Nama Resep**: [nama resep]

**Bahan-bahan**:
- Bahan 1
- Bahan 2

**Cara Membuat**:
1. Langkah pertama
2. Langkah kedua

**Produk Rekomendasi**:
[Kencur](product:kencur)
[Terasi](product:terasi)

Gunakan format yang konsisten dan pastikan setiap bagian dipisahkan dengan baris baru.'''
    }
]

@app.route('/')
def home():
    return render_template('index.html', messages=chat_history[1:])

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('user_input')
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    chat_history.append({'role': 'user', 'content': user_input})
    
    try:
        response = Generation.call(
            api_key=DASHSCOPE_API_KEY,
            model="qwen-plus",
            messages=chat_history,
            result_format='message'
        )
        bot_reply = response.output.choices[0].message.content
        formatted_reply = format_response(bot_reply)
        
        chat_history.append({'role': 'assistant', 'content': bot_reply})
        
        return jsonify({
            'user_message': user_input,
            'bot_reply': formatted_reply,
            'original_reply': bot_reply
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Di bagian route product detail
@app.route('/product/<product_id>')
def product_detail(product_id):
    # Bersihkan product_id dari karakter yang tidak perlu
    product_id = product_id.replace('product.', '')  # Hilangkan 'product.' jika ada
    product = PRODUCTS.get(product_id.lower())  # Gunakan lowercase untuk konsistensi
    
    if not product:
        # Jika produk tidak ditemukan, tampilkan halaman 404 yang lebih baik
        return render_template('404.html'), 404
    return render_template('product.html', product=product)

def format_response(text):
    # Handle line breaks first
    text = text.replace('\n', '<br>')
    
    # Format bold text (recipe titles)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Format product links
    text = re.sub(
        r'\[(.*?)\]\((product:.*?)\)', 
        r'<a href="/product/\2" class="product-link">\1</a>', 
        text
    )
    
    # Format lists
    text = text.replace('- ', '<li>')
    text = text.replace('<br><li>', '<ul><li>')
    text += '</ul>'
    
    # Add proper HTML structure
    text = f'<div class="message-content">{text}</div>'
    
    return text

if __name__ == '__main__':
    app.run(debug=True)