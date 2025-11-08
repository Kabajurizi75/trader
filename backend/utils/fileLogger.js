const fs = require('fs');
const path = require('path');

class FileLogger {
  constructor() {
    this.logDir = path.join(__dirname, '../../logs');
    this.debugLogFile = path.join(this.logDir, 'debug.log');
    this.errorLogFile = path.join(this.logDir, 'error.log');
    this.tradeLogFile = path.join(this.logDir, 'trading.log');
    
    this.ensureLogDirectory();
    
    // Initialize log files
    this.initLogFiles();
  }

  ensureLogDirectory() {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  initLogFiles() {
    const initMessage = `\n=== Amiga Trader Logs Started at ${new Date().toISOString()} ===\n`;
    
    if (!fs.existsSync(this.debugLogFile)) {
      fs.writeFileSync(this.debugLogFile, initMessage);
    }
    if (!fs.existsSync(this.errorLogFile)) {
      fs.writeFileSync(this.errorLogFile, initMessage);
    }
    if (!fs.existsSync(this.tradeLogFile)) {
      fs.writeFileSync(this.tradeLogFile, initMessage);
    }
  }

  formatLogEntry(level, message, metadata = {}) {
    const timestamp = new Date().toISOString();
    const metaStr = Object.keys(metadata).length > 0 ? ` | META: ${JSON.stringify(metadata)}` : '';
    return `[${timestamp}] [${level}] ${message}${metaStr}\n`;
  }

  writeToFile(filePath, entry) {
    try {
      fs.appendFileSync(filePath, entry);
    } catch (error) {
      console.error(`Failed to write to log file ${filePath}:`, error);
    }
  }

  debug(message, metadata = {}) {
    const entry = this.formatLogEntry('DEBUG', message, metadata);
    this.writeToFile(this.debugLogFile, entry);
    logger.debug(message, metadata);
  }

  info(message, metadata = {}) {
    const entry = this.formatLogEntry('INFO', message, metadata);
    this.writeToFile(this.debugLogFile, entry);
    logger.info(message, metadata);
  }

  warn(message, metadata = {}) {
    const entry = this.formatLogEntry('WARN', message, metadata);
    this.writeToFile(this.debugLogFile, entry);
    console.warn(`${message}`, metadata);
  }

  error(message, metadata = {}) {
    const entry = this.formatLogEntry('ERROR', message, metadata);
    this.writeToFile(this.debugLogFile, entry);
    this.writeToFile(this.errorLogFile, entry);
    console.error(`${message}`, metadata);
  }

  trade(action, data = {}) {
    const entry = this.formatLogEntry('TRADE', `${action}`, data);
    this.writeToFile(this.tradeLogFile, entry);
    this.writeToFile(this.debugLogFile, entry);
    logger.trade(action, data);
  }

  userAction(action, data = {}) {
    const entry = this.formatLogEntry('USER', action, data);
    this.writeToFile(this.debugLogFile, entry);
    logger.userAction(action, data);
  }

  apiRequest(method, url, data = {}) {
    const entry = this.formatLogEntry('API', `${method} ${url}`, data);
    this.writeToFile(this.debugLogFile, entry);
    logger.api(method, url, data);
  }

  performance(metric, value, data = {}) {
    const entry = this.formatLogEntry('PERF', `${metric}=${value}`, data);
    this.writeToFile(this.debugLogFile, entry);
    logger.performance(metric, value, data);
  }

  // Rotate logs if they get too large 
  rotateLogs() {
    const maxSize = 10 * 1024 * 1024; 
    
    [this.debugLogFile, this.errorLogFile, this.tradeLogFile].forEach(logFile => {
      try {
        const stats = fs.statSync(logFile);
        if (stats.size > maxSize) {
          const backupFile = `${logFile}.${Date.now()}.bak`;
          fs.renameSync(logFile, backupFile);
          
          const initMessage = `\n=== Log Rotated at ${new Date().toISOString()} ===\n`;
          fs.writeFileSync(logFile, initMessage);
          
          this.info(`Log rotated: ${path.basename(logFile)}`, { 
            oldSize: stats.size,
            backupFile: path.basename(backupFile)
          });
        }
      } catch (error) {
        console.error(`Error rotating log ${logFile}:`, error);
      }
    });
  }

  // Get log stats
  getLogStats() {
    try {
      const stats = {
        debugLog: { exists: false, size: 0 },
        errorLog: { exists: false, size: 0 },
        tradeLog: { exists: false, size: 0 }
      };

      if (fs.existsSync(this.debugLogFile)) {
        const debugStats = fs.statSync(this.debugLogFile);
        stats.debugLog = { exists: true, size: debugStats.size };
      }

      if (fs.existsSync(this.errorLogFile)) {
        const errorStats = fs.statSync(this.errorLogFile);
        stats.errorLog = { exists: true, size: errorStats.size };
      }

      if (fs.existsSync(this.tradeLogFile)) {
        const tradeStats = fs.statSync(this.tradeLogFile);
        stats.tradeLog = { exists: true, size: tradeStats.size };
      }

      return stats;
    } catch (error) {
      this.error('Failed to get log stats', { error: error.message });
      return null;
    }
  }

  // Clear all logs
  clearLogs() {
    try {
      const files = [this.debugLogFile, this.errorLogFile, this.tradeLogFile];
      files.forEach(file => {
        if (fs.existsSync(file)) {
          fs.unlinkSync(file);
        }
      });
      
      this.initLogFiles();
      this.info('All logs cleared and reinitialized');
    } catch (error) {
      console.error('Failed to clear logs:', error);
    }
  }
}

const fileLogger = new FileLogger();

setInterval(() => {
  fileLogger.rotateLogs();
}, 60 * 60 * 1000);

module.exports = fileLogger;