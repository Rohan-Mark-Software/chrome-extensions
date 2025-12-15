// Get current tab info
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tab = tabs[0];
  document.getElementById("pageTitle").textContent = tab.title;
  document.getElementById("pageUrl").textContent = tab.url;
});

// Handle form submission
document
  .getElementById("bookmarkForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];

    const context = document.getElementById("context").value;
    const tagsInput = document.getElementById("tags").value;
    const tags = tagsInput
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t);

    const bookmark = {
      id: Date.now().toString(),
      url: tab.url,
      title: tab.title,
      context: context,
      tags: tags,
      timestamp: new Date().toISOString(),
      favicon: tab.favIconUrl || "",
    };

    // Get existing bookmarks
    const result = await chrome.storage.local.get(["bookmarks"]);
    const bookmarks = result.bookmarks || [];

    // Add new bookmark
    bookmarks.unshift(bookmark);

    // Save to storage
    await chrome.storage.local.set({ bookmarks: bookmarks });

    // Show success message
    const successMsg = document.getElementById("successMessage");
    successMsg.style.display = "block";

    // Reset form
    document.getElementById("context").value = "";
    document.getElementById("tags").value = "";

    setTimeout(() => {
      successMsg.style.display = "none";
    }, 2000);
  });

// View all bookmarks
document.getElementById("viewAllBtn").addEventListener("click", () => {
  chrome.tabs.create({ url: "sidepanel.html" });
});
