"""
tests/conftest.py
-----------------
Shared test data and fixtures for StreamVault unit tests.
Modeled on Lecture 2 tests/conftest.py.
"""

import json
from pathlib import Path
import pandas as pd

SAMPLE_CANDIDATE_CSV = """tmdb_id
603
278
-1
603

tt0468569
N/A
155
"""

SAMPLE_FRANCHISE_DETAILS = {
    "id": 155,
    "imdb_id": "tt0468569",
    "title": "The Dark Knight",
    "original_title": "The Dark Knight",
    "release_date": "2008-07-16",
    "status": "Released",
    "runtime": 152,
    "budget": 185000000,
    "revenue": 1004558444,
    "popularity": 123.45,
    "vote_average": 8.51,
    "vote_count": 30000,
    "original_language": "en",
    "belongs_to_collection": {
        "id": 263,
        "name": "The Dark Knight Collection",
    },
    "genres": [
        {"id": 18, "name": "Drama"},
        {"id": 28, "name": "Action"},
        {"id": 80, "name": "Crime"},
    ],
}

SAMPLE_STANDALONE_DETAILS = {
    "id": 278,
    "imdb_id": "tt0111161",
    "title": "The Shawshank Redemption",
    "original_title": "The Shawshank Redemption",
    "release_date": "1994-09-23",
    "status": "Released",
    "runtime": 142,
    "budget": 25000000,
    "revenue": 28341469,
    "popularity": 95.12,
    "vote_average": 8.73,
    "vote_count": 25000,
    "original_language": "en",
    "belongs_to_collection": None,
    "genres": [
        {"id": 18, "name": "Drama"},
        {"id": 80, "name": "Crime"},
    ],
}

SAMPLE_CREDITS = {
    "id": 155,
    "cast": [
        {
            "id": 3894,
            "name": "Christian Bale",
            "character": "Bruce Wayne / Batman",
            "order": 0,
            "popularity": 45.2,
            "known_for_department": "Acting",
        },
        {
            "id": 1810,
            "name": "Heath Ledger",
            "character": "Joker",
            "order": 1,
            "popularity": 38.4,
            "known_for_department": "Acting",
        },
    ],
    "crew": [
        {
            "id": 525,
            "name": "Christopher Nolan",
            "department": "Directing",
            "job": "Director",
            "popularity": 55.0,
        },
        {
            "id": 525,
            "name": "Christopher Nolan",
            "department": "Writing",
            "job": "Screenplay",
            "popularity": 55.0,
        },
    ],
}
