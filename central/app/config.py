import os

from dotenv import load_dotenv

load_dotenv()

NODE_ID = os.getenv("NODE_ID")

if not NODE_ID:
    raise RuntimeError("NODE_ID doit être défini dans le fichier .env")