<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Research Agent - Netlify Serverless</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #f7f9fb; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <div class="max-w-4xl mx-auto">
        <!-- Header -->
        <header class="text-center mb-10">
            <div class="flex items-center justify-center text-indigo-600 mb-2">
                <i data-lucide="zap" class="w-8 h-8 mr-2"></i>
                <h1 class="text-3xl font-extrabold text-gray-800">AI Research Agent (Netlify Deployed)</h1>
            </div>
            <p class="text-lg text-gray-500">
                The secure serverless function handles the Gemini API call and returns structured, cited research.
            </p>
        </header>

        <!-- Input Section -->
        <div class="bg-white p-6 md:p-8 rounded-xl shadow-2xl border border-gray-100">
            <h2 class="text-xl font-semibold mb-4 text-gray-700">What website are you building?</h2>
            <div class="flex flex-col space-y-4">
                <textarea
                    id="userPrompt"
                    rows="4"
                    class="w-full p-4 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 resize-none"
                    placeholder="E.g., An AI-driven recipe generator with a focus on dark-mode design and fast load times."
                >A modern, interactive documentation platform similar to Next.js docs, but driven by an AI content generation model.</textarea>

                <button
                    id="generateButton"
                    class="w-full md:w-auto self-end px-6 py-3 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 transition duration-200 shadow-md flex items-center justify-center disabled:opacity-50"
                    onclick="handleGenerate()"
                >
                    <i data-lucide="loader-2" class="w-5 h-5 mr-2 hidden animate-spin" id="loadingIcon"></i>
                    <i data-lucide="search" class="w-5 h-5 mr-2" id="searchIcon"></i>
                    <span>Start Research & Collect Resources</span>
                </button>
            </div>
        </div>

        <!-- Results Section -->
        <div id="resultsContainer" class="mt-10 hidden">
            <h2 class="text-2xl font-bold mb-6 text-gray-800 border-b pb-2">Research Findings</h2>
            
            <!-- Sources Box -->
            <div id="sourcesBox" class="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mb-6 shadow-inner hidden">
                <h3 class="text-lg font-medium text-yellow-800 flex items-center mb-2">
                    <i data-lucide="link" class="w-5 h-5 mr-2"></i>
                    Cited Sources
                </h3>
                <div id="sourceList" class="text-sm text-yellow-700 space-y-1">
                    <!-- Source items will be injected here -->
                </div>
            </div>

            <!-- Content Area -->
            <div id="contentArea" class="space-y-8">
                <!-- Structured JSON results will be injected here -->
            </div>
        </div>
        
        <!-- Error Message -->
        <div id="errorMessage" class="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg hidden">
            <!-- Error messages go here -->
        </div>
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
