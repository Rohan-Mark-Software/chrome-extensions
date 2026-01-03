// Content script that runs on Polymarket event pages
// This can be extended to add inline predictions on the page itself

console.log("Polymarket Bet Analyzer: Content script loaded");

// Extract current slug from page
function getCurrentSlug() {
  const pathParts = window.location.pathname.split("/").filter((p) => p);
  if (pathParts.length >= 2 && pathParts[0] === "event") {
    return pathParts[1];
  }
  return null;
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getSlug") {
    sendResponse({ slug: getCurrentSlug() });
  }
  return true;
});

// Optional: Add a floating analysis button on the page
function addFloatingButton() {
  const button = document.createElement("button");
  button.id = "polymarket-analyzer-btn";
  button.innerHTML = "🎯 AI Analysis";
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 10000;
    padding: 12px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `;

  button.addEventListener("mouseenter", () => {
    button.style.transform = "translateY(-2px)";
    button.style.boxShadow = "0 6px 20px rgba(102, 126, 234, 0.6)";
  });

  button.addEventListener("mouseleave", () => {
    button.style.transform = "translateY(0)";
    button.style.boxShadow = "0 4px 15px rgba(102, 126, 234, 0.4)";
  });

  button.addEventListener("click", () => {
    // Open the extension popup programmatically
    // Note: This will trigger the popup to open
    chrome.runtime.sendMessage({ action: "openPopup" });
  });

  document.body.appendChild(button);
}

// Wait for page to load, then add button
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", addFloatingButton);
} else {
  addFloatingButton();
}
