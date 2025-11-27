"""
Enhanced Interactive Mental Wellness Bot - Web Application
Features: AI Chatbot, Animated Breathing Exercise, Mood Tracking, Journaling, Achievements
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import date, datetime, timedelta
from textblob import TextBlob
from dotenv import load_dotenv
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

USERS_FILE = "users.json"
ENTRIES_FILE = "entries.json"
CHAT_HISTORY_FILE = "chat_history.json"

load_dotenv()

# ==================== HELPER FUNCTIONS ====================

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

def load_chat_history(username):
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                all_history = json.load(f)
                return all_history.get(username, [])
        except:
            return []
    return []

def save_chat_history(username, history):
    all_history = {}
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                all_history = json.load(f)
        except:
            pass
    
    all_history[username] = history
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_history, f, ensure_ascii=False, indent=2)

def get_sentiment(text):
    """Calculate sentiment score from text (-1.0 to 1.0)"""
    if not text:
        return 0.0
    try:
        return TextBlob(text).sentiment.polarity
    except:
        return 0.0

def get_mood_color(mood):
    """Return color code for mood"""
    mood_colors = {
        "happy": "#10b981",
        "sad": "#3b82f6",
        "anxious": "#f59e0b",
        "calm": "#8b5cf6",
        "energetic": "#ef4444",
        "neutral": "#6b7280",
        "excited": "#ec4899",
        "overwhelmed": "#f97316"
    }
    mood_lower = mood.lower()
    for key, color in mood_colors.items():
        if key in mood_lower:
            return color
    return "#667eea"

def calculate_streak(username):
    """Calculate current mood tracking streak"""
    entries = [e for e in load_entries() if e.get('username') == username]
    if not entries:
        return 0
    
    entries.sort(key=lambda x: x.get('date', ''), reverse=True)
    streak = 1
    for i in range(len(entries) - 1):
        try:
            date1 = datetime.fromisoformat(entries[i].get('date', '')).date()
            date2 = datetime.fromisoformat(entries[i + 1].get('date', '')).date()
            days_diff = (date1 - date2).days
            if days_diff == 1:
                streak += 1
            else:
                break
        except:
            break
    return streak

def get_achievements(username):
    """Get user's achievements based on activity"""
    entries = [e for e in load_entries() if e.get('username') == username]
    achievements = []
    
    if len(entries) >= 1:
        achievements.append({"name": "Getting Started", "icon": "🌱", "desc": "Record your first entry"})
    if len(entries) >= 7:
        achievements.append({"name": "Consistent", "icon": "📝", "desc": "Log 7 entries"})
    if len(entries) >= 30:
        achievements.append({"name": "Dedicated", "icon": "⭐", "desc": "Log 30 entries"})
    
    streak = calculate_streak(username)
    if streak >= 7:
        achievements.append({"name": "On Fire!", "icon": "🔥", "desc": f"{streak} day streak"})
    
    return achievements

def get_random_affirmation():
    """Get a random positive affirmation"""
    affirmations = [
        "You are stronger than you think.",
        "Today is full of possibilities.",
        "Your mental health matters.",
        "You deserve happiness and peace.",
        "Progress, not perfection.",
        "You are doing the best you can.",
        "Be kind to yourself today.",
        "Your feelings are valid.",
        "You have the power to change.",
        "This moment does not define you.",
        "You are worthy just as you are.",
        "Your potential is limitless.",
        "Every small step counts.",
        "You are braver than you believe.",
        "Your story matters."
    ]
    return random.choice(affirmations)

def get_wellness_tip():
    """Get a daily wellness tip"""
    tips = [
        "Take 5 deep breaths to calm your mind and body.",
        "Go for a 10-minute walk to boost your mood.",
        "Drink a glass of water - hydration affects mood!",
        "Practice gratitude by listing 3 things you're thankful for.",
        "Limit social media to protect your mental health.",
        "Get 7-9 hours of sleep for better emotional balance.",
        "Eat a healthy meal to nourish your body and mind.",
        "Call a friend or family member you care about.",
        "Stretch for 5 minutes to release tension.",
        "Practice saying 'no' to protect your time and energy.",
        "Spend time in nature - it's therapeutic!",
        "Journal your thoughts without judgment.",
        "Meditate for even just 1 minute.",
        "Laugh - watch a funny video or recall a happy memory.",
        "Help someone today - kindness boosts your mood too!"
    ]
    return random.choice(tips)

