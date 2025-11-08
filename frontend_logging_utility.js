/**
 * Frontend Logging Utility
 * Sends all frontend logs to the backend API which writes them to debug.log
 * 
 * Usage:
 *   import { setupFrontendLogging } from './frontend_logging_utility';
 *   setupFrontendLogging();
 * 
 * This will intercept console.log, console.error, console.warn, and console.debug
 * and send them to the backend API endpoint /logs/frontend
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8003';

class FrontendLogger {
    constructor() {
        this.logBuffer = [];
        this.flushInterval = 5000; // Flush logs every 5 seconds
        this.maxBufferSize = 50;
        this.setupInterceptors();
        this.startFlushTimer();
    }

    setupInterceptors() {
        // Store original console methods
        const originalLog = console.log;
        const originalError = console.error;
        const originalWarn = console.warn;
        const originalDebug = console.debug;
        const originalInfo = console.info;

        // Intercept console.log
        console.log = (...args) => {
            originalLog.apply(console, args);
            this.log('INFO', this.formatMessage(args), 'console');
        };

        // Intercept console.error
        console.error = (...args) => {
            originalError.apply(console, args);
            this.log('ERROR', this.formatMessage(args), 'console');
        };

        // Intercept console.warn
        console.warn = (...args) => {
            originalWarn.apply(console, args);
            this.log('WARN', this.formatMessage(args), 'console');
        };

        // Intercept console.debug
        console.debug = (...args) => {
            originalDebug.apply(console, args);
            this.log('DEBUG', this.formatMessage(args), 'console');
        };

        // Intercept console.info
        console.info = (...args) => {
            originalInfo.apply(console, args);
            this.log('INFO', this.formatMessage(args), 'console');
        };

        // Intercept unhandled errors
        window.addEventListener('error', (event) => {
            this.log('ERROR', `Unhandled error: ${event.message}`, 'error', {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        // Intercept unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.log('ERROR', `Unhandled promise rejection: ${event.reason}`, 'promise', {
                reason: String(event.reason),
                stack: event.reason?.stack
            });
        });
    }

    formatMessage(args) {
        return args.map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');
    }

    log(level, message, category = 'frontend', metadata = null) {
        const logEntry = {
            level,
            message,
            category,
            metadata,
            timestamp: new Date().toISOString()
        };

        this.logBuffer.push(logEntry);

        // Flush if buffer is full
        if (this.logBuffer.length >= this.maxBufferSize) {
            this.flushLogs();
        }
    }

    async flushLogs() {
        if (this.logBuffer.length === 0) return;

        const logsToSend = [...this.logBuffer];
        this.logBuffer = [];

        try {
            // Send logs to backend
            const response = await fetch(`${API_BASE_URL}/logs/frontend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    level: 'INFO',
                    message: `Batch log: ${logsToSend.length} entries`,
                    category: 'frontend',
                    metadata: { logs: logsToSend }
                })
            });

            if (!response.ok) {
                console.warn('Failed to send logs to backend');
            }
        } catch (error) {
            // Silently fail - don't create infinite loop
            // Original console methods are still available
        }
    }

    startFlushTimer() {
        setInterval(() => {
            this.flushLogs();
        }, this.flushInterval);
    }

    // Manual log method for application use
    async sendLog(level, message, category = 'app', metadata = null) {
        try {
            await fetch(`${API_BASE_URL}/logs/frontend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    level,
                    message,
                    category,
                    metadata
                })
            });
        } catch (error) {
            // Fallback to console if API unavailable
            console.error('Failed to send log to backend:', error);
        }
    }
}

// Export singleton instance
let loggerInstance = null;

export function setupFrontendLogging() {
    if (!loggerInstance) {
        loggerInstance = new FrontendLogger();
        console.log('[FrontendLogger] Logging initialized - all logs will be sent to debug.log');
    }
    return loggerInstance;
}

export function getLogger() {
    if (!loggerInstance) {
        setupFrontendLogging();
    }
    return loggerInstance;
}

// Auto-setup if imported
if (typeof window !== 'undefined') {
    setupFrontendLogging();
}

