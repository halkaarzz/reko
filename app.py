import sqlite3
import requests
from bs4 import BeautifulSoup
import hashlib
import threading
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Veritabanı başlatma
def init_db():
    conn = sqlite3.connect("websites.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS websites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            last_hash TEXT
        )
    """)
    conn.commit()
    conn.close()

# Sayfa içeriğinin hash değerini al
def get_page_hash(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            page_content = soup.get_text()
            return hashlib.md5(page_content.encode()).hexdigest()
    except Exception as e:
        print(f"Hata: {e}")
    return None

# Web sitelerini kontrol et ve değişiklikleri kaydet
def check_websites():
    while True:
        conn = sqlite3.connect("websites.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, url, last_hash FROM websites")
        websites = cursor.fetchall()

        for site in websites:
            site_id, name, url, last_hash = site
            current_hash = get_page_hash(url)

            if current_hash and current_hash != last_hash:
                print(f"Değişiklik tespit edildi: {name} - {url}")

                # Hash değerini güncelle
                cursor.execute("UPDATE websites SET last_hash = ? WHERE id = ?", (current_hash, site_id))
                conn.commit()

                # Bildirim gönderme kısmı buraya eklenebilir (Telegram, e-posta, WhatsApp vb.)

        conn.close()
        time.sleep(300)  # Her 5 dakikada bir çalıştır

# Ana sayfa (Tüm web sitelerini listele)
@app.route("/")
def index():
    conn = sqlite3.connect("websites.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, url FROM websites")
    websites = cursor.fetchall()
    conn.close()
    return render_template("index.html", websites=websites)

# Yeni web sitesi ekleme
@app.route("/add", methods=["POST"])
def add_website():
    name = request.form["name"]
    url = request.form["url"]
    hash_value = get_page_hash(url)

    if hash_value:
        conn = sqlite3.connect("websites.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO websites (name, url, last_hash) VALUES (?, ?, ?)", (name, url, hash_value))
        conn.commit()
        conn.close()

    return redirect(url_for("index"))

# Web sitesi silme
@app.route("/delete/<int:site_id>")
def delete_website(site_id):
    conn = sqlite3.connect("websites.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM websites WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=check_websites, daemon=True).start()  # Arka planda çalışan web takip botu
    app.run(debug=True)
