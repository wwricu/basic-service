from dotenv import load_dotenv

from wwricu import config

load_dotenv(override=True)
config.initialize_app()
