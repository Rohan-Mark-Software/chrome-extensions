// Polymarket API and analysis functions
const POLYMARKET_API = "https://gamma-api.polymarket.com";

// Extract slug from URL
function extractSlugFromUrl(url) {
  try {
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split("/").filter((p) => p);
    if (pathParts.length >= 2 && pathParts[0] === "event") {
      return pathParts[1];
    }
  } catch (e) {
    console.error("Error parsing URL:", e);
  }
  return null;
}

// Fetch Polymarket event data
async function getPolymarketEventData(slug) {
  const endpoint = `${POLYMARKET_API}/events/slug/${slug}`;

  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching Polymarket data:", error);
    throw error;
  }
}

// Format event data for display and context
function formatEventData(eventData) {
  let formatted = `📊 POLYMARKET EVENT DATA\n${"=".repeat(60)}\n\n`;
  formatted += `📋 Event: ${eventData.title || "N/A"}\n`;
  formatted += `📝 Description: ${eventData.description || "N/A"}\n\n`;
  formatted += `🎯 MARKETS & CURRENT ODDS:\n`;

  const markets = Array.isArray(eventData.markets) ? eventData.markets : [];

  if (markets.length === 0) {
    formatted += "\n⚠️  No markets found for this event\n";
  }

  markets.forEach((market, i) => {
    formatted += `\n${"─".repeat(60)}\n`;
    formatted += `Market ${i + 1}: ${market.question || "N/A"}\n\n`;
    formatted += `💰 OUTCOMES & ODDS:\n`;

    // Handle different possible data structures
    const outcomes = Array.isArray(market.outcomes) ? market.outcomes : [];
    const prices = Array.isArray(market.outcomePrices)
      ? market.outcomePrices
      : [];

    if (outcomes.length === 0) {
      formatted += `  ⚠️  No outcomes available\n`;
    } else {
      outcomes.forEach((outcome, j) => {
        const price = prices[j] || "N/A";
        let percentage = "N/A";

        if (price !== "N/A") {
          try {
            percentage = `${(parseFloat(price) * 100).toFixed(2)}%`;
          } catch (e) {
            percentage = price;
          }
        }

        formatted += `  ${j + 1}. ${outcome}: ${percentage}\n`;
      });
    }

    formatted += `\n📈 MARKET STATS:\n`;
    formatted += `  • Total Volume: ${
      market.volume ? Number(market.volume).toLocaleString() : "N/A"
    }\n`;
    formatted += `  • 24h Volume: ${
      market.volume24hr ? Number(market.volume24hr).toLocaleString() : "N/A"
    }\n`;
    formatted += `  • Liquidity: ${
      market.liquidity ? Number(market.liquidity).toLocaleString() : "N/A"
    }\n`;
    formatted += `  • Status: ${
      market.active && !market.closed ? "🟢 Active" : "🔴 Closed"
    }\n`;
  });

  formatted += `\n${"=".repeat(60)}\n`;
  formatted += `📅 EVENT INFO:\n`;
  formatted += `  • End Date: ${eventData.endDate || "N/A"}\n`;

  return formatted;
}

// Call Ollama LLM for analysis (via background script to avoid CORS)
async function analyzeBetWithLLM(eventData) {
  const formattedData = formatEventData(eventData);

  const prompt = `You are a professional Polymarket betting analyst with access to real-time market data.

${formattedData}

Provide a concise, actionable betting analysis:

**🎲 RECOMMENDED BET** (Your top pick)
- Outcome: [Specific option with current odds]
- Expected Value: [Why this is +EV]
- Key Reasoning: [2-3 critical factors]

**📊 MARKET EFFICIENCY**
- Are current odds accurate?
- Any mispriced outcomes?

**⚡ ALTERNATIVE OPTIONS**
- Second best choice
- Long-shot opportunity (if viable)

**⚠️ KEY RISKS**
- Main factors that could change outcome
- Information gaps

**💰 POSITION SIZING**
- Recommended: Conservative/Moderate/Aggressive
- Why: [Brief explanation]

**🎯 CONFIDENCE: [X/10]**

Be direct, analytical, and focus on VALUE.`;

  try {
    // Send message to background script to call Ollama
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: "analyzeWithLLM", prompt: prompt },
        (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else if (!response.success) {
            reject(new Error(response.error));
          } else {
            resolve(response.data);
          }
        }
      );
    });

    return response;
  } catch (error) {
    console.error("Error calling Ollama via background script:", error);
    throw error;
  }
}

