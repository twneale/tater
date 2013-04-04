
LOG_MSG_MAXWIDTH = 300

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'form at': "%(asctime)s %(levelname)s %(name)s: %(message)s",
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'default': {'level': 'DEBUG',
                    'class': 'tater.utils.ansiterm.ColorizingStreamHandler',
                    'formatter': 'standard'},
    },
    'loggers': {
        'tater.Lexer': {
            'handlers': ['default'], 'level': 'DEBUG', 'propagate': False
        },
    },
}
