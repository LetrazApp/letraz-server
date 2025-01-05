from pathlib import Path


class LoggingConfig:
    def __init__(self, log_dir, log_file_initial=None):
        self.__LOG_DIR = Path(log_dir)
        self.__LOG_FILE_INITIAL = log_file_initial or 'letraz'
        self.__LOGGING = {
            'version': 1,
            'disable_existing_loggers': True,
            'filters': {
                'require_debug_false': {
                    '()': 'django.utils.log.RequireDebugFalse',
                },
                'require_debug_true': {
                    '()': 'django.utils.log.RequireDebugTrue',
                },
            },
            'formatters': {
                'simple': {
                    'format': 'LOG: [%(asctime)s] %(levelname)s %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'verbose': {
                    'format': 'LOG: [%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'filters': ['require_debug_true'],
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple'
                },
                'development_logfile': {
                    'level': 'DEBUG',
                    'filters': ['require_debug_true'],

                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': self.__LOG_DIR / f'{self.__LOG_FILE_INITIAL}_dev.log',
                    'maxBytes': 1024 * 1024 * 10,  # 10MB
                    'backupCount': 5,

                    'formatter': 'verbose'
                },
                'production_logfile': {
                    'level': 'ERROR',
                    'filters': ['require_debug_false'],
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': self.__LOG_DIR / f'{self.__LOG_FILE_INITIAL}_production.log',
                    'maxBytes': 1024 * 1024 * 100,  # 100MB
                    'backupCount': 5,
                    'formatter': 'simple'
                },
                'dba_logfile': {
                    'level': 'DEBUG',
                    'filters': ['require_debug_false', 'require_debug_true'],
                    'class': 'logging.handlers.WatchedFileHandler',
                    'filename': self.__LOG_DIR / f'{self.__LOG_FILE_INITIAL}_dba.log',
                    'formatter': 'simple'
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['console'],
            },
            'loggers': {
                f'{self.__LOG_FILE_INITIAL}': {
                    'handlers': ['development_logfile', 'production_logfile'],
                },
                'dba': {
                    'handlers': ['dba_logfile'],
                },
                'django': {
                    'handlers': ['development_logfile', 'production_logfile'],
                },
                'py.warnings': {
                    'handlers': ['development_logfile'],
                },
            }
        }

    def get_config(self):
        return self.__LOGGING
