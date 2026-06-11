import logging
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logger(config):
    # Determine log directory
    if os.name == 'nt':
        log_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'autoHao', 'logs')
    else:
        log_dir = os.path.join(os.path.expanduser('~'), '.config', 'autoHao', 'logs')
        
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            pass

    log_file = os.path.join(log_dir, 'autoHao.log')
    retention_days = int(config.get("LOG_RETENTION_DAYS", 15))

    logger = logging.getLogger("autoHao")
    logger.setLevel(logging.INFO)
    
    # Prevent adding multiple handlers if setup_logger is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Rotating file handler (1 file per day, keep retention_days backups)
        if retention_days > 0:
            file_handler = TimedRotatingFileHandler(
                log_file, when='D', interval=1, backupCount=retention_days, encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
