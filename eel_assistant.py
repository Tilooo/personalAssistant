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
            "age": ["how old", "your age", "when were you created"],
            "horoscope": ["horoscope", "zodiac", "star sign", "astrology"],
            "calendar": ["calendar", "schedule", "appointment", "event", "what's on today"],
            "calculator": ["calculate", "math", "compute", "what is"],
            "currency": ["convert currency", "exchange rate", "convert dollars", "convert euros"],
            "dictionary": ["define", "definition", "what does", "mean", "dictionary"]
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
            
        elif any(phrase in command for phrase in self.commands["horoscope"]):
            self.get_horoscope(command)
            
        elif any(phrase in command for phrase in self.commands["calendar"]):
            self.check_calendar(command)
            
        elif any(phrase in command for phrase in self.commands["calculator"]) or "+" in command or "-" in command or "*" in command or "/" in command or any(x in command for x in ["plus", "minus", "times", "divided by"]):
            self.calculate(command)
            
        elif any(phrase in command for phrase in self.commands["currency"]) or ("convert" in command and any(currency in command for currency in ["dollar", "euro", "pound", "yen", "yuan", "rupee"])):
            self.convert_currency(command)
            
        elif any(phrase in command for phrase in self.commands["dictionary"]):
            self.define_word(command)
            
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

    def get_horoscope(self, command):
        """Get horoscope for a zodiac sign"""
        # Dictionary mapping zodiac signs to their date ranges
        zodiac_signs = {
            "aries": "March 21 - April 19",
            "taurus": "April 20 - May 20",
            "gemini": "May 21 - June 20",
            "cancer": "June 21 - July 22",
            "leo": "July 23 - August 22",
            "virgo": "August 23 - September 22",
            "libra": "September 23 - October 22",
            "scorpio": "October 23 - November 21",
            "sagittarius": "November 22 - December 21",
            "capricorn": "December 22 - January 19",
            "aquarius": "January 20 - February 18",
            "pisces": "February 19 - March 20"
        }
        
        # Extracts sign from command
        sign = None
        for zodiac in zodiac_signs.keys():
            if zodiac in command:
                sign = zodiac
                break
        
        if not sign:
            # If no sign found in command, asks for it
            self.speak("Which zodiac sign would you like to hear the horoscope for?")
            return
        
        try:
            # Using Aztro API for horoscopes
            url = f"https://aztro.sameerkumar.website/?sign={sign}&day=today"
            response = requests.post(url)
            
            if response.status_code == 200:
                data = response.json()
                description = data["description"]
                compatibility = data["compatibility"]
                mood = data["mood"]
                lucky_number = data["lucky_number"]
                
                horoscope_text = f"Here's today's horoscope for {sign.capitalize()}, born {zodiac_signs[sign]}. {description} Your compatible sign is {compatibility}, your mood is {mood}, and your lucky number is {lucky_number}."
                self.speak(horoscope_text)
            else:
                # Fallbacks to predefined horoscopes if API fails
                fallback_horoscopes = {
                    "aries": "Today is a day for new beginnings. Your energy is high, and you're ready to take on challenges.",
                    "taurus": "Focus on stability today. Good time for financial decisions and enjoying life's comforts.",
                    "gemini": "Your communication skills shine today. Great day for networking and sharing ideas.",
                    "cancer": "Listen to your intuition today. Family matters may require your attention.",
                    "leo": "Your creativity is at a peak. Take the spotlight and showcase your talents.",
                    "virgo": "Details matter today. Your analytical skills will help solve a persistent problem.",
                    "libra": "Seek balance in all things today. Relationships are highlighted and may need attention.",
                    "scorpio": "Your intensity serves you well today. Good time for research and uncovering truths.",
                    "sagittarius": "Adventure calls to you today. Expand your horizons through learning or travel.",
                    "capricorn": "Focus on your goals today. Your discipline will help you make significant progress.",
                    "aquarius": "Your innovative ideas are valuable today. Connect with like-minded individuals.",
                    "pisces": "Your imagination is powerful today. Creative and spiritual pursuits are favored."
                }
                
                self.speak(f"Here's today's horoscope for {sign.capitalize()}: {fallback_horoscopes[sign]}")
        except Exception as e:
            print(f"Horoscope error: {e}")
            self.speak(f"I couldn't get the horoscope for {sign} at the moment.")

    def check_calendar(self, command):
        """Check calendar for events"""
        try:
            # Simple calendar implementation using a JSON file
            calendar_file = 'calendar.json'

            # Creates calendar file if it doesn't exist
            if not os.path.exists(calendar_file):
                with open(calendar_file, 'w') as f:
                    json.dump({"events": []}, f)
            
            # Loads existing events
            with open(calendar_file, 'r') as f:
                calendar_data = json.load(f)
            
            # Checks if command is to add an event
            if "add" in command or "new" in command or "create" in command:
                self.speak("What event would you like to add to your calendar?")
                return
                
            # Checks if command is for a specific date
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            date_to_check = today  # Default to today
            
            if "tomorrow" in command:
                tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
                date_to_check = tomorrow.strftime("%Y-%m-%d")
            elif "next week" in command:
                next_week = datetime.datetime.now() + datetime.timedelta(days=7)
                date_to_check = next_week.strftime("%Y-%m-%d")
                
            # Filters events for the requested date
            events_on_date = [event for event in calendar_data["events"] 
                             if event["date"] == date_to_check]
            
            if events_on_date:
                date_str = "today" if date_to_check == today else date_to_check
                self.speak(f"You have {len(events_on_date)} events scheduled for {date_str}:")
                for i, event in enumerate(events_on_date, 1):
                    self.speak(f"{i}. {event['title']} at {event['time']}")
            else:
                date_str = "today" if date_to_check == today else date_to_check
                self.speak(f"You don't have any events scheduled for {date_str}.")
                
        except Exception as e:
            print(f"Calendar error: {e}")
            self.speak("I couldn't access your calendar at the moment.")

    def calculate(self, command):
        """Perform basic calculations"""
        try:
            # Extracts the math expression
            expression = None
            
            # Checks if command already contains a math expression
            if any(op in command for op in ["+", "-", "*", "/", "plus", "minus", "times", "divided by"]):
                # If it's a direct expression like "2 + 2"
                expression = command
            else:
                # Otherwise tries to extract after phrases like "calculate"
                for phrase in ["calculate", "compute", "what is"]:
                    if phrase in command:
                        expression = command.split(phrase, 1)[1].strip()
                        break
                        
            if not expression:
                self.speak("What would you like me to calculate?")
                return
                
            # Replaces words with symbols
            expression = expression.replace("plus", "+")
            expression = expression.replace("minus", "-")
            expression = expression.replace("times", "*")
            expression = expression.replace("multiplied by", "*")
            expression = expression.replace("divided by", "/")
            expression = expression.replace("to the power of", "**")
            
            # Removes words like "equal", "equals", "is"
            expression = expression.replace("equal", "")
            expression = expression.replace("equals", "")
            expression = expression.replace("is", "")
            
            # Removes any non-math characters
            expression = ''.join(c for c in expression if c.isdigit() or c in '+-*/().^ ')
            expression = expression.replace('^', '**')
            
            # Calculates the result
            result = eval(expression)
            
            # Formats the result
            if result == int(result):
                result = int(result)
            
            self.speak(f"The result is {result}")
        except Exception as e:
            print(f"Calculator error: {e}")
            self.speak("I couldn't calculate that. Please try a simpler expression.")

    def convert_currency(self, command):
        """Convert between currencies"""
        try:
            # Extracts amount and currencies
            amount = None
            from_currency = None
            to_currency = None
            
            # Extracts amount
            words = command.split()
            for i, word in enumerate(words):
                if word.replace('.', '').isdigit():
                    amount = float(word)
                    break
            
            # Common currencies
            currencies = {
                "dollar": "USD", "dollars": "USD", "usd": "USD",
                "euro": "EUR", "euros": "EUR", "eur": "EUR",
                "pound": "GBP", "pounds": "GBP", "gbp": "GBP",
                "yen": "JPY", "jpy": "JPY",
                "yuan": "CNY", "cny": "CNY",
                "rupee": "INR", "rupees": "INR", "inr": "INR"
            }
            
            # Extracts currencies
            for currency_name, code in currencies.items():
                if currency_name in command:
                    if "to" in command:
                        parts = command.split("to", 1)
                        if currency_name in parts[0] and from_currency is None:
                            from_currency = code
                        elif currency_name in parts[1] and to_currency is None:
                            to_currency = code
                    else:
                        if from_currency is None:
                            from_currency = code
                        elif to_currency is None and from_currency != code:
                            to_currency = code
            
            # If missing information, asks for it
            if amount is None:
                self.speak("What amount would you like to convert?")
                return
            if from_currency is None:
                self.speak("Which currency would you like to convert from?")
                return
            if to_currency is None:
                self.speak("Which currency would you like to convert to?")
                return
            
            # Uses a free currency API (be registracijos)
            url = f"https://open.er-api.com/v6/latest/{from_currency}"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200 and data["result"] == "success":
                # Gets the exchange rate
                rate = data["rates"][to_currency]
                converted_amount = amount * rate
                
                # Formats the result
                self.speak(f"{amount} {from_currency} is approximately {converted_amount:.2f} {to_currency}")
            else:
                self.speak("I couldn't get the current exchange rate. Please try again later.")
        except Exception as e:
            print(f"Currency conversion error: {e}")
            self.speak("I had trouble converting that currency. Please try again with a simpler request.")

    def define_word(self, command):
        """Look up the definition of a word"""
        try:
            # Extracts the word to define
            word = None
            for phrase in ["define", "definition of", "what does", "mean", "dictionary"]:
                if phrase in command:
                    parts = command.split(phrase, 1)
                    if len(parts) > 1:
                        word_part = parts[1] if phrase != "what does" else parts[1].split("mean", 1)[0]
                        word = word_part.strip().rstrip('?').strip()
                        break
            
            if not word:
                self.speak("What word would you like me to define?")
                return
                
            # Uses the Free Dictionary API
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    # Gets the first definition
                    first_entry = data[0]
                    if "meanings" in first_entry and len(first_entry["meanings"]) > 0:
                        meaning = first_entry["meanings"][0]
                        part_of_speech = meaning["partOfSpeech"]
                        if "definitions" in meaning and len(meaning["definitions"]) > 0:
                            definition = meaning["definitions"][0]["definition"]
                            self.speak(f"The word {word} is a {part_of_speech}. It means: {definition}")
                            return
                
                self.speak(f"I found information about {word}, but couldn't extract a clear definition.")
            else:
                self.speak(f"I couldn't find a definition for {word}.")
        except Exception as e:
            print(f"Dictionary error: {e}")
            self.speak(f"I had trouble looking up the definition of {word}.")


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
        
        # Initializes the speech engine
        assistant.engine = None
        assistant.speech_enabled = assistant.initialize_tts()
        
        # Starts listening for commands
        assistant.start_listening()
        return True
    except Exception as e:
        print(f"Error starting assistant: {e}")
        return False

@eel.expose
def stop_assistant():
    global assistant
    if assistant:
        assistant.stop_listening()
        return True
    return False


if __name__ == "__main__":
    # Initializes Eel with web directory
    eel.init('web')
    
    # Starts the Eel application
    eel.start('index.html', size=(800, 600))