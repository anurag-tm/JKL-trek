class OfflineManager {
    constructor(storage, options = {}) {
        this.storage = storage;
        this.statusElementId = options.statusElementId || 'network-status-indicator';
        this.queueContainerId = options.queueContainerId || 'offline-status';
        this.pendingElementId = options.pendingElementId || 'pending-count';
        this.syncHandler = null;
    }

    async init() {
        this.updateStatusIndicator();
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.updateStatusIndicator());
    }

    setSyncHandler(handler) {
        this.syncHandler = handler;
    }

    async enqueueMutation(type, payload) {
        await this.storage.queueChange({ type, payload });
        await this.updateStatusIndicator();
    }

    async handleOnline() {
        await this.updateStatusIndicator();
        await this.syncQueuedChanges();
        await this.updateStatusIndicator();
    }

    async syncQueuedChanges() {
        if (!navigator.onLine || typeof this.syncHandler !== 'function') return;
        const queue = await this.storage.getQueuedChanges();
        for (const item of queue) {
            await this.syncHandler(item);
            await this.storage.removeQueuedChange(item.id);
        }
    }

    async updateStatusIndicator() {
        const statusEl = document.getElementById(this.statusElementId);
        const queueContainer = document.getElementById(this.queueContainerId);
        const pendingEl = document.getElementById(this.pendingElementId);
        const queue = await this.storage.getQueuedChanges();
        const isOnline = navigator.onLine;

        if (statusEl) {
            statusEl.textContent = isOnline ? '🟢 Online' : '🟠 Offline';
            statusEl.classList.toggle('offline', !isOnline);
        }

        if (queueContainer && pendingEl) {
            if (!isOnline || queue.length > 0) {
                queueContainer.style.display = 'block';
                pendingEl.textContent = queue.length > 0
                    ? `${queue.length} item${queue.length > 1 ? 's' : ''} waiting to sync`
                    : 'Offline mode active. Changes will sync automatically.';
            } else {
                queueContainer.style.display = 'none';
            }
        }
    }
}

window.OfflineManager = OfflineManager;
