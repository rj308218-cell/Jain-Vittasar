import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd

# Load environment variables (Local .env or Streamlit secrets)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="Jain Vittasar - Cloud Edition", layout="wide")

st.title("🏢 Jain Vittasar - Financial Intelligence & Billing (Cloud Edition)")

# Connection Verification Widget
try:
    response = supabase.table("inventory").select("id").limit(1).execute()
    st.success("Connected to Supabase cloud database successfully!")
except Exception as e:
    st.error(f"Supabase connection error: {e}")

# Navigation Sidebar for Cloud App
st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", ["Home / Company Profile", "Sales & Billing", "Inventory Control"])

if choice == "Home / Company Profile":
    st.subheader("Company Profile Management")
    # Add your Streamlit form inputs here instead of Tkinter entries
    company_name = st.text_input("Company Name")
    gstin = st.text_input("GSTIN")
    if st.button("Save Company Profile"):
        try:
            supabase.table("company_profile").insert({"name": company_name, "gstin": gstin}).execute()
            st.success("Company profile saved to cloud successfully!")
        except Exception as err:
            st.error(f"Error saving profile: {err}")

elif choice == "Sales & Billing":
    st.subheader("Billing Module")
    st.info("Build your web-based invoice generation workflow here using Streamlit inputs.")

elif choice == "Inventory Control":
    st.subheader("Inventory Management")
    try:
        inv_data = supabase.table("inventory").select("*").execute()
        if inv_data.data:
            df_inv = pd.DataFrame(inv_data.data)
            st.dataframe(df_inv)
        else:
            st.info("No inventory items found.")
    except Exception as e:
        st.error(f"Failed to load inventory: {e}")import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import time
from datetime import datetime
import os
import shutil
import hashlib
import secrets
import qrcode
from PIL import Image, ImageTk
from num2words import num2words

