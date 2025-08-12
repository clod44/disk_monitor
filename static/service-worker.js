self.addEventListener('install', function (event) {
    event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', function (event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', function (event) {
    const payload = event.data ? event.data.json() : { title: 'Notification', body: 'You have a new notification.' };
    const title = payload.title;
    const options = {
        body: payload.body,
        icon: '/static/icon.png',
        badge: '/static/icon.png',
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    event.waitUntil(clients.openWindow('/'));
});
