#!/usr/bin/env python3
"""
RingRing Backend API Tests
Tests all backend endpoints according to the review request
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime

# Get backend URL from frontend .env
FRONTEND_ENV_PATH = "/app/frontend/.env"
try:
    with open(FRONTEND_ENV_PATH, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.strip().split('=', 1)[1]
                break
        else:
            BACKEND_URL = "http://localhost:8001"
except:
    BACKEND_URL = "http://localhost:8001"

# Test configuration
BASE_URL = f"{BACKEND_URL}/api"
TEST_USER = {
    "email": "testuser@ringring.com",
    "username": "ringtest2025", 
    "password": "ringpass123",
    "display_name": "Ring Test User"
}

class TestResults:
    def __init__(self):
        self.results = []
        self.token = None
        self.user_id = None
        self.claimed_number = None
        self.contact_id = None
        self.conversation_id = None
        self.message_id = None
        
    def add_result(self, test_name, success, details, response_data=None):
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        })
        
    def print_summary(self):
        print("\n" + "="*70)
        print("RINGRING BACKEND TEST RESULTS SUMMARY")
        print("="*70)
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        # Print detailed results
        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{i:2d}. {status} - {result['test']}")
            if result["details"]:
                print(f"    Details: {result['details']}")
            if not result["success"] and result.get("response_data"):
                print(f"    Response: {json.dumps(result['response_data'], indent=6)[:200]}...")
            print()

async def make_request(session, method, endpoint, json_data=None, headers=None):
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        async with session.request(method, url, json=json_data, headers=headers, timeout=30) as resp:
            try:
                response_data = await resp.json()
            except:
                response_data = {"raw_response": await resp.text()}
            
            return {
                "status": resp.status,
                "data": response_data,
                "success": 200 <= resp.status < 300
            }
    except Exception as e:
        return {
            "status": 0,
            "data": {"error": str(e)},
            "success": False
        }

async def test_health_check(session, results):
    """Test 1: Health check endpoint"""
    print("Testing health check...")
    
    response = await make_request(session, "GET", "/health")
    
    if response["success"] and response["data"].get("status") == "healthy":
        results.add_result("Health Check", True, "Endpoint working correctly", response["data"])
    else:
        results.add_result("Health Check", False, f"Health check failed: {response['data']}", response["data"])

async def test_user_registration(session, results):
    """Test 2: User registration"""
    print("Testing user registration...")
    
    response = await make_request(session, "POST", "/auth/register", TEST_USER)
    
    if response["success"] and response["data"].get("token"):
        results.token = response["data"]["token"]
        results.user_id = response["data"]["user"]["id"]
        results.add_result("User Registration", True, "Successfully registered new user", {
            "user_id": results.user_id,
            "has_token": bool(results.token)
        })
    else:
        results.add_result("User Registration", False, f"Registration failed: {response['data']}", response["data"])

async def test_user_login(session, results):
    """Test 3: User login"""
    print("Testing user login...")
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    response = await make_request(session, "POST", "/auth/login", login_data)
    
    if response["success"] and response["data"].get("token"):
        # Use login token for subsequent tests
        results.token = response["data"]["token"]
        results.add_result("User Login", True, "Successfully logged in", {
            "has_token": bool(results.token)
        })
    else:
        results.add_result("User Login", False, f"Login failed: {response['data']}", response["data"])

async def test_auth_me(session, results):
    """Test 4: Auth me endpoint"""
    print("Testing auth me...")
    
    if not results.token:
        results.add_result("Auth Me", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    response = await make_request(session, "GET", "/auth/me", headers=headers)
    
    if response["success"] and response["data"].get("id"):
        results.add_result("Auth Me", True, "Successfully retrieved user info", {
            "user_id": response["data"]["id"],
            "email": response["data"].get("email")
        })
    else:
        results.add_result("Auth Me", False, f"Auth me failed: {response['data']}", response["data"])

async def test_number_search(session, results):
    """Test 5: Number search"""
    print("Testing number search...")
    
    if not results.token:
        results.add_result("Number Search", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    search_data = {
        "country_code": "US",
        "number_type": "LOCAL"
    }
    
    response = await make_request(session, "POST", "/numbers/search", search_data, headers)
    
    if response["success"]:
        available_numbers = response["data"].get("available_numbers", [])
        results.add_result("Number Search", True, f"Search returned {len(available_numbers)} numbers", {
            "count": len(available_numbers),
            "has_sinch_number": any("+12085686579" in str(num) for num in available_numbers)
        })
    else:
        results.add_result("Number Search", False, f"Number search failed: {response['data']}", response["data"])

async def test_number_claim(session, results):
    """Test 6: Number claim"""
    print("Testing number claim...")
    
    if not results.token:
        results.add_result("Number Claim", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    claim_data = {
        "phone_number": "+12085686579"
    }
    
    response = await make_request(session, "POST", "/numbers/claim", claim_data, headers)
    
    if response["success"]:
        results.claimed_number = "+12085686579"
        results.add_result("Number Claim", True, "Successfully claimed Sinch number", response["data"])
    else:
        # If already claimed, try to get it from my numbers
        my_numbers_response = await make_request(session, "GET", "/numbers/my", headers=headers)
        if my_numbers_response["success"]:
            numbers = my_numbers_response["data"].get("numbers", [])
            sinch_number = next((n for n in numbers if n.get("phone_number") == "+12085686579"), None)
            if sinch_number:
                results.claimed_number = "+12085686579"
                results.add_result("Number Claim", True, "Number already claimed (acceptable)", {
                    "message": "Number was already in user's account"
                })
            else:
                results.add_result("Number Claim", False, f"Claim failed and number not in account: {response['data']}", response["data"])
        else:
            results.add_result("Number Claim", False, f"Claim failed: {response['data']}", response["data"])

async def test_my_numbers(session, results):
    """Test 7: My numbers"""
    print("Testing my numbers...")
    
    if not results.token:
        results.add_result("My Numbers", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    response = await make_request(session, "GET", "/numbers/my", headers=headers)
    
    if response["success"]:
        numbers = response["data"].get("numbers", [])
        results.add_result("My Numbers", True, f"Retrieved {len(numbers)} numbers", {
            "count": len(numbers),
            "numbers": [n.get("phone_number") for n in numbers]
        })
    else:
        results.add_result("My Numbers", False, f"My numbers failed: {response['data']}", response["data"])

async def test_add_contact(session, results):
    """Test 8: Add contact"""
    print("Testing add contact...")
    
    if not results.token:
        results.add_result("Add Contact", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    contact_data = {
        "name": "Test Contact",
        "phone_number": "+15555550001"
    }
    
    response = await make_request(session, "POST", "/contacts", contact_data, headers)
    
    if response["success"] and response["data"].get("contact"):
        results.contact_id = response["data"]["contact"]["id"]
        results.add_result("Add Contact", True, "Successfully added contact", {
            "contact_id": results.contact_id,
            "name": response["data"]["contact"]["name"]
        })
    else:
        results.add_result("Add Contact", False, f"Add contact failed: {response['data']}", response["data"])

async def test_get_contacts(session, results):
    """Test 9: Get contacts"""
    print("Testing get contacts...")
    
    if not results.token:
        results.add_result("Get Contacts", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    response = await make_request(session, "GET", "/contacts", headers=headers)
    
    if response["success"]:
        contacts = response["data"].get("contacts", [])
        results.add_result("Get Contacts", True, f"Retrieved {len(contacts)} contacts", {
            "count": len(contacts)
        })
    else:
        results.add_result("Get Contacts", False, f"Get contacts failed: {response['data']}", response["data"])

async def test_sms_send(session, results):
    """Test 10: SMS send"""
    print("Testing SMS send...")
    
    if not results.token:
        results.add_result("SMS Send", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    sms_data = {
        "to_number": "+15555550001",
        "message": "Hello from RingRing API test!"
    }
    
    response = await make_request(session, "POST", "/messages/send", sms_data, headers)
    
    # SMS may fail due to Sinch test mode restrictions, but should create message record
    if response["success"] or (response["data"].get("message") and response["data"]["message"].get("id")):
        message_created = bool(response["data"].get("message", {}).get("id"))
        success_status = response["data"].get("success", False)
        
        results.add_result("SMS Send", True, 
            f"Message record created (Sinch success: {success_status})", {
            "message_created": message_created,
            "sinch_success": success_status,
            "error": response["data"].get("error") if not success_status else None
        })
    else:
        results.add_result("SMS Send", False, f"SMS send failed: {response['data']}", response["data"])

async def test_get_conversations(session, results):
    """Test 11: Get conversations"""
    print("Testing get conversations...")
    
    if not results.token:
        results.add_result("Get Conversations", False, "No token available from previous tests")
        return
    
    headers = {"Authorization": f"Bearer {results.token}"}
    response = await make_request(session, "GET", "/messages/conversations", headers=headers)
    
    if response["success"]:
        conversations = response["data"].get("conversations", [])
        results.add_result("Get Conversations", True, f"Retrieved {len(conversations)} conversations", {
            "count": len(conversations)
        })
    else:
        results.add_result("Get Conversations", False, f"Get conversations failed: {response['data']}", response["data"])

async def run_all_tests():
    """Run all backend tests"""
    print(f"Starting RingRing Backend API Tests")
    print(f"Backend URL: {BASE_URL}")
    print("=" * 50)
    
    results = TestResults()
    
    # Use aiohttp session for all requests
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # Run tests in sequence
            await test_health_check(session, results)
            await test_user_registration(session, results)
            await test_user_login(session, results)
            await test_auth_me(session, results)
            await test_number_search(session, results)
            await test_number_claim(session, results)
            await test_my_numbers(session, results)
            await test_add_contact(session, results)
            await test_get_contacts(session, results)
            await test_sms_send(session, results)
            await test_get_conversations(session, results)
            
        except Exception as e:
            print(f"Test execution error: {e}")
            results.add_result("Test Execution", False, f"Unexpected error: {e}")
    
    # Print summary
    results.print_summary()
    
    # Return results for further analysis
    return results

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())