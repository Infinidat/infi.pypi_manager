import requests
import logging
requests.packages.urllib3.disable_warnings()
logging.getLogger('requests').setLevel(logging.CRITICAL)
