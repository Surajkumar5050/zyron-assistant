// Zyron Navigation Agent - Content Script
// "The Hands" inside the webpage

console.log("👋 Zyron Content Agent Loaded!");

// Listen for messages from the background script
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("📩 Zyron received message:", message);
    let result = { success: false, error: "Unknown command" };

    if (message.action === "highlight") {
        result = highlightElement(message.selector);
    } else if (message.action === "click") {
        result = clickElement(message.selector);
    } else if (message.action === "type") {
        result = typeText(message.selector, message.text);
    } else if (message.action === "press_key") {
        result = pressKey(message.selector, message.key);
    } else if (message.action === "scroll") {
        result = scrollPage(message.direction);
    } else if (message.action === "read") {
        // Read is async, handle differently
        return readPage();
    } else if (message.action === "scan") {
        return scanPage();
    }

    // Return synchronous result immediately
    return Promise.resolve(result);
});

// --- NAVIGATION AGENT FUNCTIONS ---

/**
 * High-precision element highlighter for debugging/user feedback
 */
function highlightElement(selector) {
    console.log("🎯 highlightElement:", selector);
    try {
        const el = document.querySelector(selector);
        if (el) {
            // Save original style to restore later? (maybe v2)
            el.style.cssText += "outline: 4px solid #ff0000 !important; box-shadow: 0 0 20px rgba(255,0,0,0.5) !important; z-index: 999999 !important;";
            el.scrollIntoView({ behavior: "smooth", block: "center" });
            return { success: true, message: `Highlighted ${selector}` };
        } else {
            console.warn("❌ Element not found:", selector);
            return { success: false, error: "Element not found" };
        }
    } catch (e) {
        return { success: false, error: e.message };
    }
}

/**
 * Robust click handler
 */
function clickElement(selector) {
    console.log("🖱️ clickElement:", selector);
    try {
        const el = document.querySelector(selector);
        if (el) {
            highlightElement(selector); // Visual feedback before action

            // Wait slightly for visual feedback
            setTimeout(() => {
                el.click();
                // Special handling for form submissions or links
                if (el.tagName === 'INPUT' && el.type === 'submit') el.form.submit();
            }, 300);

            return { success: true, message: `Clicked ${selector}` };
        } else {
            return { success: false, error: "Element not found" };
        }
    } catch (e) {
        return { success: false, error: e.message };
    }
}

/**
 * Type text into an input field
 */
function typeText(selector, text) {
    console.log("⌨️ typeText:", selector, text);
    try {
        const el = document.querySelector(selector);
        if (el) {
            highlightElement(selector);
            el.focus();
            el.value = text;

            // Trigger events so React/Vue/Angular detect the change
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));

            return { success: true, message: `Typed "${text}" into ${selector}` };
        } else {
            return { success: false, error: "Element not found" };
        }
    } catch (e) {
        return { success: false, error: e.message };
    }
}

/**
 * Scroll the page
 * @param {string} direction 'up' | 'down' | 'top' | 'bottom'
 */
