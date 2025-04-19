from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# Konfigurasi Database PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/nama_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model Database
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)

# Buat tabel jika belum ada
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['GET'])
def upload_file():
    file_path = r"D:\KULIAH\PA\Dataset\data_formatted.csv"  # Path CSV
    
    try:
        df = pd.read_csv(file_path)

        # Masukkan data ke database
        for _, row in df.iterrows():
            customer = Customer(name=row['name'], email=row['email'], phone=row.get('phone'))
            db.session.add(customer)

        db.session.commit()
        return "Data berhasil dimasukkan ke database!"
    
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True)
