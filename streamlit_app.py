import streamlit as st

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="Enterprise AWS EC2 Workload Sizing Platform", 
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

import pandas as pd
from io import BytesIO
import io
from datetime import datetime
import os
import time
import plotly.express as px
import plotly.graph_objects as go
import math
import boto3
import json
import logging
from functools import lru_cache
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import hashlib
import hmac
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import pyrebase

import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import pyrebase
import json

# ========== FIREBASE CONFIGURATION ==========
def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            # Use Streamlit secrets for Firebase config
            firebase_config = {
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
            }
            
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            st.error(f"Firebase initialization failed: {e}")
            return False
    return True

def init_pyrebase():
    """Initialize Pyrebase for client-side auth"""
    try:
        firebase_web_config = {
            "apiKey": st.secrets["firebase_web"]["apiKey"],
            "authDomain": st.secrets["firebase_web"]["authDomain"],
            "projectId": st.secrets["firebase_web"]["projectId"],
            "storageBucket": st.secrets["firebase_web"]["storageBucket"],
            "messagingSenderId": st.secrets["firebase_web"]["messagingSenderId"],
            "appId": st.secrets["firebase_web"]["appId"],
            "databaseURL": ""  # Add if using Realtime Database
        }
        
        firebase = pyrebase.initialize_app(firebase_web_config)
        return firebase.auth()
    except Exception as e:
        st.error(f"Pyrebase initialization failed: {e}")
        return None

# Initialize Firebase when the app starts
firebase_available = init_firebase()
auth_client = init_pyrebase()

# ========== AUTHENTICATION FUNCTIONS ==========
def check_authentication():
    """Check if user is authenticated"""
    return 'user' in st.session_state and st.session_state.user is not None

