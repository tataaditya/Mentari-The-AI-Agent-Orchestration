/**
 * MENTARI V.20 - NUCLEAR BACKGROUND INJECTOR
 * GUARANTEED TO WORK - NO MORE EXCUSES!
 */

console.log('🚀 MENTARI NUCLEAR INJECTOR STARTING...');

// ============================================================================
// STEP 1: WAIT FOR EVERYTHING TO LOAD
// ============================================================================
function waitForChainlit() {
    return new Promise((resolve) => {
        if (document.body && document.querySelector('#root')) {
            resolve();
        } else {
            const observer = new MutationObserver(() => {
                if (document.body && document.querySelector('#root')) {
                    observer.disconnect();
                    resolve();
                }
            });
            observer.observe(document.documentElement, { childList: true, subtree: true });
        }
    });
}

// ============================================================================
// STEP 2: NUCLEAR BACKGROUND APPLICATION
// ============================================================================
async function applyNuclearBackground() {
    await waitForChainlit();
    
    console.log('💣 APPLYING NUCLEAR BACKGROUND...');
    
    const BG_URL = 'http://localhost:8000/public/mentari(2).png';
    
    // METHOD 1: Direct inline styles (HIGHEST PRIORITY)
    const applyDirectStyles = () => {
        // HTML element
        document.documentElement.setAttribute('style', `
            background: #0a0e27 url('${BG_URL}') center center / cover no-repeat fixed !important;
            min-height: 100vh !important;
        `);
        
        // BODY element - MOST IMPORTANT
        document.body.setAttribute('style', `
            background: url('${BG_URL}') center center / cover no-repeat fixed !important;
            background-color: #0a0e27 !important;
            min-height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
        `);
        
        console.log('✅ Direct styles applied');
    };
    
    // METHOD 2: CSS Injection with MAXIMUM specificity
    const injectSuperCSS = () => {
        const styleId = 'mentari-nuclear-bg';
        let style = document.getElementById(styleId);
        
        if (style) style.remove();
        
        style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* NUCLEAR BACKGROUND - MAXIMUM PRIORITY */
            html,
            html body,
            body,
            #root,
            body > div,
            body > div > div {
                background-image: url('${BG_URL}') !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
                background-color: #0a0e27 !important;
            }
            
            /* Remove background from these */
            #root,
            .cl-app-wrapper,
            main,
            [class*="MuiBox"],
            [class*="MuiContainer"],
            [class*="MuiPaper"]:not(.user-message):not(.assistant-message) {
                background: transparent !important;
                background-color: transparent !important;
                background-image: none !important;
            }
            
            /* Dark overlay */
            body::before {
                content: "" !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(0, 0, 0, 0.35) !important;
                z-index: 0 !important;
                pointer-events: none !important;
            }
            
            /* Ensure content is above overlay */
            #root {
                position: relative !important;
                z-index: 1 !important;
            }
            
            /* Glassmorphism Messages */
            .user-message,
            .step-user,
            div[class*="user"] {
                background: rgba(59, 130, 246, 0.9) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
                border-radius: 16px !important;
                color: white !important;
                padding: 12px 16px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
            }
            
            .assistant-message,
            .step-assistant,
            div[class*="assistant"] {
                background: rgba(255, 255, 255, 0.9) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(255, 255, 255, 0.5) !important;
                border-radius: 16px !important;
                color: #1a1a2e !important;
                padding: 12px 16px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
            }
            
            .step-system {
                background: rgba(156, 163, 175, 0.85) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
                border-radius: 12px !important;
                color: white !important;
                padding: 10px 14px !important;
            }
            
            /* Header */
            header,
            .cl-header {
                background: rgba(255, 255, 255, 0.12) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1) !important;
            }
            
            /* Input Container */
            .cl-input-container,
            #chat-input-container,
            form {
                background: rgba(255, 255, 255, 0.95) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border-top: 1px solid rgba(0, 0, 0, 0.1) !important;
                box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.1) !important;
            }
            
            /* Input Field */
            #chat-input,
            textarea,
            input[type="text"] {
                background: rgba(255, 255, 255, 0.98) !important;
                border: 1px solid rgba(0, 0, 0, 0.12) !important;
                border-radius: 12px !important;
                color: #1a1a2e !important;
            }
            
            /* Buttons */
            button {
                backdrop-filter: blur(8px) !important;
                -webkit-backdrop-filter: blur(8px) !important;
                transition: all 0.3s ease !important;
            }
            
            button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 12px;
                background: rgba(0, 0, 0, 0.1);
            }
            
            ::-webkit-scrollbar-thumb {
                background: rgba(59, 130, 246, 0.6);
                border-radius: 6px;
                border: 2px solid transparent;
                background-clip: padding-box;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(59, 130, 246, 0.9);
                background-clip: padding-box;
            }
        `;
        
        document.head.appendChild(style);
        console.log('✅ Nuclear CSS injected');
    };
    
    // METHOD 3: Force remove conflicting styles
    const removeConflicts = () => {
        // Remove any existing background styles
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            if (el.tagName !== 'BODY' && el.tagName !== 'HTML') {
                const computedBg = window.getComputedStyle(el).backgroundColor;
                if (computedBg && computedBg !== 'rgba(0, 0, 0, 0)' && computedBg !== 'transparent') {
                    // Don't touch message bubbles
                    if (!el.className.includes('message') && !el.className.includes('step')) {
                        el.style.backgroundColor = 'transparent';
                    }
                }
            }
        });
        console.log('✅ Conflicts removed');
    };
    
    // EXECUTE ALL METHODS
    applyDirectStyles();
    injectSuperCSS();
    setTimeout(removeConflicts, 500);
    
    // Re-apply every 3 seconds (aggressive)
    setInterval(() => {
        applyDirectStyles();
        injectSuperCSS();
    }, 3000);
    
    console.log('🎉 NUCLEAR BACKGROUND APPLIED!');
}

// ============================================================================
// STEP 3: EXECUTE WITH MULTIPLE TRIGGERS
// ============================================================================

// Trigger 1: Immediate
applyNuclearBackground();

// Trigger 2: DOM Ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyNuclearBackground);
} else {
    applyNuclearBackground();
}

// Trigger 3: Window Load
window.addEventListener('load', () => {
    setTimeout(applyNuclearBackground, 100);
    setTimeout(applyNuclearBackground, 500);
    setTimeout(applyNuclearBackground, 1000);
});

// Trigger 4: Mutation Observer (watch for Chainlit injections)
const observer = new MutationObserver(() => {
    applyNuclearBackground();
});

if (document.body) {
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });
}

// ============================================================================
// DEBUG CONSOLE
// ============================================================================
window.MentariDebug = {
    check: () => {
        console.log('=== MENTARI DEBUG ===');
        console.log('Body BG:', window.getComputedStyle(document.body).backgroundImage);
        console.log('Body BG Color:', window.getComputedStyle(document.body).backgroundColor);
        console.log('HTML BG:', window.getComputedStyle(document.documentElement).backgroundImage);
    },
    force: () => {
        console.log('🔧 FORCING BACKGROUND...');
        applyNuclearBackground();
    },
    test: () => {
        window.open('http://localhost:8000/public/mentari(2).png', '_blank');
    }
};

console.log('💡 Debug: MentariDebug.check() | .force() | .test()');