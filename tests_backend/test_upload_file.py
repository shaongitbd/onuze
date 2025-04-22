#!/usr/bin/env python
"""
Test script for uploading existing image files to the Reddit Clone API.
"""
import os
import sys
import requests
import argparse

# Configuration
API_URL = "http://localhost:8000/api/v1/uploads/images/"
TOKEN = "your_jwt_token_here"  # Replace with your actual JWT token

def upload_image_file(file_path, image_type="post"):
    """Upload an image file to the API."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
    
    headers = {
        "Authorization": f"JWT {TOKEN}"
    }
    
    with open(file_path, 'rb') as img_file:
        file_name = os.path.basename(file_path)
        
        files = {
            "image": (file_name, img_file, f"image/{file_path.split('.')[-1]}")
        }
        
        data = {
            "type": image_type
        }
        
        try:
            print(f"Uploading {file_path}...")
            response = requests.post(API_URL, headers=headers, files=files, data=data)
            
            # Print detailed info about the request and response
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                print("\nUpload Successful!")
                print(f"Image URL: {result['url']}")
                return result['url']
            else:
                print("\nUpload Failed!")
                try:
                    print(f"Error: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Upload an image to the Reddit Clone API")
    parser.add_argument("file", help="Path to the image file")
    parser.add_argument("--type", choices=["post", "community", "profile"], 
                        default="post", help="Image type (default: post)")
    
    args = parser.parse_args()
    
    upload_image_file(args.file, args.type)

if __name__ == "__main__":
    main() 