def show_login_form():
    """Display login form"""
    st.title("🔐 Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit and email and password:
            try:
                # Authenticate with Pyrebase
                user = auth_client.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error("Login failed. Please check your credentials.")

def logout():
    """Logout user"""
    if 'user' in st.session_state:
        del st.session_state.user
    st.rerun()

# ========== MAIN APP LOGIC ==========
def main():
    """Main application logic"""
    
    # Check if Firebase is available
    if not firebase_available or not auth_client:
        st.error("🔒 **Authentication System Not Available**")
        st.info("Firebase libraries are not properly configured.")
        st.stop()
    
    # Check authentication status
    if not check_authentication():
        show_login_form()
        return
    
    # ===== AUTHENTICATED USER CONTENT =====
    st.title("🎉 Welcome to Your App!")
    
    # Add logout button in sidebar
    with st.sidebar:
        st.write(f"Logged in as: {st.session_state.user['email']}")
        if st.button("Logout"):
            logout()
    
    # Your main app content goes here
    st.write("This is your protected content!")
    st.write("Add your app functionality below this line.")
    
    # ===== YOUR APP CONTENT STARTS HERE =====
    # Replace this section with your actual app code
    

# ========== RUN THE APP ==========
if __name__ == "__main__":
    main()

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #1a1a1a;
        line-height: 1.6;
    }
    
    .main .block-container {
        padding: 1rem 2rem 2rem;
        max-width: none;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-weight: 700;
        font-size: 2.5rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    .auth-container {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem auto;
        max-width: 400px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .demo-banner {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border-color: #667eea;
    }
    
    .metric-title {
        font-weight: 600;
        color: #374151;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin: 0.5rem 0;
    }
    
    .metric-description {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    
    .status-success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-demo {
        background: #ddd6fe;
        color: #5b21b6;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .section-header {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1.5rem 0 1rem 0;
    }
    
    .section-header h3 {
        margin: 0;
        color: #374151;
        font-weight: 600;
    }
    
    .user-info {
        background: #f0f9ff;
        border: 1px solid #0284c7;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .setup-instructions {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class FirebaseAuthenticator:
    """Firebase authentication manager with fallback handling."""
    
    def __init__(self):
        self.firebase_app = None
        self.auth_client = None
        self.db = None
        self.initialized = False
        self.firebase_available = FIREBASE_AVAILABLE
        
    def initialize_firebase(self):
        """Initialize Firebase with Streamlit secrets."""
        if not self.firebase_available:
            return False
            
        if self.initialized:
            return True
            
        try:
            # Check if secrets are available
            if 'firebase' not in st.secrets:
                st.error("Firebase configuration not found in Streamlit secrets. Please configure Firebase secrets in your Streamlit Cloud app.")
                with st.expander("📝 How to Configure Firebase Secrets"):
                    st.markdown("""
                    **Step 1: Create Firebase Project**
                    1. Go to [Firebase Console](https://console.firebase.google.com/)
                    2. Create a new project
                    3. Enable Authentication → Email/Password
                    4. Enable Firestore Database
                    
                    **Step 2: Get Configuration**
                    1. Project Settings → Service Accounts → Generate new private key
                    2. Project Settings → General → Web API Key
                    
                    **Step 3: Add to Streamlit Secrets**
                    Add these to your Streamlit Cloud app secrets:
                    ```toml
                    [firebase]
                    type = "service_account"
                    project_id = "your-project-id"
                    private_key_id = "your-private-key-id"
                    private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR_KEY\\n-----END PRIVATE KEY-----\\n"
                    client_email = "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com"
                    client_id = "your-client-id"
                    auth_uri = "https://accounts.google.com/o/oauth2/auth"
                    token_uri = "https://oauth2.googleapis.com/token"
                    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
                    client_x509_cert_url = "your-client-cert-url"
                    api_key = "your-web-api-key"
                    auth_domain = "your-project-id.firebaseapp.com"
                    storage_bucket = "your-project-id.appspot.com"
                    messaging_sender_id = "your-sender-id"
                    app_id = "your-app-id"
                    ```
                    """)
                return False
                
            # Get Firebase config from Streamlit secrets
            firebase_config = {
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
            }
            
            # Initialize Firebase Admin
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                self.firebase_app = firebase_admin.initialize_app(cred)
            else:
                self.firebase_app = firebase_admin.get_app()
                
            # Initialize Firestore
            self.db = firestore.client()
            
            # Initialize Pyrebase for client-side auth
            pyrebase_config = {
                "apiKey": st.secrets["firebase"]["api_key"],
                "authDomain": st.secrets["firebase"]["auth_domain"],
                "projectId": st.secrets["firebase"]["project_id"],
                "storageBucket": st.secrets["firebase"]["storage_bucket"],
                "messagingSenderId": st.secrets["firebase"]["messaging_sender_id"],
                "appId": st.secrets["firebase"]["app_id"],
                "databaseURL": ""  # Not using Realtime Database
            }
            
            firebase_client = pyrebase.initialize_app(pyrebase_config)
            self.auth_client = firebase_client.auth()
            
            self.initialized = True
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {str(e)}")
            st.info("Using demo mode without authentication.")
            return False
    
    def sign_up(self, email, password, display_name):
        """Create a new user account."""
        if not self.firebase_available or not self.initialized:
            return False, "Firebase authentication not available."
            
        try:
            # Create user with email and password
            user = self.auth_client.create_user_with_email_and_password(email, password)
            
            # Send email verification
            self.auth_client.send_email_verification(user['idToken'])
            
            # Update profile with display name
            self.auth_client.update_profile(user['idToken'], display_name=display_name)
            
            # Store additional user info in Firestore
            user_data = {
                'uid': user['localId'],
                'email': email,
                'display_name': display_name,
                'created_at': datetime.now(),
                'role': 'user',
                'last_login': datetime.now()
            }
            
            self.db.collection('users').document(user['localId']).set(user_data)
            
            return True, "Account created successfully! Please check your email for verification."
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message:
                return False, "Email already exists. Please use a different email or sign in."
            elif "WEAK_PASSWORD" in error_message:
                return False, "Password is too weak. Please use at least 6 characters."
            elif "INVALID_EMAIL" in error_message:
                return False, "Invalid email format."
            else:
                return False, f"Sign up failed: {error_message}"
    
    def sign_in(self, email, password):
        """Sign in an existing user."""
        if not self.firebase_available or not self.initialized:
            return False, "Firebase authentication not available.", None
            
        try:
            user = self.auth_client.sign_in_with_email_and_password(email, password)
            
            # Get user info from Firebase Auth
            user_info = self.auth_client.get_account_info(user['idToken'])
            
            # Check if email is verified
            if not user_info['users'][0].get('emailVerified', False):
                return False, "Please verify your email before signing in.", None
            
            # Update last login in Firestore
            self.db.collection('users').document(user['localId']).update({
                'last_login': datetime.now()
            })
            
            # Get user data from Firestore
            user_doc = self.db.collection('users').document(user['localId']).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            
            return True, "Sign in successful!", {
                'uid': user['localId'],
                'email': user_info['users'][0]['email'],
                'display_name': user_data.get('display_name', ''),
                'role': user_data.get('role', 'user'),
                'id_token': user['idToken']
            }
            
        except Exception as e:
            error_message = str(e)
            if "INVALID_EMAIL" in error_message:
                return False, "Invalid email format.", None
            elif "EMAIL_NOT_FOUND" in error_message:
                return False, "Email not found. Please check your email or sign up.", None
            elif "INVALID_PASSWORD" in error_message:
                return False, "Invalid password. Please try again.", None
            elif "USER_DISABLED" in error_message:
                return False, "User account has been disabled.", None
            else:
                return False, f"Sign in failed: {error_message}", None
    
    def reset_password(self, email):
        """Send password reset email."""
        if not self.firebase_available or not self.initialized:
            return False, "Firebase authentication not available."
            
        try:
            self.auth_client.send_password_reset_email(email)
            return True, "Password reset email sent. Please check your inbox."
        except Exception as e:
            error_message = str(e)
            if "EMAIL_NOT_FOUND" in error_message:
                return False, "Email not found."
            else:
                return False, f"Password reset failed: {error_message}"
    
    def sign_out(self):
        """Sign out current user."""
        try:
            # Clear session state
            for key in ['user_info', 'authenticated', 'id_token']:
                if key in st.session_state:
                    del st.session_state[key]
            return True
        except Exception as e:
            return False

class EnterpriseEC2WorkloadSizingCalculator:
    """Enterprise-grade AWS EC2 workload sizing calculator."""
    
    # AWS Instance Types
    INSTANCE_TYPES = [
        # General Purpose - M6i (Intel)
        {"type": "m6i.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel"},
        {"type": "m6i.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel"},
        {"type": "m6i.2xlarge", "vCPU": 8, "RAM": 32, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel"},
        {"type": "m6i.4xlarge", "vCPU": 16, "RAM": 64, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "general", "processor": "Intel"},
        {"type": "m6i.8xlarge", "vCPU": 32, "RAM": 128, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "general", "processor": "Intel"},
        
        # General Purpose - M6a (AMD)
        {"type": "m6a.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "general", "processor": "AMD"},
        {"type": "m6a.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "general", "processor": "AMD"},
        {"type": "m6a.2xlarge", "vCPU": 8, "RAM": 32, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "general", "processor": "AMD"},
        {"type": "m6a.4xlarge", "vCPU": 16, "RAM": 64, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "general", "processor": "AMD"},
        {"type": "m6a.8xlarge", "vCPU": 32, "RAM": 128, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "general", "processor": "AMD"},
        
        # Memory Optimized - R6i (Intel)
        {"type": "r6i.large", "vCPU": 2, "RAM": 16, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel"},
        {"type": "r6i.xlarge", "vCPU": 4, "RAM": 32, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel"},
        {"type": "r6i.2xlarge", "vCPU": 8, "RAM": 64, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel"},
        {"type": "r6i.4xlarge", "vCPU": 16, "RAM": 128, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "memory", "processor": "Intel"},
        {"type": "r6i.8xlarge", "vCPU": 32, "RAM": 256, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "memory", "processor": "Intel"},
        
        # Memory Optimized - R6a (AMD)
        {"type": "r6a.large", "vCPU": 2, "RAM": 16, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "AMD"},
        {"type": "r6a.xlarge", "vCPU": 4, "RAM": 32, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "AMD"},
        {"type": "r6a.2xlarge", "vCPU": 8, "RAM": 64, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "AMD"},
        {"type": "r6a.4xlarge", "vCPU": 16, "RAM": 128, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "memory", "processor": "AMD"},
        {"type": "r6a.8xlarge", "vCPU": 32, "RAM": 256, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "memory", "processor": "AMD"},
        
        # Compute Optimized - C6i (Intel)
        {"type": "c6i.large", "vCPU": 2, "RAM": 4, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel"},
        {"type": "c6i.xlarge", "vCPU": 4, "RAM": 8, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel"},
        {"type": "c6i.2xlarge", "vCPU": 8, "RAM": 16, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel"},
        {"type": "c6i.4xlarge", "vCPU": 16, "RAM": 32, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "compute", "processor": "Intel"},
        {"type": "c6i.8xlarge", "vCPU": 32, "RAM": 64, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "compute", "processor": "Intel"},
        
        # Compute Optimized - C6a (AMD)
        {"type": "c6a.large", "vCPU": 2, "RAM": 4, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "AMD"},
        {"type": "c6a.xlarge", "vCPU": 4, "RAM": 8, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "AMD"},
        {"type": "c6a.2xlarge", "vCPU": 8, "RAM": 16, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "AMD"},
        {"type": "c6a.4xlarge", "vCPU": 16, "RAM": 32, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "compute", "processor": "AMD"},
        {"type": "c6a.8xlarge", "vCPU": 32, "RAM": 64, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "compute", "processor": "AMD"},
    ]
    
    # Workload Profiles
    WORKLOAD_PROFILES = {
        "web_application": {
            "name": "Web Application",
            "description": "Frontend web servers, load balancers, CDN origins",
            "cpu_multiplier": 1.0,
            "ram_multiplier": 1.0,
            "storage_multiplier": 0.7,
            "iops_multiplier": 0.8,
            "preferred_family": "general",
        },
        "application_server": {
            "name": "Application Server", 
            "description": "Business logic tier, middleware, API servers",
            "cpu_multiplier": 1.2,
            "ram_multiplier": 1.3,
            "storage_multiplier": 0.8,
            "iops_multiplier": 1.0,
            "preferred_family": "general",
        },
        "database_server": {
            "name": "Database Server",
            "description": "RDBMS, NoSQL, data warehouses, analytics",
            "cpu_multiplier": 1.1,
            "ram_multiplier": 1.5,
            "storage_multiplier": 1.2,
            "iops_multiplier": 1.5,
            "preferred_family": "memory",
        },
        "file_server": {
            "name": "File Server",
            "description": "File shares, NAS, backup systems",
            "cpu_multiplier": 0.8,
            "ram_multiplier": 1.0,
            "storage_multiplier": 2.0,
            "iops_multiplier": 1.3,
            "preferred_family": "general",
        },
        "compute_intensive": {
            "name": "Compute Intensive",
            "description": "HPC, scientific computing, batch processing",
            "cpu_multiplier": 1.5,
            "ram_multiplier": 1.2,
            "storage_multiplier": 0.9,
            "iops_multiplier": 0.9,
            "preferred_family": "compute",
        }
    }
    
    # Environment Multipliers
    ENV_MULTIPLIERS = {
        "PROD": {"cpu_ram": 1.0, "storage": 1.0, "description": "Production environment"},
        "STAGING": {"cpu_ram": 0.8, "storage": 0.8, "description": "Pre-production testing"},
        "QA": {"cpu_ram": 0.6, "storage": 0.6, "description": "Quality assurance"},
        "DEV": {"cpu_ram": 0.4, "storage": 0.4, "description": "Development environment"},
        "DR": {"cpu_ram": 1.0, "storage": 1.0, "description": "Disaster recovery"}
    }
    
    # OS Pricing Multipliers
    OS_PRICING_MULTIPLIERS = {
        "linux": {
            "multiplier": 1.0,
            "description": "Amazon Linux 2, Ubuntu, RHEL, SUSE",
        },
        "windows": {
            "multiplier": 1.85,
            "description": "Windows Server 2019/2022",
        }
    }
    
    # Base Pricing (Linux baseline) - Updated with Asia Pacific regions
    BASE_PRICING = {
        "instance": {
            # M6i Intel instances
            "m6i.large": 0.0864, "m6i.xlarge": 0.1728, "m6i.2xlarge": 0.3456,
            "m6i.4xlarge": 0.6912, "m6i.8xlarge": 1.3824,
            
            # M6a AMD instances (10-20% less)
            "m6a.large": 0.0778, "m6a.xlarge": 0.1555, "m6a.2xlarge": 0.3110,
            "m6a.4xlarge": 0.6221, "m6a.8xlarge": 1.2442,
            
            # R6i Intel memory optimized
            "r6i.large": 0.1008, "r6i.xlarge": 0.2016, "r6i.2xlarge": 0.4032,
            "r6i.4xlarge": 0.8064, "r6i.8xlarge": 1.6128,
            
            # R6a AMD memory optimized
            "r6a.large": 0.0907, "r6a.xlarge": 0.1814, "r6a.2xlarge": 0.3629,
            "r6a.4xlarge": 0.7258, "r6a.8xlarge": 1.4515,
            
            # C6i Intel compute optimized
            "c6i.large": 0.0765, "c6i.xlarge": 0.1530, "c6i.2xlarge": 0.3060,
            "c6i.4xlarge": 0.6120, "c6i.8xlarge": 1.2240,
            
            # C6a AMD compute optimized
            "c6a.large": 0.0688, "c6a.xlarge": 0.1377, "c6a.2xlarge": 0.2754,
            "c6a.4xlarge": 0.5508, "c6a.8xlarge": 1.1016,
        },
        "ebs": {
            # US Regions
            "us-east-1": {"gp3": {"gb": 0.08, "iops": 0.005, "throughput": 0.04}, "io2": {"gb": 0.125, "iops": 0.065}},
            "us-west-1": {"gp3": {"gb": 0.088, "iops": 0.0055, "throughput": 0.044}, "io2": {"gb": 0.138, "iops": 0.0715}},
            "us-west-2": {"gp3": {"gb": 0.084, "iops": 0.0052, "throughput": 0.042}, "io2": {"gb": 0.131, "iops": 0.068}},
            
            # Europe Regions
            "eu-west-1": {"gp3": {"gb": 0.089, "iops": 0.0054, "throughput": 0.043}, "io2": {"gb": 0.138, "iops": 0.070}},
            "eu-central-1": {"gp3": {"gb": 0.092, "iops": 0.0055, "throughput": 0.044}, "io2": {"gb": 0.142, "iops": 0.072}},
            
            # Asia Pacific Regions
            "ap-southeast-1": {"gp3": {"gb": 0.095, "iops": 0.0057, "throughput": 0.046}, "io2": {"gb": 0.145, "iops": 0.073}},
            "ap-southeast-2": {"gp3": {"gb": 0.095, "iops": 0.0057, "throughput": 0.046}, "io2": {"gb": 0.145, "iops": 0.073}},
            "ap-northeast-1": {"gp3": {"gb": 0.096, "iops": 0.0058, "throughput": 0.047}, "io2": {"gb": 0.148, "iops": 0.075}},
            "ap-northeast-2": {"gp3": {"gb": 0.094, "iops": 0.0056, "throughput": 0.045}, "io2": {"gb": 0.143, "iops": 0.072}},
            "ap-south-1": {"gp3": {"gb": 0.087, "iops": 0.0052, "throughput": 0.042}, "io2": {"gb": 0.135, "iops": 0.068}},
            "ap-east-1": {"gp3": {"gb": 0.103, "iops": 0.0062, "throughput": 0.050}, "io2": {"gb": 0.158, "iops": 0.080}},
        }
    }
    
    def __init__(self):
        """Initialize calculator with default settings."""
        self.inputs = {
            "workload_name": "Sample Workload",
            "workload_type": "web_application",
            "operating_system": "linux",
            "region": "us-east-1",
            "on_prem_cores": 8,
            "peak_cpu_percent": 70,
            "avg_cpu_percent": 45,
            "on_prem_ram_gb": 32,
            "peak_ram_percent": 80,
            "avg_ram_percent": 55,
            "storage_current_gb": 500,
            "storage_growth_rate": 0.15,
            "peak_iops": 5000,
            "avg_iops": 2500,
            "peak_throughput_mbps": 250,
            "years": 3,
            "seasonality_factor": 1.2,
            "prefer_amd": True,
        }
        
        self.instance_pricing = self.BASE_PRICING["instance"].copy()
        self.ebs_pricing = self.BASE_PRICING["ebs"].copy()
        self.recommendation_cache = {}
    
    def validate_aws_credentials(self, region=None):
        """Validate AWS credentials."""
        try:
            region = region or self.inputs.get("region", "us-east-1")
            
            # Try to get credentials from Streamlit secrets first
            if hasattr(st, 'secrets') and 'aws' in st.secrets:
                try:
                    access_key = st.secrets["aws"]["access_key_id"]
                    secret_key = st.secrets["aws"]["secret_access_key"]
                    sts = boto3.client('sts', 
                                     aws_access_key_id=access_key,
                                     aws_secret_access_key=secret_key,
                                     region_name=region)
                    identity = sts.get_caller_identity()
                    account_id = identity['Arn'].split(':')[4]
                    return True, f"✅ AWS Connected (Account: {account_id})"
                except Exception:
                    pass
            
            # Fall back to environment variables or default credentials
            sts = boto3.client('sts', region_name=region)
            identity = sts.get_caller_identity()
            account_id = identity['Arn'].split(':')[4]
            return True, f"✅ AWS Connected (Account: {account_id})"
            
        except Exception as e:
            return False, "❌ AWS credentials not configured. Using base pricing."
    
    def fetch_current_prices(self, force_refresh=False):
        """Apply OS multiplier to base pricing."""
        os_multiplier = self.OS_PRICING_MULTIPLIERS[self.inputs["operating_system"]]["multiplier"]
        for instance_type, base_price in self.BASE_PRICING["instance"].items():
            self.instance_pricing[instance_type] = base_price * os_multiplier
    
    def calculate_requirements(self, env):
        """Calculate infrastructure requirements."""
        env_mult = self.ENV_MULTIPLIERS[env]
        workload_profile = self.WORKLOAD_PROFILES[self.inputs["workload_type"]]
        
        # CPU calculation
        cpu_efficiency = 0.7
        cpu_buffer = 1.3 if env == "PROD" else 1.2
        seasonality = self.inputs.get("seasonality_factor", 1.0) if env == "PROD" else 1.0
        
        required_vcpus = max(
            math.ceil(
                self.inputs["on_prem_cores"] * 
                (self.inputs["peak_cpu_percent"] / 100) *
                workload_profile["cpu_multiplier"] *
                cpu_buffer *
                seasonality *
                env_mult["cpu_ram"] / 
                cpu_efficiency
            ), 2
        )
        
        # RAM calculation
        ram_efficiency = 0.85
        required_ram = max(
            math.ceil(
                self.inputs["on_prem_ram_gb"] * 
                (self.inputs["peak_ram_percent"] / 100) *
                workload_profile["ram_multiplier"] *
                1.15 *  # OS overhead
                cpu_buffer *
                seasonality *
                env_mult["cpu_ram"] / 
                ram_efficiency
            ), 4
        )
        
        # Storage calculation
        growth_factor = (1 + self.inputs["storage_growth_rate"]) ** self.inputs["years"]
        storage_buffer = 1.3 if env == "PROD" else 1.2
        
        required_storage = max(
            math.ceil(
                self.inputs["storage_current_gb"] * 
                growth_factor * 
                workload_profile["storage_multiplier"] *
                storage_buffer *
                env_mult["storage"]
            ), 20
        )
        
        # I/O requirements
        iops_required = math.ceil(
            self.inputs["peak_iops"] * 
            workload_profile["iops_multiplier"] * 
            (1.3 if env == "PROD" else 1.2)
        )
        
        throughput_required = math.ceil(
            self.inputs["peak_throughput_mbps"] * 
            workload_profile["iops_multiplier"] * 
            (1.3 if env == "PROD" else 1.2)
        )
        
        # EBS type selection
        ebs_type = self.select_ebs_type(iops_required, throughput_required, required_storage)
        
        # Instance selection
        instance = self.select_optimal_instance(required_vcpus, required_ram, throughput_required, workload_profile)
        
        # Cost calculations
        instance_cost = self.calculate_instance_cost(instance["type"])
        ebs_cost = self.calculate_ebs_cost(ebs_type, required_storage, iops_required, throughput_required)
        network_cost = self.estimate_network_cost(env)
        total_cost = instance_cost + ebs_cost + network_cost
        
        # Optimization score
        optimization_score = self.calculate_optimization_score(instance, required_vcpus, required_ram)
        
        return {
            "environment": env,
            "instance_type": instance["type"],
            "vCPUs": required_vcpus,
            "RAM_GB": required_ram,
            "storage_GB": required_storage,
            "ebs_type": ebs_type,
            "iops_required": iops_required,
            "throughput_required": f"{throughput_required} MB/s",
            "network_performance": instance["network"],
            "family": instance["family"],
            "processor": instance["processor"],
            "operating_system": self.inputs["operating_system"],
            "instance_cost": instance_cost,
            "ebs_cost": ebs_cost,
            "network_cost": network_cost,
            "total_cost": total_cost,
            "optimization_score": optimization_score,
            "workload_optimized": workload_profile["name"]
        }
    
    def select_ebs_type(self, iops_required, throughput_required, storage_gb):
        """Select appropriate EBS type."""
        if iops_required > 16000 or throughput_required > 1000:
            return "io2"
        elif storage_gb > 16384:
            return "io2"
        elif iops_required > 3000 or throughput_required > 125:
            return "gp3"
        else:
            return "gp3"
    
    def select_optimal_instance(self, required_vcpus, required_ram, required_throughput, workload_profile):
        """Select optimal instance type."""
        preferred_family = workload_profile["preferred_family"]
        prefer_amd = self.inputs["prefer_amd"]
        
        candidates = []
        for instance in self.INSTANCE_TYPES:
            if preferred_family != "general" and instance["family"] != preferred_family:
                continue
            if not prefer_amd and instance["processor"] == "AMD":
                continue
            if (instance["vCPU"] >= required_vcpus and 
                instance["RAM"] >= required_ram and
                instance["max_ebs_bandwidth"] >= (required_throughput * 1.2)):
                candidates.append(instance)
        
        if not candidates:
            candidates = [i for i in self.INSTANCE_TYPES 
                         if (i["vCPU"] >= required_vcpus and i["RAM"] >= required_ram)]
        
        if not candidates:
            return max(self.INSTANCE_TYPES, key=lambda x: (x["vCPU"], x["RAM"]))
        
        # Score candidates
        best_instance = None
        best_score = -1
        
        for instance in candidates:
            cpu_efficiency = required_vcpus / instance["vCPU"]
            ram_efficiency = required_ram / instance["RAM"]
            hourly_cost = self.instance_pricing.get(instance["type"], 999)
            cost_per_vcpu = hourly_cost / instance["vCPU"]
            
            efficiency_score = (cpu_efficiency + ram_efficiency) / 2
            cost_score = 1 / (cost_per_vcpu + 0.01)
            amd_bonus = 1.1 if (prefer_amd and instance["processor"] == "AMD") else 1.0
            family_bonus = 1.2 if instance["family"] == preferred_family else 1.0
            
            total_score = efficiency_score * cost_score * amd_bonus * family_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_instance = instance
        
        return best_instance or candidates[0]
    
    def calculate_instance_cost(self, instance_type):
        """Calculate monthly instance cost."""
        hourly_rate = self.instance_pricing.get(instance_type, 0)
        return round(hourly_rate * 24 * 30, 2)
    
    def calculate_ebs_cost(self, ebs_type, storage_gb, iops, throughput_mbps):
        """Calculate monthly EBS cost."""
        region = self.inputs["region"]
        region_pricing = self.ebs_pricing.get(region, self.ebs_pricing["us-east-1"])
        pricing = region_pricing.get(ebs_type, region_pricing["gp3"])
        
        base_cost = storage_gb * pricing["gb"]
        
        if ebs_type == "gp3":
            extra_iops = max(0, iops - 3000)
            extra_throughput = max(0, throughput_mbps - 125)
            iops_cost = extra_iops * pricing.get("iops", 0)
            throughput_cost = extra_throughput * pricing.get("throughput", 0)
            return round(base_cost + iops_cost + throughput_cost, 2)
        elif ebs_type == "io2":
            iops_cost = iops * pricing.get("iops", 0)
            return round(base_cost + iops_cost, 2)
        else:
            return round(base_cost, 2)
    
    def estimate_network_cost(self, env):
        """Estimate monthly network costs based on workload profile and region."""
        # Base costs by environment
        base_cost = {"PROD": 50, "STAGING": 20, "QA": 15, "DEV": 10, "DR": 25}
        
        # Workload multipliers
        workload_multiplier = {
            "web_application": 1.5, "application_server": 1.2, "database_server": 1.0,
            "file_server": 2.0, "compute_intensive": 0.8
        }
        
        # Regional multipliers (data transfer costs vary by region)
        regional_multiplier = {
            # US Regions (baseline)
            "us-east-1": 1.0, "us-west-1": 1.05, "us-west-2": 1.02,
            # Europe Regions (slightly higher)
            "eu-west-1": 1.1, "eu-central-1": 1.15,
            # Asia Pacific Regions (higher data transfer costs)
            "ap-southeast-1": 1.2,  # Singapore
            "ap-southeast-2": 1.25, # Sydney  
            "ap-northeast-1": 1.3,  # Tokyo
            "ap-northeast-2": 1.25, # Seoul
            "ap-south-1": 1.15,     # Mumbai
            "ap-east-1": 1.35       # Hong Kong (highest)
        }
        
        base = base_cost.get(env, 20)
        workload_mult = workload_multiplier.get(self.inputs["workload_type"], 1.0)
        region_mult = regional_multiplier.get(self.inputs["region"], 1.0)
        
        return round(base * workload_mult * region_mult, 2)
    
    def calculate_optimization_score(self, instance, required_vcpus, required_ram):
        """Calculate optimization score (0-100%)."""
        cpu_utilization = (required_vcpus / instance["vCPU"]) * 100
        ram_utilization = (required_ram / instance["RAM"]) * 100
        
        cpu_score = 100 - abs(80 - cpu_utilization)
        ram_score = 100 - abs(80 - ram_utilization)
        
        optimization_score = (cpu_score + ram_score) / 2
        return max(0, min(100, round(optimization_score, 1)))
    
    def generate_all_recommendations(self):
        """Generate recommendations for all environments."""
        cache_key = hash(frozenset(self.inputs.items()))
        
        if cache_key in self.recommendation_cache:
            return self.recommendation_cache[cache_key]
        
        results = {}
        for env in self.ENV_MULTIPLIERS.keys():
            results[env] = self.calculate_requirements(env)
        
        self.recommendation_cache[cache_key] = results
        return results
    
    def get_workload_summary(self):
        """Get workload summary."""
        workload_profile = self.WORKLOAD_PROFILES[self.inputs["workload_type"]]
        os_info = self.OS_PRICING_MULTIPLIERS[self.inputs["operating_system"]]
        
        return {
            "workload_name": self.inputs["workload_name"],
            "workload_type": workload_profile["name"],
            "workload_description": workload_profile["description"],
            "operating_system": self.inputs["operating_system"].title(),
            "os_description": os_info["description"],
            "region": self.inputs["region"],
            "current_infrastructure": {
                "cores": self.inputs["on_prem_cores"],
                "ram_gb": self.inputs["on_prem_ram_gb"],
                "storage_gb": self.inputs["storage_current_gb"],
                "peak_cpu_util": f"{self.inputs['peak_cpu_percent']}%",
                "peak_ram_util": f"{self.inputs['peak_ram_percent']}%"
            },
            "growth_projection": f"{self.inputs['storage_growth_rate']*100:.1f}% annually for {self.inputs['years']} years"
        }

# PDF Report Generator
class EnhancedPDFReportGenerator:
    """PDF report generator."""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab library required")
        self.styles = getSampleStyleSheet()
    
    def generate_comprehensive_report(self, all_results):
        """Generate PDF report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        if isinstance(all_results, dict):
            results_list = [all_results]
        else:
            results_list = all_results
        
        if not results_list:
            story.append(Paragraph("No analysis results available.", self.styles['Normal']))
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        # Title
        story.append(Paragraph("Enterprise AWS Workload Migration Analysis", self.styles['Title']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 0.5 * inch))
        
        # Summary
        total_workloads = len(results_list)
        total_monthly_cost = sum(result['recommendations']['PROD']['total_cost'] for result in results_list)
        
        summary = f"""
        This analysis covers {total_workloads} workload(s) for AWS migration.
        Total estimated monthly cost: ${total_monthly_cost:,.2f}
        Annual projection: ${total_monthly_cost * 12:,.2f}
        """
        story.append(Paragraph(summary, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

# Authentication Functions
def render_authentication():
    """Render authentication interface."""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise AWS Workload Sizing Platform</h1>
        <p>Secure access to comprehensive infrastructure assessment and cloud migration planning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Firebase
    if 'firebase_auth' not in st.session_state:
        st.session_state.firebase_auth = FirebaseAuthenticator()
    
    firebase_auth = st.session_state.firebase_auth
    
    if not firebase_auth.firebase_available:
        st.info("🔧 **Demo Mode**: Firebase authentication is not available. You can use all features without authentication.")
        if st.button("🚀 Continue to Platform", type="primary"):
            st.session_state.authenticated = True
            st.session_state.demo_mode = True
            st.session_state.user_info = {
                'display_name': 'Demo User',
                'email': 'demo@example.com',
                'role': 'demo'
            }
            st.rerun()
        return False
    
    if not firebase_auth.initialize_firebase():
        st.info("🔧 **Demo Mode**: Firebase configuration incomplete. You can use all features without authentication.")
        if st.button("🚀 Continue to Platform", type="primary"):
            st.session_state.authenticated = True
            st.session_state.demo_mode = True
            st.session_state.user_info = {
                'display_name': 'Demo User',
                'email': 'demo@example.com',
                'role': 'demo'
            }
            st.rerun()
        return False
    
    # Check if user is already authenticated
    if st.session_state.get('authenticated', False):
        return True
    
    # Authentication tabs
    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔐 Sign In", "📝 Sign Up", "🔄 Reset Password"])
    
    with auth_tab1:
        render_sign_in(firebase_auth)
    
    with auth_tab2:
        render_sign_up(firebase_auth)
    
    with auth_tab3:
        render_password_reset(firebase_auth)
    
    return False

def render_sign_in(firebase_auth):
    """Render sign in form."""
    st.markdown("""
    <div class="auth-container">
        <h3 style="text-align: center; margin-bottom: 1rem;">Sign In</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("sign_in_form"):
        email = st.text_input("Email", placeholder="your.email@company.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            sign_in_button = st.form_submit_button("🔐 Sign In", use_container_width=True)
        with col2:
            remember_me = st.checkbox("Remember me")
        
        if sign_in_button:
            if email and password:
                with st.spinner("Signing in..."):
                    success, message, user_data = firebase_auth.sign_in(email, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_data
                        st.session_state.id_token = user_data['id_token']
                        st.session_state.demo_mode = False
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.error("Please enter both email and password.")

def render_sign_up(firebase_auth):
    """Render sign up form."""
    st.markdown("""
    <div class="auth-container">
        <h3 style="text-align: center; margin-bottom: 1rem;">Create Account</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("sign_up_form"):
        display_name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="your.email@company.com")
        password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        terms_accepted = st.checkbox("I accept the Terms of Service and Privacy Policy")
        
        sign_up_button = st.form_submit_button("📝 Create Account", use_container_width=True)
        
        if sign_up_button:
            if not all([display_name, email, password, confirm_password]):
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long.")
            elif not terms_accepted:
                st.error("Please accept the Terms of Service and Privacy Policy.")
            else:
                with st.spinner("Creating account..."):
                    success, message = firebase_auth.sign_up(email, password, display_name)
                    
                    if success:
                        st.success(message)
                        st.info("Please check your email and verify your account before signing in.")
                    else:
                        st.error(message)

def render_password_reset(firebase_auth):
    """Render password reset form."""
    st.markdown("""
    <div class="auth-container">
        <h3 style="text-align: center; margin-bottom: 1rem;">Reset Password</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("password_reset_form"):
        email = st.text_input("Email", placeholder="your.email@company.com")
        
        reset_button = st.form_submit_button("🔄 Send Reset Email", use_container_width=True)
        
        if reset_button:
            if email:
                with st.spinner("Sending reset email..."):
                    success, message = firebase_auth.reset_password(email)
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.error("Please enter your email address.")

def render_user_info():
    """Render user information in sidebar."""
    if st.session_state.get('authenticated', False):
        user_info = st.session_state.get('user_info', {})
        is_demo = st.session_state.get('demo_mode', False)
        
        if is_demo:
            st.markdown(f"""
            <div class="user-info">
                <strong>👤 {user_info.get('display_name', 'Demo User')}</strong><br>
                <small>{user_info.get('email', 'demo@example.com')}</small><br>
                <span class="status-badge status-demo">Demo Mode</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="user-info">
                <strong>👤 {user_info.get('display_name', 'User')}</strong><br>
                <small>{user_info.get('email', '')}</small><br>
                <small>Role: {user_info.get('role', 'user').title()}</small>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🚪 Sign Out", key="sign_out", use_container_width=True):
            if is_demo:
                # Simple logout for demo mode
                for key in ['authenticated', 'demo_mode', 'user_info']:
                    if key in st.session_state:
                        del st.session_state[key]
            else:
                firebase_auth = st.session_state.firebase_auth
                firebase_auth.sign_out()
            
            st.success("Signed out successfully!")
            time.sleep(1)
            st.rerun()

# Initialize session state
def initialize_session_state():
    """Initialize session state."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {}
    if 'calculator' not in st.session_state:
        st.session_state.calculator = EnterpriseEC2WorkloadSizingCalculator()
    if 'pdf_generator' not in st.session_state and REPORTLAB_AVAILABLE:
        try:
            st.session_state.pdf_generator = EnhancedPDFReportGenerator()
        except Exception:
            st.session_state.pdf_generator = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'bulk_results' not in st.session_state:
        st.session_state.bulk_results = []

# Helper functions (keeping all the existing functions)
def parse_bulk_upload_file(uploaded_file):
    """Parse bulk upload file."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        expected_columns = {
            'Workload Name': 'workload_name',
            'Workload Type': 'workload_type', 
            'Operating System': 'operating_system',
            'AWS Region': 'region',
            'Current CPU Cores': 'on_prem_cores',
            'Peak CPU Utilization (%)': 'peak_cpu_percent',
            'Current RAM (GB)': 'on_prem_ram_gb',
            'Peak RAM Utilization (%)': 'peak_ram_percent',
            'Current Storage (GB)': 'storage_current_gb',
            'Storage Growth Rate': 'storage_growth_rate',
            'Peak IOPS': 'peak_iops',
            'Peak Throughput (MB/s)': 'peak_throughput_mbps',
            'Growth Projection Years': 'years',
            'Prefer AMD': 'prefer_amd'
        }
        
        df_mapped = pd.DataFrame()
        found_columns = []
        for user_col, internal_col in expected_columns.items():
            if user_col in df.columns:
                df_mapped[internal_col] = df[user_col]
                found_columns.append(internal_col)
        
        required_columns = ['workload_name', 'workload_type', 'operating_system', 'on_prem_cores', 'on_prem_ram_gb']
        missing_columns = [col for col in required_columns if col not in found_columns]
        
        if missing_columns:
            return [], [f"Missing required columns: {', '.join(missing_columns)}"]
        
        valid_inputs = []
        errors = []
        
        for index, row in df_mapped.iterrows():
            row_data = {}
            row_errors = []
            
            for col in df_mapped.columns:
                value = row.get(col)
                if pd.isna(value) or value is None:
                    if col in required_columns:
                        row_errors.append(f"Required field '{col}' is empty")
                    else:
                        defaults = {
                            'region': 'us-east-1', 'storage_growth_rate': 0.15,
                            'peak_iops': 5000, 'peak_throughput_mbps': 250,
                            'years': 3, 'prefer_amd': True
                        }
                        row_data[col] = defaults.get(col, 0)
                else:
                    try:
                        if col in ['prefer_amd']:
                            row_data[col] = str(value).lower() in ['true', '1', 'yes']
                        elif col in ['workload_name', 'workload_type', 'operating_system', 'region']:
                            row_data[col] = str(value).strip()
                        else:
                            row_data[col] = float(value) if '.' in str(value) else int(value)
                    except (ValueError, TypeError):
                        row_errors.append(f"Invalid value for '{col}': {value}")
            
            if row_errors:
                errors.append(f"Row {index + 2}: {'; '.join(row_errors)}")
            else:
                valid_inputs.append(row_data)
        
        return valid_inputs, errors
        
    except Exception as e:
        return [], [f"File parsing error: {str(e)}"]

def render_workload_configuration():
    """Render workload configuration interface."""
    calculator = st.session_state.calculator
    
    st.markdown('<div class="section-header"><h3>🏗️ Workload Configuration</h3></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Basic Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            calculator.inputs["workload_name"] = st.text_input(
                "Workload Name", 
                value=calculator.inputs["workload_name"],
                help="Descriptive name for this workload"
            )
            
            workload_options = list(calculator.WORKLOAD_PROFILES.keys())
            workload_labels = [calculator.WORKLOAD_PROFILES[k]["name"] for k in workload_options]
            current_workload_idx = workload_options.index(calculator.inputs["workload_type"])
            
            selected_workload_idx = st.selectbox(
                "Workload Type",
                range(len(workload_options)),
                index=current_workload_idx,
                format_func=lambda x: workload_labels[x]
            )
            calculator.inputs["workload_type"] = workload_options[selected_workload_idx]
            
        with col2:
            os_options = ["linux", "windows"]
            os_labels = ["Linux (Amazon Linux, Ubuntu, RHEL)", "Windows Server"]
            current_os_idx = os_options.index(calculator.inputs["operating_system"])
            
            selected_os_idx = st.selectbox(
                "Operating System",
                range(len(os_options)),
                index=current_os_idx,
                format_func=lambda x: os_labels[x]
            )
            calculator.inputs["operating_system"] = os_options[selected_os_idx]
            
            # Updated region selection with Asia Pacific regions
            region_options = [
                "us-east-1", "us-west-1", "us-west-2", 
                "eu-west-1", "eu-central-1",
                "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", 
                "ap-northeast-2", "ap-south-1", "ap-east-1"
            ]
            region_labels = [
                "US East (N. Virginia)", "US West (N. California)", "US West (Oregon)",
                "Europe (Ireland)", "Europe (Frankfurt)", 
                "Asia Pacific (Singapore)", "Asia Pacific (Sydney)", "Asia Pacific (Tokyo)",
                "Asia Pacific (Seoul)", "Asia Pacific (Mumbai)", "Asia Pacific (Hong Kong)"
            ]
            
            current_region_idx = region_options.index(calculator.inputs["region"])
            
            selected_region_idx = st.selectbox(
                "AWS Region",
                range(len(region_options)),
                index=current_region_idx,
                format_func=lambda x: region_labels[x],
                help="Select AWS region for deployment and pricing"
            )
            calculator.inputs["region"] = region_options[selected_region_idx]
    
    selected_profile = calculator.WORKLOAD_PROFILES[calculator.inputs["workload_type"]]
    st.info(f"**{selected_profile['name']}**: {selected_profile['description']}")
    
    with st.expander("🖥️ Current Infrastructure Metrics", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Compute Resources**")
            calculator.inputs["on_prem_cores"] = st.number_input(
                "CPU Cores", min_value=1, value=calculator.inputs["on_prem_cores"]
            )
            calculator.inputs["peak_cpu_percent"] = st.slider(
                "Peak CPU %", 0, 100, calculator.inputs["peak_cpu_percent"]
            )
            calculator.inputs["avg_cpu_percent"] = st.slider(
                "Average CPU %", 0, 100, calculator.inputs["avg_cpu_percent"]
            )
            
        with col2:
            st.markdown("**Memory Resources**")
            calculator.inputs["on_prem_ram_gb"] = st.number_input(
                "RAM (GB)", min_value=1, value=calculator.inputs["on_prem_ram_gb"]
            )
            calculator.inputs["peak_ram_percent"] = st.slider(
                "Peak RAM %", 0, 100, calculator.inputs["peak_ram_percent"]
            )
            calculator.inputs["avg_ram_percent"] = st.slider(
                "Average RAM %", 0, 100, calculator.inputs["avg_ram_percent"]
            )
            
        with col3:
            st.markdown("**Storage & I/O**")
            calculator.inputs["storage_current_gb"] = st.number_input(
                "Storage (GB)", min_value=1, value=calculator.inputs["storage_current_gb"]
            )
            calculator.inputs["peak_iops"] = st.number_input(
                "Peak IOPS", min_value=1, value=calculator.inputs["peak_iops"]
            )
            calculator.inputs["peak_throughput_mbps"] = st.number_input(
                "Peak Throughput (MB/s)", min_value=1, value=calculator.inputs["peak_throughput_mbps"]
            )
    
    with st.expander("⚙️ Advanced Configuration"):
        col1, col2 = st.columns(2)
        
        with col1:
            calculator.inputs["storage_growth_rate"] = st.number_input(
                "Annual Growth Rate", min_value=0.0, max_value=1.0, 
                value=calculator.inputs["storage_growth_rate"], step=0.01, format="%.2f"
            )
            calculator.inputs["years"] = st.slider(
                "Growth Projection (Years)", 1, 10, calculator.inputs["years"]
            )
            calculator.inputs["seasonality_factor"] = st.number_input(
                "Seasonality Factor", min_value=1.0, max_value=3.0, 
                value=calculator.inputs["seasonality_factor"], step=0.1
            )
            
        with col2:
            calculator.inputs["prefer_amd"] = st.checkbox(
                "Prefer AMD Instances", value=calculator.inputs["prefer_amd"]
            )

def render_analysis_results(results):
    """Render analysis results."""
    st.markdown('<div class="section-header"><h3>📊 Analysis Results</h3></div>', unsafe_allow_html=True)
    
    summary = st.session_state.calculator.get_workload_summary()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Workload Information</div>
            <div class="metric-value">{summary['workload_type']}</div>
            <div class="metric-description">{summary['workload_description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Operating System</div>
            <div class="metric-value">{summary['operating_system']}</div>
            <div class="metric-description">{summary['os_description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        total_prod_cost = results['PROD']['total_cost']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Production Monthly Cost</div>
            <div class="metric-value">${total_prod_cost:,.2f}</div>
            <div class="metric-description">Annual: ${total_prod_cost * 12:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.subheader("Environment Comparison")
    
    df_results = pd.DataFrame.from_dict(results, orient='index').reset_index()
    df_results.rename(columns={"index": "Environment"}, inplace=True)
    
    display_columns = ["Environment", "instance_type", "vCPUs", "RAM_GB", "storage_GB", "ebs_type", "total_cost", "optimization_score"]
    df_display = df_results[display_columns].copy()
    df_display["total_cost"] = df_display["total_cost"].apply(lambda x: f"${x:,.2f}")
    df_display["optimization_score"] = df_display["optimization_score"].apply(lambda x: f"{x}%")
    df_display.columns = ["Environment", "Instance Type", "vCPUs", "RAM (GB)", "Storage (GB)", "EBS Type", "Monthly Cost", "Optimization"]
    
    st.dataframe(df_display, use_container_width=True)
    
    # Cost breakdown
    st.subheader("Cost Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        cost_data = []
        for env, rec in results.items():
            cost_data.append({
                'Environment': env,
                'Instance': rec['instance_cost'],
                'Storage': rec['ebs_cost'],
                'Network': rec['network_cost']
            })
        
        df_costs = pd.DataFrame(cost_data)
        fig_costs = px.bar(df_costs, x='Environment', y=['Instance', 'Storage', 'Network'],
                          title='Cost Breakdown by Environment', barmode='stack')
        fig_costs.update_layout(height=400)
        st.plotly_chart(fig_costs, use_container_width=True)
        
    with col2:
        opt_data = [{'Environment': env, 'Score': rec['optimization_score']} for env, rec in results.items()]
        df_opt = pd.DataFrame(opt_data)
        
        fig_opt = px.bar(df_opt, x='Environment', y='Score', title='Resource Optimization Scores',
                        color='Score', color_continuous_scale='RdYlGn')
        fig_opt.update_layout(height=400)
        st.plotly_chart(fig_opt, use_container_width=True)

def render_bulk_analysis():
    """Render bulk analysis interface."""
    st.markdown('<div class="section-header"><h3>📁 Bulk Workload Analysis</h3></div>', unsafe_allow_html=True)
    
    st.markdown("Upload a CSV or Excel file containing multiple workload configurations for batch analysis.")
    
    # Updated template with Asia Pacific examples
    if st.button("📥 Download Template"):
        template_data = {
            'Workload Name': ['Web Frontend', 'API Gateway', 'Database Server', 'File Server', 'Analytics Engine', 'Mobile Backend'],
            'Workload Type': ['web_application', 'application_server', 'database_server', 'file_server', 'compute_intensive', 'application_server'],
            'Operating System': ['linux', 'linux', 'windows', 'windows', 'linux', 'linux'],
            'AWS Region': ['us-east-1', 'eu-west-1', 'ap-southeast-1', 'us-west-2', 'ap-northeast-1', 'ap-south-1'],
            'Current CPU Cores': [8, 16, 32, 4, 24, 12],
            'Peak CPU Utilization (%)': [75, 60, 80, 40, 90, 65],
            'Current RAM (GB)': [32, 64, 128, 16, 96, 48],
            'Peak RAM Utilization (%)': [80, 70, 85, 60, 88, 75],
            'Current Storage (GB)': [500, 1000, 5000, 10000, 2000, 800],
            'Storage Growth Rate': [0.15, 0.10, 0.20, 0.25, 0.30, 0.12],
            'Peak IOPS': [5000, 8000, 15000, 3000, 12000, 6000],
            'Peak Throughput (MB/s)': [250, 400, 800, 200, 600, 300],
            'Growth Projection Years': [3, 3, 5, 3, 2, 4],
            'Prefer AMD': [True, True, False, True, True, False]
        }
        
        template_df = pd.DataFrame(template_data)
        csv_buffer = BytesIO()
        template_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        st.download_button(
            label="Download Template",
            data=csv_buffer.getvalue(),
            file_name="workload_analysis_template.csv",
            mime="text/csv"
        )
    
    uploaded_file = st.file_uploader("Upload Workload Configuration File", type=["csv", "xlsx"])
    
    if uploaded_file:
        with st.spinner("🔄 Processing uploaded file..."):
            valid_inputs, errors = parse_bulk_upload_file(uploaded_file)
        
        if errors:
            st.error("❌ **Errors found in uploaded file:**")
            for error in errors:
                st.write(f"• {error}")
            return
        
        if not valid_inputs:
            st.warning("No valid workload configurations found.")
            return
        
        st.success(f"✅ Successfully parsed {len(valid_inputs)} workload configurations.")
        
        with st.expander("👀 Preview Uploaded Data", expanded=True):
            preview_df = pd.DataFrame(valid_inputs)
            st.dataframe(preview_df.head(10), use_container_width=True)
        
        if st.button(f"🚀 Analyze {len(valid_inputs)} Workloads", type="primary"):
            analyze_bulk_workloads(valid_inputs)

def analyze_bulk_workloads(workload_configs):
    """Analyze multiple workloads."""
    calculator = st.session_state.calculator
    all_results = []
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    try:
        calculator.fetch_current_prices(force_refresh=True)
        
        for i, config in enumerate(workload_configs):
            workload_name = config.get('workload_name', f'Workload {i+1}')
            progress_text.text(f"Analyzing {workload_name} ({i+1}/{len(workload_configs)})...")
            progress_bar.progress((i + 1) / len(workload_configs))
            
            calculator.inputs.update(config)
            recommendations = calculator.generate_all_recommendations()
            
            all_results.append({'inputs': config, 'recommendations': recommendations})
            time.sleep(0.1)
        
        st.session_state.bulk_results = all_results
        progress_text.empty()
        progress_bar.empty()
        
        st.success("✅ Bulk analysis completed successfully!")
        display_bulk_analysis_results(all_results)
        
    except Exception as e:
        st.error(f"❌ Error during bulk analysis: {str(e)}")
    finally:
        progress_text.empty()
        progress_bar.empty()

def display_bulk_analysis_results(all_results):
    """Display bulk analysis results."""
    st.markdown('<div class="section-header"><h3>📈 Bulk Analysis Results</h3></div>', unsafe_allow_html=True)
    
    total_workloads = len(all_results)
    total_monthly_cost = sum(result['recommendations']['PROD']['total_cost'] for result in all_results)
    avg_optimization_score = sum(result['recommendations']['PROD']['optimization_score'] for result in all_results) / total_workloads
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Workloads</div>
            <div class="metric-value">{total_workloads}</div>
            <div class="metric-description">Analyzed successfully</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Monthly Cost</div>
            <div class="metric-value">${total_monthly_cost:,.0f}</div>
            <div class="metric-description">Production environments</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Annual Cost</div>
            <div class="metric-value">${total_monthly_cost * 12:,.0f}</div>
            <div class="metric-description">Full year projection</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        score_color = "green" if avg_optimization_score >= 80 else "orange" if avg_optimization_score >= 60 else "red"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Optimization</div>
            <div class="metric-value" style="color: {score_color}">{avg_optimization_score:.1f}%</div>
            <div class="metric-description">Resource efficiency</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.subheader("Workload Summary")
    
    summary_data = []
    for result in all_results:
        inputs = result['inputs']
        prod_rec = result['recommendations']['PROD']
        
        summary_data.append({
            'Workload': inputs.get('workload_name', 'N/A'),
            'Type': inputs.get('workload_type', 'N/A').replace('_', ' ').title(),
            'OS': inputs.get('operating_system', 'N/A').title(),
            'Region': inputs.get('region', 'N/A'),
            'Instance': prod_rec.get('instance_type', 'N/A'),
            'vCPUs': prod_rec.get('vCPUs', 'N/A'),
            'RAM (GB)': prod_rec.get('RAM_GB', 'N/A'),
            'Monthly Cost': prod_rec.get('total_cost', 0),
            'Optimization': f"{prod_rec.get('optimization_score', 0)}%"
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df['Monthly Cost'] = summary_df['Monthly Cost'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(summary_df, use_container_width=True)

def render_reports_export():
    """Render reports and export interface."""
    st.markdown('<div class="section-header"><h3>📋 Reports & Export Center</h3></div>', unsafe_allow_html=True)
    
    has_single_results = st.session_state.analysis_results is not None
    has_bulk_results = len(st.session_state.bulk_results) > 0
    
    if not has_single_results and not has_bulk_results:
        st.info("💡 No analysis results available. Please run a workload analysis first.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">📊 Executive Excel Report</div>
            <div class="metric-description">Comprehensive spreadsheet with detailed analysis and cost breakdowns.</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📈 Generate Excel Report", key="excel_report"):
            generate_excel_report()
    
    with col2:
        if REPORTLAB_AVAILABLE and st.session_state.get('pdf_generator'):
            st.markdown("""
            <div class="metric-card">
                <div class="metric-title">📄 Executive PDF Report</div>
                <div class="metric-description">Professional PDF summary for executive presentations.</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📄 Generate PDF Report", key="pdf_report"):
                generate_pdf_report()
        else:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-title">📄 PDF Reports</div>
                <div class="metric-description">PDF generation unavailable. ReportLab not installed.</div>
            </div>
            """, unsafe_allow_html=True)

def generate_excel_report():
    """Generate Excel report."""
    try:
        if st.session_state.bulk_results:
            results_to_export = st.session_state.bulk_results
        elif st.session_state.analysis_results:
            results_to_export = [st.session_state.analysis_results]
        else:
            st.error("No results available for export.")
            return
        
        with st.spinner("🔄 Generating Excel report..."):
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                summary_data = []
                for result in results_to_export:
                    inputs = result['inputs']
                    prod_rec = result['recommendations']['PROD']
                    
                    summary_data.append({
                        'Workload Name': inputs.get('workload_name', 'N/A'),
                        'Workload Type': inputs.get('workload_type', 'N/A').replace('_', ' ').title(),
                        'Operating System': inputs.get('operating_system', 'N/A').title(),
                        'AWS Region': inputs.get('region', 'N/A'),
                        'Current Cores': inputs.get('on_prem_cores', 'N/A'),
                        'Current RAM (GB)': inputs.get('on_prem_ram_gb', 'N/A'),
                        'Recommended Instance': prod_rec.get('instance_type', 'N/A'),
                        'Recommended vCPUs': prod_rec.get('vCPUs', 'N/A'),
                        'Recommended RAM (GB)': prod_rec.get('RAM_GB', 'N/A'),
                        'Storage (GB)': prod_rec.get('storage_GB', 'N/A'),
                        'Monthly Cost': prod_rec.get('total_cost', 0),
                        'Annual Cost': prod_rec.get('total_cost', 0) * 12,
                        'Optimization Score': prod_rec.get('optimization_score', 'N/A')
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="📥 Download Excel Report",
                data=output.getvalue(),
                file_name=f"aws_workload_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success("✅ Excel report generated successfully!")
            
    except Exception as e:
        st.error(f"❌ Error generating Excel report: {str(e)}")

def generate_pdf_report():
    """Generate PDF report."""
    try:
        if st.session_state.bulk_results:
            results_to_export = st.session_state.bulk_results
        elif st.session_state.analysis_results:
            results_to_export = [st.session_state.analysis_results]
        else:
            st.error("No results available for export.")
            return
        
        with st.spinner("🔄 Generating PDF report..."):
            pdf_data = st.session_state.pdf_generator.generate_comprehensive_report(results_to_export)
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"aws_workload_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
            
            st.success("✅ PDF report generated successfully!")
            
    except Exception as e:
        st.error(f"❌ Error generating PDF report: {str(e)}")

# Main application
def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        if not render_authentication():
            return
    
    # Show demo mode banner if applicable
    if st.session_state.get('demo_mode', False):
        st.markdown("""
        <div class="demo-banner">
            🔧 <strong>Demo Mode Active</strong> - Full functionality available without authentication
        </div>
        """, unsafe_allow_html=True)
    
    # Main application
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise AWS Workload Sizing Platform</h1>
        <p>Comprehensive infrastructure assessment and cloud migration planning for enterprise workloads</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🔧 Global Configuration")
        
        # User info
        render_user_info()
        
        calculator = st.session_state.calculator
        cred_status, cred_message = calculator.validate_aws_credentials()
        
        if cred_status:
            st.markdown(f'<span class="status-badge status-success">AWS Connected</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="status-badge status-error">AWS Not Connected</span>', unsafe_allow_html=True)
        
        st.markdown(f"<small>{cred_message}</small>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.session_state.analysis_results or st.session_state.bulk_results:
            st.markdown("### 📈 Quick Stats")
            
            if st.session_state.bulk_results:
                total_workloads = len(st.session_state.bulk_results)
                total_cost = sum(r['recommendations']['PROD']['total_cost'] for r in st.session_state.bulk_results)
            else:
                total_workloads = 1
                total_cost = st.session_state.analysis_results['recommendations']['PROD']['total_cost']
            
            st.metric("Workloads Analyzed", total_workloads)
            st.metric("Monthly Cost (PROD)", f"${total_cost:,.2f}")
            st.metric("Annual Cost (PROD)", f"${total_cost * 12:,.2f}")
        
        st.markdown("---")
        st.markdown("""
        ### 🚀 Platform Features
        
        **Workload Support:**
        - Web Applications
        - Application Servers  
        - Database Servers
        - File Servers
        - Compute Intensive
        
        **Operating Systems:**
        - Linux (Amazon Linux, Ubuntu, RHEL)
        - Windows Server
        
        **Global Coverage:**
        - US: East, West (N. Cal), West (Oregon)
        - Europe: Ireland, Frankfurt
        - Asia Pacific: Singapore, Sydney, Tokyo, Seoul, Mumbai, Hong Kong
        """)
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Workload Configuration", "📁 Bulk Analysis", "📋 Reports & Export"])
    
    with tab1:
        render_workload_configuration()
        
        if st.button("🚀 Generate Recommendations", type="primary", key="generate_single"):
            with st.spinner("🔄 Analyzing workload requirements..."):
                try:
                    calculator.fetch_current_prices()
                    results = calculator.generate_all_recommendations()
                    st.session_state.analysis_results = {
                        'inputs': calculator.inputs.copy(),
                        'recommendations': results
                    }
                    
                    st.success("✅ Analysis completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
        
        if st.session_state.analysis_results:
            st.markdown("---")
            render_analysis_results(st.session_state.analysis_results['recommendations'])
    
    with tab2:
        render_bulk_analysis()
        
        if st.session_state.bulk_results:
            st.markdown("---")
            display_bulk_analysis_results(st.session_state.bulk_results)
    
    with tab3:
        render_reports_export()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <strong>Enterprise AWS Workload Sizing Platform v3.0 with Authentication</strong><br>
        Secure, comprehensive cloud migration planning for enterprise infrastructure
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()