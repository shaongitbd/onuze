#!/usr/bin/env python
"""
Test script for uploading images to the Reddit Clone API.
Generates a simple test image and uploads it to the API.
"""
import os
import sys
import requests
import json
from PIL import Image, ImageDraw
import io

# Configuration
API_URL = "http://localhost:8000/api/v1/uploads/images/"
TOKEN = "your_jwt_token_here"  # Replace with your actual JWT token

def generate_test_image():
    """Generate a simple test image with some text and shapes."""
    # Create a 500x300 white image
    img = Image.new('RGB', (500, 300), color=(255, 255, 255))
    
    # Get a drawing context
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes and text
    draw.rectangle([(50, 50), (450, 250)], outline=(0, 0, 0), width=2)
    draw.ellipse([(100, 100), (400, 200)], outline=(255, 0, 0), width=2)
    draw.text((200, 150), "Test Image", fill=(0, 0, 255))
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

def upload_image(image_data, image_type="post"):
    """Upload an image to the API."""
    headers = {
        "Authorization": f"JWT {TOKEN}"
    }
    
    files = {
        "image": ("test_image.png", image_data, "image/png")
    }
    
    data = {
        "type": image_type
    }
    
    try:
        response = requests.post(API_URL, headers=headers, files=files, data=data)
        
        # Print detailed info about the request and response
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
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
    print("Generating test image...")
    image_data = generate_test_image()
    
    print("\nUploading image...")
    upload_image(image_data)

if __name__ == "__main__":
    main() 