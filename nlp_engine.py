import re
from collections import Counter
from trends import TRENDING_TOPICS

STOPWORDS = set([
    "the", "is", "in", "and", "to", "of", "a", "for", "on",
    "with", "that", "this", "it", "as", "at", "by", "an"
])

def extract_keywords(text, top_n=10):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    freq = Counter(filtered)
    return [word for word, _ in freq.most_common(top_n)]


def compute_trend_alignment(keywords):
    trending_lower = [t.lower() for t in TRENDING_TOPICS]
    overlap = set(keywords) & set(trending_lower)
    alignment_score = int((len(overlap) / len(trending_lower)) * 100) if trending_lower else 0
    return alignment_score, list(overlap)


def generate_trend_recommendation(score):
    if score > 50:
        return "Strong trend alignment. Consider amplifying trending keywords."
    elif score > 20:
        return "Moderate alignment. Add stronger trending angles."
    else:
        return "Low trend alignment. Consider incorporating current trending themes."