import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def load_metrics():
    with open(os.path.join(DATA_DIR, 'metrics.json'), 'r') as f:
        return json.load(f)

def load_feedback():
    with open(os.path.join(DATA_DIR, 'feedback.json'), 'r') as f:
        return json.load(f)

def load_release_notes():
    with open(os.path.join(DATA_DIR, 'release_notes.txt'), 'r') as f:
        return f.read()
