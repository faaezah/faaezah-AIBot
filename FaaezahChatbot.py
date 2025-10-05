import spacy
import requests
import random
from better_profanity import profanity
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("chat.html")
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    reply = chatbot_response(user_input)
    return {"reply": reply}

SERPAPI_KEY = "05e271957b72c791988993c97459e456f513a7495a77003c5dc78a9e349a3352"

try:
    nlp = spacy.load("en_core_web_md")
except Exception:
    nlp = spacy.load("en_core_web_sm")

profanity.load_censor_words()



def contains_violation(text):
    return profanity.contains_profanity(text)

def extract_intent(text):
    doc = nlp(text)
    action, topic = None, None
    for token in doc:
        if token.dep_ == "ROOT":
            action = token.lemma_
        if token.dep_ in ["dobj", "pobj", "nsubj", "attr"] and token.pos_ == "NOUN":
            topic = token.text
    return {"intent": action, "topic": topic}

#  Helps chatbot stay focused on only coral reef related questions and prevents it from drifting off
def is_about_coral(text):
    keywords = [
        "coral", "reef", "marine", "ocean", "bleaching", "sea",
        "aquatic", "ecosystem", "fish", "biodiversity", "algae",
        "climate", "conservation"
    ]
    return any(word in text.lower() for word in keywords)

# Update to make it stop cutting off messages with ellipiss from using SERPAPI
def get_coral_info(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()
    answer = (
        data.get("answer_box", {}).get("answer") or
        data.get("answer_box", {}).get("snippet") or
        data.get("organic_results", [{}])[0].get("snippet")
    )
    return answer or "Sorry, Can you please rephrase your question?"

def get_live_quiz(category):
    params = {
        "engine": "google",
        "q": f"{category} quiz for kids",
        "api_key": SERPAPI_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()
    result = data.get("organic_results", [{}])[0]
    snippet = result.get("snippet", "")
    title = result.get("title", "")
    link = result.get("link", "")

    answer = f"{title}: {snippet}\nRead more: {link}" if snippet else "Sorry, I couldn't find a complete answer."
    return answer


def is_confirmation(text):
    confirmations = ["yes", "yeah", "yep", "sure", "please", "go ahead", "okay", "ok"]
    return text.strip().lower() in confirmations

def random_Eco_tip():
    tips = [
        "🪄 Use reef-safe sunscreen to protect marine life.",
        "🪄 Say no to single-use plastics to keep oceans clean.",
        "🪄 Eat sustainable seafood to support healthy ecosystems.",
        "🪄 Reduce your carbon footprint to fight coral bleaching.",
        "🪄 Support ocean conservation groups to amplify your impact."
    ]
    return random.choice(tips)

def chatbot_response(text):
    if "ecology tip" in text or "tip" in text:
        return f"{random_Eco_tip()}"
    if "sorry" in text or "my apologies" in text:
        return f"No problem! How can I help you today?"
    if contains_violation(text):
        return "That message may violate guidelines. Let’s keep things kind and respectful."
    if is_confirmation(text):
        return "Awesome! Try outlining your thoughts or breaking the task into smaller steps."

    if text.strip().lower() in ["stop", "exit", "quit", "bye", "leave me alone"]:
        return "No problem! I’ll be here whenever you need me. Just click 💬 to reopen the chat."
    if is_about_coral(text):
        return get_coral_info(text)

    # If nothing matches, still try to answer with search
    return get_coral_info(text)


if __name__ == '__main__':
    app.run(debug=True)
