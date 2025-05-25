from flask import Flask, render_template, request, jsonify, session
import dashscope
from dashscope import Generation
from dotenv import load_dotenv
import os
import re
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c56'

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
    },
    "terasi": {
        "name": "Terasi Udang",
        "price": "Rp15.000",
        "sold": "1.2k+ terjual",
        "image": "/static/images/Terasi.png",
        "description": "Terasi udang premium kualitas terbaik"
    },
    "gula-merah": {
        "name": "Gula Merah Aren",
        "price": "Rp25.000",
        "sold": "3.5k+ terjual", 
        "image": "/static/images/Gula-Merah.png",
        "description": "Gula merah alami dari aren asli"
    },
    "cabai-rawit": {
        "name": "Cabai Rawit Merah",
        "price": "Rp12.000",
        "sold": "2.8k+ terjual",
        "image": "/static/images/cabai-rawit.png",
        "description": "Cabai rawit segar pedas"
    }
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
    if 'cart' not in session:
        session['cart'] = {}
    return render_template('index.html', messages=chat_history[1:], cart_count=len(session['cart']))

@app.route('/add_to_cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    try:
        # Normalize product ID
        product_id = product_id.lower().replace(' ', '-').replace('_', '-')
        
        # Cek apakah produk ada
        if product_id not in PRODUCTS:
            return jsonify({
                'success': False,
                'error': 'Product not found',
                'product_id': product_id
            }), 404

        # Inisialisasi cart jika belum ada
        if 'cart' not in session:
            session['cart'] = {}

        # Tambahkan/update produk di cart
        if product_id in session['cart']:
            session['cart'][product_id]['quantity'] += 1
        else:
            product = PRODUCTS[product_id]
            session['cart'][product_id] = {
                'name': product['name'],
                'price': product['price'],
                'image': product['image'],
                'quantity': 1
            }

        session.modified = True
        
        return jsonify({
            'success': True,
            'cart_count': len(session['cart']),
            'message': f'{PRODUCTS[product_id]["name"]} ditambahkan ke keranjang'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/cart')
def view_cart():
    if 'cart' not in session:
        session['cart'] = {}
    
    total = 0
    for item in session['cart'].values():
        price = int(item['price'].replace('Rp', '').replace('.', ''))
        total += price * item['quantity']
    
    return render_template('cart.html', cart=session['cart'], total=total)

@app.route('/update_cart/<product_id>', methods=['POST'])
def update_cart(product_id):
    data = request.get_json()
    quantity = data.get('quantity', 1)
    
    if 'cart' not in session or product_id not in session['cart']:
        return jsonify({'error': 'Item not in cart'}), 400
    
    if quantity <= 0:
        session['cart'].pop(product_id)
    else:
        session['cart'][product_id]['quantity'] = quantity
    
    session.modified = True
    
    total = 0
    for item in session['cart'].values():
        price = int(item['price'].replace('Rp', '').replace('.', ''))
        total += price * item['quantity']
    
    return jsonify({
        'success': True,
        'cart_count': len(session['cart']),
        'total': total
    })

@app.route('/remove_from_cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session and product_id in session['cart']:
        session['cart'].pop(product_id)
        session.modified = True
    
    total = 0
    for item in session['cart'].values():
        price = int(item['price'].replace('Rp', '').replace('.', ''))
        total += price * item['quantity']
    
    return jsonify({
        'success': True,
        'cart_count': len(session['cart']),
        'total': total
    })

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('user_input')
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    chat_history.append({'role': 'user', 'content': user_input})
    
    try:
        response = Generation.call(
            api_key=DASHSCOPE_API_KEY,
            model="qwen-max",
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

@app.route('/product/<product_id>')
def product_detail(product_id):
    product_id = product_id.replace('product.', '')
    product = PRODUCTS.get(product_id.lower())
    
    if not product:
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

    # Format produk rekomendasi dengan gambar
    if "Produk Rekomendasi" in text:
        parts = text.split("Produk Rekomendasi")
        text = parts[0]
        
        products_html = '<div class="products-recommendation"><h4>Produk Rekomendasi</h4><div class="products-grid">'
        
        # Cari produk yang disebutkan
        mentioned_products = []
        if "Terasi" in parts[1]:
            mentioned_products.append("terasi")
        if "Gula Merah" in parts[1]:
            mentioned_products.append("gula-merah")
        if "Cabai Rawit" in parts[1]:
            mentioned_products.append("cabai-rawit")
        
        for product_id in mentioned_products:
            product = PRODUCTS.get(product_id)
            if product:
                products_html += f'''
                <a href="/product/{product_id}" class="product-card">
                    <img src="{product['image']}" alt="{product['name']}">
                    <div class="product-name">{product['name']}</div>
                    <div class="product-price">{product['price']}</div>
                </a>
                '''
        
        products_html += '</div></div>'
        text += products_html
    
    return f'<div class="message-content">{text}</div>'
    
    # Format lists
    text = text.replace('- ', '<li>')
    text = text.replace('<br><li>', '<ul><li>')
    text += '</ul>'
    
    # Add proper HTML structure
    text = f'<div class="message-content">{text}</div>'
    
    return text

if __name__ == '__main__':
    app.run(debug=True)