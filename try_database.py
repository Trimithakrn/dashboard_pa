from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
import pandas as pd

app = Flask(__name__)

# Konfigurasi koneksi PostgreSQL
DATABASE_URL = "postgresql://postgres:Trimitha@localhost:5432/history-pembayaran"
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
engine = create_engine(DATABASE_URL)

# Route API dengan paginasi menggunakan SQLAlchemy
@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        # Ambil parameter paginasi dari request
        page = request.args.get('page', 1, type=int)  # Default page = 1
        limit = request.args.get('limit', 10, type=int)  # Default limit = 10
        offset = (page - 1) * limit  # Hitung offset

        # Query data dengan paginasi
        query = text(f"SELECT * FROM history_pembayaran LIMIT {limit} OFFSET {offset};")
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        # Pastikan format tanggal sesuai
        if 'tanggal_pembayaran' in df.columns:
            df['tanggal_pembayaran'] = df['tanggal_pembayaran'].astype(str)

        return jsonify(df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)