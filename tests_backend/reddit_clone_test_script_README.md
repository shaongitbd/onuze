# Reddit Clone Test Script

This script automates testing of the Reddit Clone API by performing a series of actions as three different users, creating communities, posts, and comments.

## Prerequisites

1. Python 3.6 or higher
2. The `requests` library
3. Running Reddit Clone server at http://localhost:8000

## Installation

1. Install the required Python package:
   ```
   pip install requests
   ```

## Usage

1. Make sure your Reddit Clone server is running at http://localhost:8000
2. Run the script:
   ```
   python reddit_clone_test_script.py
   ```

## What the Script Does

The script performs the following actions in sequence:

1. **User 1** (Community Owner):
   - Registers a new account
   - Logs in
   - Creates a new community
   - Creates a flair for the community

2. **User 2** (Poster):
   - Registers a new account
   - Logs in
   - Joins the community
   - Creates a new post

3. **User 3** (Commenter):
   - Registers a new account
   - Logs in
   - Joins the community
   - Comments on User 2's post
   - Edits their comment
   - Upvotes User 2's post

4. **User 2** again:
   - Logs in again
   - Edits their post
   - Replies to User 3's comment

5. **User 1** again:
   - Logs in again
   - Locks User 2's post with a reason

## Troubleshooting

- If you see connection errors, make sure your Reddit Clone server is running
- If you see authorization errors, check if the API endpoints have changed
- If there are issues with specific actions, check the error messages for details

## Customization

You can modify the script to:
- Change user credentials in the user dictionaries at the top
- Modify the content of posts, comments, and other objects
- Add more actions or change the sequence 