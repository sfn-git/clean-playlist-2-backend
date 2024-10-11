import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler(f'{os.getcwd()}/output.log'),
        logging.StreamHandler()
    ]
)