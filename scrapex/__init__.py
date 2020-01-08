#encoding: utf-8

from .core import Scraper
from . import common
from .common import DataItem
from .doc import Doc
from .node import Node
from . import excellib


#to avoid warning: "No handlers could be found...."
import logging
from logging import NullHandler
logging.getLogger(__name__).addHandler(NullHandler())


