// Background service worker for Zyron Activity Monitor
console.log("Zyron Activity Monitor - Background Service Started");

let nativePort = null;

function connectToNativeHost() {
  nativePort = chrome.runtime.connectNative("zyron.native.host");

  nativePort.onMessage.addListener((response) => {
    console.log("Received from native host:", response);

    // --- COMMAND DISPATCHER ---
    if (response.action === "close_tab") {
      if (response.tabId) {
        chrome.tabs.remove(response.tabId);
      }
    }
    else if (response.action === "mute_tab") {
      if (response.tabId) {
        chrome.tabs.update(response.tabId, { muted: response.value !== false });
      }
    }
    else if (response.action === "create_tab") {
      if (response.url) {
        chrome.tabs.create({ url: response.url, active: response.active !== false });
      }
    }
    else if (response.action === "media_control") {
      // PROPER MV3 IMPLEMENTATION
      if (response.tabId) {
        browser.scripting.executeScript({
          target: { tabId: response.tabId },
          func: (cmd) => {
            const video = document.querySelector('video');
            if (video) {
              if (cmd === 'play') video.play();
              if (cmd === 'pause') video.pause();
            }
          },
          args: [response.command]
        }).catch(err => console.error("Script injection failed:", err));
      }
    }
    else if (response.action === "capture_tab") {
      // TAB SCREENSHOT
      if (response.tabId) {
        // 1. Activate the tab first (required for captureVisibleTab)
        chrome.tabs.update(response.tabId, { active: true }, () => {
          // 2. Wait for render (500ms delay)
          setTimeout(() => {
            chrome.tabs.captureVisibleTab(response.windowId, { format: "png" }, (dataUrl) => {
              if (chrome.runtime.lastError) {
                console.error("Capture failed:", chrome.runtime.lastError);
                nativePort.postMessage({ action: "capture_error", error: chrome.runtime.lastError.message });
                return;
              }
              // 3. Send back to native host
              nativePort.postMessage({ action: "capture_result", data: dataUrl, tabId: response.tabId });
            });
          }, 800); // 800ms delay to be safe
        });
      }
    }
    // --- NAVIGATION AGENT ---
    else if (["highlight", "click", "read", "scroll", "type", "scan", "press_key"].includes(response.action)) {
      console.log("🧭 NAV COMMAND RECEIVED:", response);
      // Send to Content Script in the ACTIVE TAB
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs && tabs[0]) {
          console.log("Target Tab:", tabs[0].id, tabs[0].url);
          chrome.tabs.sendMessage(tabs[0].id, response).then(reply => {
            console.log("✅ Content Script Replied:", reply);
            if (reply) {
              nativePort.postMessage({ action: "navigation_result", data: reply });
            }
          }).catch(err => {
            console.error("Nav Error:", err);
          });
        }
      });
    }
  });

  nativePort.onDisconnect.addListener((p) => {
    if (p.error) {
      console.log("Native host disconnected with error:", p.error);
    }
    nativePort = null;
    // Try to reconnect after a delay
    setTimeout(connectToNativeHost, 10000);
  });
}

connectToNativeHost();

// Listen for messages from popup or page
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getTabs") {
    getAllTabs().then(tabs => sendResponse({ tabs: tabs }));
    return true; // Keep channel open
  }
});

// Real-time tab monitoring
async function sendTabsToHost() {
  if (!nativePort) return;

  try {
    const tabs = await chrome.tabs.query({});
    const tabData = tabs.map(tab => ({
      id: tab.id,
      title: tab.title,
      url: tab.url,
      windowId: tab.windowId,
      active: tab.active
    }));

    nativePort.postMessage({
      action: "update_tabs",
      tabs: tabData
    });
  } catch (e) {
    console.error("Error sending tabs:", e);
  }
}

// Update every 2 seconds for real-time Focus Mode support
setInterval(sendTabsToHost, 2000);
// Also update on tab events
chrome.tabs.onUpdated.addListener(sendTabsToHost);
chrome.tabs.onRemoved.addListener(sendTabsToHost);
chrome.tabs.onActivated.addListener(sendTabsToHost);

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