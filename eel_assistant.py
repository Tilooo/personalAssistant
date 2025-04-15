import eel
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import threading
import time
import random
import sys
import json
import requests

# API keys
try:
    from my_api import OPENWEATHERMAP_API_KEY, NEWS_API_KEY
except ImportError:
    print("Warning: API keys not found. Some features will be disabled.")
    OPENWEATHERMAP_API_KEY = ""
    NEWS_API_KEY = ""

# Initialized Eel with the web folder
eel.init('web')

class VoiceAssistant:
    def __init__(self, name="Assistant"):
        self.name = name
        self.recognizer = sr.Recognizer()
        self.commands = {
            "greeting": ["hello", "hi", "hey", "good day"],
            "time": ["time", "what time", "current time"],
            "weather": ["weather", "temperature", "forecast"],
            "reminder": ["reminder", "remind", "remind me"],
            "todo": ["to-do", "todo", "task", "add it", "add to list"],
            "read_todo": ["read todo", "read my list", "what is on my list"],
            "search": ["search", "look up", "find", "google"],
            "joke": ["joke", "tell me a joke", "make me laugh"],
            "news": ["news", "headlines", "latest news"],
            "fact": ["fact", "random fact", "tell me a fact", "interesting fact"],
            "exit": ["exit", "stop", "quit", "goodbye"],
            "thanks": ["thank you", "thanks", "appreciate it"],
            "music": ["play music", "music", "play song", "play some music"],
            "age": ["how old", "your age", "when were you created"]
        }
        self.listening = False
        self.listen_thread = None
    
    def setup_voice(self):
        self.engine.setProperty('rate', 170)
        self.engine.setProperty('volume', 1)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)
    
    def initialize_tts(self):
        try:
            if self.engine is not None:
                try:
                    self.engine.stop()
                except:
                    pass

            self.engine = pyttsx3.init(driverName=None)

            self.setup_voice()
            
            return True
        except Exception as e:
            print(f"TTS initialization error: {e}")
            self.engine = None
            return False
    
    def speak(self, text):
        try:
            # Updated UI - this should always work even if speech fails
            eel.updateAssistantMessage(text)
            
            # Used subprocess to call Windows speech API directly
            try:
                import subprocess
                # Used PowerShell to speak text using Windows built-in speech
                subprocess.run(['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{text}")'], 
                               shell=True, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
                print(f"Spoke: {text}")
            except Exception as speech_error:
                print(f"Speech subprocess error: {speech_error}")
                
        except Exception as e:
            print(f"Speak error: {e}")
            # Ensured the UI is updated even if there's an error
            try:
                eel.updateStatus(f"Speech error: Please check console")
            except:
                pass
    
    def listen(self):
        try:
            self.recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening...")
                eel.updateStatus("Listening...")
                eel.showListeningIndicator()
                
                # Shorter timeout for faster response
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("Processing audio...")
                eel.updateStatus("Processing audio...")

                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"Recognized: {text}")
                    eel.updateUserMessage(text)
                    eel.hideListeningIndicator()
                    return text.lower()
                except sr.UnknownValueError:
                    print("Could not understand audio")
                    eel.updateStatus("Listening...")
                    return None
                except sr.RequestError as e:
                    print(f"Request error: {e}")
                    self.speak("Sorry, I'm having trouble connecting to the speech recognition service.")
                    eel.hideListeningIndicator()
                    return None
        except Exception as e:
            print(f"Listen error: {e}")
            eel.updateStatus(f"Error: {str(e)}")
            eel.hideListeningIndicator()
            return None
    
    def greet_user(self):
        hour = datetime.datetime.now().hour  
        
        if 0 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
            
        self.speak(f"{greeting}! I'm {self.name}, your personal voice assistant. How can I help you today?")
    
    def process_command(self, command):
        if not command:
            return
            
        if any(phrase in command for phrase in self.commands["exit"]):
            self.speak("Goodbye!")
            self.listening = False
            eel.updateStatus("Ready")
            return
            
        if any(phrase in command for phrase in self.commands["greeting"]):
            self.greet_user()
            
        elif any(phrase in command for phrase in self.commands["time"]):
            current_time = datetime.datetime.now().strftime('%I:%M %p')
            self.speak(f"The current time is {current_time}")
            
        elif any(phrase in command for phrase in self.commands["weather"]):
            self.get_weather(command)
            
        elif any(phrase in command for phrase in self.commands["reminder"]):
            self.speak("What would you like me to remind you about?")
            
        elif any(phrase in command for phrase in self.commands["todo"]):
            self.add_todo(command)
            
        elif any(phrase in command for phrase in self.commands["read_todo"]):
            self.read_todo()
            
        elif any(phrase in command for phrase in self.commands["search"]):
            self.search_web(command)
            
        elif any(phrase in command for phrase in self.commands["joke"]):
            self.tell_joke()
            
        elif any(phrase in command for phrase in self.commands["news"]):
            self.get_news(command)
            
        elif any(phrase in command for phrase in self.commands["fact"]):
            self.get_random_fact()
            
        elif any(phrase in command for phrase in self.commands["thanks"]):
            self.speak("You're welcome! Is there anything else I can help you with?")
            
        elif any(phrase in command for phrase in self.commands["music"]):
            self.speak("I'd love to play music for you, but I don't have access to music services yet. I'll add that feature soon!")
            
        elif any(phrase in command for phrase in self.commands["age"]):
            self.speak("I was created recently as a voice assistant. I don't have an age in the traditional sense, but I'm here to help you!")
            
        else:
            self.speak("I heard you, but I'm not sure how to help with that yet.")
    
    def add_todo(self, command):
        # Extracted the task from the command
        task = command.split("add", 1)[-1].split("to", 1)[0].strip()
        if not task or task == "it":
            self.speak("What would you like to add to your to-do list?")
            return
            
        try:
            with open('todo.txt', 'a') as f:
                f.write(f"{task}\n")
            self.speak(f"I've added '{task}' to your to-do list.")
        except Exception as e:
            self.speak("I couldn't add that to your to-do list.")
            print(f"Error adding to todo list: {e}")
    
    def read_todo(self):
        try:
            if not os.path.exists('todo.txt') or os.path.getsize('todo.txt') == 0:
                self.speak("Your to-do list is empty.")
                return
                
            with open('todo.txt', 'r') as f:
                todos = f.readlines()
                
            if not todos:
                self.speak("Your to-do list is empty.")
                return
                
            self.speak("Here's what's on your to-do list:")
            for i, todo in enumerate(todos, 1):
                self.speak(f"{i}. {todo.strip()}")
        except Exception as e:
            self.speak("I couldn't read your to-do list.")
            print(f"Error reading todo list: {e}")
    
    def search_web(self, command):
        search_terms = ["search for", "search", "google", "look up", "find"]
        query = None
        
        for term in search_terms:
            if term in command:
                query = command.split(term, 1)[1].strip()
                break
        
        if query:
            self.speak(f"Searching for {query}")
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
        else:
            self.speak("What would you like me to search for?")
    
    def tell_joke(self):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
            "Why don't we tell secrets on a farm? Because the potatoes have eyes and the corn has ears!",
            "What do you call a fake noodle? An impasta!",
            "How does a penguin build its house? Igloos it together!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "What do you call a bear with no teeth? A gummy bear!"
        ]
        joke = random.choice(jokes)
        self.speak(joke)
    
    def restart_speech_engine(self):
        """Restarts the speech engine to fix potential issues"""
        print("Restarting speech engine")
        self.engine = None
        self.speech_enabled = self.initialize_tts()
        return self.speech_enabled

    
    def start_listening(self):
        if not self.listening:
            self.listening = True
            self.listen_thread = threading.Thread(target=self.listening_loop)
            self.listen_thread.daemon = True
            self.listen_thread.start()
    
    def stop_listening(self):
        print("Stopping listening...")
        self.listening = False

        if self.listen_thread and self.listen_thread.is_alive():
            try:
                for _ in range(5):  # for 5 seconds
                    if not self.listen_thread.is_alive():
                        break
                    time.sleep(1)
                
                if self.listen_thread.is_alive():
                    print("Warning: Listen thread did not terminate properly")
            except:
                print("Error stopping listen thread")
        
        # Updated UI
        eel.updateStatus("Ready")
        print("Listening stopped")
    
    def listening_loop(self):
        print("Starting listening loop")
        self.greet_user()
        
        # Counts consecutive failures
        failures = 0
        
        while self.listening:
            try:
                command = self.listen()
                
                if command:
                    print(f"Processing command: {command}")
                    failures = 0  # Resets failure count on success
                    self.process_command(command)
                    if not self.listening:
                        break
                else:
                    failures += 1
                    if failures > 5:
                        # After 5 consecutive failures, updates status
                        eel.updateStatus("Waiting for command...")
                        failures = 0
                
                # Smaller delay to prevent CPU hogging but be more responsive
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in listening loop: {e}")
                time.sleep(0.3)  # Shorter delay after error
    
    def get_weather(self, command):
        """Get current weather for a location"""
        # Extracts location from command
        location = None
        for phrase in ["weather in", "weather for", "weather at", "weather of", "temperature in", "temperature at", "get weather"]:
            if phrase in command:
                location = command.split(phrase, 1)[1].strip()
                break
        
        # If no location found but command contains just the word "weather", check if there's any city name after
        if not location and "weather" in command:
            parts = command.split("weather", 1)
            if len(parts) > 1 and parts[1].strip():
                location = parts[1].strip()
        
        if not location:
            self.speak("Which city would you like to know the weather for?")
            return
                
        try:
            # Using OpenWeatherMap API
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
            
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                # Extracts relevant weather information
                weather_desc = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                
                weather_info = f"The weather in {location} is {weather_desc}. The temperature is {temp:.1f}°C, feels like {feels_like:.1f}°C, with {humidity}% humidity."
                self.speak(weather_info)
            else:
                self.speak(f"I couldn't find weather information for {location}.")
        except Exception as e:
            print(f"Weather API error: {e}")
            self.speak("Sorry, I couldn't get the weather information at the moment.")

    def get_news(self, command):
        """Get latest news headlines"""
        try:
            if not NEWS_API_KEY:
                # a free news source that doesn't require API key
                self.speak("I'll get some news headlines for you from an alternative source.")
                
                # Used a public RSS feed instead
                import feedparser
                
                # Extracts category if specified
                category = None
                categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
                
                for cat in categories:
                    if cat in command:
                        category = cat
                        break
                
                # Uses different RSS feeds based on category
                if category == "technology":
                    feed_url = "https://feeds.bbci.co.uk/news/technology/rss.xml"
                    self.speak(f"Here are the latest technology news headlines from BBC:")
                elif category == "business":
                    feed_url = "https://feeds.bbci.co.uk/news/business/rss.xml"
                    self.speak(f"Here are the latest business news headlines from BBC:")
                elif category == "health":
                    feed_url = "https://feeds.bbci.co.uk/news/health/rss.xml"
                    self.speak(f"Here are the latest health news headlines from BBC:")
                elif category == "science":
                    feed_url = "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
                    self.speak(f"Here are the latest science news headlines from BBC:")
                elif category == "sports":
                    feed_url = "https://feeds.bbci.co.uk/sport/rss.xml"
                    self.speak(f"Here are the latest sports news headlines from BBC:")
                else:
                    feed_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
                    self.speak("Here are the latest world news headlines from BBC:")
                
                # Parses the feed
                feed = feedparser.parse(feed_url)
                
                # Gets the top 3 headlines
                for i, entry in enumerate(feed.entries[:3], 1):
                    headline = entry.title
                    self.speak(f"{i}. {headline}")
                
                return

            category = None
            categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
            
            if category:
                url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={NEWS_API_KEY}"
                self.speak(f"Here are the latest {category} news headlines:")
            else:
                url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
                self.speak("Here are the latest news headlines:")
            
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200 and data["articles"]:
                # Gets the top 3 headlines
                for i, article in enumerate(data["articles"][:3], 1):
                    headline = article["title"]
                    self.speak(f"{i}. {headline}")
            else:
                self.speak("I couldn't find any news headlines at the moment.")
        except Exception as e:
            print(f"News API error: {e}")
            self.speak("Sorry, I couldn't get the news headlines at the moment.")

    def get_random_fact(self):
        """Get a random fact"""
        try:
            # Using the useless facts API (no key required)
            url = "https://uselessfacts.jsph.pl/random.json?language=en"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                fact = data["text"]
                self.speak(f"Here's a random fact: {fact}")
            else:
                self.speak("I couldn't find a random fact at the moment.")
        except Exception as e:
            print(f"Random fact API error: {e}")
            self.speak("Sorry, I couldn't get a random fact at the moment.")

