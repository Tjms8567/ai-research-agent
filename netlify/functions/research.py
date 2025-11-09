import os
import json
import requests

# --- 1. CONFIGURATION ---

# IMPORTANT: The GEMINI_API_KEY must be set as an environment variable in your Netlify dashboard.
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
                }
            }
        }
    },
    "required": ["designPrinciples", "uiFrameworks", "aiApiConcepts"]
}


# --- 3. NETLIFY HANDLER FUNCTION ---

def handler(event, context):
    """
    The entry point for the Netlify function. 
    It receives the request event and returns the response.
    """
    
    # 1. API Key Check
    if not GEMINI_API_KEY:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Server API Key is missing. Set GEMINI_API_KEY environment variable in Netlify."})
        }

    try:
        # 2. Input Validation (Parsing the JSON body from the event)
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
            "tools": [{"google_search": {} }], # Enable Google Search
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
        # Raises an exception for bad status codes (4xx or 5xx)
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
        
        # The AI returns JSON as a string, so we must parse it
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

    except Exception as e:
        # Catch any errors during execution (network, parsing, etc.)
        return {"statusCode": 500, "body": json.dumps({"error": f"An unexpected server error occurred: {str(e)}", "details": str(e)})}        </div>
    </div>

    <script>
        // --- Rendering Functions (Frontend Responsibility) ---

        function renderCategory(title, data, iconName) {
            let itemsHtml = data.map(item => `
                <div class="p-5 bg-gray-50 rounded-xl border border-gray-200">
                    <h4 class="text-lg font-semibold text-indigo-700">${item.name}</h4>
                    <p class="text-gray-600 mt-1">${item.summary}</p>
                </div>
            `).join('');

            return `
                <section>
                    <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
                        <i data-lucide="${iconName}" class="w-5 h-5 mr-2 text-indigo-500"></i>
                        ${title}
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        ${itemsHtml}
                    </div>
                </section>
            `;
        }

        function renderSources(sources) {
            const sourceList = document.getElementById('sourceList');
            const sourcesBox = document.getElementById('sourcesBox');
            sourceList.innerHTML = '';
            
            if (sources.length === 0) {
                sourcesBox.classList.add('hidden');
                return;
            }

            sourcesBox.classList.remove('hidden');

            sources.forEach((source, index) => {
                const sourceElement = document.createElement('div');
                sourceElement.innerHTML = `
                    <a href="${source.uri}" target="_blank" rel="noopener noreferrer" class="hover:underline text-indigo-600 font-medium">
                        [${index + 1}] ${source.title || 'Source Link'}
                    </a>
                `;
                sourceList.appendChild(sourceElement);
            });
        }

        // --- Main Frontend Logic ---

        window.handleGenerate = async function() {
            const userPrompt = document.getElementById('userPrompt').value;
            const generateButton = document.getElementById('generateButton');
            const loadingIcon = document.getElementById('loadingIcon');
            const searchIcon = document.getElementById('searchIcon');
            const resultsContainer = document.getElementById('resultsContainer');
            const contentArea = document.getElementById('contentArea');
            const errorMessage = document.getElementById('errorMessage');

            if (!userPrompt.trim()) {
                errorMessage.textContent = "Please enter a prompt to start the research.";
                errorMessage.classList.remove('hidden');
                return;
            }

            // Reset UI
            resultsContainer.classList.add('hidden');
            errorMessage.classList.add('hidden');
            contentArea.innerHTML = '';

            // Loading state
            generateButton.disabled = true;
            generateButton.classList.add('bg-gray-400');
            generateButton.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
            loadingIcon.classList.remove('hidden');
            searchIcon.classList.add('hidden');
            generateButton.querySelector('span').textContent = 'Researching...';

            try {
                // CORE CHANGE: Fetching from the Netlify Function endpoint
                // The URL maps to netlify/functions/research.py
                const response = await fetch('/netlify/functions/research', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: userPrompt })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Serverless function returned an error.');
                }
                
                const researchData = data.research;
                const sources = data.sources;

                // Render Results
                contentArea.innerHTML = 
                    renderCategory('AI API Concepts & Integration', researchData.aiApiConcepts, 'brain-circuit') +
                    renderCategory('UI Frameworks & Component Libraries', researchData.uiFrameworks, 'layout-list') +
                    renderCategory('Key Design Principles & Patterns', researchData.designPrinciples, 'palette');

                renderSources(sources);

                resultsContainer.classList.remove('hidden');
                
                // Re-create icons for the new content
                lucide.createIcons(); 

            } catch (error) {
                console.error("Fetch or Parsing Error:", error);
                errorMessage.textContent = `Research failed: ${error.message}. Please check the browser console and Netlify function logs for details.`;
                errorMessage.classList.remove('hidden');
            } finally {
                // Reset loading state
                generateButton.disabled = false;
                generateButton.classList.remove('bg-gray-400');
                generateButton.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
                loadingIcon.classList.add('hidden');
                searchIcon.classList.remove('hidden');
                generateButton.querySelector('span').textContent = 'Start Research & Collect Resources';
            }
        }
        
        // Initial setup for icons
        document.addEventListener('DOMContentLoaded', () => {
             lucide.createIcons(); 
        });
    </script>
</body>
</html>
