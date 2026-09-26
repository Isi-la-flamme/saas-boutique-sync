import os

from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
NODE_ID = os.getenv("NODE_ID")

if not TENANT_ID:
    raise RuntimeError("TENANT_ID doit être défini dans le fichier .env")

if not NODE_ID:
    raise RuntimeError("NODE_ID doit être défini dans le fichier .env")