// Display odds in a nice format
function displayOdds(eventData) {
  const markets = Array.isArray(eventData.markets) ? eventData.markets : [];

  if (markets.length === 0) {
    return '<div class="odds-display"><p style="text-align: center; color: #6c757d;">No market data available</p></div>';
  }

  let oddsHtml = '<div class="odds-display">';

  markets.forEach((market, i) => {
    if (i > 0)
      oddsHtml +=
        '<hr style="margin: 15px 0; border: none; border-top: 2px solid #dee2e6;">';

    oddsHtml += `<div style="font-weight: 600; margin-bottom: 10px; color: #667eea;">${
      market.question || "Market"
    }</div>`;

    // Typecast to arrays to handle any data type
    const outcomes = Array.isArray(market.outcomes)
      ? market.outcomes
      : market.outcomes
      ? [market.outcomes]
      : [];
    const prices = Array.isArray(market.outcomePrices)
      ? market.outcomePrices
      : market.outcomePrices
      ? [market.outcomePrices]
      : [];

    if (outcomes.length === 0) {
      oddsHtml +=
        '<p style="color: #6c757d; font-size: 12px;">No outcomes available</p>';
    } else {
      outcomes.forEach((outcome, j) => {
        const price = prices[j] || "N/A";
        let percentage = "N/A";

        if (price !== "N/A") {
          try {
            percentage = `${(parseFloat(price) * 100).toFixed(1)}%`;
          } catch (e) {
            percentage = price;
          }
        }

        oddsHtml += `
          <div class="odds-item">
            <span class="odds-label">${outcome}</span>
            <span class="odds-value">${percentage}</span>
          </div>
        `;
      });
    }
  });

  oddsHtml += "</div>";
  return oddsHtml;
}

// UI Elements
const statusContent = document.getElementById("statusContent");
const analyzeBtn = document.getElementById("analyzeBtn");
const loading = document.getElementById("loading");
const results = document.getElementById("results");
const resultsContent = document.getElementById("resultsContent");
const errorDiv = document.getElementById("error");

let currentSlug = null;

// Check current tab
async function checkCurrentPage() {
  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });

    if (!tab.url.includes("polymarket.com/event/")) {
      statusContent.textContent = "❌ Not on a Polymarket event page";
      analyzeBtn.disabled = true;
      return;
    }

    currentSlug = extractSlugFromUrl(tab.url);

    if (currentSlug) {
      statusContent.textContent = `✅ ${currentSlug.replace(/-/g, " ")}`;
      analyzeBtn.disabled = false;
    } else {
      statusContent.textContent = "❌ Could not extract bet slug";
      analyzeBtn.disabled = true;
    }
  } catch (error) {
    statusContent.textContent = "❌ Error checking page";
    console.error(error);
  }
}

// Show error
function showError(message) {
  errorDiv.textContent = `⚠️ ${message}`;
  errorDiv.style.display = "block";
  setTimeout(() => {
    errorDiv.style.display = "none";
  }, 5000);
}

// Main analysis function
async function analyzeCurrentBet() {
  if (!currentSlug) {
    showError("No valid bet found on current page");
    return;
  }

  // Reset UI
  analyzeBtn.disabled = true;
  loading.style.display = "block";
  results.classList.remove("show");
  errorDiv.style.display = "none";

  try {
    // Step 1: Fetch Polymarket data
    statusContent.textContent = "📡 Fetching market data...";
    const eventData = await getPolymarketEventData(currentSlug);

    // Log the data for debugging
    console.log("Event Data:", eventData);

    // Check if we got valid data
    if (!eventData || (!eventData.markets && !Array.isArray(eventData))) {
      throw new Error("Invalid event data structure received");
    }

    // Step 2: Analyze with LLM
    statusContent.textContent = "🤖 Analyzing with AI...";
    const analysis = await analyzeBetWithLLM(eventData);

    // Step 3: Display results
    loading.style.display = "none";
    results.classList.add("show");

    const oddsHtml = displayOdds(eventData);
    resultsContent.innerHTML = `
      <h4 style="color: #667eea; margin-bottom: 10px;">Current Odds</h4>
      ${oddsHtml}
      <h4 style="color: #667eea; margin: 20px 0 10px 0;">AI Analysis</h4>
      <div style="white-space: pre-wrap; line-height: 1.8;">${analysis}</div>
    `;

    statusContent.textContent = `✅ Analysis complete`;
    analyzeBtn.disabled = false;
  } catch (error) {
    loading.style.display = "none";
    analyzeBtn.disabled = false;

    let errorMessage = "Analysis failed";

    if (error.message.includes("Ollama")) {
      errorMessage =
        "Could not connect to Ollama. Make sure it's running on localhost:11434";
    } else if (error.message.includes("HTTP")) {
      errorMessage = `API Error: ${error.message}`;
    } else if (error.message.includes("Invalid event data")) {
      errorMessage =
        "Could not parse Polymarket data. The event structure may be different.";
    } else {
      errorMessage = `Error: ${error.message}`;
    }

    showError(errorMessage);
    statusContent.textContent = "❌ Analysis failed";
    console.error("Analysis error:", error);
    console.error("Error stack:", error.stack);
  }
}

// Event listeners
analyzeBtn.addEventListener("click", analyzeCurrentBet);

// Initialize
checkCurrentPage();
