#!/usr/bin/env python3
"""
UPSC Sarthi — Daily Current Affairs Updater
Fetches RSS feeds from PIB, The Hindu, Indian Express, etc.,
filters for UPSC-relevant articles, categorizes by subject,
generates Hindi summary, and outputs articles.json.

Runs via GitHub Actions daily at 6:00 AM IST.
"""

import feedparser
import json
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================
# RSS FEED SOURCES
# ============================================================
FEEDS = [
    # PIB (Press Information Bureau) — English
    {"url": "https://pib.gov.in/RSS/RssMain.aspx?Mod=All", "source": "PIB", "lang": "en"},
    # The Hindu — National
    {"url": "https://www.thehindu.com/news/national/feeder/default.rss", "source": "The Hindu", "lang": "en"},
    # The Hindu — Business
    {"url": "https://www.thehindu.com/business/Economy/feeder/default.rss", "source": "The Hindu", "lang": "en"},
    # Indian Express
    {"url": "https://indianexpress.com/feed/", "source": "Indian Express", "lang": "en"},
    # DownToEarth — Environment
    {"url": "https://www.downtoearth.org.in/rss.xml", "source": "DownToEarth", "lang": "en"},
    # ISRO
    {"url": "https://www.isro.gov.in/rss.xml", "source": "ISRO", "lang": "en"},
]

# ============================================================
# UPSC KEYWORD FILTERS — Articles must contain at least one
# ============================================================
UPSC_KEYWORDS = [
    # Polity & Governance
    "parliament", "constitution", "supreme court", "high court", "amendment",
    "lok sabha", "rajya sabha", "election", "judiciary", "president",
    "governor", "cabinet", "ordinance", "bill", "policy", "committee",
    "rti", "right to information", "transparency", "accountability",
    "fundamental right", "directive principle", "federalism", "panchayat",
    "municipal", "governance", "bureaucracy", "ias", "civil service",
    # Economy
    "rbi", "repo rate", "gdp", "inflation", "fiscal", "monetary",
    "budget", "tax", "gst", "msme", "startup", "banking", "npl",
    "current account deficit", "fiscal deficit", "trade deficit",
    "employment", "unemployment", "labour", "psu", "disinvestment",
    "subsidy", "poverty", "inclusive growth", "digital payment",
    "upi", "financial inclusion", "nabard", "sidbi", "sebi",
    # International Relations
    "india", "foreign policy", "summit", "g20", "brics", "wto",
    "united nations", "un security council", "bilateral", "treaty",
    "trade agreement", "fta", "asean", "saarc", "quad", "nato",
    "diplomatic", "embassy", "consulate", "geopolitics", "border",
    # Environment
    "climate", "environment", "pollution", "emission", "carbon",
    "renewable", "solar", "wind", "hydrogen", "biodiversity",
    "wildlife", "forest", "conservation", "ecology", "wetland",
    "national park", "sanctuary", "cop", "paris agreement",
    "sustainable", "green", "clean energy", "ev", "electric vehicle",
    # Science & Tech
    "isro", "space", "satellite", "chandrayaan", "gaganyaan", "mars",
    "nuclear", "ai", "artificial intelligence", "quantum", "biotechnology",
    "genome", "crispr", "vaccine", "drug", "clinical trial",
    "cyber", "data protection", "5g", "semiconductor", "robotics",
    # Social Issues
    "education", "neet", "health", "scheme", "welfare", "women",
    "child", "sc", "st", "minority", "reservation", " caste",
    "population", "migration", "urbanization", "slum", "literacy",
    "midday meal", "icds", "anganwadi", "education policy", "nep",
    # Security
    "defence", "military", "army", "navy", "air force", "terror",
    "cyber security", "internal security", "naxal", "insurgency",
    "border", "drdo", "missile", "tejas", "submarine",
]

