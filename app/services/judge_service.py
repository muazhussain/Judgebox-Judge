import requests

BASE_URL = "http://localhost:3000/api/v1"

def get_problem(problem_id):
    url = f"{BASE_URL}/problems/{problem_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching problem with ID {problem_id}: {e}")
        return None

def get_test_cases(problem_id):
    url = f"{BASE_URL}/test-cases"
    try:
        response = requests.get(url, params={"problemId": problem_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching test cases for problem ID {problem_id}: {e}")
        return None
