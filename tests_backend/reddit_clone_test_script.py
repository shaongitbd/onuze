#!/usr/bin/env python
import requests
import time
import json
import sys
import uuid
from urllib.parse import urljoin

# Base URL for the API
BASE_URL = "http://localhost:8000/"
API_URL = urljoin(BASE_URL, "api/v1/")

# Store tokens and IDs for different users
user1 = {"username": "community_owner", "email": "owner@example.com", "password": "Password123!"}
user2 = {"username": "poster_user", "email": "poster@example.com", "password": "Password123!"}
user3 = {"username": "commenter_user", "email": "commenter@example.com", "password": "Password123!"}

# Global variables to store created objects
community_id = None
flair_id = None
post_id = None
comment_id = None

def print_step(step):
    """Print a step with some formatting"""
    print("\n" + "="*80)
    print(f"STEP: {step}")
    print("="*80)

def register_user(user_data):
    """Register a new user"""
    # Correct endpoint based on Djoser default
    url = urljoin(API_URL, "auth/users/") 
    try:
        response = requests.post(
            url, 
            json={
                "username": user_data["username"],
                "email": user_data["email"],
                "password": user_data["password"],
                "re_password": user_data["password"] # Use re_password as required by Djoser settings
            }
        )
        
        if response.status_code == 201:
            print(f"✅ User {user_data['username']} registered successfully")
            return response.json()
        else:
            print(f"❌ Failed to register user {user_data['username']}")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Check if user already exists and continue
            if response.status_code == 400 and ("username already exists" in response.text.lower() or "email already exists" in response.text.lower()):
                print("User already exists, continuing...")
                return True
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def login_user(user_data):
    """Login a user and get token"""
    # Correct endpoint based on security/urls.py for token obtainment
    url = urljoin(API_URL, "auth/token/") 
    try:
        response = requests.post(
            url, 
            json={
                "username": user_data["username"],
                "email": user_data["email"],
                "password": user_data["password"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Simple JWT usually returns 'access' and 'refresh'
            # Djoser JWT views might return 'access'
            # Custom views might return 'token' or 'key'
            if "access" in data:
                token = data["access"] 
            elif "token" in data:
                token = data["token"]
            elif "key" in data:
                token = data["key"]
            else:
                # Fallback or handle error if no known token key is found
                print(f"❌ Login successful, but no token found in response for {user_data['username']}")
                print(f"Response keys: {list(data.keys())}")
                return None
                
            user_data["token"] = token
            print(f"✅ User {user_data['username']} logged in successfully")
            return token
        else:
            print(f"❌ Failed to login user {user_data['username']} at {url}")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def create_community(user_data):
    """Create a new community"""
    global community_id
    
    url = urljoin(API_URL, "communities/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        payload = {
            "name": f"TestCommunity_{uuid.uuid4().hex[:8]}",  # Add uniqueness
            "description": "A test community created by the script",
            "sidebar_content": "Welcome to our test community!",
            "is_private": False,
            "is_nsfw": False
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            data = response.json()
            community_id = data.get("id")
            print(f"✅ Community created successfully with ID: {community_id}")
            return community_id
        else:
            print("❌ Failed to create community")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def create_flair(user_data):
    """Create a flair for the community"""
    global flair_id
    
    url = urljoin(API_URL, f"communities/{community_id}/flairs/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.post(
            url, 
            headers=headers,
            json={
                "name": "Test Flair",
                "background_color": "#FF5700",
                "text_color": "#FFFFFF",
                "is_mod_only": False
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            flair_id = data.get("id")
            print(f"✅ Flair created successfully with ID: {flair_id}")
            return flair_id
        else:
            print("❌ Failed to create flair")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def join_community(user_data):
    """Join a community"""
    url = urljoin(API_URL, f"communities/{community_id}/join/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.post(url, headers=headers)
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ User {user_data['username']} joined the community successfully")
            return True
        else:
            print(f"❌ Failed to join community for user {user_data['username']}")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def create_post(user_data):
    """Create a post in the community"""
    global post_id
    
    url = urljoin(API_URL, "posts/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        payload = {
            "title": "Test Post from automated script",
            "content": "This is a test post created by the automated script",
            "community": community_id
        }
        
        # Add optional fields if they exist
        if flair_id:
            payload["flair"] = flair_id
            
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            data = response.json()
            post_id = data.get("id")
            print(f"✅ Post created successfully with ID: {post_id}")
            return post_id
        else:
            print("❌ Failed to create post")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try without flair if that might be the issue
            if flair_id and "flair" in payload:
                print("Trying again without flair...")
                del payload["flair"]
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code in [200, 201]:
                    data = response.json()
                    post_id = data.get("id")
                    print(f"✅ Post created successfully with ID: {post_id}")
                    return post_id
            
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def create_comment(user_data):
    """Create a comment on a post"""
    global comment_id
    
    url = urljoin(API_URL, "comments/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.post(
            url, 
            headers=headers,
            json={
                "post": post_id,
                "content": "This is a test comment created by the automated script"
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            comment_id = data.get("id")
            print(f"✅ Comment created successfully with ID: {comment_id}")
            return comment_id
        else:
            print("❌ Failed to create comment")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def edit_comment(user_data):
    """Edit a comment"""
    url = urljoin(API_URL, f"comments/{comment_id}/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.patch(
            url, 
            headers=headers,
            json={"content": "This is an edited test comment"}
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ Comment edited successfully")
            return True
        else:
            print("❌ Failed to edit comment")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def upvote_post(user_data):
    """Upvote a post"""
    url = urljoin(API_URL, f"votes/posts/{post_id}/vote/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.post(
            url, 
            headers=headers,
            json={"vote_type": "upvote"}
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ Post upvoted successfully")
            return True
        else:
            print("❌ Failed to upvote post")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def edit_post(user_data):
    """Edit a post"""
    url = urljoin(API_URL, f"posts/{post_id}/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.patch(
            url, 
            headers=headers,
            json={"content": "This is an edited test post content"}
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ Post edited successfully")
            return True
        else:
            print("❌ Failed to edit post")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def reply_to_comment(user_data):
    """Reply to a comment"""
    url = urljoin(API_URL, "comments/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.post(
            url, 
            headers=headers,
            json={
                "post": post_id,
                "parent": comment_id,
                "content": "This is a reply to the test comment"
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            reply_id = data.get("id")
            print(f"✅ Reply created successfully with ID: {reply_id}")
            return reply_id
        else:
            print("❌ Failed to create reply")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def lock_post(user_data):
    """Lock a post"""
    url = urljoin(API_URL, f"posts/{post_id}/lock/")
    try:
        headers = {"Authorization": f"Token {user_data['token']}"}
        response = requests.post(
            url, 
            headers=headers,
            json={"reason": "Locking this post for testing purposes"}
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ Post locked successfully")
            return True
        else:
            print("❌ Failed to lock post")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    try:
        # User 1: Create account, login, create community and flair
        print_step("Registering community owner (User 1)")
        if not register_user(user1):
            print("❌ Failed to register User 1. Exiting.")
            return
        
        print_step("Logging in as community owner (User 1)")
        if not login_user(user1):
            print("❌ Failed to login User 1. Exiting.")
            return
        
        print_step("Creating a community")
        if not create_community(user1):
            print("❌ Failed to create community. Exiting.")
            return
        
        print_step("Creating a flair")
        create_flair(user1)  # Continue even if flair creation fails
        
        # User 2: Create account, login, join community, create post
        print_step("Registering poster (User 2)")
        if not register_user(user2):
            print("❌ Failed to register User 2. Exiting.")
            return
        
        print_step("Logging in as poster (User 2)")
        if not login_user(user2):
            print("❌ Failed to login User 2. Exiting.")
            return
        
        print_step("User 2 joins the community")
        if not join_community(user2):
            print("❌ Failed to join community. Continuing anyway...")
        
        print_step("User 2 creates a post")
        if not create_post(user2):
            print("❌ Failed to create post. Exiting.")
            return
        
        # User 3: Create account, login, join community, comment on post
        print_step("Registering commenter (User 3)")
        if not register_user(user3):
            print("❌ Failed to register User 3. Exiting.")
            return
        
        print_step("Logging in as commenter (User 3)")
        if not login_user(user3):
            print("❌ Failed to login User 3. Exiting.")
            return
        
        print_step("User 3 joins the community")
        join_community(user3)  # Continue even if joining fails
        
        print_step("User 3 comments on the post")
        if not create_comment(user3):
            print("❌ Failed to create comment. Exiting.")
            return
        
        print_step("User 3 edits their comment")
        edit_comment(user3)  # Continue even if edit fails
        
        print_step("User 3 upvotes the post")
        upvote_post(user3)  # Continue even if upvote fails
        
        # Back to User 2: Edit post, reply to comment
        print_step("User 2 edits their post")
        edit_post(user2)  # Continue even if edit fails
        
        print_step("User 2 replies to the comment")
        reply_to_comment(user2)  # Continue even if reply fails
        
        # Back to User 1: Lock the post
        print_step("User 1 locks the post")
        lock_post(user1)  # Continue even if lock fails
        
        print("\n✅ Test script completed!")
        
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 