# ============================================================
# CATEGORY CLASSIFICATION
# ============================================================
CATEGORY_KEYWORDS = {
    "polity": ["parliament", "constitution", "supreme court", "high court",
               "amendment", "lok sabha", "rajya sabha", "election", "judiciary",
               "president", "governor", "cabinet", "ordinance", "bill", "policy",
               "rti", "transparency", "accountability", "fundamental right",
               "directive principle", "federalism", "panchayat", "municipal",
               "governance", "bureaucracy", "civil service"],
    "economy": ["rbi", "repo rate", "gdp", "inflation", "fiscal", "monetary",
                "budget", "tax", "gst", "msme", "startup", "banking",
                "fiscal deficit", "trade deficit", "employment", "unemployment",
                "labour", "disinvestment", "subsidy", "poverty", "inclusive growth",
                "upi", "financial inclusion", "nabard", "sidbi", "sebi"],
    "ir": ["foreign policy", "summit", "g20", "brics", "wto",
           "united nations", "bilateral", "treaty", "trade agreement", "fta",
           "asean", "saarc", "quad", "diplomatic", "embassy", "geopolitics"],
    "environment": ["climate", "environment", "pollution", "emission", "carbon",
                    "renewable", "solar", "wind", "hydrogen", "biodiversity",
                    "wildlife", "forest", "conservation", "ecology", "wetland",
                    "national park", "cop", "paris agreement", "sustainable",
                    "green energy", "clean energy", "ev"],
    "scitech": ["isro", "space", "satellite", "chandrayaan", "gaganyaan",
                "nuclear", "ai", "artificial intelligence", "quantum",
                "biotechnology", "genome", "crispr", "vaccine", "cyber",
                "data protection", "5g", "semiconductor", "robotics"],
    "schemes": ["scheme", "yojana", "mission", "pradhan mantri", "pm-",
               "welfare", "subsidy", "midday meal", "icds", "anganwadi",
               "education policy", "nep", "reservation", "sustainable"],
    "security": ["defence", "military", "army", "navy", "air force",
                 "terror", "cyber security", "internal security", "naxal",
                 "insurgency", "border", "drdo", "missile"],
    "social": ["education", "health", "women", "child", "minority",
               "caste", "population", "migration", "urbanization",
               "literacy", "social justice", "human rights"],
}

# ============================================================
# IMPORTANCE SCORING
# ============================================================
HIGH_IMPORTANCE_KEYWORDS = [
    "constitutional", "supreme court", "parliament", "amendment",
    "bill passed", "ordinance", "rbi", "policy", "scheme launched",
    "summit", "g20", "brics", "climate", "isro", "mission",
    "agreement signed", "treaty", "national security",
]


def classify_category(text: str) -> str:
    """Classify article into UPSC subject category."""
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in text_lower)
    if not scores or max(scores.values()) == 0:
        return "polity"  # default
    return max(scores, key=scores.get)


def determine_importance(text: str) -> str:
    """Determine if article is High or Medium importance."""
    text_lower = text.lower()
    score = sum(1 for kw in HIGH_IMPORTANCE_KEYWORDS if kw in text_lower)
    return "High" if score >= 2 else "Medium"


def determine_relevance(text: str, category: str) -> dict:
    """Determine Prelims/Mains relevance."""
    text_lower = text.lower()
    prelims_keywords = ["definition", "fact", "data", "report", "index",
                        "ranking", "census", "article", "schedule",
                        "amendment", "act", "scheme"]
    mains_keywords = ["analysis", "impact", "challenge", "issue", "critic",
                      "reform", "policy", "governance", "development",
                      "evaluation", "examine", "discuss"]
    has_prelims = any(kw in text_lower for kw in prelims_keywords)
    has_mains = any(kw in text_lower for kw in mains_keywords)
    return {"prelims": has_prelims or True, "mains": has_mains or True}


def get_gs_papers(category: str) -> list:
    """Map category to GS papers."""
    mapping = {
        "polity": ["GS-2"],
        "economy": ["GS-3"],
        "ir": ["GS-2"],
        "environment": ["GS-3", "GS-1"],
        "scitech": ["GS-3", "GS-1"],
        "schemes": ["GS-2", "GS-3"],
        "security": ["GS-3"],
        "social": ["GS-1", "GS-2"],
    }
    return mapping.get(category, ["GS-3"])