def get_ai_response(user_message):
    """Generate an AI response using simple pattern matching and predefined responses"""
    user_message_lower = user_message.lower().strip()
    
    # Define response patterns
    responses = {
        'greeting': {
            'patterns': ['hi', 'hello', 'hey', 'greetings'],
            'responses': [
                "Hello! I'm here to support your mental wellness journey. How can I help you today?",
                "Hi there! It's great to see you. What's on your mind?",
                "Hey! Welcome to your wellness space. How are you feeling today?"
            ]
        },
        'mood': {
            'patterns': ['how are you', 'how do you feel', 'how are things'],
            'responses': [
                "I'm here to listen and support you. How have you been feeling lately?",
                "I appreciate you asking! More importantly, how are YOU doing?",
                "I'm doing well, thank you for asking! Tell me about your day."
            ]
        },
        'anxiety': {
            'patterns': ['anxious', 'anxiety', 'nervous', 'worried', 'stress', 'stressed'],
            'responses': [
                "I hear you. Anxiety can be overwhelming. Try the breathing exercise - it helps many people. Would you like to try it?",
                "It's normal to feel anxious sometimes. Remember, this feeling is temporary. Would a guided breathing exercise help?",
                "Anxiety is your mind trying to protect you. Let's work through this together. Try some deep breathing: inhale for 4, hold for 4, exhale for 4."
            ]
        },
        'sad': {
            'patterns': ['sad', 'depressed', 'down', 'lonely', 'alone', 'unhappy'],
            'responses': [
                "I'm sorry you're feeling down. It's okay to feel sad sometimes. Talking about it is a good first step.",
                "Sadness is a natural emotion. Remember, difficult emotions don't last forever. You're stronger than you think.",
                "It takes courage to acknowledge your feelings. Would journaling help you process what you're feeling?"
            ]
        },
        'gratitude': {
            'patterns': ['thank', 'thanks', 'grateful', 'appreciate'],
            'responses': [
                "You're welcome! I'm grateful to be part of your wellness journey.",
                "Happy to help! Remember, gratitude is a powerful tool for mental health.",
                "That's wonderful! Expressing gratitude is great for your well-being."
            ]
        },
        'exercise': {
            'patterns': ['exercise', 'workout', 'fitness', 'breathing', 'meditation'],
            'responses': [
                "Great! Exercise is excellent for mental health. Try our breathing exercise or quick workout routine.",
                "Movement and mindfulness are wonderful for wellness. Would you like to try our guided breathing or meditation?",
                "That's a fantastic idea! Physical activity boosts mood and reduces stress. Let's get started!"
            ]
        },
        'sleep': {
            'patterns': ['sleep', 'tired', 'exhausted', 'can\'t sleep', 'insomnia'],
            'responses': [
                "Sleep is crucial for mental health. Try our meditation exercise before bed - it can help you relax.",
                "Lack of sleep affects mood. Try limiting screens before bed and our breathing exercise to wind down.",
                "Feeling tired? Rest is important. Consider a short meditation or breathing exercise to help you relax."
            ]
        },
        'positive': {
            'patterns': ['great', 'good', 'excellent', 'amazing', 'wonderful', 'happy'],
            'responses': [
                "That's wonderful to hear! Keep up this positive momentum!",
                "I'm so happy for you! Celebrate these moments - you deserve it!",
                "That's fantastic! Your positive energy is inspiring. Keep going!"
            ]
        },
        'help': {
            'patterns': ['help', 'advice', 'what should', 'what can i do'],
            'responses': [
                "I'm here to help! You can journal your feelings, try our exercises, track your mood, or just talk to me.",
                "There are several things we can do: practice breathing exercises, meditation, journaling, or I can chat with you.",
                "Let's work through this together. Try one of our wellness exercises or tell me what's bothering you."
            ]
        },
        'journal': {
            'patterns': ['journal', 'write', 'entry', 'entries'],
            'responses': [
                "Journaling is a powerful way to process emotions. It helps you gain clarity and track your progress.",
                "Writing down your thoughts can be therapeutic. Go ahead and create a new journal entry!",
                "Great idea! Journaling helps you understand yourself better and track your mental wellness journey."
            ]
        }
    }
    
    # Match user message against patterns
    for category, data in responses.items():
        for pattern in data['patterns']:
            if pattern in user_message_lower:
                return random.choice(data['responses'])
    
    # Default response if no pattern matches
    default_responses = [
        "That's interesting! Tell me more about what you're experiencing.",
        "I understand. How does that make you feel?",
        "Thank you for sharing. Is there something specific you'd like help with?",
        "I'm listening. Would you like to try one of our wellness exercises?",
        "That's valuable insight. What can I help you with today?"
    ]
    
    return random.choice(default_responses)

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        
        if not username or not password:
            return render_template('register.html', error='Username and password are required')
        
        if len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        
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
    """User logout"""
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard with stats and achievements"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    
    # Calculate statistics
    last7 = datetime.now() - timedelta(days=7)
    last7_entries = [e for e in entries if datetime.fromisoformat(e.get('date', '')) >= last7]
    
    stats = {
        'total_entries': len(last7_entries),
        'total_all_time': len(entries),
        'exercises_done': sum(1 for e in last7_entries if e.get('exercise')),
        'avg_sentiment': round(sum(e.get('sentiment', 0) for e in last7_entries) / max(1, len(last7_entries)), 2),
        'streak': calculate_streak(username)
    }
    
    achievements = get_achievements(username)
    affirmation = get_random_affirmation()
    tip = get_wellness_tip()
    
    return render_template('dashboard.html', 
                         username=username, 
                         stats=stats, 
                         achievements=achievements,
                         affirmation=affirmation,
                         tip=tip)

