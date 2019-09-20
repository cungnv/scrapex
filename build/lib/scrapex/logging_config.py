import logging
from scrapex import common

default_settings = {
	"version": 1,
	"disable_existing_loggers": False,
	"formatters": {
		"to_file": {
			"format": u"%(asctime)s - %(name)s - %(module)s - %(funcName)s() - %(levelname)s: %(message)s",
			"datefmt": "%Y-%m-%d %H:%M"

		},        
		
		"to_console": {
			"format": "%(levelname)s: %(message)s"
		}
		
	},

	"handlers": {
		"console": {
			"class": "logging.StreamHandler",
			"level": "INFO",
			"formatter": "to_console",
			"stream": "ext://sys.stdout"
		},

		"file_handler": {
			"class": "logging.handlers.RotatingFileHandler",
			"level": "DEBUG",
			"formatter": "to_file",
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
		"handlers": [
		"console", 
		"file_handler"
		]
	}
}

def set_default(log_file = 'log.txt', preserve=False):
	
	settings = default_settings.copy()

	if log_file:
		settings['handlers']['file_handler']['filename'] = log_file

		if not preserve:
			common.put_file(log_file,'')	
	else:
		#just log to console
		settings['root']['handlers'] = ['console']

	logging.config.dictConfig(settings)

	return logging.getLogger('scrapex')