# Professional Document Processing & Data Engineering Libraries
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class JainVittasarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jain Vittasar - Financial Intelligence | Tax & Compliance")
        self.root.geometry("1350x880")
        self.root.configure(bg="#F4F6F9")

        self.db_name = "jain_vittasar.db"
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        # Database Initialization Engine (Cloud Supabase Mode)
        self.create_tables()

        # Active Session Variables
        self.company = None
        self.uploaded_logo_path = ""
        self.sales_cart = []  # Virtual Items Cart Memory Core
        self.purchase_cart = [] # Purchase Cart for Multiple Entries
        self.signup_cache = {}
        self.signup_data = {}
        self.entries = {}
        self.party_entries = {}
        self.inv_party_entries = {}
        self.bank_entries = {}

        # Check License Status Before Loading
        self.check_subscription_guard()

    def create_tables(self):
        """Verifies cloud connection to Supabase."""
        try:
            supabase.table("inventory").select("id").limit(1).execute()
            print("Connected to Supabase cloud database successfully!")
        except Exception as e:
            print(f"Supabase connection notice: {e}")

        # 1. Company Profile
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS company_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            business_type TEXT,
            gstin TEXT,
            pan TEXT,
            bank_name TEXT,
            account_no TEXT,
            ifsc TEXT,
            upi_id TEXT,
            state TEXT,
            logo_path TEXT,
            financial_year TEXT)''')

        # Dynamic Column Upgrade Core Strategy for Legacy Databases
        try:
            self.cursor.execute("ALTER TABLE company_profile ADD COLUMN financial_year TEXT")
        except sqlite3.OperationalError: pass
        
        # 2. Master Buyer/Party Ledger Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_name TEXT UNIQUE NOT NULL,
            contact_person TEXT,
            phone TEXT,
            gstin TEXT,
            state TEXT,
            opening_balance REAL DEFAULT 0.0,
            balance_type TEXT DEFAULT 'Dr',
            address TEXT)''')
        
        try:
            self.cursor.execute("ALTER TABLE parties ADD COLUMN address TEXT")
        except sqlite3.OperationalError: pass
        
        # 3. Master Invoices Header Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bills (
            bill_no INTEGER PRIMARY KEY AUTOINCREMENT, 
            date TEXT NOT NULL, 
            customer_name TEXT NOT NULL, 
            grand_total REAL NOT NULL, 
            payment_method TEXT, 
            invoice_type TEXT NOT NULL, 
            due_date TEXT, 
            remarks TEXT, 
            txn_category TEXT NOT NULL, 
            total_tax REAL DEFAULT 0.0, 
            total_discount REAL DEFAULT 0.0)''')
            
        # 4. Itemized Invoice Breakdown Matrix
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            bill_no INTEGER NOT NULL, 
            item_name TEXT NOT NULL, 
            qty INTEGER NOT NULL, 
            price REAL NOT NULL, 
            discount_percent REAL DEFAULT 0.0, 
            tax_rate REAL DEFAULT 0.0, 
            tax_amount REAL DEFAULT 0.0, 
            total_amount REAL NOT NULL, 
            FOREIGN KEY(bill_no) REFERENCES bills(bill_no))''')
        
        # 5. Inventory Ledger Balances Master Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item_name TEXT UNIQUE NOT NULL, 
            stock INTEGER NOT NULL DEFAULT 0, 
            price REAL NOT NULL DEFAULT 0.0,
            hsn_code TEXT DEFAULT '',
            unit TEXT DEFAULT 'Pcs')''')
            
        try:
            self.cursor.execute("ALTER TABLE inventory ADD COLUMN hsn_code TEXT DEFAULT ''")
        except sqlite3.OperationalError: pass
        try:
            self.cursor.execute("ALTER TABLE inventory ADD COLUMN unit TEXT DEFAULT 'Pcs'")
        except sqlite3.OperationalError: pass
        
        # 6. Audit System Ledger Transactions Matrix (Reconciliation Module)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            account_type TEXT NOT NULL, -- 'Cash' or 'Bank'
            account_id INTEGER,         -- Link to bank registry node
            party_name TEXT,
            bill_ref TEXT,
            txn_type TEXT NOT NULL,     -- 'Received' or 'Paid'
            amount REAL NOT NULL,
            remarks TEXT)''')

        # 7. Enterprise Core Bank Registries
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holder_name TEXT NOT NULL,
            account_no TEXT UNIQUE NOT NULL,
            ifsc TEXT NOT NULL,
            bank_branch TEXT NOT NULL,
            opening_balance REAL DEFAULT 0.0,
            as_on_date TEXT)''')

        # Seed default inventory data
        self.cursor.execute("SELECT COUNT(*) FROM inventory")
        if self.cursor.fetchone()[0] == 0:
            default_items = [
                ("Item A", 100, 500.0), 
                ("Item B", 150, 1200.0), 
                ("Service Fee", 9999, 1500.0)
            ]
            self.cursor.executemany("INSERT INTO inventory (item_name, stock, price) VALUES (?, ?, ?)", default_items)
        
        self.conn.commit()

    def clear_root_canvas(self):
        for widget in self.root.winfo_children():
            widget.destroy()
# ========================================================
    # NEW AUTHENTICATION, SIGNUP, AND DUAL LOGIN SYSTEM
    # ========================================================
    def check_subscription_guard(self):
        """Initializes user table and opens the Auth Gateway."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            address TEXT NOT NULL,
            gstin TEXT,
            plan_name TEXT NOT NULL,
            plan_days INTEGER NOT NULL,
            amount_paid REAL NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        self.conn.commit()
        self.show_auth_gateway()

    def show_auth_gateway(self):
        """Main Landing Gateway with 3 Portals."""
        self.clear_root_canvas()
        
        container = tk.Frame(self.root, bg="#FFFFFF", bd=1, relief="solid")
        container.place(relx=0.5, rely=0.5, anchor="center", width=500, height=420)
        
        tk.Frame(container, bg="#003366", height=10).pack(fill="x", side="top")
        
        tk.Label(container, text="JAIN VITTASAR GATEWAY", font=("Arial", 16, "bold"), fg="#003366", bg="#FFFFFF").pack(pady=(25, 5))
        tk.Label(container, text="Select your login type or register a new business", font=("Arial", 9), fg="#666666", bg="#FFFFFF").pack(pady=(0, 25))

        btn_frame = tk.Frame(container, bg="#FFFFFF")
        btn_frame.pack(fill="both", expand=True, padx=40)

        # 1. Customer Login Button
        tk.Button(
            btn_frame, text="1. Customer Login (Active Subscribers)", font=("Arial", 11, "bold"),
            bg="#27AE60", fg="white", bd=0, pady=10, cursor="hand2", command=self.show_customer_login_screen
        ).pack(fill="x", pady=8)

        # 2. Master Login Button
        tk.Button(
            btn_frame, text="2. Master Login (Owner Access)", font=("Arial", 11, "bold"),
            bg="#34495E", fg="white", bd=0, pady=10, cursor="hand2", command=self.show_master_login_screen
        ).pack(fill="x", pady=8)

        # 3. New Signup Button
        tk.Button(
            btn_frame, text="3. Sign Up (New Registration & Buy Plan)", font=("Arial", 11, "bold"),
            bg="#2980B9", fg="white", bd=0, pady=10, cursor="hand2", command=self.show_signup_step1_details
        ).pack(fill="x", pady=(8, 15))

    # --- 1. CUSTOMER LOGIN ---
    def show_customer_login_screen(self):
        self.clear_root_canvas()
        
        container = tk.Frame(self.root, bg="#FFFFFF", bd=1, relief="solid")
        container.place(relx=0.5, rely=0.5, anchor="center", width=420, height=380)
        
        tk.Frame(container, bg="#27AE60", height=8).pack(fill="x", side="top")
        
        tk.Label(container, text="CUSTOMER LOGIN", font=("Arial", 14, "bold"), fg="#27AE60", bg="#FFFFFF").pack(pady=(20, 5))
        tk.Label(container, text="Access your software subscription account", font=("Arial", 9), fg="#666666", bg="#FFFFFF").pack(pady=(0, 15))
        
        f = tk.Frame(container, bg="#FFFFFF")
        f.pack(fill="both", expand=True, padx=35)

        tk.Label(f, text="Username / User ID:", font=("Arial", 9, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(5, 2))
        u_ent = ttk.Entry(f, font=("Arial", 10))
        u_ent.pack(fill="x", ipady=3, pady=(0, 10))

        tk.Label(f, text="Password:", font=("Arial", 9, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(5, 2))
        p_ent = ttk.Entry(f, font=("Arial", 10), show="*")
        p_ent.pack(fill="x", ipady=3, pady=(0, 15))

        def process_customer_login():
            user = u_ent.get().strip()
            pwd = p_ent.get().strip()

            if not user or not pwd:
                messagebox.showerror("Error", "Please enter both Username and Password.")
                return

            try:
                # Query user account from Supabase
                res_user = supabase.table("users").select("*").eq("username", user).eq("password", pwd).execute()
                
                if res_user.data:
                    account = res_user.data[0]
                    
                    # Fetch company profile context from Supabase
                    res_comp = supabase.table("company_profile").select("*").eq("name", account["company_name"]).execute()
                    if res_comp.data:
                        comp_dict = res_comp.data[0]
                        # Map dict to tuple format expected by rest of app
                        self.company = (
                            comp_dict.get("id"), comp_dict.get("name"), comp_dict.get("address"),
                            comp_dict.get("phone"), comp_dict.get("email"), comp_dict.get("business_type"),
                            comp_dict.get("gstin"), comp_dict.get("pan"), comp_dict.get("bank_name"),
                            comp_dict.get("account_no"), comp_dict.get("ifsc"), comp_dict.get("upi_id"),
                            comp_dict.get("state"), comp_dict.get("logo_path"), comp_dict.get("financial_year")
                        )
                    messagebox.showinfo("Success", f"Welcome back, {account['owner_name']}!")
                    self.show_main_dashboard()
                else:
                    messagebox.showerror("Error", "Invalid Customer Username or Password!")
            except Exception as e:
                messagebox.showerror("Error", f"Login failed: {str(e)}")

        tk.Button(f, text="LOGIN TO ACCOUNT", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), bd=0, pady=8, cursor="hand2", command=process_customer_login).pack(fill="x", pady=5)
        tk.Button(f, text="← Back to Main Menu", bg="#7F8C8D", fg="white", font=("Arial", 8), bd=0, pady=4, cursor="hand2", command=self.show_auth_gateway).pack(fill="x", pady=5)

    # --- 2. MASTER LOGIN ---
    def show_master_login_screen(self):
        self.clear_root_canvas()
        
        container = tk.Frame(self.root, bg="#FFFFFF", bd=1, relief="solid")
        container.place(relx=0.5, rely=0.5, anchor="center", width=420, height=380)
        
        tk.Frame(container, bg="#34495E", height=8).pack(fill="x", side="top")
        
        tk.Label(container, text="MASTER / OWNER LOGIN", font=("Arial", 14, "bold"), fg="#34495E", bg="#FFFFFF").pack(pady=(20, 5))
        tk.Label(container, text="Restricted Owner Credentials Access", font=("Arial", 9), fg="#666666", bg="#FFFFFF").pack(pady=(0, 15))
        
        f = tk.Frame(container, bg="#FFFFFF")
        f.pack(fill="both", expand=True, padx=35)

        tk.Label(f, text="Master Login ID:", font=("Arial", 9, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(5, 2))
        m_uid = ttk.Entry(f, font=("Arial", 10))
        m_uid.pack(fill="x", ipady=3, pady=(0, 10))
        m_uid.insert(0, "Admin")

        tk.Label(f, text="Master Password:", font=("Arial", 9, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(5, 2))
        m_pwd = ttk.Entry(f, font=("Arial", 10), show="*")
        m_pwd.pack(fill="x", ipady=3, pady=(0, 15))
        m_pwd.insert(0, "Rj308218@gmail")

        def process_master_login():
            if m_uid.get().strip() == "Admin" and m_pwd.get().strip() == "Rj308218@gmail":
                messagebox.showinfo("Master Auth Passed", "Master System Admin Access Granted.")
                self.show_main_dashboard()
            else:
                messagebox.showerror("Access Denied", "Invalid Master Owner Credentials!")

        tk.Button(f, text="AUTHORIZE MASTER LOGIN", bg="#34495E", fg="white", font=("Arial", 10, "bold"), bd=0, pady=8, cursor="hand2", command=process_master_login).pack(fill="x", pady=5)
        tk.Button(f, text="← Back to Main Menu", bg="#7F8C8D", fg="white", font=("Arial", 8), bd=0, pady=4, cursor="hand2", command=self.show_auth_gateway).pack(fill="x", pady=5)

    # --- 3. SIGNUP SYSTEM ---
    def show_signup_step1_details(self):
        """Step 1: Fill Out Personal & Business Details."""
        self.clear_root_canvas()

        container = tk.Frame(self.root, bg="#FFFFFF", bd=1, relief="solid")
        container.place(relx=0.5, rely=0.5, anchor="center", width=520, height=520)

        tk.Frame(container, bg="#2980B9", height=8).pack(fill="x", side="top")
        tk.Label(container, text="STEP 1: BUSINESS REGISTRATION", font=("Arial", 14, "bold"), fg="#2980B9", bg="#FFFFFF").pack(pady=(15, 5))

        f = tk.Frame(container, bg="#FFFFFF")
        f.pack(fill="both", expand=True, padx=40, pady=10)

        fields = [
            ("Business Name *", "biz_name"),
            ("Owner Full Name *", "owner_name"),
            ("Mobile No. *", "mobile"),
            ("Address *", "address"),
            ("GSTIN (Optional)", "gstin")
        ]

        self.signup_data = {}
        for idx, (label, key) in enumerate(fields):
            tk.Label(f, text=label, font=("Arial", 9, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(4, 1))
            ent = ttk.Entry(f, font=("Arial", 10))
            ent.pack(fill="x", ipady=2, pady=(0, 6))
            self.signup_data[key] = ent

        def proceed_to_plans():
            b_name = self.signup_data["biz_name"].get().strip()
            o_name = self.signup_data["owner_name"].get().strip()
            mob = self.signup_data["mobile"].get().strip()
            addr = self.signup_data["address"].get().strip()

            if not b_name or not o_name or not mob or not addr:
                messagebox.showerror("Error", "Please fill out all mandatory fields (*).")
                return

            self.signup_cache = {
                "biz_name": b_name, "owner_name": o_name,
                "mobile": mob, "address": addr,
                "gstin": self.signup_data["gstin"].get().strip()
            }
            self.show_signup_step2_plan_selection()

        tk.Button(f, text="NEXT: SELECT SUBSCRIPTION PLAN →", bg="#2980B9", fg="white", font=("Arial", 10, "bold"), bd=0, pady=8, cursor="hand2", command=proceed_to_plans).pack(fill="x", pady=15)
        tk.Button(f, text="← Cancel & Return", bg="#7F8C8D", fg="white", font=("Arial", 8), bd=0, pady=4, cursor="hand2", command=self.show_auth_gateway).pack(fill="x")

    def show_signup_step2_plan_selection(self):
        """Step 2: Plan Selection & Discount Calculations."""
        self.clear_root_canvas()

        container = tk.Frame(self.root, bg="#FFFFFF", bd=1, relief="solid")
        container.place(relx=0.5, rely=0.5, anchor="center", width=550, height=520)

        tk.Frame(container, bg="#8E44AD", height=8).pack(fill="x", side="top")
        tk.Label(container, text="STEP 2: SELECT SUBSCRIPTION PLAN", font=("Arial", 14, "bold"), fg="#8E44AD", bg="#FFFFFF").pack(pady=(15, 5))

        f = tk.Frame(container, bg="#FFFFFF")
        f.pack(fill="both", expand=True, padx=30, pady=10)

        # Plan 1: 1 Day
        tk.Button(f, text="Plan 1: Rs. 10 / 1 Day (24 Hours)", font=("Arial", 10, "bold"), bg="#27AE60", fg="white", bd=0, pady=8, cursor="hand2",
                  command=lambda: self.show_signup_step3_payment("1 Day Plan", 1, 10)).pack(fill="x", pady=6)

        # Plan 2: 1 Month
        tk.Button(f, text="Plan 2: Rs. 250 / 1 Month (30 Days)", font=("Arial", 10, "bold"), bg="#2980B9", fg="white", bd=0, pady=8, cursor="hand2",
                  command=lambda: self.show_signup_step3_payment("1 Month Plan", 30, 250)).pack(fill="x", pady=6)

        # Custom Plan Section
        custom_frame = ttk.LabelFrame(f, text=" Plan 3: Custom Plan (10% Off > 3 Months) ", padding=10)
        custom_frame.pack(fill="x", pady=10)

        tk.Label(custom_frame, text="Enter Duration (in Days):", font=("Arial", 9, "bold")).pack(anchor="w")
        days_ent = ttk.Entry(custom_frame, font=("Arial", 10))
        days_ent.pack(fill="x", pady=4)
        days_ent.insert(0, "90")

        calc_lbl = tk.Label(custom_frame, text="", font=("Arial", 9, "bold"), fg="#27AE60")
        calc_lbl.pack(pady=2)

        def calculate_custom_rate(e=None):
            try:
                d = int(days_ent.get().strip())
                if d <= 0: return
                
                # Base rate derived from Plan 1 & Plan 2
                base = d * 10 if d < 30 else (d / 30) * 250
                if d > 90:  # Above 3 Months Subscription
                    discount = base * 0.10
                    final = base - discount
                    calc_lbl.config(text=f"Total: Rs. {final:.2f} (10% Discount Applied! Saved: Rs. {discount:.2f})")
                else:
                    calc_lbl.config(text=f"Total: Rs. {base:.2f}")
            except ValueError: pass

        days_ent.bind("<KeyRelease>", calculate_custom_rate)
        calculate_custom_rate()

        def proceed_custom():
            try:
                d = int(days_ent.get().strip())
                base = d * 10 if d < 30 else (d / 30) * 250
                final = base - (base * 0.10) if d > 90 else base
                self.show_signup_step3_payment(f"Custom ({d} Days)", d, round(final, 2))
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numeric days.")

        tk.Button(custom_frame, text="Proceed with Custom Plan", bg="#8E44AD", fg="white", font=("Arial", 9, "bold"), bd=0, pady=6, cursor="hand2", command=proceed_custom).pack(fill="x", pady=5)

    def show_signup_step3_payment(self, plan_name, days, amount):
        """Step 3: Payment Instructions & Account Credentials Creation."""
        self.clear_root_canvas()

        container = tk.Frame(self.root, bg="#FFFFFF", bd=1, relief="solid")
        container.place(relx=0.5, rely=0.5, anchor="center", width=520, height=580)

        tk.Frame(container, bg="#27AE60", height=8).pack(fill="x", side="top")
        tk.Label(container, text="STEP 3: PAYMENT & CREDENTIAL SETUP", font=("Arial", 13, "bold"), fg="#27AE60", bg="#FFFFFF").pack(pady=(10, 2))

        f = tk.Frame(container, bg="#FFFFFF")
        f.pack(fill="both", expand=True, padx=30, pady=5)

        # Payment Notice Box
        pay_box = tk.LabelFrame(f, text=" Payment Transfer Instructions ", font=("Arial", 9, "bold"), fg="#003366", bg="#FFFFFF", padding=6)
        pay_box.pack(fill="x", pady=2)

        pay_msg = (
            f"Selected Plan: {plan_name} ({days} Days) | Payable: Rs. {amount}/-\n"
            "UPI ID: Rj308218@gmail | Bank Acc: 9829XXXXXXXX (IFSC: SBIN000XXXX)"
        )
        tk.Label(pay_box, text=pay_msg, font=("Arial", 8, "bold"), fg="#333333", bg="#FFFFFF", justify="left").pack(anchor="w")

        # Credentials Fields (Fixed & Prominently Displayed)
        tk.Label(f, text="Setup Login ID / Username *:", font=("Arial", 9, "bold"), fg="#2980B9", bg="#FFFFFF").pack(anchor="w", pady=(6, 2))
        usr_ent = ttk.Entry(f, font=("Arial", 10))
        usr_ent.pack(fill="x", ipady=2, pady=(0, 4))

        tk.Label(f, text="Setup Password *:", font=("Arial", 9, "bold"), fg="#2980B9", bg="#FFFFFF").pack(anchor="w", pady=(2, 2))
        pwd_ent = ttk.Entry(f, font=("Arial", 10), show="*")
        pwd_ent.pack(fill="x", ipady=2, pady=(0, 8))

        def finalize_registration():
            u = usr_ent.get().strip()
            p = pwd_ent.get().strip()

            if not u or not p:
                messagebox.showerror("Error", "Please create a valid Username and Password for logging in.")
                return

            try:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 1. Check if username already exists in Supabase
                check_user = supabase.table("users").select("id").eq("username", u).execute()
                if check_user.data:
                    messagebox.showerror("Error", "Username already taken! Please choose another Username.")
                    return

                # 2. Insert User Account into Supabase
                user_payload = {
                    "company_name": self.signup_cache["biz_name"],
                    "owner_name": self.signup_cache["owner_name"],
                    "mobile": self.signup_cache["mobile"],
                    "address": self.signup_cache["address"],
                    "gstin": self.signup_cache["gstin"],
                    "plan_name": plan_name,
                    "plan_days": days,
                    "amount_paid": amount,
                    "username": u,
                    "password": p,
                    "created_at": now_str
                }
                supabase.table("users").insert(user_payload).execute()

                # 3. Insert Company Profile into Supabase
                company_payload = {
                    "name": self.signup_cache["biz_name"],
                    "address": self.signup_cache["address"],
                    "phone": self.signup_cache["mobile"],
                    "gstin": self.signup_cache["gstin"],
                    "financial_year": "2026-2027"
                }
                supabase.table("company_profile").insert(company_payload).execute()

                messagebox.showinfo("Registration Successful", "Account and Login ID created successfully!\nYou can now log in using Customer Login.")
                self.show_customer_login_screen()

            except Exception as e:
                messagebox.showerror("Error", f"Registration failed: {str(e)}")

        tk.Button(f, text="CONFIRM PAYMENT & COMPLETE REGISTRATION", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), bd=0, pady=8, cursor="hand2", command=finalize_registration).pack(fill="x", pady=8)
        tk.Button(f, text="← Back to Plan Selection", bg="#7F8C8D", fg="white", font=("Arial", 8), bd=0, pady=3, cursor="hand2", command=self.show_signup_step2_plan_selection).pack(fill="x")
            
    # ==========================================
    # PHASE 2: MAIN DASHBOARD & TABS CONTROL
    # ==========================================
    def show_main_dashboard(self):
        self.clear_root_canvas()
        
        self.top_ribbon = tk.Frame(self.root, bg="#003366", height=75)
        self.top_ribbon.pack(fill="x", side="top")
        self.top_ribbon.pack_propagate(False)
        
        self.title_lbl = tk.Label(self.top_ribbon, text="🏢 JAIN VITTASAR CONTROL CONSOLE (NO ACTIVE ENTERPRISE)", fg="#FFFFFF", bg="#003366", font=("Arial", 14, "bold"))
        self.title_lbl.pack(side="left", padx=25, pady=20)
        
        self.update_top_ribbon_ui()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_home = ttk.Frame(self.notebook)
        self.tab_billing = ttk.Frame(self.notebook)
        self.tab_inventory = ttk.Frame(self.notebook)
        self.tab_collection = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_home, text="  🏠 Home Tab  ")
        self.notebook.add(self.tab_billing, text="  📈 Sales & Billing Module  ")
        self.notebook.add(self.tab_inventory, text="  📦 Inventory Control & Purchases  ")
        self.notebook.add(self.tab_collection, text="  📊 Financial Ledgers Audit Logs  ")
        
        self.render_home_tab_workspace()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_switch_handler)

    def update_top_ribbon_ui(self):
        if hasattr(self, 'ribbon_logo_lbl'):
            self.ribbon_logo_lbl.destroy()
        if hasattr(self, 'buy_plan_btn'):
            self.buy_plan_btn.destroy()

        if self.company:
            fy_str = f" | FY: {self.company[14]}" if len(self.company) > 14 and self.company[14] else ""
            self.title_lbl.config(text=f"🏢 ACTIVE ENTERPRISE: {self.company[1].upper()} | GSTIN: {self.company[6] if self.company[6] else 'N/A'}{fy_str}")
            
            # Plan Status Badge / Buy Button
            self.cursor.execute("SELECT plan_type, expiry_date FROM app_license WHERE is_active=1 ORDER BY id DESC LIMIT 1")
            lic = self.cursor.fetchone()
            
            if lic:
                btn_txt = f"🟢 Plan Active ({lic[0]})"
                btn_bg = "#27AE60"
            else:
                btn_txt = "⚡ Buy Subscription Plan"
                btn_bg = "#E67E22"

            self.buy_plan_btn = tk.Button(
                self.top_ribbon, text=btn_txt, bg=btn_bg, fg="white", 
                font=("Arial", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2",
                command=self.show_signup_step2_plan_selection
            )
            self.buy_plan_btn.pack(side="right", padx=15, pady=20)
            
            logo_path = self.company[13] if len(self.company) > 13 else ""
            if logo_path and os.path.exists(logo_path):
                try:
                    raw_img = Image.open(logo_path)
                    resized_img = raw_img.resize((45, 45), Image.Resampling.LANCZOS)
                    self.tk_logo_bit = ImageTk.PhotoImage(resized_img)
                    
                    self.ribbon_logo_lbl = tk.Label(self.top_ribbon, image=self.tk_logo_bit, bg="#003366")
                    self.ribbon_logo_lbl.pack(side="right", padx=10, pady=15)
                except Exception as logo_err:
                    print("Tkinter UI logo scale asset stream dropped:", logo_err)
        else:
            self.title_lbl.config(text="🏢 JAIN VITTASAR CONTROL CONSOLE (NO ACTIVE ENTERPRISE)")
            self.buy_plan_btn = tk.Button(
                self.top_ribbon, text="⚡ Buy Subscription Plan", bg="#E67E22", fg="white", 
                font=("Arial", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2",
                command=self.show_signup_step2_plan_selection
            )
            self.buy_plan_btn.pack(side="right", padx=15, pady=20)
        
    def on_tab_switch_handler(self, event):
        """Restricts feature tabs if no active license exists."""
        selected_index = self.notebook.index(self.notebook.select())
        
        # Home Tab (Index 0) is FREE for Company Creation / Setup
        if selected_index == 0:
            return

        # Check if license is active before letting them use Billing/Inventory/Audit
        self.cursor.execute("SELECT is_active FROM app_license WHERE is_active=1")
        active_lic = self.cursor.fetchone()

        if not active_lic:
            # Switch back to Home Tab
            self.notebook.select(0)
            
            # Check if company profile is filled
            self.cursor.execute("SELECT * FROM company_profile ORDER BY id DESC LIMIT 1")
            company_data = self.cursor.fetchone()
            
            if not company_data:
                messagebox.showwarning(
                    "Company Setup Required", 
                    "Please create your Company Profile first in the Home Tab before purchasing a license plan."
                )
            else:
                messagebox.showinfo(
                    "🔒 License Subscription Required", 
                    f"Welcome {company_data[1]}!\n\nTo access Billing, Sales, and Inventory features, please purchase a subscription plan."
                )
                self.show_signup_step2_plan_selection()
            return

        # If License is active, allow switching to respective modules
        if selected_index == 1:
            self.render_sales_billing_workspace()
        elif selected_index == 2:
            self.render_procurement_inventory_workspace()
        elif selected_index == 3:
            self.render_collection_ledger_workspace()
            
    # ==========================================
    # PHASE 3: COMPREHENSIVE HOME TAB ENGINE
    # ==========================================
    def render_home_tab_workspace(self):
        for widget in self.tab_home.winfo_children(): widget.destroy()

        split_layout = ttk.Panedwindow(self.tab_home, orient="horizontal")
        split_layout.pack(fill="both", expand=True)

        left_menu_panel = tk.Frame(split_layout, bg="#2C3E50", width=260)
        self.right_workspace = tk.Frame(split_layout, bg="#F4F6F9")
        
        split_layout.add(left_menu_panel, weight=1)
        split_layout.add(self.right_workspace, weight=4)

        tk.Label(left_menu_panel, text="OPERATIONS CONTROL", font=("Arial", 11, "bold"), fg="#BDC3C7", bg="#2C3E50").pack(pady=20, padx=10, anchor="w")

        btn_configs = [
            ("📂 Open Existing Company", self.render_open_company_panel),
            ("✏️ Edit Active Company Profile", lambda: self.render_company_form_panel(is_edit=True)),
            ("➕ Create New Company", lambda: self.render_company_form_panel(is_edit=False)),
            ("🔄 Migrate External Data", self.render_migration_interface),
            ("💾 Backup System Data", self.trigger_database_backup),
            ("📥 Restore System Data", self.trigger_database_restore)
        ]

        for text, command in btn_configs:
            btn = tk.Button(
                left_menu_panel, text=text, font=("Arial", 10, "bold"), bg="#34495E", fg="#ECF0F1",
                activebackground="#1ABC9C", activeforeground="white", bd=0, cursor="hand2", anchor="w", padx=15, pady=12, command=command
            )
            btn.pack(fill="x", pady=2, padx=5)

        self.render_open_company_panel()

    def render_open_company_panel(self):
        for widget in self.right_workspace.winfo_children(): widget.destroy()
        inner_frame = ttk.Frame(self.right_workspace, padding=30)
        inner_frame.pack(fill="both", expand=True)

        ttk.Label(inner_frame, text="Active Registries: Open Registered Enterprise Cluster", font=("Arial", 14, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 15))

        columns = ("id", "name", "gstin", "state", "phone", "fy")
        tree = ttk.Treeview(inner_frame, columns=columns, show="headings", height=15)
        for col, head in zip(columns, ["ID", "Corporate Name", "GSTIN Ref", "State", "Helpline", "Financial Year"]):
            tree.heading(col, text=head)
        tree.pack(fill="both", expand=True, pady=10)

        try:
            # Query companies from Supabase
            res = supabase.table("company_profile").select("id, name, gstin, state, phone, financial_year").execute()
            if res.data:
                for row in res.data:
                    tree.insert("", "end", values=(
                        row.get("id"), row.get("name"), row.get("gstin"),
                        row.get("state"), row.get("phone"), row.get("financial_year")
                    ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch companies from cloud: {str(e)}")

        def proceed_load_company():
            selected_node = tree.selection()
            if not selected_node:
                messagebox.showwarning("Selection Required", "Please highlight an enterprise node from the table ledger to activate.")
                return
            company_id = tree.item(selected_node[0])['values'][0]
            try:
                res_comp = supabase.table("company_profile").select("*").eq("id", company_id).execute()
                if res_comp.data:
                    c = res_comp.data[0]
                    self.company = (
                        c.get("id"), c.get("name"), c.get("address"), c.get("phone"), c.get("email"),
                        c.get("business_type"), c.get("gstin"), c.get("pan"), c.get("bank_name"),
                        c.get("account_no"), c.get("ifsc"), c.get("upi_id"), c.get("state"),
                        c.get("logo_path"), c.get("financial_year")
                    )
                    self.update_top_ribbon_ui()
                    messagebox.showinfo("System Boot Successful", f"Company Context Switched to: {self.company[1]}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load company context: {str(e)}")

        action_btn = tk.Button(inner_frame, text="⚡ ACTIVATE LOAD SELECTED ENTERPRISE", font=("Arial", 10, "bold"), bg="#2980B9", fg="white", bd=0, padx=20, pady=10, cursor="hand2", command=proceed_load_company)
        action_btn.pack(anchor="w", pady=10)

    def render_company_form_panel(self, is_edit=False):
        for widget in self.right_workspace.winfo_children(): widget.destroy()
        canvas = tk.Canvas(self.right_workspace, bg="#F4F6F9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.right_workspace, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="30")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        ttk.Label(scrollable_frame, text="Initialize New Corporate Architecture Profile Entry", font=("Arial", 14, "bold"), foreground="#003366").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 20))

        fields = [
            ("Company Registered Name *", "name"), ("Office Address Coordinates *", "address"), 
            ("Primary Contact Helpline *", "phone"), ("Corporate Email Address", "email"), 
            ("GSTIN Registry Index *", "gstin"), ("PAN Card Accounting Index", "pan"),
            ("Bank Institution Name *", "bank_name"), ("Financial Account Sequence *", "account_no"),
            ("IFSC Routing Core Code *", "ifsc"), ("UPI Payment Uniform Target ID", "upi_id"),
            ("State Jurisdiction / UT", "state"), ("Financial Year (e.g. 2026-2027) *", "financial_year")
        ]
        
        self.entries = {}
        for idx, (label_text, var_name) in enumerate(fields):
            row_idx = (idx // 2) + 1
            col_idx = (idx % 2) * 2
            ttk.Label(scrollable_frame, text=label_text, font=("Arial", 9, "bold")).grid(row=row_idx, column=col_idx, sticky="w", pady=6, padx=(10, 5))
            entry = ttk.Entry(scrollable_frame, width=32, font=("Arial", 10))
            entry.grid(row=row_idx, column=col_idx+1, pady=6, padx=10, ipady=2)
            self.entries[var_name] = entry

        # Preset standard default for Financial Year input
        self.entries["financial_year"].insert(0, "2026-2027")

        biz_row = (len(fields) // 2) + 1
        ttk.Label(scrollable_frame, text="Operations Classification", font=("Arial", 9, "bold")).grid(row=biz_row, column=0, sticky="w", pady=6, padx=(10, 5))
        self.biz_type = ttk.Combobox(scrollable_frame, values=["Inventory Based", "Service Based"], width=30, font=("Arial", 10), state="readonly")
        self.biz_type.set("Inventory Based")
        self.biz_type.grid(row=biz_row, column=1, pady=6, padx=10, ipady=2)

        ttk.Label(scrollable_frame, text="Corporate Branding Logo (.JPG)", font=("Arial", 9, "bold")).grid(row=biz_row+1, column=0, sticky="w", pady=10, padx=(10, 5))
        logo_btn_frame = ttk.Frame(scrollable_frame)
        logo_btn_frame.grid(row=biz_row+1, column=1, columnspan=2, sticky="w", pady=10, padx=10)
        self.logo_preview_lbl = ttk.Label(logo_btn_frame, text="No Image Linked")

        def file_explorer_import_logo():
            file_path = filedialog.askopenfilename(title="Select Corporate Brand Logo Image", filetypes=[("JPEG Images", "*.jpg;*.jpeg")])
            if file_path:
                self.uploaded_logo_path = file_path
                self.logo_preview_lbl.config(text="Loaded: " + os.path.basename(file_path))

        tk.Button(logo_btn_frame, text="Import Brand Logo (.JPG)", font=("Arial", 8, "bold"), bg="#7F8C8D", fg="white", bd=0, padx=10, pady=4, command=file_explorer_import_logo).pack(side="left", padx=(0, 10))
        self.logo_preview_lbl.pack(side="left")

        save_btn = tk.Button(scrollable_frame, text="⚙ REGISTER CORE ENTERPRISE AND OPEN CONSOLE", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), bd=0, padx=20, pady=10, command=self.process_new_profile_save)
        save_btn.grid(row=biz_row+3, column=0, columnspan=4, pady=25, padx=10, sticky="w")
        # Auto-fill active company data into fields if editing existing profile
        if self.company:
            field_keys = ["name", "address", "phone", "email", "gstin", "pan", "bank_name", "account_no", "ifsc", "upi_id", "state", "financial_year"]
            # Database columns mapping index
            db_indices = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 14]
            
            for key, idx in zip(field_keys, db_indices):
                if key in self.entries and idx < len(self.company) and self.company[idx]:
                    self.entries[key].delete(0, tk.END)
                    self.entries[key].insert(0, str(self.company[idx]))
            
            if len(self.company) > 5 and self.company[5]:
                self.biz_type.set(self.company[5])
            if len(self.company) > 13 and self.company[13]:
                self.uploaded_logo_path = self.company[13]
                self.logo_preview_lbl.config(text="Loaded: " + os.path.basename(self.company[13]))
            
            save_btn.config(text="⚙ UPDATE ENTERPRISE PROFILE DETAILS")

    def process_new_profile_save(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}
        if not data['name'] or not data['address'] or not data['phone'] or not data['gstin'] or not data['financial_year']:
            messagebox.showerror("Validation Violation", "Mandatory Fields (* Name, Address, Phone, GSTIN, Financial Year) must be populated.")
            return

        payload = {
            "name": data['name'],
            "address": data['address'],
            "phone": data['phone'],
            "email": data['email'],
            "business_type": self.biz_type.get(),
            "gstin": data['gstin'],
            "pan": data['pan'],
            "bank_name": data['bank_name'],
            "account_no": data['account_no'],
            "ifsc": data['ifsc'],
            "upi_id": data['upi_id'],
            "state": data['state'],
            "logo_path": self.uploaded_logo_path,
            "financial_year": data['financial_year']
        }

        try:
            # If an enterprise profile is active, update it
            if self.company and len(self.company) > 0 and self.company[0]:
                company_id = self.company[0]
                supabase.table("company_profile").update(payload).eq("id", company_id).execute()
                
                # Re-fetch updated profile from Supabase
                res = supabase.table("company_profile").select("*").eq("id", company_id).execute()
                if res.data:
                    c = res.data[0]
                    self.company = (
                        c.get("id"), c.get("name"), c.get("address"), c.get("phone"), c.get("email"),
                        c.get("business_type"), c.get("gstin"), c.get("pan"), c.get("bank_name"),
                        c.get("account_no"), c.get("ifsc"), c.get("upi_id"), c.get("state"),
                        c.get("logo_path"), c.get("financial_year")
                    )
                self.update_top_ribbon_ui()
                messagebox.showinfo("Success", "Corporate Profile Updated Successfully.")
            else:
                # Insert new company profile into Supabase
                res = supabase.table("company_profile").insert(payload).execute()
                if res.data:
                    c = res.data[0]
                    self.company = (
                        c.get("id"), c.get("name"), c.get("address"), c.get("phone"), c.get("email"),
                        c.get("business_type"), c.get("gstin"), c.get("pan"), c.get("bank_name"),
                        c.get("account_no"), c.get("ifsc"), c.get("upi_id"), c.get("state"),
                        c.get("logo_path"), c.get("financial_year")
                    )
                self.update_top_ribbon_ui()
                messagebox.showinfo("Success", "Corporate Profile Registered Successfully.")

            self.render_open_company_panel()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save profile: {str(e)}")

    def render_migration_interface(self):
        for widget in self.right_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.right_workspace, padding=30)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="🔄 Cross-Platform Financial Data Migration Engine Core", font=("Arial", 14, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 5))
        ttk.Label(f, text="Seamlessly ingest database structures originating from Tally, Busy, or structural custom raw XLS/CSV tables.", font=("Arial", 9, "italic"), foreground="#555555").pack(anchor="w", pady=(0, 20))

        m_box = ttk.LabelFrame(f, text=" Structural Migration Parameters Node ", padding=15)
        m_box.pack(fill="x", pady=10)

        ttk.Label(m_box, text="Origin Platform Blueprint:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        platform_cb = ttk.Combobox(m_box, values=["TallyPrime XML/Excel Export Matrix", "Busy Accounting Package Ledger", "Standardized Universal Inventory CSV Template"], state="readonly", width=45)
        platform_cb.set("TallyPrime XML/Excel Export Matrix")
        platform_cb.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(m_box, text="Target Import Array Node:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        target_cb = ttk.Combobox(m_box, values=["Master Buyer/Party Profiles (parties)", "Inventory Stock Masters (inventory)"], state="readonly", width=45)
        target_cb.set("Master Buyer/Party Profiles (parties)")
        target_cb.grid(row=1, column=1, padx=10, pady=5)

        def proceed_data_migration_pipeline():
            file_path = filedialog.askopenfilename(
                title="Select Exported File Asset for Mapping Intake", 
                filetypes=[("Data Worksheets", "*.xlsx;*.xls;*.csv")]
            )
            if not file_path: return
            
            try:
                active_company_id = self.company[0] if self.company else None
                if not active_company_id:
                    messagebox.showerror("Error", "No active company selected for data migration!")
                    return

                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                df = df.fillna('')
                target = target_cb.get()
                
                if "parties" in target.lower():
                    name_col = next((c for c in df.columns if 'name' in c.lower() or 'party' in c.lower() or 'ledger' in c.lower()), None)
                    phone_col = next((c for c in df.columns if 'phone' in c.lower() or 'contact' in c.lower() or 'mobile' in c.lower()), None)
                    gst_col = next((c for c in df.columns if 'gst' in c.lower() or 'tax' in c.lower()), None)
                    bal_col = next((c for c in df.columns if 'bal' in c.lower() or 'open' in c.lower()), None)
                    
                    if not name_col:
                        messagebox.showerror("Mapping Violation", "Migration aborted: Unable to identify a valid 'Party Name' column.")
                        return
                    
                    payloads = []
                    for _, row in df.iterrows():
                        p_name = str(row[name_col]).strip()
                        if not p_name: continue
                        
                        payloads.append({
                            "company_id": active_company_id,
                            "party_name": p_name,
                            "phone": str(row[phone_col]).strip() if phone_col else "N/A",
                            "gstin": str(row[gst_col]).strip() if gst_col else "N/A",
                            "opening_balance": float(row[bal_col]) if (bal_col and str(row[bal_col]).replace('.','',1).isdigit()) else 0.0,
                            "balance_type": "Dr"
                        })
                    
                    if payloads:
                        supabase.table("parties").insert(payloads).execute()
                        messagebox.showinfo("Migration Complete", f"Successfully imported {len(payloads)} Party records to Cloud!")

                else: # Ingesting Inventory stock
                    name_col = next((c for c in df.columns if 'item' in c.lower() or 'product' in c.lower() or 'name' in c.lower() or 'desc' in c.lower()), None)
                    stock_col = next((c for c in df.columns if 'stock' in c.lower() or 'qty' in c.lower() or 'quantity' in c.lower() or 'avail' in c.lower()), None)
                    rate_col = next((c for c in df.columns if 'rate' in c.lower() or 'price' in c.lower() or 'cost' in c.lower()), None)
                    hsn_col = next((c for c in df.columns if 'hsn' in c.lower() or 'code' in c.lower()), None)
                    unit_col = next((c for c in df.columns if 'unit' in c.lower() or 'uom' in c.lower()), None)
                    
                    if not name_col:
                        messagebox.showerror("Mapping Violation", "Migration aborted: Unable to determine a clear 'Product Description' column.")
                        return
                        
                    payloads = []
                    for _, row in df.iterrows():
                        i_name = str(row[name_col]).strip()
                        if not i_name: continue
                        
                        payloads.append({
                            "company_id": active_company_id,
                            "item_name": i_name,
                            "stock": int(row[stock_col]) if (stock_col and str(row[stock_col]).isdigit()) else 0,
                            "price": float(row[rate_col]) if (rate_col and str(row[rate_col]).replace('.','',1).isdigit()) else 0.0,
                            "hsn_code": str(row[hsn_col]).strip() if hsn_col else "",
                            "unit": str(row[unit_col]).strip() if unit_col else "Pcs"
                        })
                    
                    if payloads:
                        supabase.table("inventory").insert(payloads).execute()
                        messagebox.showinfo("Migration Complete", f"Successfully imported {len(payloads)} Inventory items to Cloud!")

            except Exception as e:
                messagebox.showerror("Pipeline Exception Error", f"Encountered parsing error: {str(e)}")

        tk.Button(f, text="⚡ LAUNCH WORKSPACE MIGRATION DATA ASSIMILATION", font=("Arial", 11, "bold"), bg="#1ABC9C", fg="white", bd=0, padx=20, pady=12, command=proceed_data_migration_pipeline).pack(anchor="w", pady=15)

    def trigger_database_backup(self):
        dest = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database Files", "*.db")], initialfile=f"jain_vittasar_backup_{datetime.now().strftime('%Y%m%d')}.db")
        if dest:
            self.conn.close()
            shutil.copy2(self.db_name, dest)
            self.conn = sqlite3.connect(self.db_name); self.cursor = self.conn.cursor()
            messagebox.showinfo("Backup", "Snapshot Created Successfully.")

    def trigger_database_restore(self):
        src = filedialog.askopenfilename(filetypes=[("Database Files", "*.db")])
        if src and messagebox.askyesno("Overwrite Alert", "Drop current ledger and restore?"):
            self.conn.close()
            shutil.copy2(src, self.db_name)
            self.conn = sqlite3.connect(self.db_name); self.cursor = self.conn.cursor()
            self.company = None; self.update_top_ribbon_ui(); self.render_home_tab_workspace()
            messagebox.showinfo("Restored", "Ledger Infrastructure Restructured.")

    # ==========================================
    # PHASE 4: EXTENSIVE SALES & BILLING MODULE
    # ==========================================
    def render_sales_billing_workspace(self):
        for widget in self.tab_billing.winfo_children(): widget.destroy()
        
        if not self.company:
            tk.Label(self.tab_billing, text="⚠️ NO ACTIVE ENTERPRISE INSTANCE LOADED. GO TO HOME TAB TO INITIALIZE.", font=("Arial", 12, "bold"), fg="red").pack(pady=100)
            return

        split_layout = ttk.Panedwindow(self.tab_billing, orient="horizontal")
        split_layout.pack(fill="both", expand=True)

        left_side_menu = tk.Frame(split_layout, bg="#34495E", width=240)
        self.billing_workspace = tk.Frame(split_layout, bg="#F4F6F9")
        split_layout.add(left_side_menu, weight=1)
        split_layout.add(self.billing_workspace, weight=4)

        tk.Label(left_side_menu, text="BILLING OPERATIONS", font=("Arial", 10, "bold"), fg="#BDC3C7", bg="#34495E").pack(pady=15, padx=10, anchor="w")

        operations_nav = [
            ("➕ Create New Party (Buyer)", self.render_create_party_panel),
            ("📝 Create New Bill (Sales)", self.render_create_bill_panel),
            ("👥 View All Parties Ledger", self.render_parties_ledger_panel),
            ("🧾 View All Bills Console", self.render_view_bills_panel)
        ]

        for text, command in operations_nav:
            tk.Button(
                left_side_menu, text=text, font=("Arial", 9, "bold"), bg="#2C3E50", fg="#ECF0F1",
                activebackground="#1ABC9C", activeforeground="white", bd=0, cursor="hand2", anchor="w", padx=12, pady=10, command=command
            ).pack(fill="x", pady=2, padx=5)

        self.render_create_bill_panel()

    def render_create_party_panel(self):
        for widget in self.billing_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.billing_workspace, padding=30)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Register New Buyer Party Entity Node", font=("Arial", 14, "bold"), foreground="#003366").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        labels = ["Party/Buyer Corporate Name *", "Contact Person Name", "Primary Helpline Coordinates", "GSTIN Account Index", "State Jurisdiction", "Opening Balanced Value (₹)", "Balance Core Type", "Party Address"]
        vars_map = ["p_name", "p_contact", "p_phone", "p_gstin", "p_state", "p_op_bal", "p_type", "p_address"]
        
        self.party_entries = {}
        for idx, (lbl, key) in enumerate(zip(labels, vars_map)):
            ttk.Label(f, text=lbl, font=("Arial", 10, "bold")).grid(row=idx+1, column=0, sticky="w", pady=6)
            if key == "p_type":
                ent = ttk.Combobox(f, values=["Dr", "Cr"], state="readonly", width=28)
                ent.set("Dr")
            else:
                ent = ttk.Entry(f, width=30)
            ent.grid(row=idx+1, column=1, pady=6, ipady=2)
            self.party_entries[key] = ent

        def save_party_node():
            name = self.party_entries["p_name"].get().strip()
            if not name: 
                messagebox.showerror("Error", "Party Name is mandatory.")
                return
            try:
                op_bal = float(self.party_entries["p_op_bal"].get() or 0.0)
            except ValueError:
                op_bal = 0.0
            
            active_company_id = self.company[0] if self.company else None

            payload = {
                "company_id": active_company_id,
                "party_name": name,
                "contact_person": self.party_entries["p_contact"].get().strip(),
                "phone": self.party_entries["p_phone"].get().strip(),
                "gstin": self.party_entries["p_gstin"].get().strip(),
                "state": self.party_entries["p_state"].get().strip(),
                "opening_balance": op_bal,
                "balance_type": self.party_entries["p_type"].get(),
                "address": self.party_entries["p_address"].get().strip()
            }

            try:
                # Check for duplicate party name for THIS company in Supabase
                res_check = supabase.table("parties") \
                    .select("id") \
                    .eq("party_name", name) \
                    .eq("company_id", active_company_id) \
                    .execute()

                if res_check.data:
                    messagebox.showerror("Error", "Party name already exists for this company!")
                    return

                supabase.table("parties").insert(payload).execute()
                messagebox.showinfo("Success", f"Party '{name}' successfully committed to database.")
                self.render_parties_ledger_panel()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save party profile: {str(e)}")

        tk.Button(f, text="💾 COMMIT/SAVE PARTY PROFILE", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=8, command=save_party_node).grid(row=10, column=0, columnspan=2, pady=20, sticky="w")

    def render_create_bill_panel(self):
        for widget in self.billing_workspace.winfo_children(): widget.destroy()
        self.sales_cart = []

        # Compact, full-view container without internal canvas scrollbars
        form_container = ttk.Frame(self.billing_workspace, padding=12)
        form_container.pack(fill="both", expand=True)

        ttk.Label(form_container, text="Universal Sales Billing Engine Module Framework", font=("Arial", 13, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 6))

        # Compact Invoice Header Node
        meta_box = ttk.LabelFrame(form_container, text=" Header Core Parameters Node ", padding=6)
        meta_box.pack(fill="x", pady=2)

        ttk.Label(meta_box, text="Invoice Classification Head:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.bill_inv_type_cb = ttk.Combobox(meta_box, values=["TAX Invoice", "PROFORMA Invoice"], state="readonly", width=20)
        self.bill_inv_type_cb.set("TAX Invoice")
        self.bill_inv_type_cb.grid(row=0, column=1, pady=2, padx=5)

        ttk.Label(meta_box, text="Party / Buyer Registry Context:", font=("Arial", 9, "bold")).grid(row=0, column=2, sticky="w", padx=15)
        self.cursor.execute("SELECT party_name FROM parties")
        registered_parties_list = ["Walk-in Customer Client"] + [r[0] for r in self.cursor.fetchall()]
        self.bill_party_cb = ttk.Combobox(meta_box, values=registered_parties_list, state="normal", width=30)
        self.bill_party_cb.set("Walk-in Customer Client")
        self.bill_party_cb.grid(row=0, column=3, pady=2, padx=5)

        # Compact Dynamic Items Setup Panel
        item_box = ttk.LabelFrame(form_container, text=" Dynamic Items Matrix Setup Line ", padding=6)
        item_box.pack(fill="x", pady=6)

        self.cursor.execute("SELECT item_name, price, hsn_code, unit, stock FROM inventory")
        db_inv_items = self.cursor.fetchall()
        
        self.item_details_map = {}
        for r in db_inv_items:
            name, price, hsn, unit, stock = r[0], r[1], str(r[2] if r[2] else ""), str(r[3] if r[3] else "Pcs"), r[4]
            display_str = f"{name} - {stock} {unit} | HSN: {hsn}"
            self.item_details_map[display_str] = {"name": name, "price": price, "hsn": hsn, "unit": unit}

        # Row 0: Search and Autofilled Basic Specs
        ttk.Label(item_box, text="Search Item:").grid(row=0, column=0, sticky="w", padx=2)
        self.all_search_suggestions = list(self.item_details_map.keys())
        self.add_item_search_cb = ttk.Combobox(item_box, values=self.all_search_suggestions, state="normal", width=32)
        self.add_item_search_cb.grid(row=0, column=1, pady=2, padx=2)

        def google_style_predictive_search(event):
            if event.keysym in ('Up', 'Down', 'Return', 'Escape', 'Tab'): return
            search_query = self.add_item_search_cb.get().strip().lower()
            if not search_query:
                self.add_item_search_cb['values'] = self.all_search_suggestions; return
            search_terms = search_query.split()
            filtered_suggestions = [k for k in self.all_search_suggestions if all(t in k.lower() for t in search_terms)]
            self.add_item_search_cb['values'] = filtered_suggestions
            if filtered_suggestions:
                self.add_item_search_cb.tk.call(self.add_item_search_cb._w, "post")

        self.add_item_search_cb.bind("<KeyRelease>", google_style_predictive_search)

        ttk.Label(item_box, text="Name:").grid(row=0, column=2, sticky="w", padx=2)
        self.add_item_name_entry = ttk.Entry(item_box, width=16, state="readonly")
        self.add_item_name_entry.grid(row=0, column=3, pady=2, padx=2)

        ttk.Label(item_box, text="HSN:").grid(row=0, column=4, sticky="w", padx=2)
        self.add_item_hsn_entry = ttk.Entry(item_box, width=10, state="readonly")
        self.add_item_hsn_entry.grid(row=0, column=5, pady=2, padx=2)

        ttk.Label(item_box, text="Tax Rate (%):").grid(row=0, column=6, sticky="w", padx=2)
        self.add_item_tax = ttk.Combobox(item_box, values=["0", "5", "12", "18", "28"], state="readonly", width=6)
        self.add_item_tax.set("18")
        self.add_item_tax.grid(row=0, column=7, pady=2, padx=2)

        # Row 1: Quantity, Rate, Unit, Discount & Line Buttons
        ttk.Label(item_box, text="Qty:").grid(row=1, column=0, sticky="w", padx=2, pady=4)
        self.add_item_qty = ttk.Entry(item_box, width=8)
        self.add_item_qty.insert(0, "1")
        self.add_item_qty.grid(row=1, column=1, pady=4, padx=2, sticky="w")

        ttk.Label(item_box, text="Unit:").grid(row=1, column=2, sticky="w", padx=2, pady=4)
        self.add_item_unit_entry = ttk.Entry(item_box, width=8)
        self.add_item_unit_entry.insert(0, "Pcs")
        self.add_item_unit_entry.grid(row=1, column=3, pady=4, padx=2, sticky="w")

        ttk.Label(item_box, text="Rate (₹):").grid(row=1, column=4, sticky="w", padx=2, pady=4)
        self.add_item_rate = ttk.Entry(item_box, width=10)
        self.add_item_rate.grid(row=1, column=5, pady=4, padx=2, sticky="w")

        ttk.Label(item_box, text="Disc (%):").grid(row=1, column=6, sticky="w", padx=2, pady=4)
        self.add_item_discount = ttk.Entry(item_box, width=6)
        self.add_item_discount.insert(0, "0")
        self.add_item_discount.grid(row=1, column=7, pady=4, padx=2, sticky="w")

        def perform_dynamic_search_autofill(e):
            selected_string = self.add_item_search_cb.get()
            if selected_string in self.item_details_map:
                props = self.item_details_map[selected_string]
                self.add_item_name_entry.config(state="normal")
                self.add_item_name_entry.delete(0, tk.END)
                self.add_item_name_entry.insert(0, props["name"])
                self.add_item_name_entry.config(state="readonly")

                self.add_item_hsn_entry.config(state="normal")
                self.add_item_hsn_entry.delete(0, tk.END)
                self.add_item_hsn_entry.insert(0, props["hsn"])
                self.add_item_hsn_entry.config(state="readonly")

                self.add_item_unit_entry.delete(0, tk.END)
                self.add_item_unit_entry.insert(0, props["unit"])
                self.add_item_rate.delete(0, tk.END)
                self.add_item_rate.insert(0, str(props["price"]))

        self.add_item_search_cb.bind("<<ComboboxSelected>>", perform_dynamic_search_autofill)
        self.add_item_search_cb.bind("<Return>", perform_dynamic_search_autofill)

        # Cart Tree Layout with clear, full-view height
        cart_tree_columns = ("name", "hsn", "qty", "unit", "rate", "disc_p", "tax_p", "tax_amt", "amount")
        self.cart_tree = ttk.Treeview(form_container, columns=cart_tree_columns, show="headings", height=12)
        
        headers_titles = ["Item Name Description", "HSN Code", "Quantity", "Unit", "Rate Per Unit", "Discount %", "Tax %", "Tax Amt", "Total Net Amount"]
        for c, h in zip(cart_tree_columns, headers_titles):
            self.cart_tree.heading(c, text=h)
            if c == "name": self.cart_tree.column(c, width=240, anchor="w")
            elif c in ("qty", "unit", "disc_p", "tax_p"): self.cart_tree.column(c, width=70, anchor="center")
            else: self.cart_tree.column(c, width=100, anchor="center")
                
        self.cart_tree.pack(fill="both", expand=True, pady=4)

        # Bottom Actions & Totals Area
        bottom_bar = ttk.Frame(form_container)
        bottom_bar.pack(fill="x", pady=4)

        self.totals_summary_lbl = ttk.Label(bottom_bar, text="Grand Total Aggregates: ₹ 0.00", font=("Arial", 11, "bold"), foreground="#2C3E50")
        self.totals_summary_lbl.pack(side="right", padx=10)

        def process_append_item_to_cart():
            name = self.add_item_name_entry.get()
            hsn = self.add_item_hsn_entry.get()
            unit = self.add_item_unit_entry.get().strip()
            if not name:
                messagebox.showwarning("Missing Item Selection", "Please use the Search box to successfully fetch an inventory item first.")
                return
            try:
                q = int(self.add_item_qty.get() or 1)
                r = float(self.add_item_rate.get() or 0.0)
                dp = float(self.add_item_discount.get() or 0.0)
                tp = float(self.add_item_tax.get() or 0.0)
            except ValueError:
                messagebox.showerror("Error", "Invalid format entry fields inside numeric cell parameters."); return

            self.cursor.execute("SELECT stock FROM inventory WHERE item_name=?", (name,))
            stock_row = self.cursor.fetchone()
            available_stock = stock_row[0] if stock_row else 0
            already_in_cart = sum(item["qty"] for item in self.sales_cart if item["name"] == name)
            total_requested = q + already_in_cart

            if total_requested > available_stock:
                messagebox.showerror("Insufficient Stock", f"Transaction Denied: Insufficient stock units available!\nAvailable: {available_stock}")
                return

            remaining_stock_projection = available_stock - total_requested
            if remaining_stock_projection <= 10:
                messagebox.showwarning("Low Stock Alert", f"⚠️ Warning: Critical low inventory footprint projection: {remaining_stock_projection} remaining.")

            raw_base_cost = r * q
            discount_deduction = raw_base_cost * (dp / 100.0)
            discounted_subtotal = raw_base_cost - discount_deduction
            tax_amt = discounted_subtotal * (tp / 100.0)
            total_net_cost = discounted_subtotal + tax_amt
            
            row_entry = {
                "name": name, "hsn": hsn, "qty": q, "unit": unit, "price": r, 
                "discount_percent": dp, "discount_amount": discount_deduction,
                "tax_rate": tp, "tax_amount": tax_amt, "total_amount": total_net_cost
            }
            self.sales_cart.append(row_entry)
            
            self.cart_tree.insert("", "end", values=(
                name, hsn, q, unit, f"₹{r:.2f}", f"{dp}%", f"{tp}%", f"₹{tax_amt:.2f}", f"₹{total_net_cost:.2f}"
            ))
            grand_sum = sum(item["total_amount"] for item in self.sales_cart)
            self.totals_summary_lbl.config(text=f"Grand Total Aggregates: ₹ {grand_sum:,.2f}")

        def remove_selected_cart_item():
            selected_item = self.cart_tree.selection()
            if not selected_item:
                messagebox.showwarning("Selection Required", "Please select a line item from the cart table to remove.")
                return
            
            index = self.cart_tree.index(selected_item[0])
            del self.sales_cart[index]
            self.cart_tree.delete(selected_item[0])
            
            grand_sum = sum(item["total_amount"] for item in self.sales_cart)
            self.totals_summary_lbl.config(text=f"Grand Total Aggregates: ₹ {grand_sum:,.2f}")

        tk.Button(item_box, text="➕ APPEND ITEM LINE", bg="#3498DB", fg="white", font=("Arial", 9, "bold"), bd=0, padx=10, pady=4, command=process_append_item_to_cart).grid(row=1, column=8, padx=6, pady=4)
        tk.Button(item_box, text="❌ REMOVE LINE", bg="#C0392B", fg="white", font=("Arial", 9, "bold"), bd=0, padx=10, pady=4, command=remove_selected_cart_item).grid(row=1, column=9, padx=4, pady=4)

        def commit_save_invoice_dispatch():
            if not self.sales_cart: 
                messagebox.showerror("Error", "Cart buffer empty!")
                return
                
            p_name = self.bill_party_cb.get().strip()
            inv_type = self.bill_inv_type_cb.get()
            pay_method = "Bank Remittance"
            
            g_tot = sum(i["total_amount"] for i in self.sales_cart)
            t_tax = sum(i["tax_amount"] for i in self.sales_cart)
            t_disc = sum(i["discount_amount"] for i in self.sales_cart)
            cur_date = datetime.now().strftime("%Y-%m-%d %H:%M")

            try:
                active_company_id = self.company[0] if self.company else None

                # 1. Insert main Bill into Supabase
                bill_payload = {
                    "company_id": active_company_id,
                    "date": cur_date,
                    "customer_name": p_name,
                    "grand_total": g_tot,
                    "payment_method": pay_method,
                    "invoice_type": inv_type,
                    "txn_category": "Sales",
                    "total_tax": t_tax,
                    "total_discount": t_disc
                }
                bill_res = supabase.table("bills").insert(bill_payload).execute()
                
                if not bill_res.data:
                    messagebox.showerror("Error", "Failed to save invoice to cloud.")
                    return
                    
                b_no = bill_res.data[0]["bill_no"]

                # 2. Insert Bill Line Items & Deduct Inventory Stock
                for item in self.sales_cart:
                    item_payload = {
                        "bill_no": b_no,
                        "item_name": item["name"],
                        "qty": item["qty"],
                        "price": item["price"],
                        "discount_percent": item["discount_percent"],
                        "tax_rate": item["tax_rate"],
                        "tax_amount": item["tax_amount"],
                        "total_amount": item["total_amount"]
                    }
                    supabase.table("bill_items").insert(item_payload).execute()

                    # Fetch current stock from Supabase to deduct
                    inv_res = supabase.table("inventory") \
                        .select("stock") \
                        .eq("item_name", item["name"]) \
                        .eq("company_id", active_company_id) \
                        .execute()

                    if inv_res.data:
                        current_stock = inv_res.data[0]["stock"]
                        new_stock = max(0, current_stock - item["qty"])
                        supabase.table("inventory") \
                            .update({"stock": new_stock}) \
                            .eq("item_name", item["name"]) \
                            .eq("company_id", active_company_id) \
                            .execute()

                # 3. Log into Audit Trail
                supabase.table("audit_logs").insert({
                    "company_id": active_company_id,
                    "date": cur_date,
                    "account_type": "Bank",
                    "party_name": p_name,
                    "bill_ref": f"INV-{b_no}",
                    "txn_type": "Received",
                    "amount": g_tot,
                    "remarks": "Automated billing system execution sales module clear."
                }).execute()

                messagebox.showinfo("Committed", f"Invoice #{b_no} successfully logged and committed.")
                self.generate_pdf_invoice_document(b_no)
                self.render_view_bills_panel()
            except Exception as e:
                messagebox.showerror("Billing Error", f"Failed to commit invoice: {str(e)}")

        tk.Button(bottom_bar, text="💾 COMMIT EXECUTE & SAVE INVOICE", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), bd=0, padx=20, pady=8, command=commit_save_invoice_dispatch).pack(side="left", padx=5)

    def render_parties_ledger_panel(self):
        for widget in self.billing_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.billing_workspace, padding=25)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Parties Registry Summary Console", font=("Arial", 14, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 5))
        ttk.Label(f, text="💡 Double click any entry line row to fetch full statement breakdown history.", font=("Arial", 9, "italic"), foreground="#E67E22").pack(anchor="w", pady=(0, 10))

        columns = ("id", "name", "gstin", "state", "closing_bal")
        tree = ttk.Treeview(f, columns=columns, show="headings", height=15)
        for col, head in zip(columns, ["Party ID", "Buyer Corporate Title", "GSTIN Registry", "Jurisdiction State", "Closing Balance"]):
            tree.heading(col, text=head)
        tree.pack(fill="both", expand=True, pady=10)

        try:
            active_company_id = self.company[0] if self.company else None

            # Fetch parties belonging to active company from Supabase
            parties_res = supabase.table("parties") \
                .select("id, party_name, gstin, state, opening_balance, balance_type") \
                .eq("company_id", active_company_id) \
                .execute()
            
            if parties_res.data:
                for row in parties_res.data:
                    p_name = row["party_name"]

                    # Calculate total sales for this company
                    bills_res = supabase.table("bills") \
                        .select("grand_total") \
                        .eq("customer_name", p_name) \
                        .eq("company_id", active_company_id) \
                        .execute()
                    total_sales = sum(b["grand_total"] for b in bills_res.data) if bills_res.data else 0.0

                    # Calculate total received payments for this company
                    audit_res = supabase.table("audit_logs") \
                        .select("amount") \
                        .eq("party_name", p_name) \
                        .eq("txn_type", "Received") \
                        .eq("company_id", active_company_id) \
                        .execute()
                    total_rec = sum(a["amount"] for a in audit_res.data) if audit_res.data else 0.0

                    op_bal = row.get("opening_balance", 0.0)
                    bal_type = row.get("balance_type", "Dr")
                    init_bal = op_bal if bal_type == 'Dr' else -op_bal
                    
                    net_balance = init_bal + total_sales - total_rec
                    type_str = "Dr" if net_balance >= 0 else "Cr"
                    bal_str = f"₹ {abs(net_balance):,.2f} {type_str}"

                    tree.insert("", "end", values=(row["id"], p_name, row.get("gstin", ""), row.get("state", ""), bal_str))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch party ledgers: {str(e)}")

        def on_double_click_handler(event):
            selected = tree.selection()
            if not selected: return
            p_name = tree.item(selected[0])['values'][1]
            self.open_detailed_party_statement_window(p_name)

        tree.bind("<Double-1>", on_double_click_handler)

    def open_detailed_party_statement_window(self, party_name):
        win = tk.Toplevel(self.root)
        win.title(f"Ledger Statement Profile Breakdown - {party_name}")
        win.geometry("900x600")
        
        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)
        
        ttk.Label(f, text=f"Account Ledger Statement for: {party_name.upper()}", font=("Arial", 12, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 10))

        # Re-fetch architectural data structures baseline values
        self.cursor.execute("SELECT opening_balance, balance_type FROM parties WHERE party_name=?", (party_name,))
        p_row = self.cursor.fetchone()
        op_bal = p_row[0] if p_row else 0.0
        op_type = p_row[1] if p_row else "Dr"

        columns = ("date", "ref", "type", "sold", "rec")
        st_tree = ttk.Treeview(f, columns=columns, show="headings", height=15)
        for col, head in zip(columns, ["Date Timestamp", "Invoice / Ref Number", "Transaction Mode", "Goods Sold (Dr) ₹", "Payment Received (Cr) ₹"]):
            st_tree.heading(col, text=head)
            st_tree.column(col, width=150, anchor="center")
        st_tree.pack(fill="both", expand=True, pady=10)

        # Ingest structural values from dynamic nodes
        statement_data_matrix = []
        
        self.cursor.execute("SELECT date, bill_no, grand_total FROM bills WHERE customer_name=? AND txn_category='Sales'", (party_name,))
        for r in self.cursor.fetchall():
            statement_data_matrix.append({"date": r[0], "ref": f"INV-{r[1]}", "type": "Sales Bill", "sold": r[2], "rec": 0.0})

        self.cursor.execute("SELECT date, id, account_type, amount FROM audit_logs WHERE party_name=? AND txn_type='Received'", (party_name,))
        for r in self.cursor.fetchall():
            statement_data_matrix.append({"date": r[0], "ref": f"REC-{r[1]}", "type": f"Receipt ({r[2]})", "sold": 0.0, "rec": r[3]})

        # Sort matrix layout timeline strictly
        statement_data_matrix.sort(key=lambda x: x["date"])
        
        tot_sold = 0.0
        tot_received = 0.0
        
        for entry in statement_data_matrix:
            tot_sold += entry["sold"]
            tot_received += entry["rec"]
            st_tree.insert("", "end", values=(entry["date"], entry["ref"], entry["type"], f"{entry['sold']:.2f}", f"{entry['rec']:.2f}"))

        init_signed = op_bal if op_type == "Dr" else -op_bal
        net_bal = init_signed + tot_sold - tot_received
        bal_type = "Dr" if net_bal >= 0 else "Cr"

        summary_frame = ttk.Frame(f, padding=5)
        summary_frame.pack(fill="x", side="bottom", pady=10)

        ttk.Label(summary_frame, text=f"Opening Balance: ₹ {op_bal:,.2f} {op_type}  |  Total Sales: ₹ {tot_sold:,.2f}  |  Total Received: ₹ {tot_received:,.2f}", font=("Arial", 10, "bold")).pack(anchor="w")
        ttk.Label(summary_frame, text=f"Net Balance Closing Value: ₹ {abs(net_bal):,.2f} {bal_type}", font=("Arial", 11, "bold"), foreground="#27AE60" if bal_type=="Dr" else "#C0392B").pack(anchor="w", pady=5)

        def print_ledger_to_pdf_excel(export_mode="pdf"):
            export_array = []
            export_array.append(["Opening Balance Base Baseline", "", "", f"{op_bal if op_type=='Dr' else 0.0}", f"{op_bal if op_type=='Cr' else 0.0}"])
            for e in statement_data_matrix:
                export_array.append([e["date"], e["ref"], e["type"], e["sold"], e["rec"]])
            
            df_export = pd.DataFrame(export_array, columns=["Date Timestamp", "Ref Code", "Classification Type", "Debit (Sold) ₹", "Credit (Received) ₹"])
            
            if export_mode == "excel":
                target_file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Sheet", "*.xlsx")])
                if target_file:
                    df_export.to_excel(target_file, index=False)
                    messagebox.showinfo("Export Engine Success", "Ledger sheet successfully saved.")
            else:
                target_pdf = f"Ledger_Statement_{party_name.replace(' ', '_')}_{int(time.time())}.pdf"
                doc = SimpleDocTemplate(target_pdf, pagesize=letter)
                styles = getSampleStyleSheet()
                story = [
                    Paragraph(f"ACCOUNT STATEMENT LEDGER: {party_name.upper()}", styles["Title"]),
                    Spacer(1, 15)
                ]
                
                table_content = [["Date", "Ref Code", "Type", "Debit (Dr)", "Credit (Cr)"]]
                for row in export_array:
                    table_content.append([str(x) for x in row])
                table_content.append(["CLOSING BAL", "", "", f"₹{abs(net_bal):,.2f} {bal_type}", ""])
                
                t = Table(table_content)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('PADDING', (0,0), (-1,-1), 6)
                ]))
                story.append(t)
                doc.build(story)
                messagebox.showinfo("Export Engine Success", f"Statement compiled: {target_pdf}")
                if os.name == 'nt': os.startfile(target_pdf)
                else: os.system(f"open '{target_pdf}' || xdg-open '{target_pdf}'")

        btn_f = ttk.Frame(summary_frame)
        btn_f.pack(anchor="e", pady=5)
        tk.Button(btn_f, text="🖨️ Export PDF Report", bg="#E74C3C", fg="white", font=("Arial", 9, "bold"), bd=0, padx=10, pady=5, command=lambda: print_ledger_to_pdf_excel("pdf")).pack(side="left", padx=5)
        tk.Button(btn_f, text="📊 Export Excel Sheet", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), bd=0, padx=10, pady=5, command=lambda: print_ledger_to_pdf_excel("excel")).pack(side="left", padx=5)

    def render_view_bills_panel(self):
        for widget in self.billing_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.billing_workspace, padding=25)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Historical Master Invoices Console Core", font=("Arial", 14, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 10))

        filter_box = ttk.LabelFrame(f, text=" Chronological Search Range Selector ", padding=10)
        filter_box.pack(fill="x", pady=5)

        ttk.Label(filter_box, text="From Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        from_dt = ttk.Entry(filter_box, width=15)
        from_dt.insert(0, datetime.now().strftime("%Y-%m-%d"))
        from_dt.grid(row=0, column=1, padx=5)

        ttk.Label(filter_box, text="To Date (YYYY-MM-DD):").grid(row=0, column=2, sticky="w", padx=10)
        to_dt = ttk.Entry(filter_box, width=15)
        to_dt.insert(0, datetime.now().strftime("%Y-%m-%d"))
        to_dt.grid(row=0, column=3, padx=5)

        columns = ("no", "date", "party", "type", "total", "tax")
        tree = ttk.Treeview(f, columns=columns, show="headings", height=12)
        for col, head in zip(columns, ["Bill No", "Timestamp", "Buyer Party Context", "Invoice Classification", "Gross Grand Total", "Surcharge Tax Total"]):
            tree.heading(col, text=head)
            tree.column(col, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)

        def execute_chronological_bill_filter():
            for row in tree.get_children(): 
                tree.delete(row)
            f_str = from_dt.get().strip() + " 00:00"
            t_str = to_dt.get().strip() + " 23:59"
            
            try:
                active_company_id = self.company[0] if self.company else None

                res = supabase.table("bills") \
                    .select("bill_no, date, customer_name, invoice_type, grand_total, total_tax") \
                    .eq("txn_category", "Sales") \
                    .eq("company_id", active_company_id) \
                    .gte("date", f_str) \
                    .lte("date", t_str) \
                    .execute()
                    
                if res.data:
                    for row in res.data:
                        tree.insert("", "end", values=(
                            row.get("bill_no"),
                            row.get("date"),
                            row.get("customer_name"),
                            row.get("invoice_type"),
                            f"₹{row.get('grand_total', 0.0):,.2f}",
                            f"₹{row.get('total_tax', 0.0):,.2f}"
                        ))
            except Exception as e:
                messagebox.showerror("Query Error", f"Failed to fetch bills: {str(e)}")
                
        def export_filtered_bills_to_worksheet():
            f_str = from_dt.get().strip() + " 00:00"
            t_str = to_dt.get().strip() + " 23:59"
            self.cursor.execute("SELECT bill_no, date, customer_name, invoice_type, grand_total, total_tax, payment_method FROM bills WHERE txn_category='Sales' AND date BETWEEN ? AND ?", (f_str, t_str))
            rows = self.cursor.fetchall()
            
            df = pd.DataFrame(rows, columns=["Bill Number", "Date Timestamp", "Customer Profile Name", "Classification", "Grand Total Value", "Tax Component", "Settlement Method"])
            target = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Sheet", "*.xlsx")])
            if target:
                df.to_excel(target, index=False)
                messagebox.showinfo("Export Core", "Historical data segment exported cleanly to Excel sheet.")

        tk.Button(filter_box, text="🔍 Query Filter Logs", bg="#34495E", fg="white", font=("Arial", 9, "bold"), bd=0, padx=10, pady=4, command=execute_chronological_bill_filter).grid(row=0, column=4, padx=10)
        tk.Button(filter_box, text="📊 Export Range to Excel", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), bd=0, padx=10, pady=4, command=export_filtered_bills_to_worksheet).grid(row=0, column=5, padx=5)

        execute_chronological_bill_filter()

        def reprint_trigger_pdf():
            sel = tree.selection()
            if not sel: return
            b_id = tree.item(sel[0])['values'][0]
            self.generate_pdf_invoice_document(b_id)

        tk.Button(f, text="🖨️ RE-PRINT SELECTED INVOICE (PDF)", bg="#E67E22", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=8, command=reprint_trigger_pdf).pack(anchor="w", pady=10)

    # ==========================================
    # PHASE 5: BULLETPROOF PDF GENERATOR ENGINE
    # ==========================================
    def generate_software_license_invoice(self, company_data, plan_name, days, amount, act_date, exp_date):
        """Generates a clean PDF Subscription Invoice issued by Jain Vittasar to the Business Owner."""
        unique_id = int(time.time())
        pdf_path = f"JainVittasar_Software_Invoice_{unique_id}.pdf"

        try:
            doc = SimpleDocTemplate(
                pdf_path, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40
            )
            story = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TStyle', fontName='Helvetica-Bold', fontSize=15, textColor=colors.HexColor('#003366'), spaceAfter=4)
            body_style = ParagraphStyle('BStyle', fontName='Helvetica', fontSize=9, leading=12)
            tbl_body_style = ParagraphStyle('TblStyle', fontName='Helvetica', fontSize=8, leading=11, alignment=1) # Center aligned
            tbl_head_style = ParagraphStyle('TblHeadStyle', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.white, alignment=1)

            # Header
            story.append(Paragraph("JAIN VITTASAR FINANCIAL INTELLIGENCE", title_style))
            story.append(Paragraph(f"<b>SOFTWARE SUBSCRIPTION INVOICE</b> | Ref: JV-LIC-{unique_id}", body_style))
            story.append(Spacer(1, 12))

            # Seller vs Buyer Details
            seller_info = (
                "<b>ISSUED BY (Software Provider):</b><br/>"
                "Jain Vittasar Software Technologies<br/>"
                "Support Email: Rj308218@gmail.com<br/>"
                "GSTIN: 08AAAAA0000A1Z5<br/>"
                "Rajasthan, India"
            )
            
            buyer_company_name = str(company_data[1]) if len(company_data) > 1 and company_data[1] else "N/A"
            buyer_address = str(company_data[2]) if len(company_data) > 2 and company_data[2] else "N/A"
            buyer_phone = str(company_data[3]) if len(company_data) > 3 and company_data[3] else "N/A"
            buyer_gstin = str(company_data[6]) if len(company_data) > 6 and company_data[6] else "N/A"

            buyer_info = (
                f"<b>ISSUED TO (Business Owner):</b><br/>"
                f"<b>{buyer_company_name}</b><br/>"
                f"Address: {buyer_address}<br/>"
                f"Phone: {buyer_phone}<br/>"
                f"GSTIN: {buyer_gstin}"
            )

            info_table = Table([[Paragraph(seller_info, body_style), Paragraph(buyer_info, body_style)]], colWidths=[270, 270])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F7')),
                ('PADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#BDC3C7')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7'))
            ]))
            story.append(info_table)
            story.append(Spacer(1, 15))

            # Clean formatted Plan String
            clean_plan_title = f"Jain Vittasar Desktop License - {plan_name}"

            # Table Data with wrapped paragraphs to avoid string cutting
            grid_data = [
                [
                    Paragraph("Item Description", tbl_head_style), 
                    Paragraph("Validity", tbl_head_style), 
                    Paragraph("Activation Date", tbl_head_style), 
                    Paragraph("Expiry Date", tbl_head_style), 
                    Paragraph("Amount (INR)", tbl_head_style)
                ],
                [
                    Paragraph(clean_plan_title, body_style), 
                    Paragraph(f"{days} Days", tbl_body_style), 
                    Paragraph(act_date, tbl_body_style), 
                    Paragraph(exp_date, tbl_body_style), 
                    Paragraph(f"₹ {amount:.2f}", tbl_body_style)
                ],
                [
                    "", "", "", 
                    Paragraph("<b>Total Payable:</b>", body_style), 
                    Paragraph(f"<b>₹ {amount:.2f}</b>", tbl_body_style)
                ]
            ]

            grid_table = Table(grid_data, colWidths=[180, 65, 110, 110, 75])
            grid_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EAEDED')),
            ]))
            story.append(grid_table)
            story.append(Spacer(1, 15))

            try:
                words = num2words(amount, lang='en_IN').title() + " Only"
            except Exception:
                words = f"{amount} Rupees Only"

            story.append(Paragraph(f"<b>Amount in Words:</b> INR {words}", body_style))
            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>Payment Terms:</b> Paid in Full via Master Authorization Payment Gateway.", body_style))
            story.append(Spacer(1, 25))
            story.append(Paragraph("<para align='right'><b>for Jain Vittasar Software Technologies</b><br/><br/><br/>Authorized Signatory</para>", body_style))

            doc.build(story)

            # Auto open PDF
            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                os.system(f"open '{pdf_path}' || xdg-open '{pdf_path}'")

        except Exception as e:
            messagebox.showerror("Invoice Generation Error", f"Failed to generate software license invoice: {str(e)}")
                        
    def generate_pdf_invoice_document(self, bill_no, copy_type="BUYER'S COPY"):
        unique_id = int(time.time())
        output_pdf_path = f"Invoice_{bill_no}_{unique_id}.pdf"
        
        try:
            # Fetch Bill Header from Supabase
            res_bill = supabase.table("bills").select("*").eq("bill_no", bill_no).execute()
            if not res_bill.data:
                messagebox.showerror("Error", "Invoice records empty inside DB.")
                return
            
            b_dict = res_bill.data[0]
            # Convert dictionary to tuple mapping matching old code indexes
            bill_hdr = (
                b_dict.get("bill_no"), b_dict.get("date"), b_dict.get("customer_name"),
                b_dict.get("grand_total"), b_dict.get("payment_method"), b_dict.get("invoice_type"),
                b_dict.get("due_date"), b_dict.get("remarks"), b_dict.get("txn_category"),
                b_dict.get("total_tax"), b_dict.get("total_discount")
            )

            # Fetch Bill Items from Supabase
            res_items = supabase.table("bill_items").select("item_name, qty, price, discount_percent, tax_rate, tax_amount, total_amount").eq("bill_no", bill_no).execute()
            
            items_rows = []
            if res_items.data:
                for item in res_items.data:
                    items_rows.append((
                        item.get("item_name"), item.get("qty"), item.get("price"),
                        item.get("discount_percent"), item.get("tax_rate"),
                        item.get("tax_amount"), item.get("total_amount")
                    ))

            if not bill_hdr:
                messagebox.showerror("Error", "Invoice records empty inside DB.")
                return

            doc = SimpleDocTemplate(
                output_pdf_path, 
                pagesize=letter, 
                rightMargin=40, 
                leftMargin=40, 
                topMargin=50, 
                bottomMargin=60
            )
            story = []

            if self.company:
                c_name = str(self.company[1] if self.company[1] else "N/A")
                c_addr = str(self.company[2] if self.company[2] else "N/A")
                c_phone = str(self.company[3] if self.company[3] else "N/A")
                c_email = str(self.company[4] if self.company[4] else "")
                c_gstin = str(self.company[6] if self.company[6] else "N/A")
                c_state = str(self.company[12] if len(self.company) > 12 and self.company[12] else "N/A")
                c_logo_path = str(self.company[13] if len(self.company) > 13 and self.company[13] else "")
                
                b_name_meta = str(self.company[8] if len(self.company) > 8 and self.company[8] else "N/A")
                b_acc = str(self.company[9] if len(self.company) > 9 and self.company[9] else "N/A")
                b_ifsc = str(self.company[10] if len(self.company) > 10 and self.company[10] else "N/A")
                b_upi = str(self.company[11] if len(self.company) > 11 and self.company[11] else "N/A")
            else:
                messagebox.showerror("Profile Error", "No Active Enterprise Instance Loaded.")
                return

            title_style = ParagraphStyle('TStyle', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#003366'), spaceAfter=5)
            body_style = ParagraphStyle('BStyle', fontName='Helvetica', fontSize=9, leading=13)
            header_style = ParagraphStyle('HStyle', fontName='Helvetica-Bold', fontSize=9, leading=13)

            header_table_data = []
            title_block = [
                Paragraph(f"{str(bill_hdr[5]).upper()} - ({copy_type})", title_style),
                Paragraph(f"<b>Invoice No:</b> {bill_hdr[0]} | <b>Dated:</b> {bill_hdr[1]}", body_style)
            ]
            
            from reportlab.platypus import Image as RLImage
            
            if c_logo_path and os.path.exists(c_logo_path):
                try:
                    logo_img = RLImage(c_logo_path, width=50, height=50)
                    header_table_data = [[title_block, logo_img]]
                    header_table = Table(header_table_data, colWidths=[440, 80])
                except Exception:
                    header_table = Table([[title_block, ""]], colWidths=[440, 80])
            else:
                header_table = Table([[title_block, ""]], colWidths=[440, 80])
                
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,0), 'RIGHT')
            ]))
            story.append(header_table)
            story.append(Spacer(1, 15))

            email_part = f"<br/>Email: {c_email}" if c_email else ""
            profile_text = f"<b>COMPANY PROFILE (Owner Details):</b><br/>{c_name}<br/>{c_addr}<br/>Phone: {c_phone}{email_part}<br/>GSTIN/UIN: {c_gstin}<br/>State: {c_state}"
            buyer_text = f"<b>Buyer (Bill to):</b><br/>{bill_hdr[2]}<br/>State Name: {c_state}<br/>Payment Mode: {bill_hdr[4]}"
            
            party_data = [[Paragraph(profile_text, body_style), Paragraph(buyer_text, body_style)]]
            party_table = Table(party_data, colWidths=[260, 260])
            party_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F7')),
                ('PADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#BDC3C7')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7'))
            ]))
            story.append(party_table)
            story.append(Spacer(1, 15))

            grid_data = [["Sl No", "Description of Goods", "HSN Code", "Qty", "Unit", "Rate", "Disc %", "Amount"]]
            sub_total = 0.0
            total_tax_accrued = 0.0
            active_tax_rate = 18.0

            for idx, row in enumerate(items_rows, start=1):
                item_qty = row[1]
                item_rate = row[2]
                item_disc_p = row[3]  
                item_tax_rate = row[4] 
                item_tax_amt = row[5]  
                item_gross = row[6]   
                
                active_tax_rate = item_tax_rate
                base_taxable_amount = item_gross - item_tax_amt
                sub_total += base_taxable_amount
                total_tax_accrued += item_tax_amt

                grid_data.append([
                    str(idx),
                    Paragraph(str(row[0]), body_style),
                    "85446090",
                    f"{item_qty:.2f}",
                    "MTR" if "WIRE" in str(row[0]).upper() else "PCS",
                    f"{item_rate:.2f}",
                    f"{item_disc_p}%", 
                    f"{base_taxable_amount:.2f}"
                ])
            
            half_tax = total_tax_accrued / 2.0
            grand_total_calc = sub_total + total_tax_accrued
            
            grid_data.append(["", Paragraph("<b>Sub Total</b>", body_style), "", "", "", "", "", f"{sub_total:.2f}"])
            grid_data.append(["", Paragraph(f"OUTPUT CGST @ {active_tax_rate / 2:.1f}%", body_style), "", "", "", "", "", f"{half_tax:.2f}"])
            grid_data.append(["", Paragraph(f"OUTPUT SGST @ {active_tax_rate / 2:.1f}%", body_style), "", "", "", "", "", f"{half_tax:.2f}"])
            
            rounded_grand_total = round(grand_total_calc)
            round_off_diff = rounded_grand_total - grand_total_calc
            if abs(round_off_diff) > 0.001:
                grid_data.append(["", Paragraph("Less: ROUND OFF", body_style), "", "", "", "", "", f"{round_off_diff:.2f}"])

            grid_data.append(["", Paragraph("<b>Grand Total</b>", header_style), "", "", "", "", "", f"INR {rounded_grand_total:.2f}"])

            grid_table = Table(grid_data, colWidths=[30, 180, 55, 35, 35, 55, 45, 85], repeatRows=1)
            grid_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EAEDED')),
            ]))
            story.append(grid_table)
            story.append(Spacer(1, 15))

            try:
                words_string = num2words(rounded_grand_total, lang='en_IN').title() + " Only"
                words_string = words_string.replace("And", "and")
            except Exception:
                words_string = "Conversion Error"

            story.append(Paragraph(f"<b>Amount Chargeable (in words):</b> INR {words_string}", body_style))
            story.append(Spacer(1, 15))

            remit_text = f"<b>BANK REMITTANCE DETAILS:</b><br/>Bank Name: {b_name_meta} | Account No: {b_acc}<br/>IFSC Core: {b_ifsc} | UPI ID: {b_upi}"
            
            # Generate Dynamic UPI QR Code Image if UPI ID exists
            qr_temp_path = None
            if b_upi and b_upi != "N/A" and rounded_grand_total > 0:
                try:
                    upi_uri = f"upi://pay?pa={b_upi}&pn={c_name}&am={rounded_grand_total:.2f}&tn=Bill_{bill_hdr[0]}&cu=INR"
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=3, border=1)
                    qr.add_data(upi_uri)
                    qr.make(fit=True)
                    qr_img_obj = qr.make_image(fill_color="#003366", back_color="white")
                    qr_temp_path = f"temp_qr_{bill_no}.png"
                    qr_img_obj.save(qr_temp_path)
                    
                    qr_rl_img = RLImage(qr_temp_path, width=65, height=65)
                    remit_table = Table([[Paragraph(remit_text, body_style), qr_rl_img]], colWidths=[420, 100])
                    remit_table.setStyle(TableStyle([
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('ALIGN', (1,0), (1,0), 'RIGHT')
                    ]))
                    story.append(remit_table)
                except Exception:
                    story.append(Paragraph(remit_text, body_style))
            else:
                story.append(Paragraph(remit_text, body_style))

            story.append(Spacer(1, 15))
            
            story.append(Paragraph("<b>Declaration:</b><br/>We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.", body_style))
            story.append(Spacer(1, 25))
            story.append(Paragraph(f"<para align='right'><b>for {c_name}</b><br/><br/><br/>Authorised Signatory</para>", body_style))

            def add_multipage_decorations(canvas, document):
                canvas.saveState()
                canvas.setFont('Helvetica-Oblique', 8)
                canvas.setFillColor(colors.HexColor('#555555'))
                canvas.drawString(40, 760, f"{c_name} - TAX INVOICE")
                canvas.setStrokeColor(colors.HexColor('#BDC3C7'))
                canvas.setLineWidth(0.5)
                canvas.line(40, 755, 570, 755)
                page_num = canvas.getPageNumber()
                canvas.drawRightString(570, 30, f"Page {page_num}")
                canvas.drawString(40, 30, "Computer Generated Document Check")
                canvas.restoreState()

            doc.build(story, onFirstPage=add_multipage_decorations, onLaterPages=add_multipage_decorations)
            messagebox.showinfo("Success", f"PDF Generated successfully!\nSaved as: {output_pdf_path}")
            
            if os.name == 'nt': os.startfile(output_pdf_path)
            else: os.system(f"open '{output_pdf_path}' || xdg-open '{output_pdf_path}'")
        except Exception as e:
            messagebox.showerror("PDF Compilation Error", f"ReportLab Engine Failed: {str(e)}")

    # =================================================-------
    # PHASE 6: INVENTORY CONTROL & PURCHASE MODULE
    # ========================================================
    def render_procurement_inventory_workspace(self):
        for widget in self.tab_inventory.winfo_children(): widget.destroy()
        
        if not self.company:
            tk.Label(self.tab_inventory, text="⚠️ NO ACTIVE ENTERPRISE INSTANCE LOADED. GO TO HOME TAB TO INITIALIZE.", font=("Arial", 12, "bold"), fg="red").pack(pady=100)
            return

        split_layout = ttk.Panedwindow(self.tab_inventory, orient="horizontal")
        split_layout.pack(fill="both", expand=True)

        left_side_menu = tk.Frame(split_layout, bg="#2C3E50", width=240)
        self.inventory_workspace = tk.Frame(split_layout, bg="#F4F6F9")
        split_layout.add(left_side_menu, weight=1)
        split_layout.add(self.inventory_workspace, weight=4)

        tk.Label(left_side_menu, text="INVENTORY & PURCHASE", font=("Arial", 10, "bold"), fg="#BDC3C7", bg="#2C3E50").pack(pady=15, padx=10, anchor="w")

        operations_nav = [
            ("➕ Create New Party", self.render_inv_create_party_panel),
            ("📦 Add New Item (Purchase)", self.render_inv_add_item_panel),
            ("📊 View All Stock Items", self.render_inv_view_stock_panel)
        ]

        for text, command in operations_nav:
            tk.Button(
                left_side_menu, text=text, font=("Arial", 9, "bold"), bg="#34495E", fg="#ECF0F1",
                activebackground="#1ABC9C", activeforeground="white", bd=0, cursor="hand2", anchor="w", padx=12, pady=10, command=command
            ).pack(fill="x", pady=2, padx=5)

        self.render_inv_add_item_panel()

    def render_inv_create_party_panel(self):
        for widget in self.inventory_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.inventory_workspace, padding=30)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Register New Purchase Supplier / Party", font=("Arial", 14, "bold"), foreground="#003366").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        labels = ["Party Corporate Name *", "Contact Person Name", "Primary Helpline Coordinates", "GSTIN Account Index", "State Jurisdiction", "Opening Balanced Value (₹)", "Balance Core Type", "Party Address"]
        vars_map = ["p_name", "p_contact", "p_phone", "p_gstin", "p_state", "p_op_bal", "p_type", "p_address"]
        
        self.inv_party_entries = {}
        for idx, (lbl, key) in enumerate(zip(labels, vars_map)):
            ttk.Label(f, text=lbl, font=("Arial", 10, "bold")).grid(row=idx+1, column=0, sticky="w", pady=6)
            if key == "p_type":
                ent = ttk.Combobox(f, values=["Dr", "Cr"], state="readonly", width=28)
                ent.set("Cr")
            else:
                ent = ttk.Entry(f, width=30)
            ent.grid(row=idx+1, column=1, pady=6, ipady=2)
            self.inv_party_entries[key] = ent

        def save_inv_party():
            name = self.inv_party_entries["p_name"].get().strip()
            if not name: messagebox.showerror("Error", "Party Name is mandatory."); return
            try: op_bal = float(self.inv_party_entries["p_op_bal"].get() or 0.0)
            except ValueError: op_bal = 0.0
            
            try:
                self.cursor.execute("INSERT INTO parties (party_name, contact_person, phone, gstin, state, opening_balance, balance_type, address) VALUES (?,?,?,?,?,?,?,?)",
                                    (name, self.inv_party_entries["p_contact"].get(), self.inv_party_entries["p_phone"].get(), self.inv_party_entries["p_gstin"].get(), self.inv_party_entries["p_state"].get(), op_bal, self.inv_party_entries["p_type"].get(), self.inv_party_entries["p_address"].get()))
                self.conn.commit()
                messagebox.showinfo("Success", f"Supplier Party '{name}' saved successfully.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Party name already exists!")

        tk.Button(f, text="💾 SAVE SUPPLIER PARTY", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=8, command=save_inv_party).grid(row=9, column=0, columnspan=2, pady=20, sticky="w")

    def render_inv_add_item_panel(self):
        for widget in self.inventory_workspace.winfo_children(): widget.destroy()
        self.purchase_cart = []

        f = ttk.Frame(self.inventory_workspace, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Purchase Entry & Item Intake System", font=("Arial", 14, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 10))

        meta_box = ttk.LabelFrame(f, text=" Vendor & Settlement Parameters ", padding=10)
        meta_box.pack(fill="x", pady=5)
        
        ttk.Label(meta_box, text="Select Supplier Party:").grid(row=0, column=0, sticky="w", padx=5)
        self.cursor.execute("SELECT party_name FROM parties")
        parties = [r[0] for r in self.cursor.fetchall()]
        self.purch_party_cb = ttk.Combobox(meta_box, values=parties, state="normal", width=25)
        self.purch_party_cb.grid(row=0, column=1, pady=4)

        ttk.Label(meta_box, text="Goods Receiver Name * :").grid(row=0, column=2, sticky="w", padx=20)
        self.purch_receiver_ent = ttk.Entry(meta_box, width=22)
        self.purch_receiver_ent.grid(row=0, column=3, pady=4)

        ttk.Label(meta_box, text="Settlement Account:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.purch_payment_method_cb = ttk.Combobox(meta_box, values=["Cash", "Bank Remittance"], state="readonly", width=25)
        self.purch_payment_method_cb.set("Bank Remittance")
        self.purch_payment_method_cb.grid(row=1, column=1, pady=5)

        item_box = ttk.LabelFrame(f, text=" Add Item Details Line Matrix ", padding=10)
        item_box.pack(fill="x", pady=5)

        ttk.Label(item_box, text="Item Name *:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.p_item_name = ttk.Entry(item_box, width=15)
        self.p_item_name.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(item_box, text="HSN Code:").grid(row=0, column=2, sticky="w", padx=2, pady=2)
        self.p_item_hsn = ttk.Entry(item_box, width=10)
        self.p_item_hsn.insert(0, "85446090")
        self.p_item_hsn.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(item_box, text="Qty *:").grid(row=0, column=4, sticky="w", padx=2, pady=2)
        self.p_item_qty = ttk.Entry(item_box, width=6)
        self.p_item_qty.grid(row=0, column=5, padx=5, pady=2)

        ttk.Label(item_box, text="Unit:").grid(row=0, column=6, sticky="w", padx=2, pady=2)
        self.p_item_unit = ttk.Combobox(item_box, values=["PCS", "MTR", "KG", "BOX", "SET", "NOS"], state="normal", width=6)
        self.p_item_unit.set("PCS")
        self.p_item_unit.grid(row=0, column=7, padx=5, pady=2)

        ttk.Label(item_box, text="Rate Per (Unit) *:").grid(row=1, column=0, sticky="w", padx=2, pady=4)
        self.p_item_price = ttk.Entry(item_box, width=12)
        self.p_item_price.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(item_box, text="Discount %:").grid(row=1, column=2, sticky="w", padx=2, pady=4)
        self.p_item_disc = ttk.Entry(item_box, width=8)
        self.p_item_disc.insert(0, "0.0")
        self.p_item_disc.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(item_box, text="Tax Rate %:").grid(row=1, column=4, sticky="w", padx=2, pady=4)
        self.p_item_tax_rate = ttk.Combobox(item_box, values=["0", "5", "12", "18", "28"], state="readonly", width=6)
        self.p_item_tax_rate.set("18")
        self.p_item_tax_rate.grid(row=1, column=5, padx=5, pady=4)

        cart_cols = ("name", "hsn", "qty", "unit", "rate", "disc", "tax_amt", "total")
        self.purch_tree = ttk.Treeview(f, columns=cart_cols, show="headings", height=8)
        
        headers_config = [
            ("name", "Item Name"), ("hsn", "HSN Code"), ("qty", "Quantity"), 
            ("unit", "Unit"), ("rate", "Rate Per Unit"), ("disc", "Discount %"), 
            ("tax_amt", "Tax Amount"), ("total", "Grand Total")
        ]
        for col, head in headers_config:
            self.purch_tree.heading(col, text=head)
            self.purch_tree.column(col, width=120, anchor="center" if col != "name" else "w")
        self.purch_tree.pack(fill="x", pady=5)

        def add_item_to_purch_cart():
            name = self.p_item_name.get().strip()
            hsn = self.p_item_hsn.get().strip() or "N/A"
            qty_str = self.p_item_qty.get().strip()
            unit = self.p_item_unit.get().strip() or "PCS"
            price_str = self.p_item_price.get().strip()
            disc_str = self.p_item_disc.get().strip() or "0.0"
            tax_p_str = self.p_item_tax_rate.get()

            if not name or not qty_str or not price_str:
                messagebox.showerror("Validation Failed", "Please populate critical item fields (Name, Qty, Rate)."); return
            try:
                q = int(qty_str); p = float(price_str); d_p = float(disc_str); t_p = float(tax_p_str)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be Integer. Price/Discount must be Numeric."); return

            base_cost = q * p
            disc_amount = base_cost * (d_p / 100.0)
            taxable_val = base_cost - disc_amount
            tax_amount = taxable_val * (t_p / 100.0)
            grand_total = taxable_val + tax_amount

            entry_dict = {
                "name": name, "hsn": hsn, "qty": q, "unit": unit, 
                "price": p, "disc_percent": d_p, "tax_rate": t_p, 
                "tax_amount": tax_amount, "total_amount": grand_total
            }
            self.purchase_cart.append(entry_dict)
            
            self.purch_tree.insert("", "end", values=(
                name, hsn, q, unit, f"₹{p:.2f}", f"{d_p}%", f"₹{tax_amount:.2f}", f"₹{grand_total:.2f}"
            ))
            
            self.p_item_name.delete(0, tk.END); self.p_item_qty.delete(0, tk.END); self.p_item_price.delete(0, tk.END)
            self.p_item_disc.delete(0, tk.END); self.p_item_disc.insert(0, "0.0")

        tk.Button(item_box, text="➕ APPEND ENTRY LINE", bg="#3498DB", fg="white", font=("Arial", 9, "bold"), bd=0, padx=12, pady=4, command=add_item_to_purch_cart).grid(row=1, column=6, columnspan=2, padx=10, sticky="e")

        def commit_purchase_and_receipt():
            receiver = self.purch_receiver_ent.get().strip()
            party = self.purch_party_cb.get().strip()
            p_method = self.purch_payment_method_cb.get()
            if not receiver: 
                messagebox.showerror("Error", "Receiver Identity Name is required for inventory logs.")
                return
            if not self.purchase_cart: 
                messagebox.showerror("Error", "No records exist inside the transaction matrix buffer.")
                return

            cur_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            gross_total_purchase = sum(x["total_amount"] for x in self.purchase_cart)

            try:
                active_company_id = self.company[0] if self.company else None

                for item in self.purchase_cart:
                    # Check if item exists in Supabase for THIS company
                    res_inv = supabase.table("inventory") \
                        .select("stock") \
                        .eq("item_name", item["name"]) \
                        .eq("company_id", active_company_id) \
                        .execute()
                    
                    if res_inv.data:
                        new_stock = res_inv.data[0]["stock"] + item["qty"]
                        supabase.table("inventory").update({
                            "stock": new_stock,
                            "price": item["price"]
                        }).eq("item_name", item["name"]).eq("company_id", active_company_id).execute()
                    else:
                        supabase.table("inventory").insert({
                            "company_id": active_company_id,
                            "item_name": item["name"],
                            "stock": item["qty"],
                            "price": item["price"],
                            "hsn_code": item["hsn"],
                            "unit": item["unit"]
                        }).execute()
                
                # Record Audit Log in Supabase
                acc_type = "Cash" if p_method == "Cash" else "Bank"
                supabase.table("audit_logs").insert({
                    "date": cur_date,
                    "account_type": acc_type,
                    "party_name": party,
                    "bill_ref": "PURCH-GRN",
                    "txn_type": "Paid",
                    "amount": gross_total_purchase,
                    "remarks": f"Inward Procurement Module executed by {receiver}."
                }).execute()

                current_cart_items = list(self.purchase_cart)
                self.generate_pdf_purchase_receipt(party, receiver, current_cart_items)
                self.render_inv_view_stock_panel()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to commit purchase: {str(e)}")

        tk.Button(f, text="💾 RECEIVE STOCK & GENERATE PROOF RECEIPT", bg="#27AE60", fg="white", font=("Arial", 11, "bold"), bd=0, padx=25, pady=10, command=commit_purchase_and_receipt).pack(anchor="w", pady=10)

    def generate_pdf_purchase_receipt(self, party_name, receiver_name, items_list):
        unique_id = int(time.time())
        output_pdf_path = f"PurchaseReceipt_{unique_id}.pdf"
        
        try:
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=60)
            story = []

            if self.company:
                c_name = str(self.company[1] if self.company[1] else "N/A")
                c_addr = str(self.company[2] if self.company[2] else "N/A")
                c_phone = str(self.company[3] if self.company[3] else "N/A")
                c_gstin = str(self.company[6] if self.company[6] else "N/A")
                c_logo_path = str(self.company[13] if len(self.company) > 13 and self.company[13] else "")
            else:
                messagebox.showerror("Profile Error", "No Active Enterprise Profile Context."); return

            title_style = ParagraphStyle('TStyle', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#003366'), spaceAfter=5)
            body_style = ParagraphStyle('BStyle', fontName='Helvetica', fontSize=9, leading=13)
            header_style = ParagraphStyle('HStyle', fontName='Helvetica-Bold', fontSize=9, leading=13)

            title_block = [
                Paragraph("GOODS RECEIPT NOTE (PURCHASE)", title_style),
                Paragraph(f"<b>Transaction Reference:</b> GRN-{unique_id} | <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style)
            ]
            
            from reportlab.platypus import Image as RLImage
            if c_logo_path and os.path.exists(c_logo_path):
                try:
                    logo_img = RLImage(c_logo_path, width=50, height=50)
                    header_table = Table([[title_block, logo_img]], colWidths=[440, 80])
                except Exception:
                    header_table = Table([[title_block, ""]], colWidths=[440, 80])
            else:
                header_table = Table([[title_block, ""]], colWidths=[440, 80])
                
            header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
            story.append(header_table)
            story.append(Spacer(1, 15))

            self.cursor.execute("SELECT address, gstin FROM parties WHERE party_name=?", (party_name,))
            party_row = self.cursor.fetchone()
            p_addr = party_row[0] if party_row and party_row[0] else "N/A"
            p_gstin = party_row[1] if party_row and party_row[1] else "N/A"

            profile_text = f"<b>CONSIGNEE / RECEIVER (Owner Details):</b><br/>{c_name}<br/>{c_addr}<br/>GSTIN/UIN: {c_gstin}<br/><b>Received By Signature:</b> {receiver_name}"
            supplier_text = f"<b>SUPPLIER VENDOR VOUCHER:</b><br/>{party_name}<br/>Address: {p_addr}<br/>GSTIN: {p_gstin}"
            
            party_table = Table([[Paragraph(profile_text, body_style), Paragraph(supplier_text, body_style)]], colWidths=[260, 260])
            party_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F7')),
                ('PADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#BDC3C7')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7'))
            ]))
            story.append(party_table)
            story.append(Spacer(1, 15))

            grid_data = [["Sl", "Description of Goods", "HSN Code", "Qty", "Unit", "Rate", "Disc %", "Amount"]]
            sub_total = 0.0
            total_tax_accrued = 0.0
            last_tax_rate = 18.0 

            for idx, item in enumerate(items_list, start=1):
                qty = item["qty"]; rate = item["price"]; disc_p = item["disc_percent"]; tax_amt = item["tax_amount"]; gross = item["total_amount"]
                last_tax_rate = item["tax_rate"]
                taxable_val = gross - tax_amt
                sub_total += taxable_val; total_tax_accrued += tax_amt

                grid_data.append([
                    str(idx), Paragraph(item["name"], body_style), Paragraph(str(item["hsn"]), body_style),
                    Paragraph(f"{qty:.2f}", body_style), Paragraph(str(item["unit"]), body_style),
                    Paragraph(f"{rate:.2f}", body_style), Paragraph(f"{disc_p}%", body_style), Paragraph(f"{taxable_val:.2f}", body_style)
                ])
                
            half_tax = total_tax_accrued / 2.0
            grand_total_calc = sub_total + total_tax_accrued
            split_tax_percentage = last_tax_rate / 2.0

            grid_data.append(["", Paragraph("<b>Sub Total</b>", body_style), "", "", "", "", "", Paragraph(f"<b>{sub_total:.2f}</b>", body_style)])
            grid_data.append(["", Paragraph(f"INPUT CGST @ {split_tax_percentage:.1f}%", body_style), "", "", "", "", "", Paragraph(f"{half_tax:.2f}", body_style)])
            grid_data.append(["", Paragraph(f"INPUT SGST @ {split_tax_percentage:.1f}%", body_style), "", "", "", "", "", Paragraph(f"{half_tax:.2f}", body_style)])
            rounded_grand_total = round(grand_total_calc)
            grid_data.append(["", Paragraph("<b>Grand Total</b>", header_style), "", "", "", "", "", Paragraph(f"<b>INR {rounded_grand_total:.2f}</b>", header_style)])

            grid_table = Table(grid_data, colWidths=[25, 175, 55, 45, 35, 55, 45, 85], repeatRows=1)
            grid_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EAEDED')),
            ]))
            story.append(grid_table)
            story.append(Spacer(1, 15))

            try: words_string = num2words(rounded_grand_total, lang='en_IN').title() + " Only"
            except Exception: words_string = "Conversion Error"

            story.append(Paragraph(f"<b>Total Value (In Words):</b> INR {words_string}", body_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph("<b>Declaration Inventory Verification:</b> Materials checked and entered safely within corporate repository ledgers.", body_style))
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"<para align='right'><b>for {c_name}</b><br/><br/><br/>Store Officer / Authenticated Receiver</para>", body_style))

            def add_decorations(canvas, document):
                canvas.saveState(); canvas.setFont('Helvetica-Oblique', 8); canvas.drawString(40, 760, f"{c_name} - GOODS RECEIPT RUNTIME PROOF")
                canvas.line(40, 755, 570, 755); canvas.drawRightString(570, 30, f"Page {canvas.getPageNumber()}"); canvas.restoreState()

            doc.build(story, onFirstPage=add_decorations, onLaterPages=add_decorations)
            messagebox.showinfo("Success", f"GRN Inward Purchase Receipt Compiled Saved as: {output_pdf_path}")
            if os.name == 'nt': os.startfile(output_pdf_path)
            else: os.system(f"open '{output_pdf_path}' || xdg-open '{output_pdf_path}'")
        except Exception as e:
            messagebox.showerror("Purchase PDF Error", f"ReportLab Engine compilation failure: {str(e)}")

    def render_inv_view_stock_panel(self):
        for widget in self.inventory_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.inventory_workspace, padding=25)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Current Live Inventory Stock Levels Console", font=("Arial", 14, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 5))

        filter_box = ttk.LabelFrame(f, text=" Chronological Excel Data Export Console ", padding=10)
        filter_box.pack(fill="x", pady=5)
        
        ttk.Label(filter_box, text="Export Snapshot Matrix Structure:").grid(row=0, column=0, sticky="w")
        
        def export_stock_report_to_excel():
            try:
                if not self.company or not self.company[0]:
                    messagebox.showwarning("Warning", "No active company context loaded!")
                    return

                active_company_id = self.company[0]
                res = supabase.table("inventory") \
                    .select("id, item_name, stock, price, hsn_code, unit") \
                    .eq("company_id", active_company_id) \
                    .execute()

                if res.data:
                    for row in res.data:
                        tree.insert("", "end", values=(
                            row.get("id"),
                            row.get("item_name"),
                            row.get("stock"),
                            f"₹ {row.get('price', 0.0):,.2f}",
                            row.get("hsn_code", ""),
                            row.get("unit", "Pcs")
                        ))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load inventory: {str(e)}")

        tk.Button(filter_box, text="📊 Run Export Stock Ledger Matrix", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), bd=0, padx=12, pady=4, command=export_stock_report_to_excel).grid(row=0, column=1, padx=15)

        columns = ("id", "name", "stock", "price", "hsn", "unit")
        tree = ttk.Treeview(f, columns=columns, show="headings", height=12)
        for col, head in zip(columns, ["Item ID", "Item Description", "Available Stock Qty", "Last Purchase Rate", "HSN Code", "Unit"]):
            tree.heading(col, text=head)
            tree.column(col, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)

        try:
            res = supabase.table("inventory").select("id, item_name, stock, price, hsn_code, unit").execute()
            if res.data:
                for row in res.data:
                    tree.insert("", "end", values=(
                        row.get("id"),
                        row.get("item_name"),
                        row.get("stock"),
                        f"₹ {row.get('price', 0.0):,.2f}",
                        row.get("hsn_code", ""),
                        row.get("unit", "Pcs")
                    ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load inventory: {str(e)}")

    # ==========================================================
    # PHASE 7: FINANCIAL AUDIT LOGS & ADVANCED RECONCILIATION
    # ==========================================================
    def render_collection_ledger_workspace(self):
        for widget in self.tab_collection.winfo_children(): widget.destroy()
        if not self.company:
            tk.Label(self.tab_collection, text="⚠️ NO ACTIVE ENTERPRISE INSTANCE LOADED. GO TO HOME TAB TO INITIALIZE.", font=("Arial", 12, "bold"), fg="red").pack(pady=100)
            return

        split_layout = ttk.Panedwindow(self.tab_collection, orient="horizontal")
        split_layout.pack(fill="both", expand=True)

        left_side_menu = tk.Frame(split_layout, bg="#2C3E50", width=250)
        self.audit_workspace = tk.Frame(split_layout, bg="#F4F6F9")
        split_layout.add(left_side_menu, weight=1)
        split_layout.add(self.audit_workspace, weight=4)

        tk.Label(left_side_menu, text="AUDIT LOG MODULES", font=("Arial", 10, "bold"), fg="#BDC3C7", bg="#2C3E50").pack(pady=15, padx=10, anchor="w")

        operations_nav = [
            ("🏦 Add New Bank Account", self.render_audit_add_bank_panel),
            ("📝 Log Payment Reconcile", self.render_audit_payment_entry_panel),
            ("📅 View Daily Audit Reports", self.render_audit_daily_report_panel)
        ]

        for text, command in operations_nav:
            tk.Button(
                left_side_menu, text=text, font=("Arial", 9, "bold"), bg="#34495E", fg="#ECF0F1",
                activebackground="#1ABC9C", activeforeground="white", bd=0, cursor="hand2", anchor="w", padx=12, pady=10, command=command
            ).pack(fill="x", pady=2, padx=5)

        self.render_audit_daily_report_panel()

    def render_audit_add_bank_panel(self):
        for widget in self.audit_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.audit_workspace, padding=30)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Register New Corporate Bank Institutional Account Node", font=("Arial", 14, "bold"), foreground="#003366").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        labels = ["Name of Account Holder *", "Account Sequence Number *", "IFS Routing Code *", "Bank Name & Branch Title *", "Opening balance as on (01-April) *"]
        keys = ["holder", "acc_num", "ifsc", "branch", "op_bal"]
        
        self.bank_entries = {}
        for idx, (lbl, k) in enumerate(zip(labels, keys)):
            ttk.Label(f, text=lbl, font=("Arial", 10, "bold")).grid(row=idx+1, column=0, sticky="w", pady=6)
            ent = ttk.Entry(f, width=35)
            ent.grid(row=idx+1, column=1, pady=6, ipady=2)
            self.bank_entries[k] = ent
            
        def process_save_bank_account():
            d = {k: v.get().strip() for k, v in self.bank_entries.items()}
            if not d["holder"] or not d["acc_num"] or not d["ifsc"] or not d["branch"]:
                messagebox.showerror("Error", "Please populate all mandatory fields."); return
            try: ob = float(d["op_bal"] or 0.0)
            except ValueError: ob = 0.0
            
            try:
                self.cursor.execute("INSERT INTO bank_accounts (holder_name, account_no, ifsc, bank_branch, opening_balance, as_on_date) VALUES (?,?,?,?,?,?)",
                                    (d["holder"], d["acc_num"], d["ifsc"], d["branch"], ob, f"{datetime.now().year}-04-01"))
                self.conn.commit()
                messagebox.showinfo("Success", "Bank account node added into system registry ledger cleanly.")
                self.render_audit_daily_report_panel()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Account sequence code already maps to another institution inside database.")

        tk.Button(f, text="💾 SUBMIT REGISTER BANK ACCOUNT", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=8, command=process_save_bank_account).grid(row=7, column=0, columnspan=2, pady=25, sticky="w")

    def render_audit_payment_entry_panel(self):
        for widget in self.audit_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.audit_workspace, padding=30)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Manual Payment Voucher Entry & Reconciliation Console", font=("Arial", 14, "bold"), foreground="#003366").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        ttk.Label(f, text="Select Mode *:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        mode_cb = ttk.Combobox(f, values=["Cash", "Bank Account"], state="readonly", width=32)
        mode_cb.set("Bank Account"); mode_cb.grid(row=1, column=1, pady=6)

        ttk.Label(f, text="Select Target Registry (If Bank):", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.cursor.execute("SELECT id, bank_branch, account_no FROM bank_accounts")
        banks = [f"{r[0]} | {r[1]} - ({r[2]})" for r in self.cursor.fetchall()]
        bank_target_cb = ttk.Combobox(f, values=banks, state="readonly", width=32)
        if banks: bank_target_cb.set(banks[0])
        bank_target_cb.grid(row=2, column=1, pady=6)

        ttk.Label(f, text="Select Counterparty Client *:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        self.cursor.execute("SELECT party_name FROM parties")
        parties = [r[0] for r in self.cursor.fetchall()]
        party_cb = ttk.Combobox(f, values=parties, state="normal", width=32)
        if parties: party_cb.set(parties[0])
        party_cb.grid(row=3, column=1, pady=6)

        ttk.Label(f, text="Invoice Ref Mapping / Notes:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=6)
        ref_ent = ttk.Entry(f, width=35)
        ref_ent.grid(row=4, column=1, pady=6, ipady=2)

        ttk.Label(f, text="Transaction Classification Type *:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", pady=6)
        type_cb = ttk.Combobox(f, values=["Received", "Paid"], state="readonly", width=32)
        type_cb.set("Received"); type_cb.grid(row=5, column=1, pady=6)

        ttk.Label(f, text="Net Settle Valuation (₹) *:", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky="w", pady=6)
        amt_ent = ttk.Entry(f, width=35)
        amt_ent.grid(row=6, column=1, pady=6, ipady=2)

        def process_submit_payment_voucher():
            mode = mode_cb.get()
            party = party_cb.get().strip()
            ref = ref_ent.get().strip() or "DIRECT-VOUCHER"
            txtype = type_cb.get()
            val_str = amt_ent.get().strip()
            
            if not party or not val_str:
                messagebox.showerror("Validation Violation", "Mandatory details missing."); return
            try: val = float(val_str)
            except ValueError: messagebox.showerror("Error", "Value must be numeric."); return

            b_id = None
            if mode == "Bank Account" and bank_target_cb.get():
                b_id = int(bank_target_cb.get().split(" | ")[0])

            cur_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.cursor.execute("INSERT INTO audit_logs (date, account_type, account_id, party_name, bill_ref, txn_type, amount, remarks) VALUES (?,?, ?,?,?,?,?,?)",
                                (cur_date, "Cash" if mode=="Cash" else "Bank", b_id, party, ref, txtype, val, f"Manual Ledger entry reconciliation sequence check."))
            self.conn.commit()
            messagebox.showinfo("Success", "Financial voucher processed successfully into matrix layout mapping loops.")
            self.render_audit_daily_report_panel()

        tk.Button(f, text="⚙ PROCESSED COMMIT RECONCILED TRANSACTION", bg="#2980B9", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=8, command=process_submit_payment_voucher).grid(row=7, column=0, columnspan=2, pady=25, sticky="w")

    def render_audit_daily_report_panel(self):
        for widget in self.audit_workspace.winfo_children(): widget.destroy()
        f = ttk.Frame(self.audit_workspace, padding=20)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Comprehensive Daily Audit Log & Operational Reports Console", font=("Arial", 14, "bold"), foreground="#003366").pack(anchor="w", pady=(0, 10))

        filter_box = ttk.LabelFrame(f, text=" Timeline Audit Range Vector Selection ", padding=10)
        filter_box.pack(fill="x", pady=5)

        ttk.Label(filter_box, text="Query Target Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        target_dt = ttk.Entry(filter_box, width=15)
        target_dt.insert(0, datetime.now().strftime("%Y-%m-%d"))
        target_dt.grid(row=0, column=1, padx=5)

        columns = ("id", "date", "acc", "party", "ref", "type", "amt")
        tree = ttk.Treeview(f, columns=columns, show="headings", height=15)
        for col, head in zip(columns, ["Log ID", "Timestamp", "Asset Channel", "Party Context", "Invoice Ref", "Txn Type", "Net Amount ₹"]):
            tree.heading(col, text=head)
            tree.column(col, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)

        def run_daily_audit_query_matrix():
            for row in tree.get_children(): 
                tree.delete(row)
            d_str = target_dt.get().strip()
            f_str = d_str + " 00:00"
            t_str = d_str + " 23:59"
            
            try:
                active_company_id = self.company[0] if self.company else None

                res = supabase.table("audit_logs") \
                    .select("id, date, account_type, party_name, bill_ref, txn_type, amount") \
                    .eq("company_id", active_company_id) \
                    .gte("date", f_str) \
                    .lte("date", t_str) \
                    .execute()

                if res.data:
                    for row in res.data:
                        tree.insert("", "end", values=(
                            row.get("id"),
                            row.get("date"),
                            row.get("account_type"),
                            row.get("party_name"),
                            row.get("bill_ref"),
                            row.get("txn_type"),
                            f"₹ {row.get('amount', 0.0):,.2f}"
                        ))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch audit report: {str(e)}")

        tk.Button(filter_box, text="⚡ Execute Search Vector Query", bg="#34495E", fg="white", font=("Arial", 9, "bold"), bd=0, padx=12, pady=4, command=run_daily_audit_query_matrix).grid(row=0, column=2, padx=15)
        
        run_daily_audit_query_matrix()


if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    app = JainVittasarApp(root)
    root.mainloop()