function scrollPage(direction) {
    console.log("📜 scrollPage:", direction);
    try {
        if (direction === 'down') {
            window.scrollBy({ top: window.innerHeight * 0.8, behavior: 'smooth' });
        } else if (direction === 'up') {
            window.scrollBy({ top: -window.innerHeight * 0.8, behavior: 'smooth' });
        } else if (direction === 'top') {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else if (direction === 'bottom') {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }
        return { success: true, message: `Scrolled ${direction}` };
    } catch (e) {
        return { success: false, error: e.message };
    }
}

/**
 * Extract main content intelligently
 */
function readPage() {
    console.log("📖 readPage called");
    try {
        // 1. clone body to avoid mutating the page
        const clone = document.body.cloneNode(true);

        // 2. aggressive noise removal
        const noiseSelectors = [
            'script', 'style', 'noscript', 'iframe', 'svg', 'button', 'input', 'form',
            'nav', 'footer', 'header', 'aside',
            '.ad', '.ads', '.advertisement', '.social-share', '.share-buttons',
            '[role="banner"]', '[role="contentinfo"]', '[role="navigation"]', '[role="search"]',
            // wikipedia specific
            '.mw-jump-link', '.mw-editsection', '.reference', '.reflist', '.catlinks',
            '.printfooter', '#footer', '.mw-indicators',
            // generic noise(any website)
            '.cookie-consent', '.popup', '.sidebar', '.widget'
        ];

        noiseSelectors.forEach(selector => {
            const elements = clone.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        });

        // 3. remove citations from websites that has them (sup tags like [1])
        clone.querySelectorAll('sup').forEach(el => el.remove());

        // 4. find valid paragraphs
        // we only want paragraphs with substantial text
        const paragraphs = Array.from(clone.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li'));
        let cleanText = "";

        // 5. intelligent text assembly
        paragraphs.forEach(p => {
            const text = p.innerText.trim();

            // skip empty or super short noise
            if (text.length < 20 && !p.tagName.startsWith('H')) return;

            // skip lines that look like navigation ("Home > category...")
            if (text.includes('>') && text.length < 50) return;

            // skip high-link-density lines (menus acting as paragraphs)
            const linkCount = p.querySelectorAll('a').length;
            if (linkCount > 3 && text.length < 100) return; // mostly links

            // formatting
            if (p.tagName.startsWith('H')) {
                cleanText += `\n\n# ${text}\n`; // headers get markdown style
            } else if (p.tagName === 'LI') {
                cleanText += `• ${text}\n`;
            } else {
                cleanText += `${text}\n\n`; // paragraphs get double spacing
            }
        });

        // 6. fallback: if heuristic failed and text is empty, grab raw body
        if (cleanText.length < 100) {
            cleanText = clone.innerText.replace(/\s+/g, ' ').substring(0, 4000);
        }

        // 7. final cleanup
        cleanText = cleanText.replace(/\n{3,}/g, '\n\n').trim();

        // limit to 100k chars for now (File can handle it)
        if (cleanText.length > 100000) {
            cleanText = cleanText.substring(0, 100000) + "... [Truncated]";
        }

        return Promise.resolve({
            success: true,
            title: document.title,
            url: window.location.href,
            content: cleanText || "No readable content found."
        });
    } catch (e) {
        return Promise.resolve({ success: false, error: e.message });
    }
}

/**
 * Scan page for interactive elements and assign IDs
 */
function pressKey(selector, key) {
    console.log("⌨️ pressKey called:", selector, key);
    const el = document.querySelector(selector) || document.querySelector(`[data-zyron-id="${selector}"]`);
    if (el) {
        const event = new KeyboardEvent('keydown', {
            key: key,
            code: key === 'Enter' ? 'Enter' : key,
            keyCode: key === 'Enter' ? 13 : 0,
            which: key === 'Enter' ? 13 : 0,
            bubbles: true
        });
        el.dispatchEvent(event);
        return { success: true };
    }
    return { success: false, error: "Element not found" };
}

function scanPage() {
    console.log("🔍 scanPage called");
    try {
        // 1. clean up old tags if any
        document.querySelectorAll('.zyron-tag').forEach(el => el.remove());

        // 2. find interactive elements
        const selectors = [
            'a[href]', 'button', 'input', 'textarea', 'select', '[role="button"]', '[onclick]'
        ];

        const elements = document.querySelectorAll(selectors.join(','));
        const interactables = [];
        let idCounter = 1;

        elements.forEach(el => {
            // skip hidden elements
            if (el.offsetParent === null) return;

            // assign id
            const zyronId = idCounter++;
            el.dataset.zyronId = zyronId;

            // get text content
            let text = el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || "Unlabeled";
            text = text.replace(/\s+/g, ' ').trim().substring(0, 50);

            if (!text) return; // skip empty elements

            interactables.push({
                id: zyronId,
                type: el.tagName.toLowerCase(),
                text: text
            });
        });

        return Promise.resolve({
            success: true,
            elements: interactables.slice(0, 100) // limit to 100 items to avoid token overflow
        });
    } catch (e) {
        return Promise.resolve({ success: false, error: e.message });
    }
}
