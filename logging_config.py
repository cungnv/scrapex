


default_settings = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "full": {
            "format": "%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s: %(message)s"
        },        
        
        "no_time": {
            "format": "%(name)s - %(levelname)s: %(message)s"
        },

        "console": {
            "format": "%(levelname)s: %(message)s"
        },

        "message_only": {
            "format": "%(message)s"
        }

    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "console",
            "stream": "ext://sys.stdout"
        },

        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "full",
            "filename": "log.txt",
            "mode": "w",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    },

    "loggers": {
        "requests.packages.urllib3.connectionpool": {
            "level": "ERROR",
            "handlers": ["file_handler"],
            "propagate": "no"
        }
    },

    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file_handler"]
    }
}