def get_syllabus_points(category: str) -> list:
    """Return relevant syllabus points for the category."""
    syllabus = {
        "polity": [
            "GS-2: Functions and responsibilities of the Union and the States",
            "GS-2: Parliament and State legislatures",
            "GS-2: Separation of powers between various organs",
        ],
        "economy": [
            "GS-3: Indian Economy and issues relating to planning, mobilization of resources",
            "GS-3: Inclusive growth and issues arising from it",
            "GS-3: Government budgeting",
        ],
        "ir": [
            "GS-2: India and its neighborhood- relations",
            "GS-2: Important International institutions, agencies and fora",
        ],
        "environment": [
            "GS-3: Conservation, environmental pollution and degradation",
            "GS-3: Environmental impact assessment",
        ],
        "scitech": [
            "GS-3: Science and Technology- developments and their applications",
            "GS-3: Achievements of Indians in science & technology",
        ],
        "schemes": [
            "GS-2: Welfare schemes for vulnerable sections",
            "GS-3: Government policies and interventions",
        ],
        "security": [
            "GS-3: Linkages between development and spread of extremism",
            "GS-3: Basics of cyber security",
            "GS-3: Role of external state and non-state actors",
        ],
        "social": [
            "GS-1: Population and associated issues",
            "GS-2: Issues relating to development and management of Social Sector/Services",
        ],
    }
    return syllabus.get(category, ["GS-3: General awareness"])


def generate_summary_hindi(title: str, summary: str) -> str:
    """Generate a Hindi summary of the article.

    In production, this would call a translation API (e.g., Google Translate,
    Sarvam AI, or Bhashini). For GitHub Actions without API keys,
    we generate a structured summary in Hindi using keyword mapping.
    """
    # This is a simplified approach — maps key English terms to Hindi
    # In production, integrate with Sarvam AI translate API or Bhashini
    term_map = {
        "parliament": "संसद",
        "constitution": "संविधान",
        "supreme court": "सुप्रीम कोर्ट",
        "amendment": "संशोधन",
        "bill": "विधेयक",
        "policy": "नीति",
        "scheme": "योजना",
        "election": "चुनाव",
        "government": "सरकार",
        "president": "राष्ट्रपति",
        "prime minister": "प्रधानमंत्री",
        "cabinet": "मंत्रिमंडल",
        "rbi": "RBI",
        "gdp": "GDP",
        "inflation": "मुद्रास्फीति",
        "economy": "अर्थव्यवस्था",
        "climate": "जलवायु",
        "environment": "पर्यावरण",
        "defence": "रक्षा",
        "security": "सुरक्षा",
        "isro": "ISRO",
        "space": "अंतरिक्ष",
        "technology": "प्रौद्योगिकी",
        "education": "शिक्षा",
        "health": "स्वास्थ्य",
        "development": "विकास",
        "reform": "सुधार",
        "agriculture": "कृषि",
        "farmer": "किसान",
        "treaty": "संधि",
        "agreement": "समझौता",
        "summit": "शिखर सम्मेलन",
        "bilateral": "द्विपक्षीय",
    }

    # Take first 300 chars of summary for a concise version
    concise = summary[:500] if len(summary) > 500 else summary
    concise = re.sub(r'<[^>]+>', '', concise)  # strip HTML tags
    concise = concise.strip()

    # Simple translation: replace known terms
    result = concise
    for en, hi in term_map.items():
        result = re.sub(r'\b' + re.escape(en) + r'\b', hi, result, flags=re.IGNORECASE)

    # If the result is mostly still English, prepend a Hindi intro
    hindi_intro = "यह लेख UPSC के दृष्टिकोण से महत्वपूर्ण है। "
    return hindi_intro + result


