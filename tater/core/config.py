import os
import logging


LOG_MSG_MAXWIDTH = 300
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
        'tater': {
            'handlers': ['default'], 'level': 'DEBUG', 'propagate': False
        },
        'tater.Lexer': {
            'handlers': ['default'], 'level': 'DEBUG', 'propagate': False
        },
    },
}

LOGLEVEL = None
if not os.environ.get('TATER_IGNORE_COMMANDLINE'):
    import argparse
    parser = argparse.ArgumentParser(description='Tater')
    parser.add_argument('--fatal', action='store_true')
    parser.add_argument('--critical', action='store_true')
    parser.add_argument('--warning', action='store_true')
    parser.add_argument('--error', action='store_true')
    parser.add_argument('--info', action='store_true')
    parser.add_argument('--debug', action='store_true')
    args, unknown = parser.parse_known_args()

    loglevels = []
    for level in 'critical info debug error fatal warning'.split():
        if getattr(args, level):
            loglevel = getattr(logging, level.upper())
            loglevels.append(loglevel)

    if loglevels:
        LOGLEVEL = max(loglevels)
