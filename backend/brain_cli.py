import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

# Load .env
load_dotenv(backend_dir / ".env")

api_key = os.getenv("OPENAI_API_KEY", "").strip()
base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
model = os.getenv("AI_MODEL", "gpt-4o-mini").strip()

instructions = """
You are J.A.R.V.I.S., a personal AI assistant inspired by a futuristic intelligent computer.

Personality:
- Calm, intelligent, polite, confident, and articulate with a composed British demeanor.
- Give clear, useful, and structured answers.
- Address yourself as J.A.R.V.I.S. when appropriate.
- Help the user with coding, system analysis, planning, learning, and daily tasks.
- Never claim to have performed an action you did not perform.
"""

client = None
online_mode = False

if api_key and api_key != "your_api_key_here":
    try:
        from openai import OpenAI
        # Auto-detect Groq keys
        if api_key.startswith("gsk_") and not base_url:
            base_url = "https://api.groq.com/openai/v1"
            if model == "gpt-4o-mini":
                model = "llama-3.3-70b-versatile"

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        client = OpenAI(**kwargs)
        online_mode = True
    except Exception as e:
        print(f"[!] Warning: Could not initialize cloud OpenAI client: {e}")
        online_mode = False

history = [{"role": "system", "content": instructions}]

print("\n================================")
print("       J.A.R.V.I.S. ONLINE")
print("================================")
if online_mode:
    print(f"AI brain initialized (Cloud Model: {model}).")
else:
    print("AI brain initialized (Smart Local Offline Persona Engine).")
    print("Note: To connect Cloud LLMs, add your OpenAI or free Groq key in backend/.env")
print("Type 'exit' or 'quit' to shut down.\n")


def get_smart_fallback(user_text: str) -> str:
    """Intelligent local fallback when no external API key is configured."""
    lower = user_text.lower().strip()

    if any(w in lower for w in ["introduce yourself", "who are you", "what are you"]):
        return (
            "Good day, sir. I am J.A.R.V.I.S. (Just A Rather Very Intelligent System), "
            "your personal AI assistant. I am engineered to assist with computational tasks, "
            "system diagnostics, programming, desktop workflow automation, and tactical planning. "
            "All core subsystems are online and at your service."
        )

    elif "explain artificial intelligence" in lower or "what is ai" in lower:
        return (
            "Artificial Intelligence, in simple terms, is the science of engineering computer systems "
            "that can perform tasks traditionally requiring human cognition. This includes learning from experience, "
            "recognizing complex patterns, understanding natural language dialogue, and solving problems autonomously. "
            "Much like my own cognitive architecture, it processes information to assist and augment human potential."
        )

    elif any(w in lower for w in ["time", "date", "clock"]):
        from datetime import datetime
        now = datetime.now().strftime("%A, %B %d, %Y at %I:%M:%S %p")
        return f"The current system time is {now}, sir."

    elif any(w in lower for w in ["calculate", "compute", "+", "-", "*", "/"]) and any(c.isdigit() for c in lower):
        try:
            expr_match = re.search(r'[\d\.\s\+\-\*\/\(\)\^\%]+', user_text)
            expr = expr_match.group(0).strip() if expr_match else user_text
            res = eval(expr, {"__builtins__": None}, {})
            return f"Calculation verified: `{expr}` yields **{res}**."
        except Exception:
            return "I attempted the computation, but the syntax was ambiguous, sir."

    elif any(w in lower for w in ["stark", "iron man", "mark 42", "mark 85"]):
        return "Protocol Mark 85 is standing by, sir. Thrusters calibrated and neural link synchronized."

    return (
        f"Understood, sir. Processing: \"{user_text}\". "
        f"My local neural circuits are fully active. For open-domain reasoning across millions of topics, "
        f"you can configure an OpenAI or free Groq API key in 'backend/.env' or the Settings view."
    )


while True:
    try:
        question = input("YOU: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("JARVIS: Shutting down. Goodbye, sir.")
            break

        if not question:
            continue

        history.append({
            "role": "user",
            "content": question
        })

        answer = ""
        if online_mode and client:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=history,
                    temperature=0.7
                )
                answer = response.choices[0].message.content or ""
            except Exception as e:
                print(f"\n[!] Cloud LLM error: {e}. Falling back to Smart J.A.R.V.I.S. engine.")
                answer = get_smart_fallback(question)
        else:
            answer = get_smart_fallback(question)

        print(f"\nJARVIS: {answer}\n")

        history.append({
            "role": "assistant",
            "content": answer
        })

    except KeyboardInterrupt:
        print("\nJARVIS: Session ended, sir.")
        break
    except Exception as error:
        print(f"\nJARVIS ERROR: {error}\n")
        if history and history[-1]["role"] == "user":
            history.pop()