# Creates an instance of the assistant after Eel is ready
assistant = None

@eel.expose
def start_assistant():
    global assistant
    try:
        print("Starting assistant...")
        
        # Always creates a fresh instance to avoid state issues
        assistant = VoiceAssistant()
        
        # Makes sure microphone is available
        mics = sr.Microphone.list_microphone_names()
        print(f"Available microphones: {mics}")
        
        assistant.start_listening()
        return "Assistant started"
    except Exception as e:
        print(f"Error starting assistant: {e}")
        return f"Error: {str(e)}"

@eel.expose
def stop_assistant():
    global assistant
    if assistant:
        assistant.stop_listening()
    return "Assistant stopped"

# Starts the Eel application
def ensure_background_image():
    """Ensure a background image exists for the web interface"""
    background_path = os.path.join('web', 'background1.jpg')

    if not os.path.exists(background_path):
        try:
            import urllib.request
            print("Downloading a background image...")
            image_url = "https://source.unsplash.com/1600x900/?digital,assistant,blue"
            urllib.request.urlretrieve(image_url, background_path)
            print(f"Background image downloaded to {background_path}")
        except Exception as e:
            print(f"Could not download background image: {e}")
            print("Using a solid color background instead")


if __name__ == "__main__":
    try:
        ensure_background_image()
        
        eel.start('index.html', size=(800, 600), block=False)
        
        # Keeps the application running
        while True:
            eel.sleep(1.0)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Application closed")