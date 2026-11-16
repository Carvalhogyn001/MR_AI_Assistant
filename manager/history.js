"use strict";

// One record per message keeps simultaneous tabs from overwriting each other.
function openConversation() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("mr-robot.conversation", 1);
    request.onupgradeneeded = () => {
      const messages = request.result.createObjectStore("messages", {autoIncrement: true});
      messages.createIndex("image", "imageId", {unique: true});
      request.result.createObjectStore("preferences");
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(Error("Conversation storage is busy"));
  });
}

async function conversationStorage(database, mode, update) {
  const db = await database;
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(["messages", "preferences"], mode);
    const request = update(transaction.objectStore("messages"), transaction.objectStore("preferences"));
    transaction.oncomplete = () => resolve(request?.result);
    transaction.onabort = () => reject(transaction.error);
  });
}
