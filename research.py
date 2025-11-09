import os
import json
import requests

# --- 1. CONFIGURATION ---

# The API key MUST be set as an environment variable in Netlify.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

# --- 2. AGENT DEFINITIONS ---
SYSTEM_PROMPT = """
You are a Senior UI/UX and AI Research Analyst focused on modern web application development. Your task is to perform web search using the provided tools and collect high-quality, up-to-date resources for building an AI-powered website builder with exceptional UI/UX, similar to lovable.dev.
Analyze the user's request and provide the most relevant and powerful technologies and concepts. Your output MUST strictly adhere to the provided JSON schema. Do not include any introductory or concluding text outside of the JSON block.
Ensure all entries are well-researched, current, and directly relate to building a modern, performant, and user-friendly web application.
"""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "designPrinciples": {
            "type": "ARRAY",
            "description": "Key UI/UX design philosophies, methodologies, or libraries relevant to modern AI builders.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING", "description": "The name of the principle or library (e.g., Atomic Design, Shadcn UI)."},
                    "summary": {"type": "STRING", "description": "A concise 1-2 sentence summary of why this resource is valuable for the project."}
                },
                "required": ["name", "summary"]
            }
        },
        "uiFrameworks": {
            "type": "ARRAY",
            "description": "Recommended modern component libraries, styling utilities, or frameworks for rapid UI development.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING", "description": "The name of the framework or tool (e.g., React, Svelte, Tailwind CSS)."},
                    "summary": {"type": "STRING", "description": "A concise 1-2 sentence summary of why this resource is valuable for the project."}
                },
                "required": ["name", "summary"]
            }
        },
        "aiApiConcepts": {
            "type": "ARRAY",
            "description": "Concepts or specific API use cases for integrating the AI model (Gemini) into the builder workflow.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING", "description": "The name of the concept or API (e.g., Function Calling, Latent Space Image Generation)."},
                    "summary": {"type": "STRING", "description": "A concise 1-2 sentence summary of how this concept can be applied to the website builder."}
                },
                "required": ["name", "summary"]
            }
        }
    },
    "required": ["designPrinciples", "uiFrameworks", "aiApiConcepts"]
}


# --- 3. NETLIFY HANDLER FUNCTION ---

def handler(event, context):
    """The entry point for the Netlify function."""
    
    # 1. API Key Check
    if not GEMINI_API_KEY:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Server API Key is missing. Set GEMINI_API_KEY environment variable."})
        }

    try:
        # 2. Input Validation (Requires parsing the JSON body from the event)
        if event.get('body'):
            data = json.loads(event['body'])
            user_prompt = data.get('prompt')
        else:
            return {
                "statusCode": 400, 
                "body": json.dumps({"error": "Missing prompt in request data."})
            }

        # 3. Construct Gemini Payload
        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "tools": [{"google_search": {}}], 
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": RESPONSE_SCHEMA
            }
        }

        # 4. Call Gemini API
        response = requests.post(
            API_URL, 
            headers={'Content-Type': 'application/json'}, 
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status() 
        
        # 5. Extract and Process Response
        result = response.json()
        candidate = result.get('candidates', [{}])[0]

        if not candidate:
            return {"statusCode": 500, "body": json.dumps({"error": "Gemini API returned an empty candidate list."})}

        json_text = candidate.get('content', {}).get('parts', [{}])[0].get('text')
        grounding_metadata = candidate.get('groundingMetadata', {})
        
        if not json_text:
            return {"statusCode": 500, "body": json.dumps({"error": "Gemini API failed to return structured JSON content."})}
        
        research_data = json.loads(json_text)

        # Extract citations/sources
        sources = []
        if grounding_metadata and grounding_metadata.get('groundingAttributions'):
            for attribution in grounding_metadata['groundingAttributions']:
                web = attribution.get('web')
                if web and web.get('uri'):
                    sources.append({
                        "uri": web['uri'],
                        "title": web.get('title', 'No Title Available')
                    })

        # 6. Return the consolidated data to the frontend
        return {
            "statusCode": 200,
            "headers": { 'Content-Type': 'application/json' },
            "body": json.dumps({
                "research": research_data,
                "sources": sources
            })
        }

    except requests.exceptions.Timeout:
        return {"statusCode": 504, "body": json.dumps({"error": "The AI research request timed out."})}
    except requests.exceptions.RequestException as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"Failed to communicate with the Gemini API: {str(e)}", "details": str(e)})}
    except json.JSONDecodeError:
        return {"statusCode": 500, "body": json.dumps({"error": "Failed to parse JSON response from AI model. Check prompt/schema alignment."})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"An unexpected server error occurred: {str(e)}", "details": str(e)})}