@app.route('/add-entry', methods=['GET', 'POST'])
def add_entry():
    """Add new journal entry"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = session['username']
        mood = request.form.get('mood', '').strip()
        journal = request.form.get('journal', '').strip()
        exercise = request.form.get('exercise', '')
        gratitude = request.form.get('gratitude', '').strip()
        
        if not mood or not journal:
            return render_template('add_entry.html', error='Mood and journal entry are required')
        
        entry_sentiment = get_sentiment(journal)
        
        entry = {
            'username': username,
            'date': datetime.now().isoformat(),
            'mood': mood,
            'journal': journal,
            'exercise': exercise,
            'gratitude': gratitude,
            'sentiment': entry_sentiment,
            'mood_color': get_mood_color(mood)
        }
        
        entries = load_entries()
        entries.append(entry)
        save_entries(entries)
        
        return redirect(url_for('dashboard'))
    
    moods = ['Happy', 'Sad', 'Anxious', 'Calm', 'Energetic', 'Neutral', 'Excited', 'Overwhelmed']
    exercises = ['Walking', 'Running', 'Yoga', 'Meditation', 'Stretching', 'Dancing', 'Swimming', 'Cycling', 'None']
    
    return render_template('add_entry.html', moods=moods, exercises=exercises)

@app.route('/entries')
def list_entries():
    """View all entries"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    entries.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template('entries.html', entries=entries)

@app.route('/stats')
def stats():
    """View detailed statistics"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    
    last7 = datetime.now() - timedelta(days=7)
    last7_entries = [e for e in entries if datetime.fromisoformat(e.get('date', '')) >= last7]
    
    total_entries_7d = len(last7_entries)
    exercises_count = sum(1 for e in last7_entries if e.get('exercise'))
    avg_sentiment = round(sum(e.get('sentiment', 0) for e in last7_entries) / max(1, total_entries_7d), 2)
    
    mood_dist = {}
    for entry in last7_entries:
        mood = entry.get('mood', 'Unknown')
        mood_dist[mood] = mood_dist.get(mood, 0) + 1
    
    stats_data = {
        'total_entries': total_entries_7d,
        'total_all_time': len(entries),
        'exercises_done': exercises_count,
        'avg_sentiment': avg_sentiment,
        'streak': calculate_streak(username),
        'mood_distribution': mood_dist
    }
    
    return render_template('stats.html', stats=stats_data)

@app.route('/breathing-exercise')
def breathing_exercise():
    """Interactive animated breathing exercise"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('breathing_exercise.html')

@app.route('/meditation')
def meditation():
    """Guided meditation with visualization"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('meditation.html')

@app.route('/quick-workout')
def quick_workout():
    """Quick 5-minute exercise routine with visuals"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    exercises = [
        {
            "name": "Neck Rolls",
            "duration": "30 seconds",
            "instructions": "Slowly roll your neck in circles. Do 5-10 circles each direction. Breathe deeply.",
            "emoji": "🧪"
        },
        {
            "name": "Shoulder Shrugs",
            "duration": "30 seconds",
            "instructions": "Lift shoulders to ears. Hold for 2 seconds. Release. Repeat 15 times.",
            "emoji": "🏋️"
        },
        {
            "name": "Wrist Stretches",
            "duration": "30 seconds",
            "instructions": "Extend arms forward. Gently pull back fingers. Hold 15 seconds each hand.",
            "emoji": "🤝"
        },
        {
            "name": "Standing Stretch",
            "duration": "1 minute",
            "instructions": "Reach arms overhead. Bend gently to each side. Hold 15 seconds each.",
            "emoji": "🧘"
        }
    ]
    
    return render_template('quick_workout.html', exercises=exercises)

@app.route('/chatbot')
def chatbot():
    """AI Chatbot page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    chat_history = load_chat_history(username)
    
    return render_template('chatbot.html', chat_history=chat_history)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    user_message = request.json.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message required'}), 400
    
    # Get AI response
    ai_response = get_ai_response(user_message)
    
    # Save to chat history
    chat_history = load_chat_history(username)
    chat_history.append({
        'timestamp': datetime.now().isoformat(),
        'user': user_message,
        'bot': ai_response
    })
    save_chat_history(username, chat_history)
    
    return jsonify({
        'user_message': user_message,
        'bot_response': ai_response
    })

@app.route('/api/affirmation')
def get_affirmation_api():
    """API endpoint for random affirmation"""
    return jsonify({'affirmation': get_random_affirmation()})

@app.route('/api/tip')
def get_tip_api():
    """API endpoint for wellness tip"""
    return jsonify({'tip': get_wellness_tip()})

@app.route('/export')
def export_entries():
    """Export entries as JSON"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    entries = [e for e in load_entries() if e.get('username') == username]
    return jsonify(entries)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
