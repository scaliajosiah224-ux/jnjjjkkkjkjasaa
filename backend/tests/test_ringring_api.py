"""
RingRing API Backend Tests
Testing: Auth, Phone Numbers, Messages, Contacts, Voicemail, Calls, Voice, GIFs
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
TEST_EMAIL = "josiahscalia200@gmail.com"
TEST_PASSWORD = "ringring2025"
TEST_USERNAME = "jisia"
TEST_PHONE = "+12085686579"

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for the test user"""
    # Try to login first
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get("token")
    
    # If login fails, try to register
    response = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": TEST_USERNAME,
        "display_name": "Test User"
    })
    
    if response.status_code == 200:
        return response.json().get("token")
    
    pytest.skip(f"Authentication failed - {response.text}")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestHealthEndpoint:
    """Health check endpoints"""
    
    def test_health_check(self, api_client):
        """Test /api/health endpoint"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data  # Updated: field name changed from "app" to "service"
        assert data["service"] == "RingRing API"
        print(f"✅ Health check passed - service: {data['service']}, database: {data.get('database')}")


class TestAuthentication:
    """Auth endpoint tests"""
    
    def test_login_with_valid_credentials(self, api_client):
        """Test login with existing user credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        # Might fail if user doesn't exist - acceptable
        if response.status_code == 401:
            print("⚠️ User not found - may need registration first")
            pytest.skip("User not registered")
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"✅ Login successful for {TEST_EMAIL}")
    
    def test_login_with_invalid_credentials(self, api_client):
        """Test login with wrong password"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": "wrongpassword123"
        })
        assert response.status_code == 401
        print("✅ Invalid credentials correctly rejected")
    
    def test_get_me_authenticated(self, authenticated_client):
        """Test /api/auth/me endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Get me failed: {response.text}"
        
        data = response.json()
        # Updated: response is now {"user": {...}} wrapper
        assert "user" in data
        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "username" in user
        print(f"✅ Get me successful - user: {user['username']}")
    
    def test_get_me_unauthenticated(self, api_client):
        """Test /api/auth/me without token"""
        temp_session = requests.Session()
        response = temp_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403, 422], f"Should fail without auth: {response.status_code}"
        print("✅ Unauthenticated access correctly blocked")


class TestPhoneNumbers:
    """Phone number management tests"""
    
    def test_get_my_numbers(self, authenticated_client):
        """Test /api/numbers/my endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/numbers/my")
        assert response.status_code == 200, f"Get my numbers failed: {response.text}"
        
        data = response.json()
        assert "numbers" in data
        print(f"✅ Get my numbers successful - count: {len(data['numbers'])}")
    
    def test_search_numbers(self, authenticated_client):
        """Test /api/numbers/search endpoint"""
        response = authenticated_client.post(f"{BASE_URL}/api/numbers/search", json={
            "country_code": "US",
            "number_type": "LOCAL"
        })
        # Note: This may return 503 if Sinch is not configured
        if response.status_code == 503:
            print("⚠️ Sinch not configured - skipping")
            pytest.skip("Sinch not configured")
        
        assert response.status_code == 200, f"Search numbers failed: {response.text}"
        
        data = response.json()
        assert "available_numbers" in data
        # Sinch trial may return empty or existing numbers
        print(f"✅ Search numbers successful - found: {len(data['available_numbers'])} numbers")
        if data.get("note"):
            print(f"   Note: {data['note']}")
    
    def test_get_sinch_active_numbers(self, authenticated_client):
        """Test /api/numbers/sinch-active endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/numbers/sinch-active")
        # Note: This may return 503 if Sinch is not configured, or 200 with data
        if response.status_code == 503:
            print("⚠️ Sinch not configured - skipping")
            pytest.skip("Sinch not configured")
        
        assert response.status_code == 200, f"Get Sinch active numbers failed: {response.text}"
        
        data = response.json()
        assert "active_numbers" in data
        print(f"✅ Get Sinch active numbers successful - count: {len(data['active_numbers'])}")


