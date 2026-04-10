/**
 * WebSocket Alert Client for SecuWatch 2.0
 * 
 * Usage:
 *   const client = new AlertClient('ws://localhost:8000/ws/alerts');
 *   client.onAlert = (alert) => console.log('New alert:', alert);
 *   client.connect();
 */

class AlertClient {
  /**
   * Initialize the alert client
   * @param {string} url - WebSocket URL (e.g., 'ws://localhost:8000/ws/alerts')
   * @param {Object} options - Configuration options
   * @param {number} options.reconnectInterval - Time in ms before reconnection attempt (default: 3000)
   * @param {number} options.maxReconnectAttempts - Max reconnection attempts (default: 5)
   */
  constructor(url, options = {}) {
    this.url = url;
    this.ws = null;
    this.connected = false;
    this.reconnectInterval = options.reconnectInterval || 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    this.reconnectAttempts = 0;
    
    // Callbacks
    this.onAlert = null;
    this.onConnect = null;
    this.onDisconnect = null;
    this.onError = null;
  }

  /**
   * Connect to the WebSocket server
   */
  connect() {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = () => this.handleClose();
      this.ws.onerror = (event) => this.handleError(event);
    } catch (error) {
      this.log('error', `Failed to create WebSocket: ${error.message}`);
      if (this.onError) {
        this.onError(error);
      }
    }
  }

  /**
   * Disconnect from the server
   */
  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
    }
  }

  /**
   * Handle WebSocket connection opened
   * @private
   */
  handleOpen() {
    this.connected = true;
    this.reconnectAttempts = 0;
    this.log('info', 'Connected to alert stream');
    
    if (this.onConnect) {
      this.onConnect();
    }
  }

  /**
   * Handle incoming messages
   * @private
   */
  handleMessage(event) {
    try {
      const alert = JSON.parse(event.data);
      this.log('info', `Alert received: ${alert.type} (${alert.severity})`);
      
      if (this.onAlert) {
        this.onAlert(alert);
      }
    } catch (error) {
      this.log('error', `Failed to parse alert: ${error.message}`);
    }
  }

  /**
   * Handle WebSocket connection closed
   * @private
   */
  handleClose() {
    this.connected = false;
    this.log('warning', 'Disconnected from alert stream');
    
    if (this.onDisconnect) {
      this.onDisconnect();
    }
    
    // Attempt to reconnect
    this.attemptReconnect();
  }

  /**
   * Handle WebSocket errors
   * @private
   */
  handleError(event) {
    this.log('error', 'WebSocket error occurred');
    
    if (this.onError) {
      this.onError(event);
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   * @private
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.log('error', `Failed to reconnect after ${this.maxReconnectAttempts} attempts`);
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * this.reconnectAttempts;
    
    this.log('warning', `Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => this.connect(), delay);
  }

  /**
   * Log a message
   * @private
   */
  log(level, message) {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = `[${timestamp}] [AlertClient] [${level.toUpperCase()}]`;
    console.log(`${prefix} ${message}`);
  }

  /**
   * Check if connected
   * @returns {boolean}
   */
  isConnected() {
    return this.connected;
  }
}


/**
 * Alert Display Manager
 * Handles displaying alerts in the UI
 */
class AlertDisplayManager {
  /**
   * Initialize the display manager
   * @param {string} containerId - ID of the container to display alerts in
   * @param {Object} options - Configuration options
   * @param {number} options.maxAlerts - Maximum alerts to keep displayed (default: 10)
   * @param {number} options.autoRemoveDelay - Time in ms before auto-removing alert (default: 0 = no auto-remove)
   */
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Container with ID "${containerId}" not found`);
    }
    
    this.maxAlerts = options.maxAlerts || 10;
    this.autoRemoveDelay = options.autoRemoveDelay || 0;
    this.alertCount = 0;
  }

  /**
   * Display an alert
   * @param {Object} alert - Alert object from WebSocket
   */
  displayAlert(alert) {
    if (!this.container) return;

    this.alertCount++;
    const alertElement = this.createAlertElement(alert, this.alertCount);
    
    // Add to container (prepend to show newest first)
    this.container.insertBefore(alertElement, this.container.firstChild);
    
    // Trigger animation
    setTimeout(() => alertElement.classList.add('show'), 10);
    
    // Remove old alerts if exceeding max
    while (this.container.children.length > this.maxAlerts) {
      const lastAlert = this.container.lastChild;
      lastAlert.classList.remove('show');
      setTimeout(() => lastAlert.remove(), 300);
    }

    // Auto-remove after delay if configured
    if (this.autoRemoveDelay > 0) {
      setTimeout(() => this.removeAlertElement(alertElement), this.autoRemoveDelay);
    }
  }

  /**
   * Create an alert HTML element
   * @private
   * @returns {HTMLElement}
   */
  createAlertElement(alert, alertNumber) {
    const div = document.createElement('div');
    const severityClass = `severity-${alert.severity.toLowerCase()}`;
    const timestamp = new Date(alert.created_at).toLocaleString();

    div.className = `alert ${severityClass}`;
    div.innerHTML = `
      <div class="alert-header">
        <span class="alert-number">#${alertNumber}</span>
        <span class="alert-severity">${alert.severity}</span>
        <span class="alert-type">${alert.type}</span>
        <span class="alert-time">${timestamp}</span>
      </div>
      <div class="alert-body">
        <p class="alert-description">${this.escapeHtml(alert.description)}</p>
        <div class="alert-metadata">
          <span>Alert ID: ${alert.id}</span>
          <span>Device ID: ${alert.device_id}</span>
        </div>
      </div>
      <button class="alert-close" onclick="this.parentElement.remove()">×</button>
    `;

    return div;
  }

  /**
   * Remove an alert element
   * @private
   */
  removeAlertElement(element) {
    element.classList.remove('show');
    setTimeout(() => element.remove(), 300);
  }

  /**
   * Escape HTML to prevent XSS
   * @private
   */
  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  /**
   * Clear all alerts
   */
  clearAlerts() {
    while (this.container.firstChild) {
      this.container.removeChild(this.container.firstChild);
    }
  }
}


/**
 * Example CSS for alerts
 * Add this to your stylesheet:
 */
const ALERT_STYLES = `
.alert {
  padding: 16px;
  margin: 8px 0;
  border-radius: 4px;
  background: #f5f5f5;
  border-left: 4px solid #999;
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.alert.show {
  opacity: 1;
}

.alert-header {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
}

.alert-number {
  font-weight: bold;
  color: #666;
}

.alert-severity {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
}

.alert-type {
  flex: 1;
  color: #333;
}

.alert-time {
  color: #999;
  font-size: 12px;
}

.alert-description {
  margin: 8px 0;
  color: #333;
  line-height: 1.5;
}

.alert-metadata {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.alert-close {
  position: absolute;
  right: 12px;
  top: 12px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

/* Severity colors */
.severity-high {
  background: #ffebee;
  border-left-color: #d32f2f;
}

.severity-high .alert-severity {
  background: #d32f2f;
  color: white;
}

.severity-medium {
  background: #fff3e0;
  border-left-color: #f57c00;
}

.severity-medium .alert-severity {
  background: #f57c00;
  color: white;
}

.severity-low {
  background: #e8f5e9;
  border-left-color: #388e3c;
}

.severity-low .alert-severity {
  background: #388e3c;
  color: white;
}
`;

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AlertClient, AlertDisplayManager };
}
