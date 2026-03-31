/**
 * WhatsApp Web.js Bridge for Digital FTE
 *
 * This Node.js script provides a bridge between Python watchers and WhatsApp Web
 * using the whatsapp-web.js library.
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

// Configuration
const SESSION_PATH = '.wwebjs_auth';
const MESSAGE_LOG_PATH = 'messages.json';

// Initialize WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth({
        clientId: 'digital-fte',
        dataPath: SESSION_PATH
    }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// Store messages for polling
let messageQueue = [];

// QR Code event - display for user to scan
client.on('qr', (qr) => {
    console.log('[WhatsApp Bridge] QR Code received. Scan with WhatsApp mobile app:');
    qrcode.generate(qr, { small: true });
});

// Ready event - client is authenticated and ready
client.on('ready', () => {
    console.log('[WhatsApp Bridge] Client is ready!');
    console.log('[WhatsApp Bridge] Listening for messages...');
});

// Authentication success
client.on('authenticated', () => {
    console.log('[WhatsApp Bridge] Authentication successful');
});

// Authentication failure
client.on('auth_failure', (msg) => {
    console.error('[WhatsApp Bridge] Authentication failed:', msg);
    process.exit(1);
});

// Disconnected event
client.on('disconnected', (reason) => {
    console.log('[WhatsApp Bridge] Client disconnected:', reason);
    process.exit(0);
});

// Message received event
client.on('message', async (message) => {
    try {
        const contact = await message.getContact();
        const chat = await message.getChat();

        const messageData = {
            id: message.id._serialized,
            from: message.from,
            fromName: contact.pushname || contact.name || 'Unknown',
            body: message.body,
            timestamp: new Date(message.timestamp * 1000).toISOString(),
            isGroup: chat.isGroup,
            groupName: chat.isGroup ? chat.name : null
        };

        // Add to message queue
        messageQueue.push(messageData);

        // Log message
        console.log(`[WhatsApp Bridge] Message from ${messageData.fromName}: ${messageData.body.substring(0, 50)}...`);

        // Persist messages to file for Python polling
        saveMessages();

    } catch (error) {
        console.error('[WhatsApp Bridge] Error processing message:', error);
    }
});

// Save messages to JSON file for Python polling
function saveMessages() {
    try {
        fs.writeFileSync(
            path.join(__dirname, MESSAGE_LOG_PATH),
            JSON.stringify(messageQueue, null, 2)
        );
    } catch (error) {
        console.error('[WhatsApp Bridge] Error saving messages:', error);
    }
}

// Clear processed messages (called by Python watcher)
function clearMessages() {
    messageQueue = [];
    saveMessages();
}

// Handle process termination
process.on('SIGINT', () => {
    console.log('\n[WhatsApp Bridge] Shutting down...');
    client.destroy();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n[WhatsApp Bridge] Shutting down...');
    client.destroy();
    process.exit(0);
});

// Initialize client
console.log('[WhatsApp Bridge] Starting WhatsApp Web.js client...');
client.initialize();

// Export for IPC (if needed)
module.exports = {
    client,
    messageQueue,
    clearMessages
};
