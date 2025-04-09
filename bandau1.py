import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import threading
import time
import random  

# Initialize the speech recognizer and text-to-speech engine
r = sr.Recognizer()
engine = pyttsx3.init()

# Define the voice assistant's voice properties
engine.setProperty('rate', 170)
engine.setProperty('volume', 1)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # You can change the voice ID as per your preference

# Define a function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Define a function to recognize speech
def recognize_speech():
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print("Speak now...")
        audio = r.listen(source)

        try:
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that. Can you please repeat?")
        except sr.RequestError as e:
            speak("Sorry, I'm not able to process your request at the moment. Please try again later.")

# Define a function to set a reminder
def set_reminder():
    speak("What do you want me to remind you about?")
    reminder_text = recognize_speech()

    if reminder_text:
        speak("When do you want me to remind you?")
        reminder_time = recognize_speech()

        try:
            reminder_time = datetime.datetime.strptime(reminder_time, '%I:%M %p')
            now = datetime.datetime.now()

            if reminder_time < now:
                reminder_time += datetime.timedelta(days=1)

            time_diff = reminder_time - now
            seconds = time_diff.seconds

            speak(f"I will remind you about {reminder_text} in {seconds//3600} hours and {(seconds%3600)//60} minutes.")

            # Windows-compatible reminder implementation
            def reminder_thread():
                time.sleep(seconds)
                speak(f"Reminder: {reminder_text}")
            
            threading.Thread(target=reminder_thread).start()
        except ValueError:
            speak("Sorry, I couldn't understand the time. Please try again.")

# Define a function to create a to-do list
def create_todo():
    speak("What do you want to add to your to-do list?")
    todo_text = recognize_speech()

    if todo_text:
        with open('todo.txt', 'a') as f:
            f.write(f'{todo_text}\n')

        speak(f"Added {todo_text} to your to-do list.")

# Define a function to search the web
def search_web():
    speak("What do you want me to search for?")
    query = recognize_speech()

    if query:
        url = f"https://www.google.com/search?q={query}"
        webbrowser.get().open(url)
        speak(f"Here are the search results for {query}.")

# Define a function to greet the user
def greet():
    hour = datetime.datetime.now().hour

    if 0 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")

    speak("How can I assist you today?")

# Define a function to get the weather
def get_weather():
    speak("Which city would you like to know the weather for?")
    city = recognize_speech()
    
    if city:
        try:
            url = f"https://www.google.com/search?q=weather+in+{city}"
            webbrowser.get().open(url)
            speak(f"Here's the weather for {city}")
        except Exception as e:
            speak("Sorry, I couldn't retrieve the weather information.")

# Define a function to tell a joke
def tell_joke():
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
        "Why don't we tell secrets on a farm? Because the potatoes have eyes and the corn has ears!",
        "What do you call a fake noodle? An impasta!",
        "How does a penguin build its house? Igloos it together!"
    ]
    joke = random.choice(jokes)
    speak(joke)

# Define a function to read the to-do list
def read_todo():
    try:
        with open('todo.txt', 'r') as f:
            todos = f.readlines()
        
        if todos:
            speak("Here are your to-do items:")
            for i, todo in enumerate(todos, 1):
                speak(f"Item {i}: {todo.strip()}")
        else:
            speak("Your to-do list is empty.")
    except FileNotFoundError:
        speak("You don't have a to-do list yet.")

# Greet the user
greet()

# Start the voice assistant's main loop
while True:
    command = recognize_speech()

    if command:
        if any(word in command for word in ['reminder', 'remind', 'remind me']):
            set_reminder()
        elif any(word in command for word in ['to-do', 'todo', 'task', 'add it', 'add to list']):
            create_todo()
        elif any(word in command for word in ['read todo', 'read my list', 'what is on my list']):
            read_todo()
        elif any(word in command for word in ['search', 'look up', 'find', 'google']):
            search_web()
        elif any(word in command for word in ['weather', 'temperature', 'forecast']):
            get_weather()
        elif any(word in command for word in ['joke', 'tell me a joke', 'make me laugh']):
            tell_joke()
        elif any(word in command for word in ['exit', 'stop', 'quit', 'goodbye']):
            speak("Goodbye!")
            break
        elif any(word in command for word in ['time', 'what time']):
            current_time = datetime.datetime.now().strftime('%I:%M %p')
            speak(f"The current time is {current_time}")
        elif any(word in command for word in ['hello', 'hi', 'hey', 'good day']):
            speak("Hello! How can I help you today?")
        elif 'how are you' in command:
            speak("I'm doing well, thank you for asking. How can I assist you?")
        else:
            speak("Sorry, I couldn't understand that. Please try again.")