"""
Logging utilities.
"""
import sys
from enum import Enum

class LogColor:
    """
    Logging color.
    """

    INFO = '\033[94m'
    WARNING = '\033[93m'
    ERROR = '\033[91m\033[1m'
    ENDC = '\033[0m'


class LogLevel(Enum):
    """
    Logging level.
    """

    INFO = 1
    WARNING = 2
    ERROR = 3

def log(output,level=LogLevel.INFO):
    """
    Log a message.

    :param output: message
    :type output: str
    :param level: logging level
    :type level: LogLevel
    """

    if level == LogLevel.INFO:
        sys.stderr.write(LogColor.INFO)
    elif level == LogLevel.WARNING:
        sys.stderr.write(LogColor.WARNING)
    elif level == LogLevel.ERROR:
        sys.stderr.write(LogColor.ERROR)
    sys.stderr.write(str(output))
    sys.stderr.write(LogColor.ENDC)
    sys.stderr.write("\n")
    sys.stderr.flush()
