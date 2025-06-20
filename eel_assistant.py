import eel
import speech_recognition as sr
import datetime
import webbrowser
import os
import threading
import time
import random
import sys
import json
import requests
import subprocess
import feedparser

# --- CONFIGURATION & API KEYS ---
try:
    # OPENWEATHERMAP_API_KEY = "your_key_here"
    # NEWS_API_KEY = "your_key_here"
    from my_api import OPENWEATHERMAP_API_KEY, NEWS_API_KEY
except ImportError:
    print("Warning: API keys file 'my_api.py' not found. Some features will be disabled.")
    OPENWEATHERMAP_API_KEY = ""
    NEWS_API_KEY = ""


# --- THE MAIN ASSISTANT CLASS (with ALL functions) ---
class VoiceAssistant:
    def __init__(self, name="Assistant"):
        self.name = name
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.listen_thread = None
        self.is_eel_running = 'eel' in sys.modules

        # KEYWORD DICTIONARY
        self.commands = {
            "exit": ["exit", "stop", "quit", "goodbye", "bye-bye"],
            "weather": ["weather", "temperature", "forecast"],
            "news": ["news", "headlines"],
            "horoscope": ["horoscope", "zodiac"],
            "todo": ["to-do", "todo", "task", "add to list"],
            "read_todo": ["read todo", "read my list"],
            "search": ["search", "look up", "find", "google"],
            "joke": ["joke", "tell me a joke"],
            "calculator": ["calculate", "math", "compute", "plus", "minus", "times", "divided by", "*", "+", "-", "/"],
            "currency": ["convert", "dollar", "euro"],
            "time": ["time", "what time"],
            "greeting": ["hello", "hi", "hey"],
            "thanks": ["thank you", "thanks"],
        }

    def ui_update(self, func_name, *args):
        if self.is_eel_running:
            try:
                getattr(eel, func_name)(*args)
            except Exception as e:
                print(f"Eel UI error: {e}")

    def speak(self, text):
        print(f"Assistant: {text}")
        self.ui_update('updateAssistantMessage', text)
        try:
            command = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{text}")'
            subprocess.run(['powershell', '-Command', command], check=True, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        except Exception as e:
            print(f"Speech error: {e}")

    def listen(self):
        try:
            with sr.Microphone() as source:
                self.ui_update('updateStatus', "Adjusting noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.ui_update('updateStatus', "Listening...")
                self.ui_update('showListeningIndicator')
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                self.ui_update('hideListeningIndicator')
                self.ui_update('updateStatus', "Processing...")
                text = self.recognizer.recognize_google(audio)
                print(f"User: {text}")
                self.ui_update('updateUserMessage', text)
                return text.lower()
        except Exception:
            return None

    # --- COMMAND FUNCTIONS ---

    def get_weather(self, command):
        if not OPENWEATHERMAP_API_KEY:
            self.speak("The weather service is not configured. I need an API key.")
            return

        # Find city name after "in" or "for"
        city = None
        if "in" in command:
            city = command.split("in", 1)[1].strip()
        elif "for" in command:
            city = command.split("for", 1)[1].strip()

        if not city:
            self.speak("Which city's weather would you like to know?")
            return

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
            data = requests.get(url).json()
            if data.get("cod") == 200:
                desc = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                self.speak(
                    f"The weather in {city} is currently {desc} with a temperature of {temp:.0f} degrees Celsius.")
            else:
                self.speak(f"Sorry, I couldn't find weather information for {city}.")
        except Exception as e:
            self.speak(f"Sorry, an error occurred while fetching the weather. {e}")

    def get_news(self, command):
        self.speak("Fetching top headlines from the BBC News feed...")
        try:
            feed = feedparser.parse("https://feeds.bbci.co.uk/news/world/rss.xml")
            if not feed.entries:
                self.speak("I couldn't retrieve any news headlines at this time.")
                return
            for entry in feed.entries[:3]:  # Read the top 3 headlines
                self.speak(entry.title)
        except Exception as e:
            self.speak(f"Sorry, I ran into an error trying to get the news. {e}")

    def get_horoscope(self, command):
        signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn",
                 "aquarius", "pisces"]
        sign = next((s for s in signs if s in command), None)

        if not sign:
            self.speak("Which zodiac sign's horoscope would you like?")
            return

        try:
            # Using Aztro API for horoscopes
            url = f"https://aztro.sameerkumar.website/?sign={sign}&day=today"
            data = requests.post(url).json()
            description = data["description"]
            self.speak(f"Today's horoscope for {sign.capitalize()}: {description}")
        except Exception as e:
            self.speak(f"Sorry, I couldn't get the horoscope right now. Error: {e}")

    def calculate(self, command):
        try:
            expression = command.replace("x", "*").replace("times", "*").replace("divided by", "/")
            allowed_chars = "0123456789.+-*/()"
            clean_expression = "".join(c for c in expression if c in allowed_chars)
            if not any(c.isdigit() for c in clean_expression):
                self.speak("What would you like me to calculate?")
                return
            result = eval(clean_expression)
            self.speak(f"The result is {result}")
        except Exception:
            self.speak("I couldn't calculate that. Please ask a simpler math question.")

    def search_web(self, command):
        query = command.replace("search for", "").replace("search", "").strip()
        if query:
            self.speak(f"Searching for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
        else:
            self.speak("What would you like me to search for?")

    def tell_joke(self):
        jokes = ["Why don't scientists trust atoms? Because they make up everything!",
                 "What do you call a fake noodle? An impasta!"]
        self.speak(random.choice(jokes))

    # --- CORE LOGIC ---

    def process_command(self, command):
        if not command: return

        # specific, complex commands first
        if any(phrase in command for phrase in self.commands["weather"]):
            self.get_weather(command)
        elif any(phrase in command for phrase in self.commands["news"]):
            self.get_news(command)
        elif any(phrase in command for phrase in self.commands["horoscope"]):
            self.get_horoscope(command)
        # Then check for more general commands
        elif any(phrase in command for phrase in self.commands["calculator"]):
            self.calculate(command)
        elif any(phrase in command for phrase in self.commands["search"]):
            self.search_web(command)
        elif any(phrase in command for phrase in self.commands["joke"]):
            self.tell_joke()
        elif any(phrase in command for phrase in self.commands["time"]):
            self.speak(f"The time is {datetime.datetime.now().strftime('%I:%M %p')}")
        elif any(phrase in command for phrase in self.commands["greeting"]):
            self.speak("Hello there!")
        elif any(phrase in command for phrase in self.commands["thanks"]):
            self.speak("You're welcome!")
        elif any(phrase in command for phrase in self.commands["exit"]):
            self.speak("Goodbye!")
            self.stop_listening()
        else:
            # If nothing else matches, assume it's a general question and search for it
            self.speak(f"I'm not sure how to answer that, but I can search for '{command}' for you.")
            self.search_web(command)

    def start_listening(self):
        if not self.listening:
            self.listening = True
            self.listen_thread = threading.Thread(target=self.listening_loop, daemon=True)
            self.listen_thread.start()

    def stop_listening(self):
        if self.listening:
            self.listening = False
            self.ui_update('updateStatus', "Ready")
            self.ui_update('hideListeningIndicator')

    def listening_loop(self):
        self.speak(f"Hello! I'm {self.name}. How can I help you today?")
        while self.listening:
            command = self.listen()
            if command:
                self.process_command(command)
            eel.sleep(0.1)
        print("Listening loop has ended.")


# --- EEL SETUP AND EXECUTION ---
assistant = VoiceAssistant()


@eel.expose
def start_assistant():
    assistant.start_listening()


@eel.expose
def stop_assistant():
    assistant.stop_listening()


if __name__ == "__main__":
    web_folder = 'web'
    if not os.path.isdir(web_folder):
        print(f"Error: Directory '{web_folder}' not found.")
        sys.exit(1)

    eel.init(web_folder)
    print("Starting Eel server for web UI...")
    eel.start('index.html', size=(850, 750), block=True)
    print("Eel application closed.")