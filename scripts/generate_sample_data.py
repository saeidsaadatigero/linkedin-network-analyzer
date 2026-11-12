# scripts/generate_sample_data.py
"""Generate data/raw/profiles.json: exactly 10 SYNTHETIC LinkedIn-style profiles
belonging to ONE fictional organization. Fake profile_urls act only as IDs.

No scraping, no real people, no network access.
Some skill spellings are intentionally messy (e.g. 'ML', ' Python ') so the
normalizer has something to clean.

Run: python scripts/generate_sample_data.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

# Allow running as: python scripts/generate_sample_data.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RAW_DATA_PATH

ORG_NAME: str = "Nimbus Analytics"
PROFILE_COUNT: int = 10

# (id, name, headline, city, summary, current title, current start, previous job,
#  education, skills, interests)
PEOPLE: list[tuple] = [
    ("p01", "Elena Markovic", "CTO at Nimbus Analytics", "Berlin, Germany",
     "Engineering leader focused on scalable platforms and applied AI.",
     "Chief Technology Officer", "2021-06",
     ("VP Engineering", "Fjord Systems", "2015-03", "2021-05"),
     ("TU Berlin", "MSc", "Computer Science", 2008, 2010),
     ["Engineering Leadership", "System Architecture", "Cloud Strategy", "ML", "Hiring", "Roadmapping"],
     ["AI Strategy", "Engineering Culture", "Open Source"]),
    ("p02", "Daniel Reyes", "Head of AI at Nimbus Analytics", "Madrid, Spain",
     "Leads the AI team; NLP and MLOps practitioner.",
     "Head of AI", "2022-01",
     ("Senior ML Engineer", "BlueRiver Labs", "2017-09", "2021-12"),
     ("UPM Madrid", "MSc", "Artificial Intelligence", 2013, 2015),
     ["Machine Learning", "Python", "NLP", "Team Leadership", "MLOps", "PyTorch"],
     ["Language Models", "Mentoring", "Running"]),
    ("p03", "Sofia Lindqvist", "ML Engineer | Computer Vision", "Stockholm, Sweden",
     "Builds and ships computer vision models to production.",
     "ML Engineer", "2022-08",
     ("Data Scientist", "Fjord Systems", "2019-02", "2022-07"),
     ("KTH", "MSc", "Machine Learning", 2016, 2018),
     ["Python", "PyTorch", "ml", "Computer Vision", "MLOps", "Docker"],
     ["Computer Vision", "Photography", "Hiking"]),
    ("p04", "Omar Haddad", "NLP Engineer", "Amsterdam, Netherlands",
     "Works on transformers, retrieval and LLM applications.",
     "NLP Engineer", "2023-03",
     ("Research Engineer", "Lumen AI", "2020-06", "2023-02"),
     ("University of Amsterdam", "MSc", "Artificial Intelligence", 2018, 2020),
     [" Python ", "NLP", "Transformers", "PyTorch", "Machine Learning", "LangChain"],
     ["LLM Agents", "Chess", "Podcasts"]),
    ("p05", "Priya Nair", "Data Scientist | Analytics", "Dublin, Ireland",
     "Turns messy business data into models and dashboards.",
     "Data Scientist", "2022-04",
     ("Data Analyst", "Greenfield Retail", "2018-07", "2022-03"),
     ("Trinity College Dublin", "BSc", "Statistics", 2014, 2018),
     ["Python", "Pandas", "Statistics", "Machine Learning", "SQL", "Data Visualization"],
     ["Data Storytelling", "Cycling", "Open Data"]),
    ("p06", "Lukas Weber", "Engineering Manager, Backend", "Munich, Germany",
     "Manages the backend team; Django and PostgreSQL at scale.",
     "Engineering Manager", "2021-09",
     ("Senior Backend Engineer", "Fjord Systems", "2016-01", "2021-08"),
     ("LMU Munich", "BSc", "Informatics", 2011, 2015),
     ["Django", "PostgreSQL", "System Architecture", "Team Leadership", "Docker", "REST API"],
     ["Distributed Systems", "Coaching", "Board Games"]),
    ("p07", "Anna Kowalski", "Backend Engineer", "Warsaw, Poland",
     "Builds Django REST services with Redis and Celery.",
     "Backend Engineer", "2022-11",
     ("Software Engineer", "Vistula Soft", "2019-09", "2022-10"),
     ("Warsaw University of Technology", "BSc", "Computer Science", 2015, 2019),
     ["Python", "Django", "Postgres", "REST API", "Redis", "Celery"],
     ["API Design", "Climbing", "Clean Code"]),
    ("p08", "Tomas Silva", "DevOps / Platform Engineer", "Lisbon, Portugal",
     "Runs the platform: Kubernetes, CI/CD and observability.",
     "Platform Engineer", "2022-02",
     ("DevOps Engineer", "Atlantic Cloud", "2018-05", "2022-01"),
     ("University of Lisbon", "BSc", "Computer Engineering", 2014, 2018),
     ["Docker", "K8s", "CI CD", "Linux", "Terraform", "Prometheus"],
     ["Infrastructure as Code", "Surfing", "Observability"]),
    ("p09", "Mei Tanaka", "Product Manager", "London, United Kingdom",
     "Product manager who connects engineering, AI and design.",
     "Product Manager", "2021-11",
     ("Associate Product Manager", "Brightpath", "2018-03", "2021-10"),
     ("UCL", "MSc", "Management", 2015, 2017),
     ["Product Management", "Roadmapping", "User Research", "Agile", "Stakeholder Management", "SQL"],
     ["Product Strategy", "Design Thinking", "Travel"]),
    ("p10", "James Oconnor", "UX Designer", "Dublin, Ireland",
     "Designs data-heavy products people actually enjoy using.",
     "UX Designer", "2023-01",
     ("UI Designer", "Brightpath", "2019-06", "2022-12"),
     ("NCAD Dublin", "BA", "Visual Communication", 2015, 2019),
     ["UX", "Figma", "User Research", "Prototyping", "Design Systems", "Accessibility"],
     ["Typography", "Accessibility", "Cycling"]),
]

# Declared relations between the 10 people: owner -> [(target, relation)]
CONNECTIONS: dict[str, list[tuple[str, str]]] = {
    "p01": [("p09", "mentor")],
    "p02": [("p01", "reports_to"), ("p09", "colleague")],
    "p03": [("p02", "reports_to"), ("p02", "mentor"), ("p04", "colleague"), ("p08", "colleague")],
    "p04": [("p02", "reports_to"), ("p05", "colleague")],
    "p05": [("p02", "reports_to"), ("p03", "colleague"), ("p07", "colleague")],
    "p06": [("p01", "reports_to"), ("p07", "mentor"), ("p09", "colleague")],
    "p07": [("p06", "reports_to"), ("p08", "colleague")],
    "p08": [("p06", "reports_to")],
    "p09": [("p01", "reports_to"), ("p10", "mentor")],
    "p10": [("p09", "reports_to"), ("p07", "colleague")],
}

# Recent activity per person: (type, date, text, target_profile_id or None for own post)
ACTIVITY: dict[str, list[tuple[str, str, str, str | None]]] = {
    "p01": [("post", "2026-10-02", "Why we invest in a shared ML platform.", None),
            ("reaction", "2026-10-05", "Liked a post about the Q3 AI roadmap.", "p02"),
            ("comment", "2026-10-09", "Great product framing, thanks Mei.", "p09")],
    "p02": [("post", "2026-10-04", "Lessons from shipping our first LLM feature.", None),
            ("comment", "2026-10-06", "Nice results on the embeddings benchmark.", "p03"),
            ("reaction", "2026-10-07", "Liked a post about retrieval quality.", "p04"),
            ("comment", "2026-10-11", "Can we add a baseline for this?", "p05"),
            ("repost", "2026-10-12", "Reposted the ML platform post.", "p01")],
    "p03": [("post", "2026-10-03", "Fine-tuning a vision model on limited data.", None),
            ("comment", "2026-10-08", "The transformer demo is impressive.", "p04"),
            ("reaction", "2026-10-09", "Liked the LLM feature post.", "p02"),
            ("comment", "2026-10-13", "Happy to pair on the GPU deployment.", "p08")],
    "p04": [("post", "2026-10-01", "Building retrieval pipelines that actually work.", None),
            ("reaction", "2026-10-08", "Liked a post about vision fine-tuning.", "p03"),
            ("comment", "2026-10-10", "Great chart, very clear.", "p05"),
            ("reaction", "2026-10-12", "Liked the LLM feature post.", "p02")],
    "p05": [("post", "2026-10-05", "Churn analysis: what the data really says.", None),
            ("comment", "2026-10-07", "Could we expose this through the API?", "p07"),
            ("reaction", "2026-10-09", "Liked the LLM feature post.", "p02"),
            ("comment", "2026-10-14", "Good point about label noise.", "p03")],
    "p06": [("post", "2026-10-02", "How we keep Django queries fast.", None),
            ("comment", "2026-10-06", "Clean PR, thanks Anna.", "p07"),
            ("reaction", "2026-10-08", "Liked the Kubernetes rollout post.", "p08"),
            ("comment", "2026-10-10", "Aligned with the platform plan.", "p01"),
            ("reaction", "2026-10-13", "Liked the roadmap update.", "p09")],
    "p07": [("post", "2026-10-04", "Celery retries: patterns that saved us.", None),
            ("reaction", "2026-10-06", "Liked the Django queries post.", "p06"),
            ("comment", "2026-10-09", "Thanks for the zero-downtime tips.", "p08"),
            ("comment", "2026-10-12", "Let's connect the model output to the API.", "p05")],
    "p08": [("post", "2026-10-03", "Zero-downtime rollouts on Kubernetes.", None),
            ("comment", "2026-10-07", "Container sizes look good.", "p03"),
            ("reaction", "2026-10-08", "Liked the Celery retries post.", "p07"),
            ("repost", "2026-10-11", "Reposted the Django queries post.", "p06")],
    "p09": [("post", "2026-10-05", "Roadmap update: AI features for Q1.", None),
            ("comment", "2026-10-07", "Can we scope the NLP work for Q1?", "p02"),
            ("comment", "2026-10-08", "What is the API impact?", "p06"),
            ("reaction", "2026-10-10", "Liked the new design system post.", "p10"),
            ("reaction", "2026-10-11", "Liked the ML platform post.", "p01"),
            ("comment", "2026-10-13", "Love the churn insight.", "p05")],
    "p10": [("post", "2026-10-06", "Designing dashboards for non-technical users.", None),
            ("reaction", "2026-10-07", "Liked the roadmap update.", "p09"),
            ("comment", "2026-10-12", "Can we expose a clean endpoint for this view?", "p07")],
}


def build_profile(person: tuple) -> dict:
    """Map one person tuple to a raw profile dict with all required sections."""
    pid, name, headline, city, summary, title, start, prev, edu, skills, interests = person
    prev_title, prev_company, prev_start, prev_end = prev
    school, degree, field, edu_start, edu_end = edu
    number = pid[1:]
    return {
        "id": pid,
        "profile_url": f"https://www.linkedin.com/in/example-person-{number}",
        "basic_info": {
            "full_name": name,
            "headline": headline,
            "location": city,
            "summary": summary,
        },
        "experience": [
            {"title": title, "company": ORG_NAME, "start": start, "end": None,
             "description": f"{title} at {ORG_NAME}."},
            {"title": prev_title, "company": prev_company, "start": prev_start, "end": prev_end,
             "description": f"{prev_title} at {prev_company}."},
        ],
        "education": [
            {"school": school, "degree": degree, "field": field,
             "start_year": edu_start, "end_year": edu_end},
        ],
        "skills": skills,
        "interests": interests,
        "activity": [
            {"type": kind, "date": date, "text": text, "target_profile_id": target}
            for kind, date, text, target in ACTIVITY[pid]
        ],
        "connections": [
            {"profile_id": target, "relation": relation} for target, relation in CONNECTIONS[pid]
        ],
    }


def write_profiles(profiles: list[dict], path: Path = RAW_DATA_PATH) -> None:
    """Write the profiles list as indented UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=2, ensure_ascii=False)


def main() -> None:
    """Build PROFILE_COUNT synthetic profiles and write them to disk."""
    if len(PEOPLE) != PROFILE_COUNT:
        raise ValueError(f"Expected {PROFILE_COUNT} people, got {len(PEOPLE)}")
    profiles = [build_profile(person) for person in PEOPLE]
    write_profiles(profiles)
    print(f"Wrote {len(profiles)} synthetic profiles to {RAW_DATA_PATH}")


if __name__ == "__main__":
    main()