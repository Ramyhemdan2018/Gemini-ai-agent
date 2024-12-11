import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from flask import Flask, render_template, request
import discord
from discord.ext import commands
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a special object to tell the bot what to listen for
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Initialize API keys from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def generate_response(prompt):
    try:
        # Create the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Return the text of the response
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return "Sorry, I'm experiencing technical difficulties."

def fetch_wikipedia_summary(topic):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('extract', 'No information found.')
    except requests.RequestException as e:
        logger.error(f"Wikipedia API Error: {e}")
        return "Failed to fetch information."

# Personality Module: Humor and Empathy
def personality_response(user_input):
    humor_prompts = ["tell me a joke", "make me laugh", "say something funny"]
    empathy_prompts = ["I'm sad", "I feel down", "cheer me up"]

    if any(prompt in user_input.lower() for prompt in humor_prompts):
        return generate_response("Tell a light-hearted joke.")
    elif any(prompt in user_input.lower() for prompt in empathy_prompts):
        return generate_response("Say something encouraging to lift someone's spirits.")
    else:
        return generate_response(user_input)

# Initialize Flask App
app = Flask(__name__)

# Text-Based Interaction: Chat Route
@app.route("/")
def home():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]
    response = personality_response(user_message)
    return {"response": response}

# Discord Bot Configuration
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ask(ctx, *, question):
    response = generate_response(question)
    await ctx.send(response)

# Contextual Memory for Multi-Turn Conversations
class Memory:
    def __init__(self):
        self.conversation_history = []

    def add_to_memory(self, user_input, bot_response):
        self.conversation_history.append({
            "user": user_input,
            "bot": bot_response
        })

    def get_context(self):
        return " ".join([
            f"User: {entry['user']} Bot: {entry['bot']}"
            for entry in self.conversation_history
        ])

memory = Memory()

# Main Loop
if __name__ == "__main__":
    try:
        # Conditional running based on environment
        if os.getenv('RUN_FLASK', 'False') == 'True':
            port = int(os.environ.get('PORT', 5000))
            app.run(host='0.0.0.0', port=port)
            app.run(debug=True)
        
        if os.getenv('RUN_DISCORD', 'False') == 'True':
            bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Startup Error: {e}")
 