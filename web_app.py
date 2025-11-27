"""
web_app.py - Flask-based web interface for Mental Wellness Bot

Exposes the CLI functionality (login, journal, stats, exercises) as a web app
so users can access it through any browser (no terminal needed).
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import date, datetime, timedelta
from functools import wraps
from textblob import TextBlob
from dotenv import load_dotenv
import openai

app = Flask(__name__)
app.secret_key = os.urandom(24)

USERS_FILE = "users.json"
ENTRIES_FILE = "entries.json"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# helpers
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_entries():
    if os.path.exists(ENTRIES_FILE):
        with open(ENTRIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_entries(entries):
    with open(ENTRIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

# sentiment helper
def sentiment(text):
    if not text:
        return 0.0
    return TextBlob(text).sentiment.polarity

# routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        
        if not username or not password:
            return render_template('register.html', error='Username and password required')
        
        if password != confirm:
            return render_template('register.html', error='Passwords do not match')
        
        if username in users:
            return render_template('register.html', error='Username already exists')
        
        users[username] = password
        save_users(users)
        session['username'] = username
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    return render_template('dashboard.html', username=username, entries=entries)

@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session['username']
        mood = request.form.get('mood')
        journal = request.form.get('journal')
        exercise = request.form.get('exercise')
        entry = {
            'username': username,
            'date': datetime.now().isoformat(),
            'mood': mood,
            'journal': journal,
            'exercise': exercise,
            'sentiment': sentiment(journal)
        }
        entries = load_entries()
        entries.append(entry)
        save_entries(entries)
        return redirect(url_for('dashboard'))
    return render_template('add.html')

@app.route('/entries')
def list_entries():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    return render_template('entries.html', entries=entries)

@app.route('/export')
def export_json():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    return jsonify(entries)

@app.route('/stats')
def stats():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    # calculate simple stats
    last7 = datetime.now() - timedelta(days=7)
    last7_entries = [e for e in entries if datetime.fromisoformat(e['date']) >= last7]
    total = len(last7_entries)
    avg_sent = sum(e.get('sentiment', 0) for e in last7_entries) / max(1, total)
    exercises = sum(1 for e in last7_entries if e.get('exercise') and e.get('exercise') != 'None')
    return render_template('stats.html', total=total, avg_sent=avg_sent, exercises=exercises)

if __name__ == '__main__':
    app.run(debug=True)
