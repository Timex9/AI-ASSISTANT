from flask import Flask, render_template
from flask_socketio import SocketIO
import pyautogui
import platform
import wikipediaapi
import subprocess
import re
import webbrowser
from datetime import datetime
import os

# --- Initialization ---
app = Flask(__name__)
socketio = SocketIO(app)
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MyVirtualAssistant/1.0 (merlin@example.com)',
    language='en'
)

# --- Command Functions ---
def increase_volume():
    if platform.system() == "Darwin":  # macOS
        script = 'set volume output volume ((output volume of (get volume settings)) + 10)'
        subprocess.run(['osascript', '-e', script])
    elif platform.system() == "Linux":
        subprocess.run(['amixer', 'set', 'Master', '5%+'])
    elif platform.system() == "Windows":
        pyautogui.press("volumeup")
    return "Volume increased."

def decrease_volume():
    if platform.system() == "Darwin":
        script = 'set volume output volume ((output volume of (get volume settings)) - 10)'
        subprocess.run(['osascript', '-e', script])
    elif platform.system() == "Linux":
        subprocess.run(['amixer', 'set', 'Master', '5%-'])
    elif platform.system() == "Windows":
        pyautogui.press("volumedown")
    return "Volume decreased."

def mute_volume():
    if platform.system() == "Darwin":
        script = '''
            if output muted of (get volume settings) is false then
                set volume output muted true
            else
                set volume output muted false
            end if
        '''
        subprocess.run(['osascript', '-e', script])
    elif platform.system() == "Linux":
        subprocess.run(['amixer', 'set', 'Master', 'toggle'])
    elif platform.system() == "Windows":
        pyautogui.press("volumemute")
    return "Toggled mute."

def close_current_tab():
    if platform.system() == "Darwin":
        pyautogui.hotkey('command', 'w')
    else:
        pyautogui.hotkey('ctrl', 'w')
    return "Tab closed."

def search_wikipedia(query):
    page = wiki_wiki.page(query)
    if page.exists():
        summary = ". ".join(page.summary.split('.')[:2])
        return summary
    else:
        return f"Sorry, I could not find any results for {query} on Wikipedia."

def tell_time():
    now = datetime.now().strftime("%I:%M %p")
    return f"The current time is {now}."

def tell_date():
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"Today is {today}."

def open_website(site_name):
    sites = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://www.github.com",
        "wikipedia": "https://www.wikipedia.org"
    }
    url = sites.get(site_name.lower())
    if url:
        webbrowser.open(url)
        return f"Opening {site_name}."
    return f"Sorry, I don't know the website {site_name}."

def open_application(app_name):
    system = platform.system()
    try:
        if system == "Windows":
            apps = {
                "notepad": "notepad",
                "calculator": "calc"
            }
            if app_name in apps:
                subprocess.Popen(apps[app_name])
                return f"Opening {app_name}."
        elif system == "Darwin":  # macOS
            apps = {
                "notes": "Notes",
                "calculator": "Calculator"
            }
            if app_name in apps:
                subprocess.run(["open", "-a", apps[app_name]])
                return f"Opening {app_name}."
        elif system == "Linux":
            apps = {
                "calculator": "gnome-calculator",
                "gedit": "gedit"
            }
            if app_name in apps:
                subprocess.Popen([apps[app_name]])
                return f"Opening {app_name}."
        return f"Sorry, I cannot open {app_name} on this system."
    except Exception as e:
        return f"Error opening {app_name}: {e}"

# --- Web Server and SocketIO Logic ---
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('command')
def handle_command(json):
    command = json.get('data', '').lower()
    print(f"Received command: {command}")
    
    response = "I don't know how to do that yet."

    try:
        if "increase volume" in command:
            response = increase_volume()
        elif "decrease volume" in command:
            response = decrease_volume()
        elif "mute" in command:
            response = mute_volume()
        elif ("close" in command and "tab" in command) or ("close" in command and "window" in command):
            response = close_current_tab()
        elif "wikipedia" in command:
            query = re.sub(r'\bwikipedia\b', '', command).strip()
            if query:
                response = search_wikipedia(query)
            else:
                response = "What would you like to search for on Wikipedia?"
        elif "time" in command:
            response = tell_time()
        elif "date" in command:
            response = tell_date()
        elif "open" in command and any(site in command for site in ["google", "youtube", "github", "wikipedia"]):
            for site in ["google", "youtube", "github", "wikipedia"]:
                if site in command:
                    response = open_website(site)
        elif "open" in command:
            app_name = command.replace("open", "").strip()
            response = open_application(app_name)
        elif "goodbye" in command or "exit" in command:
            response = "Goodbye!"
    except Exception as e:
        response = f"Error executing command: {e}"

    socketio.emit('response', {'data': response})

if __name__ == '__main__':
    print("Starting web server at http://127.0.0.1:5000")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
