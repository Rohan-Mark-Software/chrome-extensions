const OLLAMA_API = "http://127.0.0.1:11434";
const MODEL = "deepseek-v3.1:671b-cloud";
const FLASK_API = "http://127.0.0.1:5000";

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyzeWithLLM") {
    handleAnalysis(request.prompt)
      .then((response) => sendResponse({ success: true, data: response }))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true;
  } else if (request.action === "searchDuckDuckGo") {
    fetch(`${FLASK_API}/search?q=${encodeURIComponent(request.query)}`)
      .then((response) => response.json())
      .then((data) => {
        sendResponse({ success: data.success, data: data.data });
      })
      .catch((error) => {
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  return false;
});

async function handleAnalysis(prompt) {
  try {
    const response = await fetch(`${OLLAMA_API}/api/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: MODEL,
        prompt: prompt,
        stream: false,
      }),
    });

    if (!response.ok) {
      throw new Error(
        `Ollama API error: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    return data.response;
  } catch (error) {
    console.error("Background script error:", error);
    throw error;
  }
}
