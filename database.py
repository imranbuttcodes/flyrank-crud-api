from sqlmodel import SQLModel, Session, create_engine
from models import Task
from dotenv import load_dotenv
import os

from supabase import create_client, Client


load_dotenv()


sqlite_url = os.getenv('DATABASE_URL', "sqlite:///tasks.db")
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not found in .env")
# This creates the powerful 'supabase' object we will use for Auth
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Server running and connected to Supabase!")