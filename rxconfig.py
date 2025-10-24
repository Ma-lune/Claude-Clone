from dotenv import load_dotenv
import reflex as rx

# Load environment variables from .env (if present)
load_dotenv()

config = rx.Config(app_name="app")
