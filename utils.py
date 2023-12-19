import logging
import sys


def handler(signum, frame):
    logging.info('Stopping the script ....')
    sys.exit(0)