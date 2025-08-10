# logger_setup.py
import logging
import sys
import os
import platform
from logging.handlers import RotatingFileHandler

def get_log_file_path():
    """Finds a safe, user-accessible location for the log file."""
    app_name = "UniversalDocSearch"

    if platform.system() == "Windows":
        log_dir = os.path.join(os.getenv('LOCALAPPDATA'), app_name)
    else:
        home_dir = os.path.expanduser('~')
        if platform.system() == "Darwin": # macOS
             log_dir = os.path.join(home_dir, 'Library', 'Application Support', app_name)
        else: # Linux
             log_dir = os.path.join(home_dir, f'.{app_name}')

    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'app_errors.log')

def setup_global_logging():
    """
    Configures the root logger and sets up global exception handlers.
    This should be called ONCE at the very start of the application.
    """
    log_file_path = get_log_file_path()

    log_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5*1024*1024, # 5MB
        backupCount=2,
        encoding='utf-8'
    )
    
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s'
    )
    log_handler.setFormatter(log_formatter)
    
    root_logger = logging.getLogger()
    
    # --- THIS IS THE KEY CHANGE ---
    # Set the level to ERROR. This means only ERROR and CRITICAL
    # messages will be processed by the handler and written to the file.
    # INFO and WARNING messages will be ignored.
    root_logger.setLevel(logging.ERROR)
    # ----------------------------
    
    root_logger.addHandler(log_handler)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        # Use CRITICAL for uncaught exceptions, as they are fatal to the app's execution.
        root_logger.critical(
            "Uncaught exception:",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception
    
    def handle_thread_exception(args):
        root_logger.critical(
            "Uncaught exception in thread:",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
        )

    threading.excepthook = handle_thread_exception

    # This print statement is still useful to show the user where logs *would* go.
    print(f"Error logging configured. Critical errors will be saved to: {log_file_path}")