def is_upsc_relevant(text: str) -> bool:
    """Check if article contains UPSC-relevant keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in UPSC_KEYWORDS)


def parse_date(entry):
    """Parse date from feed entry."""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    except Exception:
        pass
    try:
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


def generate_analysis(title: str, summary: str, category: str, source: str) -> dict:
    """Generate detailed analysis sections (संदर्भ and प्रमुख बिंदु)."""
    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
    clean_summary = clean_summary[:1000]  # limit length

    # Extract key sentences (sentences with important keywords)
    sentences = clean_summary.split('. ')
    key_sentences = [s for s in sentences if len(s) > 30][:5]

    analysis_hi = f"संदर्भ: {clean_summary[:300]}...\n\nप्रमुख बिंदु:\n"
    for i, s in enumerate(key_sentences, 1):
        analysis_hi += f"• {s.strip()}\n"

    analysis_en = f"Reference: {clean_summary[:300]}...\n\nKey Points:\n"
    for i, s in enumerate(key_sentences, 1):
        analysis_en += f"• {s.strip()}\n"

    return {"analysis_hi": analysis_hi, "analysis_en": analysis_en}


def main():
    print("=" * 60)
    print("UPSC Sarthi — Daily Current Affairs Updater")
    print(f"Run time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    articles = []

    for feed_info in FEEDS:
        url = feed_info["url"]
        source = feed_info["source"]
        print(f"\nFetching: {source} ({url})")

        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                print(f"  ⚠️  Feed error: {feed.bozo_exception}")
                continue

            print(f"  Found {len(feed.entries)} entries")

            for entry in feed.entries[:20]:  # limit per feed
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                link = entry.get("link", "")
                pub_date = parse_date(entry)

                # Combine title + summary for filtering
                full_text = f"{title} {summary}"

                # Filter: must be UPSC-relevant
                if not is_upsc_relevant(full_text):
                    continue

                # Strip HTML from summary
                clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                if len(clean_summary) < 50:
                    clean_summary = title  # use title if summary too short

                # Classify
                category = classify_category(full_text)
                importance = determine_importance(full_text)
                relevance = determine_relevance(full_text, category)
                gs_papers = get_gs_papers(category)
                syllabus = get_syllabus_points(category)
                subjects_map = {
                    "polity": ["Polity", "Governance"],
                    "economy": ["Economy"],
                    "ir": ["International Relations"],
                    "environment": ["Environment"],
                    "scitech": ["Science & Tech"],
                    "schemes": ["Schemes", "Governance"],
                    "security": ["Security"],
                    "social": ["Social Issues"],
                }
                subjects = subjects_map.get(category, [category.title()])

                # Generate analysis
                analysis = generate_analysis(title, clean_summary, category, source)

                # Generate Hindi summary
                summary_hi = generate_summary_hindi(title, clean_summary)

                # Generate article ID (hash of title+link for dedup)
                article_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()[:12]

                # Format date for display
                try:
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    date_display = dt.strftime("%d %b %Y")
                except Exception:
                    date_display = datetime.now().strftime("%d %b %Y")

                article = {
                    "id": article_id,
                    "date": date_display,
                    "iso_date": pub_date,
                    "category": category,
                    "source": source,
                    "importance": importance,
                    "gs_papers": gs_papers,
                    "subjects": subjects,
                    "prelims": relevance["prelims"],
                    "mains": relevance["mains"],
                    "syllabus": syllabus,
                    "title_en": title,
                    "title_hi": title,  # Will be translated by API in production
                    "summary_en": clean_summary[:500],
                    "summary_hi": summary_hi,
                    "analysis_hi": analysis["analysis_hi"],
                    "analysis_en": analysis["analysis_en"],
                    "link": link,
                }

                # Dedup check
                if not any(a["id"] == article_id for a in articles):
                    articles.append(article)

        except Exception as e:
            print(f"  ❌ Error fetching {source}: {e}")
            continue

    # Sort by date (newest first)
    articles.sort(key=lambda a: a.get("iso_date", ""), reverse=True)

    # Keep top 50 articles
    articles = articles[:50]

    print(f"\n{'=' * 60}")
    print(f"Total UPSC-relevant articles collected: {len(articles)}")
    print(f"Categories: { {a['category'] for a in articles} }")
    print(f"{'=' * 60}")

    # Load existing articles and merge (keep last 7 days)
    output_path = Path(__file__).parent / "data" / "articles.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_articles = []
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_articles = data.get("articles", [])
        except Exception:
            pass

    # Merge: new articles + existing (dedup by ID)
    all_ids = {a["id"] for a in articles}
    for old_a in existing_articles:
        if old_a["id"] not in all_ids:
            articles.append(old_a)
            all_ids.add(old_a["id"])

    # Keep only last 200 articles
    articles = articles[:200]

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "last_updated_ist": (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).strftime("%d %B %Y, %I:%M %p IST"),
        "total_articles": len(articles),
        "articles": articles,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Articles saved to {output_path}")
    print(f"   Last updated: {output['last_updated_ist']}")
    print(f"   Total articles: {output['total_articles']}")


if __name__ == "__main__":
    main()
