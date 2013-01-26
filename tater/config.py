


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "%(asctime)s %(levelname)s %(name)s: %(message)s",
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'default': {'level': 'DEBUG',
                    'class': 'tater.utils.ansiterm.ColorizingStreamHandler',
                    'formatter': 'standard'},
    },
    'loggers': {
        'tater.Tokenizer': {
            'handlers': ['default'], 'level': 'DEBUG', 'propagate': False
        },
    },
}