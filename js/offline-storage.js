class OfflineStorage {
    constructor() {
        this.dbName = 'jkl_trek_offline_db';
        this.dbVersion = 1;
        this.db = null;
    }

    async init() {
        if (this.db) return this.db;

        this.db = await new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('favorites')) db.createObjectStore('favorites', { keyPath: 'id' });
                if (!db.objectStoreNames.contains('progress')) db.createObjectStore('progress', { keyPath: 'id' });
                if (!db.objectStoreNames.contains('maps')) db.createObjectStore('maps', { keyPath: 'id' });
                if (!db.objectStoreNames.contains('queue')) db.createObjectStore('queue', { keyPath: 'id', autoIncrement: true });
                if (!db.objectStoreNames.contains('peaks')) db.createObjectStore('peaks', { keyPath: 'id' });
            };

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });

        return this.db;
    }

    async withStore(storeName, mode, operation) {
        const db = await this.init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, mode);
            const store = tx.objectStore(storeName);
            const request = operation(store);
            tx.oncomplete = () => resolve(request ? request.result : undefined);
            tx.onerror = () => reject(tx.error);
        });
    }

    async put(storeName, value) {
        return this.withStore(storeName, 'readwrite', (store) => store.put(value));
    }

    async get(storeName, id) {
        await this.init();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readonly');
            const req = tx.objectStore(storeName).get(id);
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    }

    async getAll(storeName) {
        await this.init();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readonly');
            const req = tx.objectStore(storeName).getAll();
            req.onsuccess = () => resolve(req.result || []);
            req.onerror = () => reject(req.error);
        });
    }

    async delete(storeName, id) {
        return this.withStore(storeName, 'readwrite', (store) => store.delete(id));
    }

    async saveFavorite(peak) {
        const safeName = encodeURIComponent(peak.name || 'peak');
        const lat = Number(peak.latitude).toFixed(5);
        const lng = Number(peak.longitude).toFixed(5);
        return this.put('favorites', { id: `peak_${safeName}_${lat}_${lng}`, ...peak, updatedAt: Date.now() });
    }

    async removeFavorite(id) {
        return this.delete('favorites', id);
    }

    async getFavorites() {
        return this.getAll('favorites');
    }

    async saveProgress(key, payload) {
        return this.put('progress', { id: key, payload, updatedAt: Date.now() });
    }

    async getProgress(key) {
        const record = await this.get('progress', key);
        return record ? record.payload : null;
    }

    async saveDownloadedMap(mapInfo) {
        return this.put('maps', { id: mapInfo.id, ...mapInfo, updatedAt: Date.now() });
    }

    async getDownloadedMaps() {
        return this.getAll('maps');
    }

    async queueChange(change) {
        await this.init();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction('queue', 'readwrite');
            const req = tx.objectStore('queue').add({ ...change, createdAt: Date.now() });
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    }

    async getQueuedChanges() {
        const items = await this.getAll('queue');
        return items.sort((a, b) => a.id - b.id);
    }

    async removeQueuedChange(id) {
        return this.delete('queue', id);
    }

    async savePeaksData(peaks) {
        return this.put('peaks', { id: 'all_peaks', peaks, updatedAt: Date.now() });
    }

    async getPeaksData() {
        const data = await this.get('peaks', 'all_peaks');
        return data ? data.peaks : [];
    }
}

window.OfflineStorage = OfflineStorage;
window.offlineStorage = new OfflineStorage();
