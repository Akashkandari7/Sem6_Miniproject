import requests
import json
import os

BASE_URL = "http://127.0.0.1:5000/api"
TOKEN = None

def get_headers():
    return {"Authorization": f"Bearer {TOKEN}"}

def test_teacher_service():
    global TOKEN
    
    # 1. Login as teacher1
    print("Logging in as teacher1...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "teacher1@test.com",
        "password": "teacher123"
    })
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
    TOKEN = res.json()['access_token']
    
    # 2. Get subjects
    print("\nRequesting /api/teacher/subjects...")
    res = requests.get(f"{BASE_URL}/teacher/subjects", headers=get_headers())
    print(f"Status: {res.status_code}, Subjects: {[s['code'] for s in res.json()['data']]}")
    
    # 3. Manual Add (Success - TOC ID 1)
    print("\nAdding question manually for TOC (ID 1)...")
    res = requests.post(f"{BASE_URL}/teacher/questions", headers=get_headers(), json={
        "subject_id": 1,
        "text": "What is a finite automaton?",
        "question_type": "short",
        "blooms_level": "remember",
        "difficulty": "easy",
        "marks": 2
    })
    print(f"Status: {res.status_code}, Success: {res.json().get('success')}")
    
    # 4. Manual Add (Failure - CN ID 4)
    print("\nAttempting to add question for CN (ID 4 - Unauthorized)...")
    res = requests.post(f"{BASE_URL}/teacher/questions", headers=get_headers(), json={
        "subject_id": 4,
        "text": "Explain TCP/IP.",
        "question_type": "long",
        "blooms_level": "understand",
        "difficulty": "medium",
        "marks": 5
    })
    print(f"Status: {res.status_code}, Message: {res.json().get('message')}")
    if res.status_code == 403:
        print("CORRECT: Blocked from unauthorized subject.")

    # 5. AI Generate + Save (Success - DBMS ID 2)
    print("\nGenerating AI question for DBMS (ID 2)...")
    # Note: Using mock or real depending on environment
    res = requests.post(f"{BASE_URL}/teacher/questions/generate", headers=get_headers(), json={
        "subject_id": 2,
        "topic": "SQL Joins",
        "difficulty": "medium",
        "blooms_level": "apply",
        "question_type": "mcq",
        "marks": 1
    })
    print(f"Status: {res.status_code}")
    if res.status_code == 201:
        print(f"CORRECT: AI Question Generated and Saved. ID: {res.json()['data']['id']}")
        print(f"Question Text: {res.json()['data']['text'][:50]}...")
    else:
        print(f"AI Generation failed: {res.text}")

if __name__ == "__main__":
    test_teacher_service()
