"""
CodmetricBot (GUI) — Rule-Based Chatbot without internet dependencies
Features:
- Tkinter chat UI (scrollable, Enter-to-send, buttons for Send/Clear/Save)
- Smarter small-talk + FAQs (name, creator, thanks, bye, help)
- Date & time answers
- Safe math evaluator (e.g., "2+3*4", "2^8", "3.5 x 4")
- Graceful fallback for unknown inputs
NOTE: Weather/temperature fetching is intentionally removed.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import datetime
import re
import ast
import operator
import random

BOT_NAME = "CodmetricBot"
CREATOR_NAME = "Rohith"
ORG_NAME = "Codmetric"

# ------------------------ Safe Math Evaluator ------------------------
# Supports: +, -, *, /, //, %, **, parentheses, unary +/- and floats.
# Also accepts user-friendly "^" for power and "x" for multiply.
_ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Num):  # Py <3.8
        return node.n
    if isinstance(node, ast.Constant):  # Py 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed.")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        operand = _eval_ast(node.operand)
        return _ALLOWED_UNARY_OPS[type(node.op)](operand)
    if isinstance(node, ast.Expr):
        return _eval_ast(node.value)
    raise ValueError("Unsupported expression.")

def try_eval_math(text):
    # Quickly check if it *looks* like math
    candidate = text.strip().lower()
    # Accept friendly inputs: replace ^ with **, and 'x' with '*' when used like math
    candidate = candidate.replace("^", "**")
    candidate = re.sub(r"(?<=\d)\s*[x]\s*(?=\d)", "*", candidate)  # 3x4 -> 3*4

    # Only allow digits, operators, spaces, dot and parentheses
    if not re.fullmatch(r"[0-9\.\s\+\-\*\/\%\(\)]{1,1000}|[0-9\.\s\+\-\*\/\%\(\)\*]{1,1000}", candidate.replace("**", "*")):
        return None  # Not a pure math expression

    try:
        node = ast.parse(candidate, mode="eval")
        result = _eval_ast(node)
        return result
    except Exception:
        return None

# ------------------------ Core Chatbot Logic ------------------------
GREETINGS = ("hi", "hello", "hey", "hola", "hai")
BYE_WORDS = ("bye", "goodbye", "see you", "see ya", "cya", "quit", "exit")
THANKS = ("thanks", "thank you", "ty", "thx")
JOKE_LIST = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "I told my computer I needed a break, and it said: 'No problem, I’ll go to sleep.'",
    "There are 10 types of people in the world: those who understand binary and those who don’t.",
]
QUOTES = [
    "“Code is like humor. When you have to explain it, it’s bad.” — Cory House",
    "“First, solve the problem. Then, write the code.” — John Johnson",
    "“Simplicity is the soul of efficiency.” — Austin Freeman",
]

HELP_TEXT = (
    "You can try:\n"
    "• greetings (hi, hello)\n"
    "• who are you / your name\n"
    "• who created you\n"
    "• date / time\n"
    "• math: 2+3*4, 2^10, 3.5 x 4\n"
    "• tell me a joke / quote\n"
    "• clear / save / bye\n"
)

def generate_response(user_input: str) -> str:
    text = user_input.strip()
    low = text.lower()

    # 1) Quick commands
    if low in ("/help", "help", "commands"):
        return HELP_TEXT

    if low in ("clear", "/clear"):
        clear_chat()
        return "Chat cleared ✅"

    if low in ("save", "/save"):
        save_chat()
        return "Chat saved ✅"

    if any(g in low for g in GREETINGS):
        return random.choice([
            "Hello! 👋 How can I assist you today?",
            "Hi there! Ready when you are.",
            "Hey! What can I do for you?"
        ])

    if "how are you" in low:
        return random.choice([
            "I’m running at full speed ⚡ How about you?",
            "All systems green ✅ What’s up?",
            "Doing great! Thanks for asking 😊"
        ])

    if "your name" in low or "who are you" in low or "what is your name" in low or "what's your name" in low:
        return f"I’m {BOT_NAME}, your rule-based assistant."

    if "who created you" in low or "who made you" in low or "creator" in low:
        return f"I was created by {CREATOR_NAME} as part of the {ORG_NAME} AI Internship."

    if any(b in low for b in BYE_WORDS):
        # Optional: close the app after a short goodbye
        root.after(400, root.destroy)
        return "Goodbye! 👋 Have a great day."

    if any(t in low for t in THANKS):
        return "You're welcome! 🙌"

    # 2) Date / Time
    if "time" in low:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is ⏰ {now}"

    if "date" in low or "day" in low:
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is 📅 {today}"

    # 3) Weather/temperature intentionally removed
    if "weather" in low or "temperature" in low:
        return "Weather/temperature feature is disabled. Try time, date, math, jokes, or /help."

    # 4) Jokes / Quotes
    if "joke" in low:
        return random.choice(JOKE_LIST)
    if "quote" in low or "motivate" in low or "motivation" in low:
        return random.choice(QUOTES)

    # 5) Math evaluation (safe)
    math_result = try_eval_math(low)
    if math_result is not None:
        return f"Result = {math_result}"

    # 6) Some brand/context awareness
    if "codmetric" in low:
        return f"{ORG_NAME} focuses on practical AI learning and projects. Anything specific you’d like to explore?"

    if "intern" in low or "internship" in low or "offer letter" in low:
        return "Congrats on the internship! 🎉 If you need help with projects or docs, just tell me what you’re working on."

    # 7) Fallback
    return (
        "🤔 I didn’t quite get that.\n"
        "Try /help, or ask about time, date, a quick math expression, a joke, or who created me."
    )

# ------------------------ GUI Actions ------------------------
def send_message(event=None):
    user_text = entry.get()
    if not user_text.strip():
        return
    append_chat(f"You: {user_text}\n", "user")
    entry.delete(0, tk.END)

    bot_text = generate_response(user_text)
    append_chat(f"{BOT_NAME}: {bot_text}\n\n", "bot")
    chat_area.yview(tk.END)

def append_chat(text, tag=None):
    chat_area.configure(state="normal")
    if tag:
        chat_area.insert(tk.END, text, tag)
    else:
        chat_area.insert(tk.END, text)
    chat_area.configure(state="disabled")

def clear_chat():
    chat_area.configure(state="normal")
    chat_area.delete("1.0", tk.END)
    chat_area.configure(state="disabled")

def save_chat():
    try:
        content = chat_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("Save Chat", "Nothing to save yet.")
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chatlog_{ts}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Save Chat", f"Saved as {filename}")
    except Exception as e:
        messagebox.showerror("Save Chat", f"Could not save file: {e}")

# ------------------------ UI Setup ------------------------
root = tk.Tk()
root.title(f"{BOT_NAME} — Rule-Based Chatbot (No Weather)")
root.geometry("620x560")

chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), state="disabled")
chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
chat_area.tag_config("user", foreground="blue")
chat_area.tag_config("bot", foreground="green")

entry_frame = tk.Frame(root)
entry_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

entry = tk.Entry(entry_frame, font=("Arial", 12))
entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
entry.bind("<Return>", send_message)

btn_send = tk.Button(entry_frame, text="Send", command=send_message, font=("Arial", 12))
btn_send.pack(side=tk.LEFT, padx=5)

btn_clear = tk.Button(entry_frame, text="Clear", command=clear_chat, font=("Arial", 12))
btn_clear.pack(side=tk.LEFT, padx=5)

btn_save = tk.Button(entry_frame, text="Save", command=save_chat, font=("Arial", 12))
btn_save.pack(side=tk.LEFT, padx=5)

# Greeting
append_chat(f"{BOT_NAME}: Hello! 👋 Type /help to see what I can do.\n\n", "bot")

root.mainloop()