function urlB64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) { outputArray[i] = rawData.charCodeAt(i); }
    return outputArray;
}

document.addEventListener('DOMContentLoaded', function() {
    // Inject PWA meta tags dynamically
    const manifestLink = document.createElement('link');
    manifestLink.rel = 'manifest';
    manifestLink.href = '/manifest.json';
    document.head.appendChild(manifestLink);

    const metaCapable = document.createElement('meta');
    metaCapable.name = 'apple-mobile-web-app-capable';
    metaCapable.content = 'yes';
    document.head.appendChild(metaCapable);

    const metaStatus = document.createElement('meta');
    metaStatus.name = 'apple-mobile-web-app-status-bar-style';
    metaStatus.content = 'black-translucent';
    document.head.appendChild(metaStatus);

    const appleIcon = document.createElement('link');
    appleIcon.rel = 'apple-touch-icon';
    appleIcon.href = '/static/images/logo.png';
    document.head.appendChild(appleIcon);

    // iOS check
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isStandalone = window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches;

    // Inject styles
    const style = document.createElement('style');
    style.innerHTML = 
        .push-alert-btn {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 9999;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            font-weight: bold;
            text-align: center;
            width: 80%;
            max-width: 400px;
            color: #fff;
            font-size: 16px;
        }
        #ios-pwa-alert { background: #e74c3c; }
        #subscribe-push-btn { background: #2ecc71; display: none; }
    ;
    document.head.appendChild(style);

    if (isIOS && !isStandalone) {
        const alertBtn = document.createElement('div');
        alertBtn.id = 'ios-pwa-alert';
        alertBtn.className = 'push-alert-btn';
        alertBtn.innerHTML = '⚠️ Setup iOS Push Alerts';
        alertBtn.onclick = function() {
            alert('To receive push notifications on iOS, tap the "Share" icon at the bottom of Safari, then select "Add to Home Screen". Open the app from your home screen to enable notifications!');
        };
        document.body.appendChild(alertBtn);
    } else {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            const subBtn = document.createElement('div');
            subBtn.id = 'subscribe-push-btn';
            subBtn.className = 'push-alert-btn';
            subBtn.innerHTML = '🔔 Enable Push Notifications';
            document.body.appendChild(subBtn);

            navigator.serviceWorker.register('/sw.js').then(function(swReg) {
                console.log('Service Worker is registered', swReg);
                
                swReg.pushManager.getSubscription().then(function(sub) {
                    if (sub === null) {
                        subBtn.style.display = 'block';
                    }
                });

                subBtn.onclick = function() {
                    fetch('/accounts/push/vapid-public-key/')
                        .then(response => response.json())
                        .then(data => {
                            if (!data.public_key) {
                                alert("VAPID key not configured on server.");
                                return;
                            }
                            const applicationServerKey = urlB64ToUint8Array(data.public_key);
                            swReg.pushManager.subscribe({
                                userVisibleOnly: true,
                                applicationServerKey: applicationServerKey
                            }).then(function(subscription) {
                                console.log('User is subscribed:', subscription);
                                fetch('/accounts/push/save/', {
                                    method: 'POST',
                                    credentials: 'same-origin',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(subscription)
                                }).then(() => {
                                    subBtn.style.display = 'none';
                                    alert('Notifications enabled successfully!');
                                });
                            }).catch(function(err) {
                                console.log('Failed to subscribe the user: ', err);
                                alert('Failed to subscribe to notifications: ' + err.message);
                            });
                        });
                };
            }).catch(function(error) {
                console.error('Service Worker Error', error);
            });
        }
    }
});
