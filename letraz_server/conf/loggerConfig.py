from pathlib import Path


class LoggingConfig:
    def __init__(self, log_dir, project_name=None):
        self.__LOG_DIR = Path(log_dir)
        self.__PROJECT_NAME = project_name or 'letraz'
        self.__MAIN_LOGGER = {
            'handlers': ['development_logfile', 'production_logfile', 'production_console'],
            'level': 'DEBUG',
        }
        self.__formatters = {
            'simple': {
                'format': 'LOG: [%(asctime)s] %(levelname)s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'verbose': {
                'format': 'LOG: [%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        }
        self.__handlers = {
            'console': {
                'level': 'DEBUG',
                'filters': ['require_debug_true'],
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'production_console': {
                'level': 'DEBUG',
                'filters': ['require_debug_false'],
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'development_logfile': {
                'level': 'DEBUG',
                'filters': ['require_debug_true'],

                'class': 'logging.handlers.RotatingFileHandler',
                'filename': self.__LOG_DIR / f'{self.__PROJECT_NAME}_dev.log',
                'maxBytes': 1024 * 1024 * 10,  # 10MB
                'backupCount': 5,

                'formatter': 'verbose'
            },
            'production_logfile': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': self.__LOG_DIR / f'{self.__PROJECT_NAME}_production.log',
                'maxBytes': 1024 * 1024 * 100,  # 100MB
                'backupCount': 5,
                'formatter': 'simple'
            },
            'dba_logfile': {
                'level': 'DEBUG',
                'filters': ['require_debug_false', 'require_debug_true'],
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': self.__LOG_DIR / f'{self.__PROJECT_NAME}_dba.log',
                'formatter': 'simple'
            }
        }

    def connect_logtail(self, host, token):
        if host and token:
            self.__handlers['logtail'] = {
                'level': 'INFO',
                'class': 'logtail.LogtailHandler',
                'source_token': token,
                'host': host,
            }
            self.__MAIN_LOGGER['handlers'].append('logtail')
        return self

    def get_config(self):
        return {
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
            'formatters': self.__formatters,
            'handlers': self.__handlers,
            'root': {
                'level': 'DEBUG',
                'handlers': ['console', 'production_console'],
            },
            'loggers': {
                f'{self.__PROJECT_NAME}': self.__MAIN_LOGGER,
                'dba': {
                    'handlers': ['dba_logfile'],
                },
                'django': {
                    'handlers': ['development_logfile', 'production_logfile', 'production_console'],
                    'level': 'INFO',
                },
                'django.request': {
                    'handlers': ['production_console'],
                    'level': 'INFO',
                },
                'django.server': {
                    'handlers': ['production_console'],
                    'level': 'INFO',
                },
                'gunicorn.error': {
                    'handlers': ['production_console'],
                    'level': 'INFO',
                },
                'gunicorn.access': {
                    'handlers': ['production_console'],
                    'level': 'INFO',
                },
                'py.warnings': {
                    'handlers': ['development_logfile'],
                },
            }
        }
