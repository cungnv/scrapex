import logging
from scrapex import common

default_settings = {
	"version": 1,
	"disable_existing_loggers": False,
	"formatters": {
		"full": {
			"format": "%(asctime)s - %(name)s - %(module)s - %(funcName)s() - %(levelname)s: %(message)s"
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

def set_default(log_file = 'log.txt', preserve=False):
	

	if log_file:
		default_settings['handlers']['file_handler']['filename'] = log_file

	if not preserve:
		common.put_file(log_file,'')	

	logging.config.dictConfig(default_settings)

	return logging.getLogger('scrapex')


