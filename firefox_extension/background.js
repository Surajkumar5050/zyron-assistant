// Background service worker for Pikachu Activity Monitor
console.log("Pikachu Activity Monitor - Background Service Started");

// Listen for messages from native host or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getTabs") {
    getAllTabs().then(tabs => {
      sendResponse({ tabs: tabs });
    });
    return true; // Indicates async response
  }
});

// Function to get all tabs from all windows
async function getAllTabs() {
  try {
    const windows = await chrome.windows.getAll({ populate: true });
    const allTabs = [];
    
    for (const window of windows) {
      for (const tab of window.tabs) {
        allTabs.push({
          id: tab.id,
          title: tab.title,
          url: tab.url,
          windowId: window.id,
          active: tab.active,
          favIconUrl: tab.favIconUrl
        });
      }
    }
    
    return allTabs;
  } catch (error) {
    console.error("Error getting tabs:", error);
    return [];
  }
}

// Listen for native messaging connection
chrome.runtime.onConnectExternal.addListener((port) => {
  console.log("Native messaging connection established");
  
  port.onMessage.addListener(async (msg) => {
    if (msg.command === "get_tabs") {
      const tabs = await getAllTabs();
      port.postMessage({ tabs: tabs });
    }
  });
});

// Alternative: Use chrome.runtime.sendNativeMessage for one-time requests
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
  if (request.command === "get_tabs") {
    getAllTabs().then(tabs => {
      sendResponse({ tabs: tabs });
    });
    return true;
  }
});