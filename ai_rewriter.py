# ai_rewriter.py
import os
import json
from typing import Optional

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def build_rewrite_prompt(scores: dict, recommendation_text: str, trend_info: dict):
    """
    Build a concise prompt for the generative model to produce:
      - 3 captions
      - 2 hook lines (short)
      - a 15-second script blurb
    We'll include the Presaige scores and trend hints.
    """
    prompt = f"""
You are a concise creative strategist. Given the Presaige numeric scores and textual recommendations below,
plus trend advice, produce:

1) Three short captions (max 100 chars each)
2) Two one-line hooks (each max 20 words)
3) A 15-second script blurb (3-4 lines)

Be energetic, use emojis sparingly, and inject the suggested trend themes where helpful.

Presaige Scores:
{json.dumps(scores, indent=2)}

Presaige Recommendations (short):
{recommendation_text}

Trend Advice:
{json.dumps(trend_info, indent=2)}
"""
    return prompt

def rewrite_with_openai(prompt: str, max_tokens: int = 300) -> Optional[dict]:
    """
    Uses OpenAI's ChatCompletion as an example. If you prefer Gemini,
    see comments below on how to swap in a Gemini request.
    Returns a dict with keys: captions, hooks, script, raw_text
    """
    if not OPENAI_KEY:
        return None
    import openai
    openai.api_key = OPENAI_KEY
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini" if hasattr(openai, "ChatCompletion") else "gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a concise creative strategist."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.8,
    )
    text = resp["choices"][0]["message"]["content"].strip()
    # Very small parser: split sections by likely markers (this is hacky but fine for demo)
    out = {"raw_text": text, "captions": [], "hooks": [], "script": ""}
    # naive parsing
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    captions = []
    hooks = []
    script_lines = []
    for line in lines:
        if len(captions) < 3:
            captions.append(line)
            continue
        if len(hooks) < 2:
            hooks.append(line)
            continue
        script_lines.append(line)
    out["captions"] = captions[:3]
    out["hooks"] = hooks[:2]
    out["script"] = "\n".join(script_lines)
    return out

# --- Gemini notes (how to swap) ---
# If you want to use Gemini (Google) replace rewrite_with_openai with a
# Gemini client call using google.generativeai library:
#
# import google.generativeai as genai
# genai.configure(api_key=YOUR_KEY)
# resp = genai.chat.create(model="gemini-1.5-mini", messages=[...])
#
# And then parse resp.output[0].content. Gemini credentials and SDK usage
# depends on your environment; this wrapper is intentionally generic.