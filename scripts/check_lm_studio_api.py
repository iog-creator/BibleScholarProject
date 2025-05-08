#!/usr/bin/env python3
"""
Simple check for LM Studio API connection.
Tests if the LM Studio API is accessible and returns valid responses.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.dspy")

# LM Studio API configuration
api_base = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
model_name = os.getenv("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")

print(f"Checking LM Studio API at {api_base} with model {model_name}")

# 1. Check models endpoint
try:
    models_response = requests.get(f"{api_base}/models")
    if models_response.status_code == 200:
        models_data = models_response.json()
        print(f"Models API accessible: {models_response.status_code}")
        print(f"Available models: {json.dumps(models_data, indent=2)[:200]}...")
    else:
        print(f"Models API error: {models_response.status_code}, {models_response.text}")
except Exception as e:
    print(f"Models API request failed: {e}")

# 2. Test chat completion API
try:
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "What is Genesis 1:1?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    chat_response = requests.post(
        f"{api_base}/chat/completions", 
        headers=headers,
        json=payload
    )
    
    if chat_response.status_code == 200:
        chat_data = chat_response.json()
        content = chat_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"Chat API accessible: {chat_response.status_code}")
        print(f"Response: {content[:200]}...")
    else:
        print(f"Chat API error: {chat_response.status_code}, {chat_response.text}")
except Exception as e:
    print(f"Chat API request failed: {e}")

# 3. Test embeddings API
try:
    embedding_model = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5@q8_0")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": embedding_model,
        "input": "Genesis 1:1: In the beginning God created the heavens and the earth."
    }
    
    embedding_response = requests.post(
        f"{api_base}/embeddings", 
        headers=headers,
        json=payload
    )
    
    if embedding_response.status_code == 200:
        embedding_data = embedding_response.json()
        embedding = embedding_data.get('data', [{}])[0].get('embedding', [])
        print(f"Embeddings API accessible: {embedding_response.status_code}")
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    else:
        print(f"Embeddings API error: {embedding_response.status_code}, {embedding_response.text}")
except Exception as e:
    print(f"Embeddings API request failed: {e}")

print("\nAPI check complete") 