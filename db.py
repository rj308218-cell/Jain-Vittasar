import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from the .env file
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Initialize the Supabase client
supabase: Client = create_client(url, key)

def get_invoices():
    response = supabase.table("invoices").select("*").execute()
    return response.data

def add_invoice(invoice_data):
    response = supabase.table("invoices").insert(invoice_data).execute()
    return response.data