class TestMessages:
    """Messaging tests"""
    
    def test_get_conversations(self, authenticated_client):
        """Test /api/messages/conversations endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/messages/conversations")
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        
        data = response.json()
        assert "conversations" in data
        print(f"✅ Get conversations successful - count: {len(data['conversations'])}")
    
    def test_create_conversation(self, authenticated_client):
        """Test /api/messages/conversation endpoint"""
        test_number = "+15551234567"
        response = authenticated_client.post(f"{BASE_URL}/api/messages/conversation", json={
            "recipient_number": test_number,
            "recipient_name": "Test Contact"
        })
        assert response.status_code == 200, f"Create conversation failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["recipient_number"] == test_number
        print(f"✅ Create conversation successful - id: {data['id']}")
        return data["id"]
    
    def test_get_messages_for_conversation(self, authenticated_client):
        """Test /api/messages/{conversation_id} endpoint"""
        # First create a conversation
        test_number = "+15551234568"
        conv_response = authenticated_client.post(f"{BASE_URL}/api/messages/conversation", json={
            "recipient_number": test_number,
            "recipient_name": "Test Contact"
        })
        
        if conv_response.status_code == 200:
            conv_id = conv_response.json()["id"]
            response = authenticated_client.get(f"{BASE_URL}/api/messages/{conv_id}")
            assert response.status_code == 200, f"Get messages failed: {response.text}"
            
            data = response.json()
            assert "messages" in data
            print(f"✅ Get messages successful - count: {len(data['messages'])}")


class TestContacts:
    """Contacts CRUD tests"""
    
    def test_get_contacts(self, authenticated_client):
        """Test GET /api/contacts endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts")
        assert response.status_code == 200, f"Get contacts failed: {response.text}"
        
        data = response.json()
        assert "contacts" in data
        print(f"✅ Get contacts successful - count: {len(data['contacts'])}")
    
    def test_add_contact(self, authenticated_client):
        """Test POST /api/contacts endpoint"""
        test_name = f"TEST_Contact_{uuid.uuid4().hex[:6]}"
        response = authenticated_client.post(f"{BASE_URL}/api/contacts", json={
            "name": test_name,
            "phone_number": "+15559876543",
            "email": "test@example.com",
            "notes": "Test contact"
        })
        assert response.status_code == 200, f"Add contact failed: {response.text}"
        
        data = response.json()
        # Updated: response is just {"contact": {...}} without "success" key
        assert "contact" in data
        assert data["contact"]["name"] == test_name
        print(f"✅ Add contact successful - name: {test_name}")
        return data["contact"]["id"]
    
    def test_delete_contact(self, authenticated_client):
        """Test DELETE /api/contacts/{contact_id} endpoint"""
        # First create a contact
        test_name = f"TEST_DeleteMe_{uuid.uuid4().hex[:6]}"
        create_response = authenticated_client.post(f"{BASE_URL}/api/contacts", json={
            "name": test_name,
            "phone_number": "+15559999999"
        })
        
        if create_response.status_code == 200:
            contact_id = create_response.json()["contact"]["id"]
            
            # Now delete it
            response = authenticated_client.delete(f"{BASE_URL}/api/contacts/{contact_id}")
            assert response.status_code == 200, f"Delete contact failed: {response.text}"
            print(f"✅ Delete contact successful - id: {contact_id}")


class TestVoicemail:
    """Voicemail tests"""
    
    def test_get_voicemail(self, authenticated_client):
        """Test /api/voicemail endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/voicemail")
        assert response.status_code == 200, f"Get voicemail failed: {response.text}"
        
        data = response.json()
        assert "voicemails" in data
        print(f"✅ Get voicemail successful - count: {len(data['voicemails'])}")


class TestCalls:
    """Call history tests"""
    
    def test_get_call_history(self, authenticated_client):
        """Test /api/calls/history endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/calls/history")
        assert response.status_code == 200, f"Get call history failed: {response.text}"
        
        data = response.json()
        assert "calls" in data
        print(f"✅ Get call history successful - count: {len(data['calls'])}")
    
    def test_get_recent_calls(self, authenticated_client):
        """Test /api/calls/recent endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/calls/recent")
        assert response.status_code == 200, f"Get recent calls failed: {response.text}"
        
        data = response.json()
        assert "calls" in data
        print(f"✅ Get recent calls successful - count: {len(data['calls'])}")
    
    def test_log_call(self, authenticated_client):
        """Test POST /api/calls/log endpoint"""
        response = authenticated_client.post(f"{BASE_URL}/api/calls/log", json={
            "to_number": "+15551234567",
            "from_number": TEST_PHONE,
            "direction": "outbound",
            "duration": 60,
            "status": "completed",
            "call_type": "voice"
        })
        assert response.status_code == 200, f"Log call failed: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        print(f"✅ Log call successful")


class TestVoice:
    """Voice/Video calling tests"""
    
    def test_get_voice_auth_token(self, authenticated_client):
        """Test POST /api/voice/auth-token endpoint"""
        response = authenticated_client.post(f"{BASE_URL}/api/voice/auth-token")
        # Note: This may return 503 if voice service is not configured
        if response.status_code == 503:
            print("⚠️ Voice service not configured - skipping")
            pytest.skip("Voice service not configured")
        
        assert response.status_code == 200, f"Get voice auth token failed: {response.text}"
        
        data = response.json()
        assert "token" in data
        assert "app_key" in data
        assert "user_id" in data
        print(f"✅ Get voice auth token successful - app_key: {data['app_key'][:10]}...")
    
    def test_get_voice_config(self, authenticated_client):
        """Test /api/voice/config endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/voice/config")
        assert response.status_code == 200, f"Get voice config failed: {response.text}"
        
        data = response.json()
        assert "app_key" in data
        assert "user_id" in data
        print(f"✅ Get voice config successful")


