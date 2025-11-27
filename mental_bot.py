"""
mental_bot.py - Terminal-based Mental Wellness Companion

This module replaces the previous Streamlit UI with a simple, text-based menu
interface you can run in a terminal. It provides account management, journaling,
simple analytics, therapeutic exercises guidance, AI chat (optional), JSON/PDF
export, and data management.
"""

import os
import json
import time
import sys
from datetime import date, datetime, timedelta
from collections import Counter
from textblob import TextBlob
from dotenv import load_dotenv
import openai

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    # ReportLab used for PDF export; optional but included in requirements
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    import io
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


# Files
USERS_FILE = "users.json"
ENTRIES_FILE = "entries.json"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_entries():
    if os.path.exists(ENTRIES_FILE):
        try:
            with open(ENTRIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_entries(entries):
    with open(ENTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


AFFIRMATIONS = [
    "I am enough, just as I am.",
    "I can handle this, one step at a time.",
    "My feelings are valid, and they will pass.",
    "I choose kindness toward myself today.",
    "I am learning, growing, and healing.",
    "I can create moments of calm in my day.",
]


def daily_affirmation():
    idx = (date.today().timetuple().tm_yday) % len(AFFIRMATIONS)
    return AFFIRMATIONS[idx]


def safe_parse_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None


def calculate_weekly_stats(user_entries):
    if not user_entries:
        return None
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    recent_entries = [e for e in user_entries if safe_parse_date(e.get("date")) and safe_parse_date(e.get("date")) >= week_ago]
    if not recent_entries:
        return None
    stats = {
        "total_entries": len(recent_entries),
        "moods": Counter([e.get("mood", "Unknown") for e in recent_entries]),
        "exercises_done": len([e for e in recent_entries if e.get("exercise") and e.get("exercise") != "None"]),
        "avg_sentiment": 0,
        "streak_days": 0,
    }
    sentiments = []
    for e in recent_entries:
        text = e.get("journal", "")
        if isinstance(text, str) and text.strip():
            try:
                sentiments.append(TextBlob(text).sentiment.polarity)
            except Exception:
                pass
    if sentiments:
        stats["avg_sentiment"] = sum(sentiments) / len(sentiments)

    sorted_dates = sorted([safe_parse_date(e.get("date")) for e in user_entries if safe_parse_date(e.get("date")) is not None], reverse=True)
    streak = 0
    check_date = datetime.now().date()
    for ed in sorted_dates:
        if ed == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif ed < check_date:
            break
    stats["streak_days"] = streak
    return stats


def ai_response(prompt_text):
    text = (prompt_text or "").strip()
    if not text:
        return "I'm here and listening."
    if not openai.api_key:
        return "OpenAI API key not configured. Set OPENAI_API_KEY in environment to enable AI chat."
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a gentle, supportive mental wellness companion. Respond concisely, kindly, and practically."},
                {"role": "user", "content": text},
            ],
            max_tokens=180,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"AI is unavailable right now. Error: {e}"


def generate_pdf_report(user_entries, username, out_path=None):
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is not available in this environment")
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#0c2461"), alignment=1)
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#38ada9"))
    story.append(Paragraph("Mental Wellness Report", title_style))
    story.append(Paragraph(f"User: {username}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {date.today().strftime('%Y-%m-%d')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    total_entries = len(user_entries)
    moods = [e.get("mood", "Unknown") for e in user_entries]
    mood_counts = Counter(moods)
    exercises = [e.get("exercise", "None") for e in user_entries if e.get("exercise") and e.get("exercise") != "None"]
    summary_data = [["Metric", "Value"], ["Total Entries", str(total_entries)], ["Most Common Mood", mood_counts.most_common(1)[0][0] if mood_counts else "N/A"], ["Exercises Completed", str(len(exercises))]]
    summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#38ada9")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke), ("GRID", (0, 0), (-1, -1), 1, colors.grey)]))
    story.append(summary_table)
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Journal Entries (last 10)", heading_style))
    for entry in user_entries[-10:]:
        story.append(Paragraph(f"Date: {entry.get('date','')} | Mood: {entry.get('mood','')}", styles["Normal"]))
        story.append(Paragraph(f"Exercise: {entry.get('exercise','')}", styles["Normal"]))
        story.append(Paragraph(f"Journal: {entry.get('journal','')[:300]}", styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))
    doc.build(story)
    buffer.seek(0)
    if out_path:
        with open(out_path, "wb") as f:
            f.write(buffer.getvalue())
        return out_path
    return buffer


def print_menu():
    print("\n=== Mental Wellness Companion (text mode) ===")
    print("1) Login")
    print("2) Create account")
    print("3) Add journal entry")
    print("4) List my entries")
    print("5) Weekly stats")
    print("6) Exercises")
    print("7) Talk to AI companion")
    print("8) Export JSON")
    print("9) Export PDF")
    print("10) Delete my account")
    print("0) Exit")


def prompt_login(users):
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    if username in users and users[username] == password:
        print(f"[OK] Logged in as {username}")
        return username
    print("[ERROR] Invalid username or password")
    return None


def create_account(users):
    username = input("Choose a username: ").strip()
    if not username:
        print("Username cannot be empty")
        return None
    if username in users:
        print("Username already exists")
        return None
    password = input("Choose a password: ").strip()
    if not password:
        print("Password cannot be empty")
        return None
    users[username] = password
    save_users(users)
    print("🎉 Account created. You can now log in.")
    return username


def add_entry(username):
    mood = input("How are you feeling? (e.g. Happy, Sad, Anxious): ").strip() or "Unknown"
    journal = input("Write about your day (press Enter to skip): \n")
    exercise = input("Exercise done (None/Breathing/Grounding/Affirmation/Meditation): ").strip() or "None"
    entry = {
        "username": username,
        "date": date.today().strftime("%Y-%m-%d"),
        "mood": mood,
        "journal": journal,
        "exercise": exercise,
        "unusual_breathing": False,
    }
    entries = load_entries()
    entries.append(entry)
    save_entries(entries)
    print("[OK] Entry saved.")


def list_entries(username):
    entries = load_entries()
    my = [e for e in entries if e.get("username") == username]
    if not my:
        print("No entries found.")
        return
    for i, e in enumerate(sorted(my, key=lambda x: x.get("date", ""))):
        print(f"\nEntry #{i+1} — Date: {e.get('date')}")
        print(f"Mood: {e.get('mood')}")
        print(f"Exercise: {e.get('exercise')}")
        print(f"Journal: {e.get('journal')}")


def show_weekly_stats(username):
    entries = load_entries()
    my = [e for e in entries if e.get("username") == username]
    stats = calculate_weekly_stats(my)
    if not stats:
        print("No entries in the past 7 days.")
        return
    print(f"Total entries (7d): {stats['total_entries']}")
    print(f"Exercises done (7d): {stats['exercises_done']}")
    print(f"Avg sentiment (7d): {stats['avg_sentiment']:.2f}")
    print(f"Streak days: {stats['streak_days']}")
    print("Mood distribution:")
    for k, v in stats['moods'].items():
        print(f" - {k}: {v}")


def exercises_menu(username):
    print("\nExercises:")
    print("1) Breathing 4-7-8 (text guidance)")
    print("2) 5-4-3-2-1 Grounding (text guidance)")
    print("3) Daily Affirmation")
    print("0) Back")
    choice = input("Choose: ")
    if choice == "1":
        print("Practice: Inhale 4s → Hold 7s → Exhale 8s. Repeat 2-4 cycles. Stop if dizzy.")
    elif choice == "2":
        print("Grounding: Identify 5 things you see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.")
    elif choice == "3":
        print(f"Affirmation: \"{daily_affirmation()}\"")
    else:
        return
    save = input("Save this as an exercise entry? (y/N): ").lower()
    if save == "y":
        entries = load_entries()
        entries.append({
            "username": username,
            "date": date.today().strftime("%Y-%m-%d"),
            "mood": "",
            "journal": f"Completed exercise: {choice}",
            "exercise": "Breathing" if choice == "1" else "Grounding" if choice == "2" else "Affirmation",
            "unusual_breathing": False,
        })
        save_entries(entries)
        print("[OK] Exercise saved.")


def export_json(username):
    entries = load_entries()
    my = [e for e in entries if e.get("username") == username]
    if not my:
        print("No entries to export.")
        return
    filename = f"wellness_data_{username}_{date.today().strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(my, f, ensure_ascii=False, indent=2)
    print(f"[OK] Exported to {filename}")


def export_pdf(username):
    entries = load_entries()
    my = [e for e in entries if e.get("username") == username]
    if not my:
        print("No entries to export.")
        return
    if not REPORTLAB_AVAILABLE:
        print("reportlab not available. Install reportlab to enable PDF export.")
        return
    filename = f"wellness_report_{username}_{date.today().strftime('%Y%m%d')}.pdf"
    generate_pdf_report(my, username, out_path=filename)
    print(f"[OK] PDF saved to {filename}")


def delete_account(username):
    confirm = input("Type DELETE to permanently delete your account and entries: ")
    if confirm != "DELETE":
        print("Aborted.")
        return False
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
    entries = load_entries()
    remaining = [e for e in entries if e.get("username") != username]
    save_entries(remaining)
    print("Account and entries deleted.")
    return True


def main_loop():
    users = load_users()
    current_user = None
    while True:
        print_menu()
        choice = input("Choose an option: ").strip()
        if choice == "1":
            if current_user:
                print(f"Already logged in as {current_user}")
            else:
                u = prompt_login(users)
                if u:
                    current_user = u
        elif choice == "2":
            u = create_account(users)
            if u:
                current_user = None
        elif choice == "3":
            if not current_user:
                print("Please log in first.")
            else:
                add_entry(current_user)
        elif choice == "4":
            if not current_user:
                print("Please log in first.")
            else:
                list_entries(current_user)
        elif choice == "5":
            if not current_user:
                print("Please log in first.")
            else:
                show_weekly_stats(current_user)
        elif choice == "6":
            if not current_user:
                print("Please log in first.")
            else:
                exercises_menu(current_user)
        elif choice == "7":
            if not current_user:
                print("Please log in first.")
            else:
                prompt = input("Say something to your AI companion: \n")
                print("AI: ", ai_response(prompt))
        elif choice == "8":
            if not current_user:
                print("Please log in first.")
            else:
                export_json(current_user)
        elif choice == "9":
            if not current_user:
                print("Please log in first.")
            else:
                export_pdf(current_user)
        elif choice == "10":
            if not current_user:
                print("Please log in first.")
            else:
                deleted = delete_account(current_user)
                if deleted:
                    current_user = None
        elif choice == "0":
            print("Goodbye — take care.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    print("Starting Mental Wellness Companion (text mode)")
    main_loop()

