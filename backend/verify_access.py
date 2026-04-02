import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_teacher_access():
    # 1. Login as teacher1
    print("Logging in as teacher1...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "teacher1@test.com",
        "password": "teacher123"
    })
    
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
        
    token = login_res.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get my questions
    print("\nRequesting /questions/my-subjects...")
    res = requests.get(f"{BASE_URL}/questions/my-subjects", headers=headers)
    
    if res.status_code == 200:
        data = res.json()
        print(f"Success: {data['success']}")
        print(f"Count: {data['count']}")
        subject_ids_seen = set(q['subject_id'] for q in data['data'])
        print(f"Subject IDs seen in list: {subject_ids_seen}")
        
        # Verify only Subject IDs 1 and 2 are seen
        if all(sid in [1, 2] for sid in subject_ids_seen):
            print("CORRECT: Only assigned subjects (IDs 1, 2) are visible.")
        else:
            print(f"ERROR: Unexpected subject IDs found: {subject_ids_seen}")
    else:
        print(f"Failed to get questions: {res.text}")

    # 3. Try to access CN question (ID 88, Subject ID 4) directly
    print("\nAttempting to access CN question (ID 88) directly...")
    res = requests.get(f"{BASE_URL}/questions/88", headers=headers)
    
    if res.status_code == 403:
        print("CORRECT: Access denied (403 Forbidden).")
        print(f"Error message: {res.json()['message']}")
    elif res.status_code == 200:
        print(f"ERROR: Expected 403 but got 200. Question Subject ID: {res.json()['question']['subject_id']}")
    else:
        print(f"ERROR: Got status code {res.status_code}: {res.text}")

if __name__ == "__main__":
    test_teacher_access()