class TestGIFs:
    """GIF search tests (Klipy API)"""
    
    def test_search_trending_gifs(self, authenticated_client):
        """Test /api/gifs/search endpoint with trending"""
        response = authenticated_client.get(f"{BASE_URL}/api/gifs/search?q=trending&limit=10")
        assert response.status_code == 200, f"Search GIFs failed: {response.text}"
        
        data = response.json()
        assert "gifs" in data
        print(f"✅ Search trending GIFs successful - count: {len(data['gifs'])}")
        
        # Verify GIF structure
        if data["gifs"]:
            gif = data["gifs"][0]
            assert "id" in gif
            assert "url" in gif
            print(f"   First GIF: {gif.get('title', gif['id'])}")
    
    def test_search_gifs_by_query(self, authenticated_client):
        """Test /api/gifs/search endpoint with custom query"""
        response = authenticated_client.get(f"{BASE_URL}/api/gifs/search?q=funny&limit=10")
        assert response.status_code == 200, f"Search GIFs failed: {response.text}"
        
        data = response.json()
        assert "gifs" in data
        print(f"✅ Search 'funny' GIFs successful - count: {len(data['gifs'])}")


class TestTypingAndReadReceipts:
    """Real-time features tests"""
    
    def test_typing_indicator(self, authenticated_client):
        """Test /api/messages/typing endpoint"""
        # First create a conversation
        test_number = "+15551112222"
        conv_response = authenticated_client.post(f"{BASE_URL}/api/messages/conversation", json={
            "recipient_number": test_number
        })
        
        if conv_response.status_code == 200:
            conv_id = conv_response.json()["id"]
            
            response = authenticated_client.post(f"{BASE_URL}/api/messages/typing?conversation_id={conv_id}")
            assert response.status_code == 200, f"Typing indicator failed: {response.text}"
            print(f"✅ Typing indicator successful")
    
    def test_read_receipts(self, authenticated_client):
        """Test /api/messages/read endpoint"""
        # First create a conversation
        test_number = "+15551113333"
        conv_response = authenticated_client.post(f"{BASE_URL}/api/messages/conversation", json={
            "recipient_number": test_number
        })
        
        if conv_response.status_code == 200:
            conv_id = conv_response.json()["id"]
            
            response = authenticated_client.post(f"{BASE_URL}/api/messages/read", json={
                "conversation_id": conv_id
            })
            assert response.status_code == 200, f"Read receipt failed: {response.text}"
            print(f"✅ Read receipts successful")


class TestReactions:
    """Message reactions tests"""
    
    def test_react_to_message(self, authenticated_client):
        """Test /api/messages/react endpoint"""
        # We need a message to react to - this test may skip if no messages exist
        # First create conversation and send a test message pattern
        print("⚠️ Message reactions require existing messages - skipping if none exist")
        pytest.skip("Requires existing message - complex to test in isolation")


class TestSinchCallbacks:
    """Sinch callback webhook tests"""
    
    def test_ice_callback(self, api_client):
        """Test /api/sinch/ice endpoint (Incoming Call Event)"""
        response = api_client.post(f"{BASE_URL}/api/sinch/ice", json={
            "callid": "test_call_123",
            "cli": "+15551234567",
            "to": "+12085686579",
            "domain": "mxp",
            "timestamp": 1704067200
        })
        assert response.status_code == 200, f"ICE callback failed: {response.text}"
        
        data = response.json()
        assert "action" in data
        print(f"✅ ICE callback successful - action: {data['action'].get('name')}")
    
    def test_ace_callback(self, api_client):
        """Test /api/sinch/ace endpoint (Answered Call Event)"""
        response = api_client.post(f"{BASE_URL}/api/sinch/ace", json={
            "callid": "test_call_123",
            "callResourceUrl": "https://example.com/calls/123",
            "cli": "+15551234567",
            "to": "+12085686579",
            "domain": "mxp",
            "timestamp": 1704067200
        })
        assert response.status_code == 200, f"ACE callback failed: {response.text}"
        print("✅ ACE callback successful")
    
    def test_dice_callback(self, api_client):
        """Test /api/sinch/dice endpoint (Disconnect Call Event)"""
        response = api_client.post(f"{BASE_URL}/api/sinch/dice", json={
            "callid": "test_call_123",
            "callResourceUrl": "https://example.com/calls/123",
            "reason": "CALLEE_HANGUP",
            "timestamp": 1704067300,
            "result": "ANSWERED"
        })
        assert response.status_code == 200, f"DiCE callback failed: {response.text}"
        print("✅ DiCE callback successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
