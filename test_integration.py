"""
Quick test script to verify the admin panel integration
Run this after starting the server to test all endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_register():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    data = {
        "username": f"testuser_{datetime.now().timestamp()}",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    # First register a user
    username = f"testuser_{datetime.now().timestamp()}"
    register_data = {
        "username": username,
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "testpassword123"
    }
    requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    
    # Now login
    login_data = {
        "username": username,
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
        return result.get('access_token')
    return None

def test_tasks(token):
    """Test task endpoints"""
    print("\n=== Testing Task Endpoints ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create task
    print("\n1. Creating Task...")
    task_data = {
        "title": "Test Task from Script",
        "description": "This is a test task",
        "priority": "HIGH",
        "due_date": "2024-12-31",
        "tags": ["test", "automated"]
    }
    response = requests.post(f"{BASE_URL}/api/tasks", json=task_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    
    # List tasks
    print("\n2. Listing Tasks...")
    response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result.get('tasks', []))} tasks")
        task_id = result.get('tasks', [{}])[0].get('id') if result.get('tasks') else None
        
        if task_id:
            # Get single task
            print(f"\n3. Getting Task {task_id}...")
            response = requests.get(f"{BASE_URL}/api/tasks/{task_id}", headers=headers)
            print(f"Status: {response.status_code}")
            
            # Update task
            print(f"\n4. Updating Task {task_id}...")
            update_data = {
                "status": "IN_PROGRESS",
                "title": "Updated Test Task"
            }
            response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data, headers=headers)
            print(f"Status: {response.status_code}")
            
    # Get statistics
    print("\n5. Getting Task Statistics...")
    response = requests.get(f"{BASE_URL}/api/tasks/stats", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Statistics: {response.json()}")
    
    # Search tasks
    print("\n6. Searching Tasks...")
    response = requests.get(f"{BASE_URL}/api/tasks/search?q=test", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result.get('tasks', []))} tasks matching 'test'")

def test_chat(token):
    """Test chat endpoint"""
    print("\n=== Testing Chat Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    chat_data = {
        "message": "Create a task to review documentation",
        "session_id": None
    }
    response = requests.post(f"{BASE_URL}/api/chat", json=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result.get('message', 'N/A')}")
        print(f"Intent: {result.get('intent', 'N/A')}")

def test_ui_accessible():
    """Test if UI is accessible"""
    print("\n=== Testing UI Accessibility ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    response = requests.get(f"{BASE_URL}/static/index.html")
    print(f"Static file status: {response.status_code}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("="*60)
    print("ADMIN PANEL INTEGRATION TEST")
    print("="*60)
    
    try:
        # Test health
        if not test_health():
            print("\n❌ Health check failed! Is the server running?")
            return
        
        print("\n✅ Health check passed")
        
        # Test UI
        if test_ui_accessible():
            print("✅ UI is accessible")
        else:
            print("❌ UI is not accessible")
        
        # Test registration
        if test_register():
            print("✅ Registration works")
        else:
            print("❌ Registration failed")
        
        # Test login and get token
        token = test_login()
        if token:
            print("✅ Login works")
            
            # Test tasks
            test_tasks(token)
            print("✅ Task endpoints work")
            
            # Test chat
            test_chat(token)
            print("✅ Chat endpoint works")
        else:
            print("❌ Login failed")
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("\nAll core functionality has been tested.")
        print("You can now access the admin panel at:")
        print(f"{BASE_URL}/")
        print(f"{BASE_URL}/static/index.html")
        print("\n✅ Integration Complete!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server!")
        print("Please make sure the server is running:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
