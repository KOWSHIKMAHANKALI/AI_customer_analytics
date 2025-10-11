import os
import sys

# Test Gemini API key
try:
    import google.generativeai as genai
    
    # Read the API key from secrets  
    api_key = "AIzaSyBQ1Q28PzWO0X_lenMhtpfIJE8JlYQJLRI"
    print(f"API Key loaded: {api_key[:20]}...")
    
    genai.configure(api_key=api_key)
    
    # First, list available models
    print("\n🔍 Available models:")
    try:
        models = genai.list_models()
        for model in models:
            if hasattr(model, 'name'):
                print(f"  - {model.name}")
                if hasattr(model, 'supported_generation_methods'):
                    print(f"    Supports: {model.supported_generation_methods}")
    except Exception as e:
        print(f"Could not list models: {e}")
    
    # Test with gemini-2.0-flash (latest stable)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Test simple query
    response = model.generate_content("Hello, can you say 'API is working'?")
    print(f"\n✅ Response: {response.text}")
    print("✅ Gemini API is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()