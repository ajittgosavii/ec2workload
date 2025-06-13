import streamlit as st

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="Enterprise AWS EC2 Workload Sizing Platform v4.0", 
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

import pandas as pd
from io import BytesIO
import io
from datetime import datetime, timedelta
import os
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import boto3
import json
import logging
from functools import lru_cache
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import hashlib
import hmac
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
# Add this import near the top of the file with other imports
import pandas as pd  # (this should already exist)
from datetime import datetime, timedelta  # (this should already exist)
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Firebase imports with error handling
FIREBASE_AVAILABLE = False
try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    import requests
    FIREBASE_AVAILABLE = True
except ImportError as e:
    firebase_admin = None
    credentials = None
    auth = None
    firestore = None
    requests = None
    FIREBASE_AVAILABLE = False

# Try to import pyrebase for client-side auth
PYREBASE_AVAILABLE = False
try:
    import pyrebase
    PYREBASE_AVAILABLE = True
except ImportError:
    pyrebase = None
    PYREBASE_AVAILABLE = False

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

# Enhanced custom CSS with new styling for enterprise features
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
    
    .enterprise-badge {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-left: 1rem;
        display: inline-block;
    }
    
    .savings-highlight {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
    }
    
    .cost-comparison-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .cost-comparison-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .ri-badge {
        background: #ddd6fe;
        color: #5b21b6;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .sp-badge {
        background: #d1fae5;
        color: #065f46;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .spot-badge {
        background: #fef3c7;
        color: #92400e;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
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
    
    .tco-summary {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 2px solid #0284c7;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        text-align: center;
    }
    
    .compliance-badge {
        background: #fee2e2;
        color: #991b1b;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .migration-phase {
        background: white;
        border-left: 4px solid #10b981;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .risk-indicator {
        padding: 0.5rem;
        border-radius: 6px;
        font-weight: 600;
        text-align: center;
        margin: 0.25rem 0;
    }
    
    .risk-low { background: #d1fae5; color: #065f46; }
    .risk-medium { background: #fef3c7; color: #92400e; }
    .risk-high { background: #fee2e2; color: #991b1b; }
    
    .demo-banner {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
    }
    
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .user-info {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-top: 0.5rem;
        display: inline-block;
    }
    
    .status-success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .status-demo {
        background: #fbbf24;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class EnterpriseEC2WorkloadSizingCalculator:
    """Enterprise-grade AWS EC2 workload sizing calculator with advanced features."""
    
    # AWS Instance Types (expanded with more options)
    INSTANCE_TYPES = [
        # General Purpose - M6i (Intel)
        {"type": "m6i.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
        {"type": "m6i.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
        {"type": "m6i.2xlarge", "vCPU": 8, "RAM": 32, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
        {"type": "m6i.4xlarge", "vCPU": 16, "RAM": 64, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
        {"type": "m6i.8xlarge", "vCPU": 32, "RAM": 128, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
        {"type": "m6i.12xlarge", "vCPU": 48, "RAM": 192, "max_ebs_bandwidth": 57000, "network": "37.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
        {"type": "m6i.16xlarge", "vCPU": 64, "RAM": 256, "max_ebs_bandwidth": 76000, "network": "50 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
        
        # General Purpose - M6a (AMD)
        {"type": "m6a.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "general", "processor": "AMD", "architecture": "x86_64"},
        {"type": "m6a.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "general", "processor": "AMD", "architecture": "x86_64"},
        {"type": "m6a.2xlarge", "vCPU": 8, "RAM": 32, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "general", "processor": "AMD", "architecture": "x86_64"},
        {"type": "m6a.4xlarge", "vCPU": 16, "RAM": 64, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "general", "processor": "AMD", "architecture": "x86_64"},
        {"type": "m6a.8xlarge", "vCPU": 32, "RAM": 128, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "general", "processor": "AMD", "architecture": "x86_64"},
        {"type": "m6a.12xlarge", "vCPU": 48, "RAM": 192, "max_ebs_bandwidth": 57000, "network": "37.5 Gbps", "family": "general", "processor": "AMD", "architecture": "x86_64"},
        
        # Memory Optimized - R6i (Intel)
        {"type": "r6i.large", "vCPU": 2, "RAM": 16, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel", "architecture": "x86_64"},
        {"type": "r6i.xlarge", "vCPU": 4, "RAM": 32, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel", "architecture": "x86_64"},
        {"type": "r6i.2xlarge", "vCPU": 8, "RAM": 64, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel", "architecture": "x86_64"},
        {"type": "r6i.4xlarge", "vCPU": 16, "RAM": 128, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "memory", "processor": "Intel", "architecture": "x86_64"},
        {"type": "r6i.8xlarge", "vCPU": 32, "RAM": 256, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "memory", "processor": "Intel", "architecture": "x86_64"},
        {"type": "r6i.12xlarge", "vCPU": 48, "RAM": 384, "max_ebs_bandwidth": 57000, "network": "37.5 Gbps", "family": "memory", "processor": "Intel", "architecture": "x86_64"},
        
        # Compute Optimized - C6i (Intel)
        {"type": "c6i.large", "vCPU": 2, "RAM": 4, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel", "architecture": "x86_64"},
        {"type": "c6i.xlarge", "vCPU": 4, "RAM": 8, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel", "architecture": "x86_64"},
        {"type": "c6i.2xlarge", "vCPU": 8, "RAM": 16, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel", "architecture": "x86_64"},
        {"type": "c6i.4xlarge", "vCPU": 16, "RAM": 32, "max_ebs_bandwidth": 38000, "network": "12.5 Gbps", "family": "compute", "processor": "Intel", "architecture": "x86_64"},
        {"type": "c6i.8xlarge", "vCPU": 32, "RAM": 64, "max_ebs_bandwidth": 47500, "network": "25 Gbps", "family": "compute", "processor": "Intel", "architecture": "x86_64"},
        
        # Graviton instances (ARM)
        {"type": "m6g.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750, "network": "Up to 10 Gbps", "family": "general", "processor": "Graviton", "architecture": "arm64"},
        {"type": "m6g.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500, "network": "Up to 10 Gbps", "family": "general", "processor": "Graviton", "architecture": "arm64"},
        {"type": "m6g.2xlarge", "vCPU": 8, "RAM": 32, "max_ebs_bandwidth": 19000, "network": "Up to 10 Gbps", "family": "general", "processor": "Graviton", "architecture": "arm64"},
        {"type": "m6g.4xlarge", "vCPU": 16, "RAM": 64, "max_ebs_bandwidth": 38000, "network": "10 Gbps", "family": "general", "processor": "Graviton", "architecture": "arm64"},
    ]
    
    # Workload Profiles (enhanced)
    WORKLOAD_PROFILES = {
        "web_application": {
            "name": "Web Application",
            "description": "Frontend web servers, load balancers, CDN origins",
            "cpu_multiplier": 1.0,
            "ram_multiplier": 1.0,
            "storage_multiplier": 0.7,
            "iops_multiplier": 0.8,
            "preferred_family": "general",
            "graviton_compatible": True,
            "spot_suitable": True,
            "compliance_requirements": ["SOC2"],
        },
        "application_server": {
            "name": "Application Server", 
            "description": "Business logic tier, middleware, API servers",
            "cpu_multiplier": 1.2,
            "ram_multiplier": 1.3,
            "storage_multiplier": 0.8,
            "iops_multiplier": 1.0,
            "preferred_family": "general",
            "graviton_compatible": True,
            "spot_suitable": False,
            "compliance_requirements": ["SOC2"],
        },
        "database_server": {
            "name": "Database Server",
            "description": "RDBMS, NoSQL, data warehouses, analytics",
            "cpu_multiplier": 1.1,
            "ram_multiplier": 1.5,
            "storage_multiplier": 1.2,
            "iops_multiplier": 1.5,
            "preferred_family": "memory",
            "graviton_compatible": False,
            "spot_suitable": False,
            "compliance_requirements": ["SOC2", "PCI-DSS"],
        },
        "file_server": {
            "name": "File Server",
            "description": "File shares, NAS, backup systems",
            "cpu_multiplier": 0.8,
            "ram_multiplier": 1.0,
            "storage_multiplier": 2.0,
            "iops_multiplier": 1.3,
            "preferred_family": "general",
            "graviton_compatible": True,
            "spot_suitable": True,
            "compliance_requirements": ["SOC2"],
        },
        "compute_intensive": {
            "name": "Compute Intensive",
            "description": "HPC, scientific computing, batch processing",
            "cpu_multiplier": 1.5,
            "ram_multiplier": 1.2,
            "storage_multiplier": 0.9,
            "iops_multiplier": 0.9,
            "preferred_family": "compute",
            "graviton_compatible": False,
            "spot_suitable": True,
            "compliance_requirements": [],
        },
        "analytics_workload": {
            "name": "Analytics Workload",
            "description": "Data processing, ETL, business intelligence",
            "cpu_multiplier": 1.3,
            "ram_multiplier": 1.4,
            "storage_multiplier": 1.5,
            "iops_multiplier": 1.2,
            "preferred_family": "memory",
            "graviton_compatible": True,
            "spot_suitable": True,
            "compliance_requirements": ["SOC2"],
        }
    }
    
    # Environment Multipliers (enhanced)
    ENV_MULTIPLIERS = {
        "PROD": {"cpu_ram": 1.0, "storage": 1.0, "description": "Production environment", "availability_requirement": "99.9%"},
        "STAGING": {"cpu_ram": 0.8, "storage": 0.8, "description": "Pre-production testing", "availability_requirement": "99.0%"},
        "QA": {"cpu_ram": 0.6, "storage": 0.6, "description": "Quality assurance", "availability_requirement": "95.0%"},
        "DEV": {"cpu_ram": 0.4, "storage": 0.4, "description": "Development environment", "availability_requirement": "90.0%"},
        "DR": {"cpu_ram": 1.0, "storage": 1.0, "description": "Disaster recovery", "availability_requirement": "99.9%"}
    }
    
    # Enhanced Pricing with RI and Savings Plans
    BASE_PRICING = {
        "instance": {
            # On-Demand Pricing
            "on_demand": {
                # M6i Intel instances
                "m6i.large": 0.0864, "m6i.xlarge": 0.1728, "m6i.2xlarge": 0.3456,
                "m6i.4xlarge": 0.6912, "m6i.8xlarge": 1.3824, "m6i.12xlarge": 2.0736, "m6i.16xlarge": 2.7648,
                
                # M6a AMD instances
                "m6a.large": 0.0778, "m6a.xlarge": 0.1555, "m6a.2xlarge": 0.3110,
                "m6a.4xlarge": 0.6221, "m6a.8xlarge": 1.2442, "m6a.12xlarge": 1.8663,
                
                # R6i Intel memory optimized
                "r6i.large": 0.1008, "r6i.xlarge": 0.2016, "r6i.2xlarge": 0.4032,
                "r6i.4xlarge": 0.8064, "r6i.8xlarge": 1.6128, "r6i.12xlarge": 2.4192,
                
                # C6i Intel compute optimized
                "c6i.large": 0.0765, "c6i.xlarge": 0.1530, "c6i.2xlarge": 0.3060,
                "c6i.4xlarge": 0.6120, "c6i.8xlarge": 1.2240,
                
                # Graviton instances (15-20% cost advantage)
                "m6g.large": 0.0692, "m6g.xlarge": 0.1384, "m6g.2xlarge": 0.2768, "m6g.4xlarge": 0.5536,
            },
            
            # Reserved Instance Pricing (1-year, no upfront)
            "ri_1y_no_upfront": {
                # M6i Intel (approximately 30% discount)
                "m6i.large": 0.0605, "m6i.xlarge": 0.1210, "m6i.2xlarge": 0.2419,
                "m6i.4xlarge": 0.4838, "m6i.8xlarge": 0.9677, "m6i.12xlarge": 0.4515, "m6i.16xlarge": 1.9354,
                
                # M6a AMD instances
                "m6a.large": 0.0545, "m6a.xlarge": 0.1089, "m6a.2xlarge": 0.2177,
                "m6a.4xlarge": 0.4355, "m6a.8xlarge": 0.8709, "m6a.12xlarge": 1.3064,
                
                # R6i Intel memory optimized
                "r6i.large": 0.0706, "r6i.xlarge": 0.1411, "r6i.2xlarge": 0.2822,
                "r6i.4xlarge": 0.5645, "r6i.8xlarge": 1.1290, "r6i.12xlarge": 1.6934,
                
                # C6i Intel compute optimized
                "c6i.large": 0.0536, "c6i.xlarge": 0.1071, "c6i.2xlarge": 0.2142,
                "c6i.4xlarge": 0.4284, "c6i.8xlarge": 0.8568,
                
                # Graviton instances
                "m6g.large": 0.0485, "m6g.xlarge": 0.0969, "m6g.2xlarge": 0.1938, "m6g.4xlarge": 0.3875,
            },
            
            # Reserved Instance Pricing (3-year, no upfront)
            "ri_3y_no_upfront": {
                # M6i Intel (approximately 50% discount)
                "m6i.large": 0.0432, "m6i.xlarge": 0.0864, "m6i.2xlarge": 0.1728,
                "m6i.4xlarge": 0.3456, "m6i.8xlarge": 0.6912, "m6i.12xlarge": 1.0368, "m6i.16xlarge": 1.3824,
                
                # M6a AMD instances
                "m6a.large": 0.0389, "m6a.xlarge": 0.0778, "m6a.2xlarge": 0.1555,
                "m6a.4xlarge": 0.3111, "m6a.8xlarge": 0.6221, "m6a.12xlarge": 0.9332,
                
                # R6i Intel memory optimized
                "r6i.large": 0.0504, "r6i.xlarge": 0.1008, "r6i.2xlarge": 0.2016,
                "r6i.4xlarge": 0.4032, "r6i.8xlarge": 0.8064, "r6i.12xlarge": 1.2096,
                
                # C6i Intel compute optimized
                "c6i.large": 0.0383, "c6i.xlarge": 0.0765, "c6i.2xlarge": 0.1530,
                "c6i.4xlarge": 0.3060, "c6i.8xlarge": 0.6120,
                
                # Graviton instances
                "m6g.large": 0.0346, "m6g.xlarge": 0.0692, "m6g.2xlarge": 0.1384, "m6g.4xlarge": 0.2768,
            },
            
            # Spot Instance Pricing (typically 50-90% discount)
            "spot": {
                # Average spot prices (varies significantly)
                "m6i.large": 0.0259, "m6i.xlarge": 0.0518, "m6i.2xlarge": 0.1037,
                "m6i.4xlarge": 0.2074, "m6i.8xlarge": 0.4147, "m6i.12xlarge": 0.6221, "m6i.16xlarge": 0.8294,
                
                "m6a.large": 0.0233, "m6a.xlarge": 0.0467, "m6a.2xlarge": 0.0933,
                "m6a.4xlarge": 0.1866, "m6a.8xlarge": 0.3733, "m6a.12xlarge": 0.5599,
                
                "r6i.large": 0.0302, "r6i.xlarge": 0.0605, "r6i.2xlarge": 0.1210,
                "r6i.4xlarge": 0.2419, "r6i.8xlarge": 0.4838, "r6i.12xlarge": 0.7258,
                
                "c6i.large": 0.0230, "c6i.xlarge": 0.0459, "c6i.2xlarge": 0.0918,
                "c6i.4xlarge": 0.1836, "c6i.8xlarge": 0.3672,
                
                "m6g.large": 0.0208, "m6g.xlarge": 0.0415, "m6g.2xlarge": 0.0830, "m6g.4xlarge": 0.1661,
            }
        },
        
        # Savings Plans Discounts
        "savings_plans": {
            "compute_1y": 0.28,  # 28% discount for 1-year Compute Savings Plan
            "compute_3y": 0.46,  # 46% discount for 3-year Compute Savings Plan
            "ec2_1y": 0.31,      # 31% discount for 1-year EC2 Instance Savings Plan
            "ec2_3y": 0.50,      # 50% discount for 3-year EC2 Instance Savings Plan
        },
        
        # EBS Pricing by region
        "ebs": {
            "us-east-1": {"gp3": {"gb": 0.08, "iops": 0.005, "throughput": 0.04}, "io2": {"gb": 0.125, "iops": 0.065}},
            "us-west-1": {"gp3": {"gb": 0.088, "iops": 0.0055, "throughput": 0.044}, "io2": {"gb": 0.138, "iops": 0.0715}},
            "us-west-2": {"gp3": {"gb": 0.084, "iops": 0.0052, "throughput": 0.042}, "io2": {"gb": 0.131, "iops": 0.068}},
            "eu-west-1": {"gp3": {"gb": 0.089, "iops": 0.0054, "throughput": 0.043}, "io2": {"gb": 0.138, "iops": 0.070}},
            "eu-central-1": {"gp3": {"gb": 0.092, "iops": 0.0055, "throughput": 0.044}, "io2": {"gb": 0.142, "iops": 0.072}},
            "ap-southeast-1": {"gp3": {"gb": 0.095, "iops": 0.0057, "throughput": 0.046}, "io2": {"gb": 0.145, "iops": 0.073}},
            "ap-southeast-2": {"gp3": {"gb": 0.095, "iops": 0.0057, "throughput": 0.046}, "io2": {"gb": 0.145, "iops": 0.073}},
            "ap-northeast-1": {"gp3": {"gb": 0.096, "iops": 0.0058, "throughput": 0.047}, "io2": {"gb": 0.148, "iops": 0.075}},
            "ap-northeast-2": {"gp3": {"gb": 0.094, "iops": 0.0056, "throughput": 0.045}, "io2": {"gb": 0.143, "iops": 0.072}},
            "ap-south-1": {"gp3": {"gb": 0.087, "iops": 0.0052, "throughput": 0.042}, "io2": {"gb": 0.135, "iops": 0.068}},
            "ap-east-1": {"gp3": {"gb": 0.103, "iops": 0.0062, "throughput": 0.050}, "io2": {"gb": 0.158, "iops": 0.080}},
        },
        
        # Additional AWS Services Pricing
        "additional_services": {
            "load_balancer": {
                "alb": {"hourly": 0.0225, "lcu": 0.008},  # Application Load Balancer
                "nlb": {"hourly": 0.0225, "lcus": 0.006}, # Network Load Balancer
            },
            "nat_gateway": {"hourly": 0.045, "per_gb": 0.045},
            "vpc_endpoints": {"hourly": 0.01, "per_gb": 0.01},
            "cloudwatch": {
                "logs": {"ingestion": 0.50, "storage": 0.03},  # per GB
                "metrics": {"custom": 0.30},  # per metric per month
                "alarms": 0.10,  # per alarm per month
            },
            "backup": {"storage": 0.05, "restore": 0.02},  # per GB
        }
    }
    
    # Compliance Requirements
    COMPLIANCE_FRAMEWORKS = {
        "SOC2": {
            "name": "SOC 2",
            "description": "Service Organization Control 2",
            "requirements": ["Encryption at rest", "Encryption in transit", "Access logging", "Multi-AZ deployment"],
            "additional_cost_factor": 1.05
        },
        "PCI-DSS": {
            "name": "PCI DSS",
            "description": "Payment Card Industry Data Security Standard",
            "requirements": ["Dedicated tenancy", "Enhanced monitoring", "Network segmentation", "Regular security scans"],
            "additional_cost_factor": 1.15
        },
        "HIPAA": {
            "name": "HIPAA",
            "description": "Health Insurance Portability and Accountability Act",
            "requirements": ["BAA required", "Enhanced encryption", "Audit logging", "Access controls"],
            "additional_cost_factor": 1.12
        },
        "FedRAMP": {
            "name": "FedRAMP",
            "description": "Federal Risk and Authorization Management Program",
            "requirements": ["GovCloud deployment", "Enhanced monitoring", "Continuous compliance"],
            "additional_cost_factor": 1.25
        }
    }
    
    def __init__(self):
        """Initialize calculator with default settings."""
        self.inputs = {
            "workload_name": "Sample Enterprise Workload",
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
            "enable_graviton": True,
            "pricing_model": "on_demand",  # on_demand, ri_1y, ri_3y, savings_plan_compute_1y, etc.
            "spot_percentage": 0,  # Percentage of workload suitable for spot instances
            "multi_az": True,
            "compliance_requirements": [],
            "backup_retention_days": 30,
            "monitoring_level": "basic",  # basic, detailed, enhanced
            "disaster_recovery": False,
            "auto_scaling": True,
            "load_balancer": "alb",  # alb, nlb, none
        }
        
        self.instance_pricing = {}
        self.recommendation_cache = {}
        self._setup_pricing()
    
    def _setup_pricing(self):
        """Setup pricing structures."""
        for pricing_type, instances in self.BASE_PRICING["instance"].items():
            self.instance_pricing[pricing_type] = instances.copy()
    
    def validate_aws_credentials(self):
        """Validate AWS credentials."""
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials is None:
                return False, "❌ No AWS credentials found"
            
            # Test credentials by making a simple call
            ec2 = session.client('ec2', region_name='us-east-1')
            ec2.describe_regions()
            return True, "✅ AWS credentials valid"
        except (NoCredentialsError, PartialCredentialsError):
            return False, "❌ AWS credentials not configured"
        except Exception as e:
            return False, f"❌ AWS connection error: {str(e)}"
    
    def calculate_comprehensive_requirements(self, env: str) -> Dict[str, Any]:
        """Calculate comprehensive infrastructure requirements with enterprise features."""
        env_mult = self.ENV_MULTIPLIERS[env]
        workload_profile = self.WORKLOAD_PROFILES[self.inputs["workload_type"]]
        
        # Base calculations
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
        
        # Enhanced storage calculation
        growth_factor = (1 + self.inputs["storage_growth_rate"]) ** self.inputs["years"]
        storage_buffer = 1.3 if env == "PROD" else 1.2
        
        base_storage = math.ceil(
            self.inputs["storage_current_gb"] * 
            growth_factor * 
            workload_profile["storage_multiplier"] *
            storage_buffer *
            env_mult["storage"]
        )
        
        # Add backup storage requirements
        backup_multiplier = self.inputs["backup_retention_days"] / 30.0
        backup_storage = math.ceil(base_storage * backup_multiplier * 0.7)  # Assume 70% compression
        
        total_storage = base_storage + backup_storage
        
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
        
        # Multi-AZ adjustments
        if self.inputs["multi_az"] and env in ["PROD", "DR"]:
            az_multiplier = 2
            required_vcpus = math.ceil(required_vcpus * 1.1)  # Account for cross-AZ overhead
            required_ram = math.ceil(required_ram * 1.1)
        else:
            az_multiplier = 1
        
        # Instance selection
        instance_options = self._get_optimal_instance_options(
            required_vcpus, required_ram, throughput_required, workload_profile, env
        )
        
        # Cost calculations
        cost_breakdown = self._calculate_comprehensive_costs(
            instance_options, total_storage, iops_required, throughput_required, env, az_multiplier
        )
        # Add network costs
        network_costs = self.calculate_network_costs(self.inputs)
        cost_breakdown["network_costs"].update(network_costs)
        
        
        # Compliance cost adjustments
        compliance_factor = 1.0
        for compliance in self.inputs["compliance_requirements"]:
            if compliance in self.COMPLIANCE_FRAMEWORKS:
                compliance_factor *= self.COMPLIANCE_FRAMEWORKS[compliance]["additional_cost_factor"]
        
        # Apply compliance factor to all costs
        for cost_type in cost_breakdown:
            if isinstance(cost_breakdown[cost_type], dict):
                for subtype in cost_breakdown[cost_type]:
                    if isinstance(cost_breakdown[cost_type][subtype], (int, float)):
                        cost_breakdown[cost_type][subtype] *= compliance_factor
            elif isinstance(cost_breakdown[cost_type], (int, float)):
                cost_breakdown[cost_type] *= compliance_factor
        
        # TCO calculation
        tco_analysis = self._calculate_tco_analysis(cost_breakdown, env)
        
        # Risk assessment
        risk_assessment = self._assess_migration_risks(workload_profile, env)
        
        return {
            "environment": env,
            "requirements": {
                "vCPUs": required_vcpus,
                "RAM_GB": required_ram,
                "storage_GB": total_storage,
                "base_storage_GB": base_storage,
                "backup_storage_GB": backup_storage,
                "iops_required": iops_required,
                "throughput_required": f"{throughput_required} MB/s",
                "multi_az": self.inputs["multi_az"] and env in ["PROD", "DR"],
                "availability_zones": az_multiplier,
            },
            "instance_options": instance_options,
            "cost_breakdown": cost_breakdown,
            "tco_analysis": tco_analysis,
            "compliance": {
                "requirements": self.inputs["compliance_requirements"],
                "cost_factor": compliance_factor,
            },
            "risk_assessment": risk_assessment,
            "optimization_recommendations": self._generate_optimization_recommendations(
                instance_options, cost_breakdown, workload_profile, env
            )
        }
    
    def _get_optimal_instance_options(self, required_vcpus: int, required_ram: int, 
                                    required_throughput: int, workload_profile: Dict, env: str) -> Dict[str, Any]:
        """Get optimal instance options including Graviton and different families."""
        options = {}
        
        # Filter instances based on requirements
        candidates = []
        for instance in self.INSTANCE_TYPES:
            if (instance["vCPU"] >= required_vcpus and 
                instance["RAM"] >= required_ram and
                instance["max_ebs_bandwidth"] >= (required_throughput * 1.2)):
                
                # Check Graviton compatibility
                if (instance["processor"] == "Graviton" and 
                    not (self.inputs["enable_graviton"] and workload_profile["graviton_compatible"])):
                    continue
                
                candidates.append(instance)
        
        if not candidates:
            # Fallback to instances that meet CPU and RAM requirements
            candidates = [i for i in self.INSTANCE_TYPES 
                         if (i["vCPU"] >= required_vcpus and i["RAM"] >= required_ram)]
        
        # Score and select best options for different scenarios
        scenarios = ["cost_optimized", "performance_optimized", "balanced"]
        
        for scenario in scenarios:
            best_instance = self._select_best_instance(candidates, required_vcpus, required_ram, scenario)
            if best_instance:
                options[scenario] = best_instance
        
        # Add spot instance recommendation if suitable
        if workload_profile["spot_suitable"] and env not in ["PROD", "DR"]:
            spot_instance = self._select_best_instance(candidates, required_vcpus, required_ram, "cost_optimized")
            if spot_instance:
                options["spot_recommended"] = spot_instance
        
        return options
    
    def _select_best_instance(self, candidates: List[Dict], required_vcpus: int, 
                            required_ram: int, optimization_goal: str) -> Optional[Dict]:
        """Select the best instance based on optimization goal."""
        if not candidates:
            return None
        
        scored_instances = []
        
        for instance in candidates:
            cpu_efficiency = required_vcpus / instance["vCPU"]
            ram_efficiency = required_ram / instance["RAM"]
            base_cost = self.instance_pricing["on_demand"].get(instance["type"], 999)
            
            if optimization_goal == "cost_optimized":
                score = (cpu_efficiency + ram_efficiency) / 2 / base_cost * 1000
                # Boost score for AMD and Graviton
                if instance["processor"] in ["AMD", "Graviton"]:
                    score *= 1.2
            elif optimization_goal == "performance_optimized":
                score = instance["vCPU"] + instance["RAM"] / 10
                # Prefer Intel for performance-critical workloads
                if instance["processor"] == "Intel":
                    score *= 1.1
            else:  # balanced
                efficiency_score = (cpu_efficiency + ram_efficiency) / 2
                cost_score = 1 / (base_cost + 0.01)
                score = efficiency_score * cost_score * 100
            
            scored_instances.append((score, instance))
        
        # Return the best scoring instance
        scored_instances.sort(key=lambda x: x[0], reverse=True)
        return scored_instances[0][1]
    
    def _calculate_comprehensive_costs(self, instance_options: Dict, storage_gb: int, 
                                     iops: int, throughput_mbps: int, env: str, az_multiplier: int) -> Dict[str, Any]:
        """Calculate comprehensive costs for all pricing models."""
        cost_breakdown = {
            "instance_costs": {},
            "storage_costs": {},
            "network_costs": {},
            "additional_services": {},
            "total_costs": {}
        }
        
        # Instance costs for different pricing models
        primary_instance = instance_options.get("balanced", instance_options.get("cost_optimized"))
        if not primary_instance:
            return cost_breakdown
        
        instance_type = primary_instance["type"]
        
        # Calculate for different pricing models
        pricing_models = ["on_demand", "ri_1y_no_upfront", "ri_3y_no_upfront", "spot"]
        
        for model in pricing_models:
            if instance_type in self.instance_pricing.get(model, {}):
                hourly_rate = self.instance_pricing[model][instance_type]
                monthly_cost = hourly_rate * 24 * 30 * az_multiplier
                cost_breakdown["instance_costs"][model] = round(monthly_cost, 2)
        
        # Savings Plans pricing
        base_hourly = self.instance_pricing["on_demand"].get(instance_type, 0)
        for sp_type, discount in self.BASE_PRICING["savings_plans"].items():
            sp_hourly = base_hourly * (1 - discount)
            sp_monthly = sp_hourly * 24 * 30 * az_multiplier
            cost_breakdown["instance_costs"][f"savings_plan_{sp_type}"] = round(sp_monthly, 2)
        
        # Storage costs
        storage_costs = self._calculate_enhanced_storage_costs(storage_gb, iops, throughput_mbps, az_multiplier)
        cost_breakdown["storage_costs"] = storage_costs
        
        # Network costs
        network_costs = self._calculate_network_costs(env, az_multiplier)
        cost_breakdown["network_costs"] = network_costs
        
        # Additional services costs
        additional_costs = self._calculate_additional_services_costs(env, az_multiplier)
        cost_breakdown["additional_services"] = additional_costs
        
        # Calculate total costs for each pricing model
        for model in cost_breakdown["instance_costs"]:
            total = (cost_breakdown["instance_costs"][model] + 
                    sum(storage_costs.values()) + 
                    sum(network_costs.values()) + 
                    sum(additional_costs.values()))
            cost_breakdown["total_costs"][model] = round(total, 2)
        
        return cost_breakdown
    
    def _calculate_enhanced_storage_costs(self, storage_gb: int, iops: int, 
                                        throughput_mbps: int, az_multiplier: int) -> Dict[str, float]:
        """Calculate enhanced storage costs including backups and snapshots."""
        region = self.inputs["region"]
        region_pricing = self.BASE_PRICING["ebs"].get(region, self.BASE_PRICING["ebs"]["us-east-1"])
        
        # Primary storage
        ebs_type = "io2" if iops > 16000 or throughput_mbps > 1000 else "gp3"
        pricing = region_pricing[ebs_type]
        
        base_cost = storage_gb * pricing["gb"] * az_multiplier
        
        storage_costs = {
            "primary_storage": round(base_cost, 2),
        }
        
        # IOPS costs (for gp3 > 3000 IOPS or io2)
        if ebs_type == "gp3" and iops > 3000:
            extra_iops = iops - 3000
            iops_cost = extra_iops * pricing.get("iops", 0) * az_multiplier
            storage_costs["additional_iops"] = round(iops_cost, 2)
        elif ebs_type == "io2":
            iops_cost = iops * pricing.get("iops", 0) * az_multiplier
            storage_costs["provisioned_iops"] = round(iops_cost, 2)
        
        # Throughput costs (for gp3 > 125 MB/s)
        if ebs_type == "gp3" and throughput_mbps > 125:
            extra_throughput = throughput_mbps - 125
            throughput_cost = extra_throughput * pricing.get("throughput", 0) * az_multiplier
            storage_costs["additional_throughput"] = round(throughput_cost, 2)
        
        # Backup costs
        backup_storage_gb = storage_gb * (self.inputs["backup_retention_days"] / 30.0) * 0.7
        backup_cost = backup_storage_gb * self.BASE_PRICING["additional_services"]["backup"]["storage"]
        storage_costs["backup_storage"] = round(backup_cost, 2)
        
        # Snapshot costs (daily snapshots)
        snapshot_cost = storage_gb * 0.05 * az_multiplier  # Assume $0.05/GB/month for snapshots
        storage_costs["snapshots"] = round(snapshot_cost, 2)
        
        return storage_costs
    
    def _calculate_network_costs(self, env: str, az_multiplier: int) -> Dict[str, float]:
        """Calculate comprehensive network costs."""
        base_data_transfer = {"PROD": 100, "STAGING": 50, "QA": 30, "DEV": 20, "DR": 75}
        workload_multiplier = {
            "web_application": 1.5, "application_server": 1.2, "database_server": 1.0,
            "file_server": 2.0, "compute_intensive": 0.8, "analytics_workload": 1.3
        }
        
        base_transfer_gb = base_data_transfer.get(env, 50)
        workload_mult = workload_multiplier.get(self.inputs["workload_type"], 1.0)
        monthly_transfer_gb = base_transfer_gb * workload_mult * az_multiplier
        
        network_costs = {
            "data_transfer_out": round(monthly_transfer_gb * 0.09, 2),  # $0.09/GB typical
        }
        
        # NAT Gateway costs (if required)
        if self.inputs.get("multi_az", False):
            nat_costs = self.BASE_PRICING["additional_services"]["nat_gateway"]
            nat_cost = (nat_costs["hourly"] * 24 * 30 * az_multiplier + 
                       monthly_transfer_gb * nat_costs["per_gb"])
            network_costs["nat_gateway"] = round(nat_cost, 2)
        
        # VPC Endpoint costs (for enhanced security)
        if self.inputs["compliance_requirements"]:
            vpc_endpoint_cost = (self.BASE_PRICING["additional_services"]["vpc_endpoints"]["hourly"] * 
                               24 * 30 * 2)  # Assume 2 endpoints
            network_costs["vpc_endpoints"] = round(vpc_endpoint_cost, 2)
        
        return network_costs
    
    def _calculate_additional_services_costs(self, env: str, az_multiplier: int) -> Dict[str, float]:
        """Calculate costs for additional AWS services."""
        additional_costs = {}
        
        # Load Balancer costs
        lb_type = self.inputs.get("load_balancer", "alb")
        if lb_type != "none":
            lb_pricing = self.BASE_PRICING["additional_services"]["load_balancer"][lb_type]
            lb_cost = lb_pricing["hourly"] * 24 * 30 * az_multiplier
            
            # Add LCU costs (estimated based on workload type)
            lcu_usage = {"web_application": 50, "application_server": 30, "database_server": 10}.get(
                self.inputs["workload_type"], 20
            )
            lcu_key = "lcu" if lb_type == "alb" else "lcus"
            lcu_cost = lcu_usage * lb_pricing[lcu_key] * 24 * 30
            
            additional_costs["load_balancer"] = round(lb_cost + lcu_cost, 2)
        
        # CloudWatch costs
        monitoring_level = self.inputs.get("monitoring_level", "basic")
        if monitoring_level == "enhanced":
            cw_pricing = self.BASE_PRICING["additional_services"]["cloudwatch"]
            
            # Logs (estimated 10GB/month per instance)
            log_volume = 10 * az_multiplier
            log_cost = log_volume * cw_pricing["logs"]["ingestion"] + log_volume * cw_pricing["logs"]["storage"]
            
            # Custom metrics (estimated 20 metrics per instance)
            metrics_cost = 20 * az_multiplier * cw_pricing["metrics"]["custom"]
            
            # Alarms (estimated 5 alarms per instance)
            alarms_cost = 5 * az_multiplier * cw_pricing["alarms"]
            
            additional_costs["cloudwatch"] = round(log_cost + metrics_cost + alarms_cost, 2)
        
        return additional_costs
    
    def _calculate_tco_analysis(self, cost_breakdown: Dict, env: str) -> Dict[str, Any]:
        """Calculate Total Cost of Ownership analysis."""
        # Get best cost option
        total_costs = cost_breakdown["total_costs"]
        best_option = min(total_costs.items(), key=lambda x: x[1])
        
        monthly_cost = best_option[1]
        annual_cost = monthly_cost * 12
        three_year_cost = annual_cost * 3
        
        # Calculate potential savings
        on_demand_cost = total_costs.get("on_demand", monthly_cost)
        savings_amount = on_demand_cost - monthly_cost
        savings_percentage = (savings_amount / on_demand_cost * 100) if on_demand_cost > 0 else 0
        
        # Migration costs (estimated)
        migration_cost = self._estimate_migration_costs(env)
        
        # Break-even analysis
        break_even_months = migration_cost / savings_amount if savings_amount > 0 else float('inf')
        
        return {
            "best_pricing_option": best_option[0],
            "monthly_cost": round(monthly_cost, 2),
            "annual_cost": round(annual_cost, 2),
            "three_year_cost": round(three_year_cost, 2),
            "monthly_savings": round(savings_amount, 2),
            "savings_percentage": round(savings_percentage, 1),
            "migration_cost": round(migration_cost, 2),
            "break_even_months": round(break_even_months, 1) if break_even_months != float('inf') else "N/A",
            "roi_3_years": round(((savings_amount * 36 - migration_cost) / migration_cost * 100), 1) if migration_cost > 0 else "N/A"
        }
    
    def _estimate_migration_costs(self, env: str) -> float:
        """Estimate one-time migration costs."""
        base_migration_costs = {
            "PROD": 15000,
            "STAGING": 8000,
            "QA": 5000,
            "DEV": 3000,
            "DR": 12000
        }
        
        workload_complexity = {
            "web_application": 1.0,
            "application_server": 1.2,
            "database_server": 1.5,
            "file_server": 0.8,
            "compute_intensive": 1.1,
            "analytics_workload": 1.3
        }
        
        base_cost = base_migration_costs.get(env, 10000)
        complexity_multiplier = workload_complexity.get(self.inputs["workload_type"], 1.0)
        compliance_multiplier = 1 + (len(self.inputs["compliance_requirements"]) * 0.2)
        
        return base_cost * complexity_multiplier * compliance_multiplier
    
    def _assess_migration_risks(self, workload_profile: Dict, env: str) -> Dict[str, Any]:
        """Assess migration risks and provide mitigation strategies."""
        risks = {
            "overall_risk": "Low",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        risk_score = 0
        
        # Assess various risk factors
        if env == "PROD":
            risk_score += 2
            risks["risk_factors"].append("Production environment migration")
        
        if workload_profile["name"] == "Database Server":
            risk_score += 3
            risks["risk_factors"].append("Database migration complexity")
            risks["mitigation_strategies"].append("Implement comprehensive backup and rollback strategy")
        
        if self.inputs["compliance_requirements"]:
            risk_score += 1
            risks["risk_factors"].append("Compliance requirements")
            risks["mitigation_strategies"].append("Conduct compliance validation testing")
        
        if not workload_profile["graviton_compatible"] and self.inputs["enable_graviton"]:
            risk_score += 2
            risks["risk_factors"].append("Architecture change (x86 to ARM)")
            risks["mitigation_strategies"].append("Extensive application testing required")
        
        # Determine overall risk level
        if risk_score <= 2:
            risks["overall_risk"] = "Low"
        elif risk_score <= 5:
            risks["overall_risk"] = "Medium"
        else:
            risks["overall_risk"] = "High"
        
        # Add general mitigation strategies
        risks["mitigation_strategies"].extend([
            "Implement comprehensive monitoring and alerting",
            "Create detailed rollback procedures",
            "Conduct thorough performance testing",
            "Plan migration during low-traffic periods"
        ])
        
        return risks
    
    def _generate_optimization_recommendations(self, instance_options: Dict, cost_breakdown: Dict, 
                                             workload_profile: Dict, env: str) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Cost optimization recommendations
        total_costs = cost_breakdown["total_costs"]
        on_demand_cost = total_costs.get("on_demand", 0)
        
        # Reserved Instance recommendations
        ri_1y_cost = total_costs.get("ri_1y_no_upfront", 0)
        ri_3y_cost = total_costs.get("ri_3y_no_upfront", 0)
        
        if ri_1y_cost < on_demand_cost:
            savings = on_demand_cost - ri_1y_cost
            recommendations.append(f"Consider 1-year Reserved Instances for ${savings:.2f}/month savings")
        
        if ri_3y_cost < ri_1y_cost:
            savings = ri_1y_cost - ri_3y_cost
            recommendations.append(f"Consider 3-year Reserved Instances for additional ${savings:.2f}/month savings")
        
        # Savings Plans recommendations
        sp_costs = {k: v for k, v in total_costs.items() if k.startswith("savings_plan")}
        if sp_costs:
            best_sp = min(sp_costs.items(), key=lambda x: x[1])
            if best_sp[1] < on_demand_cost:
                savings = on_demand_cost - best_sp[1]
                recommendations.append(f"Consider {best_sp[0].replace('_', ' ').title()} for ${savings:.2f}/month savings")
        
        # Spot instance recommendations
        if workload_profile["spot_suitable"] and env not in ["PROD", "DR"]:
            spot_cost = total_costs.get("spot", 0)
            if spot_cost > 0:
                savings = on_demand_cost - spot_cost
                recommendations.append(f"Consider Spot Instances for ${savings:.2f}/month savings (70-90% discount)")
        
        # Graviton recommendations
        if (workload_profile["graviton_compatible"] and 
            self.inputs["enable_graviton"] and 
            "spot_recommended" in instance_options):
            recommendations.append("Consider Graviton processors for 15-20% better price-performance")
        
        # Auto Scaling recommendations
        if self.inputs["auto_scaling"]:
            recommendations.append("Implement Auto Scaling to optimize costs during low-demand periods")
        
        # Storage optimization
        storage_costs = cost_breakdown["storage_costs"]
        total_storage_cost = sum(storage_costs.values())
        if total_storage_cost > on_demand_cost * 0.3:  # If storage is >30% of total cost
            recommendations.append("Consider storage optimization: lifecycle policies, compression, archiving")
        
        return recommendations
# INSERT THIS RIGHT AFTER THE EnterpriseEC2WorkloadSizingCalculator class ends
# (Around line 800-900, after the last method of the calculator class)

class CloudMigrationDecisionEngine:
    """
    Enhanced decision engine to determine whether cloud migration is beneficial
    based on financial, technical, operational, and strategic factors.
    """
    
    def __init__(self):
        # Decision thresholds and weights
        self.decision_weights = {
            'financial': 0.35,      # 35% weight for financial factors
            'technical': 0.25,      # 25% weight for technical factors  
            'operational': 0.20,    # 20% weight for operational factors
            'strategic': 0.20       # 20% weight for strategic factors
        }
        
        # Scoring thresholds
        self.thresholds = {
            'strong_recommendation': 75,    # 75+ = Strong recommendation to migrate
            'moderate_recommendation': 60,  # 60-74 = Moderate recommendation
            'neutral': 45,                 # 45-59 = Neutral/depends on priorities
            'stay_on_premises': 44         # <45 = Stay on-premises
        }
    
    def calculate_financial_score(self, inputs, cloud_results):
        """Calculate financial viability score (0-100)."""
        financial_factors = {}
        
        # 1. TCO Comparison
        on_prem_annual_cost = inputs.get('current_annual_cost', 0)
        cloud_annual_cost = cloud_results['tco_analysis']['annual_cost']
        
        if on_prem_annual_cost > 0:
            cost_savings_ratio = (on_prem_annual_cost - cloud_annual_cost) / on_prem_annual_cost
            financial_factors['cost_savings'] = min(max(cost_savings_ratio * 100 + 50, 0), 100)
        else:
            financial_factors['cost_savings'] = 50  # Neutral if no data
        
        # 2. ROI Analysis  
        roi_3_years = cloud_results['tco_analysis'].get('roi_3_years', 0)
        if isinstance(roi_3_years, (int, float)):
            if roi_3_years >= 200:
                financial_factors['roi'] = 100
            elif roi_3_years >= 100:
                financial_factors['roi'] = 80
            elif roi_3_years >= 50:
                financial_factors['roi'] = 60
            elif roi_3_years >= 20:
                financial_factors['roi'] = 40
            else:
                financial_factors['roi'] = 20
        else:
            financial_factors['roi'] = 30  # Conservative if ROI not calculable
        
        # 3. Break-even Analysis
        break_even_months = cloud_results['tco_analysis'].get('break_even_months', 'N/A')
        if isinstance(break_even_months, (int, float)):
            if break_even_months <= 12:
                financial_factors['break_even'] = 90
            elif break_even_months <= 24:
                financial_factors['break_even'] = 70
            elif break_even_months <= 36:
                financial_factors['break_even'] = 50
            else:
                financial_factors['break_even'] = 20
        else:
            financial_factors['break_even'] = 30
        
        # 4. Capital vs Operational Expenditure
        capex_preference = inputs.get('prefer_opex', True)  # Prefer OpEx model
        financial_factors['capex_opex'] = 80 if capex_preference else 40
        
        # 5. Migration Cost Impact
        migration_cost = cloud_results['tco_analysis'].get('migration_cost', 0)
        annual_savings = cloud_results['tco_analysis'].get('monthly_savings', 0) * 12
        
        if annual_savings > 0:
            migration_impact = migration_cost / annual_savings
            if migration_impact <= 0.5:
                financial_factors['migration_impact'] = 90
            elif migration_impact <= 1.0:
                financial_factors['migration_impact'] = 70
            elif migration_impact <= 2.0:
                financial_factors['migration_impact'] = 50
            else:
                financial_factors['migration_impact'] = 20
        else:
            financial_factors['migration_impact'] = 30
        
        # Weighted average of financial factors
        weights = {
            'cost_savings': 0.30,
            'roi': 0.25,
            'break_even': 0.20,
            'capex_opex': 0.15,
            'migration_impact': 0.10
        }
        
        financial_score = sum(financial_factors[factor] * weights[factor] 
                            for factor in financial_factors)
        
        return financial_score, financial_factors
    
    def calculate_technical_score(self, inputs, cloud_results):
        """Calculate technical factors score (0-100)."""
        technical_factors = {}
        
        # 1. Infrastructure Age
        infrastructure_age = inputs.get('infrastructure_age_years', 3)
        if infrastructure_age >= 5:
            technical_factors['infrastructure_age'] = 90
        elif infrastructure_age >= 3:
            technical_factors['infrastructure_age'] = 70
        elif infrastructure_age >= 2:
            technical_factors['infrastructure_age'] = 50
        else:
            technical_factors['infrastructure_age'] = 30
        
        # 2. Scalability Requirements
        scalability_needs = inputs.get('scalability_importance', 'medium')  # high/medium/low
        scalability_scores = {'high': 90, 'medium': 60, 'low': 30}
        technical_factors['scalability'] = scalability_scores.get(scalability_needs, 60)
        
        # 3. Performance Requirements
        performance_criticality = inputs.get('performance_criticality', 'medium')
        performance_scores = {'high': 70, 'medium': 80, 'low': 90}  # Cloud often better for non-critical
        technical_factors['performance'] = performance_scores.get(performance_criticality, 80)
        
        # 4. Disaster Recovery Needs
        dr_requirements = inputs.get('disaster_recovery_needs', 'medium')
        dr_scores = {'high': 85, 'medium': 70, 'low': 50}
        technical_factors['disaster_recovery'] = dr_scores.get(dr_requirements, 70)
        
        # 5. Geographic Distribution
        multi_region_needs = inputs.get('multi_region_required', False)
        technical_factors['geographic'] = 85 if multi_region_needs else 40
        
        # 6. Technology Stack Compatibility
        cloud_native_compatible = inputs.get('cloud_native_compatible', True)
        technical_factors['compatibility'] = 80 if cloud_native_compatible else 30
        
        # 7. Security Requirements
        security_level = inputs.get('security_requirements', 'medium')  # high/medium/low
        security_scores = {'high': 60, 'medium': 80, 'low': 90}  # High security might prefer on-prem
        technical_factors['security'] = security_scores.get(security_level, 80)
        
        # Weighted average
        weights = {
            'infrastructure_age': 0.20,
            'scalability': 0.18,
            'performance': 0.15,
            'disaster_recovery': 0.15,
            'geographic': 0.12,
            'compatibility': 0.12,
            'security': 0.08
        }
        
        technical_score = sum(technical_factors[factor] * weights[factor] 
                            for factor in technical_factors)
        
        return technical_score, technical_factors
    
    def calculate_operational_score(self, inputs):
        """Calculate operational factors score (0-100)."""
        operational_factors = {}
        
        # 1. IT Staff Expertise
        cloud_expertise = inputs.get('cloud_expertise_level', 'medium')  # high/medium/low
        expertise_scores = {'high': 90, 'medium': 60, 'low': 30}
        operational_factors['expertise'] = expertise_scores.get(cloud_expertise, 60)
        
        # 2. Maintenance Overhead
        current_maintenance_burden = inputs.get('maintenance_burden', 'high')  # high/medium/low
        maintenance_scores = {'high': 90, 'medium': 70, 'low': 40}  # High burden = good for cloud
        operational_factors['maintenance'] = maintenance_scores.get(current_maintenance_burden, 70)
        
        # 3. Compliance Requirements
        compliance_complexity = len(inputs.get('compliance_requirements', []))
        if compliance_complexity >= 3:
            operational_factors['compliance'] = 50  # Complex compliance might favor on-prem
        elif compliance_complexity >= 1:
            operational_factors['compliance'] = 70
        else:
            operational_factors['compliance'] = 85
        
        # 4. Backup and Recovery Complexity
        backup_complexity = inputs.get('backup_complexity', 'medium')
        backup_scores = {'high': 85, 'medium': 70, 'low': 50}
        operational_factors['backup'] = backup_scores.get(backup_complexity, 70)
        
        # 5. Monitoring and Management
        current_monitoring = inputs.get('current_monitoring_quality', 'medium')
        monitoring_scores = {'poor': 90, 'medium': 70, 'excellent': 40}
        operational_factors['monitoring'] = monitoring_scores.get(current_monitoring, 70)
        
        # 6. Change Management Capability
        change_management = inputs.get('change_management_capability', 'medium')
        change_scores = {'high': 85, 'medium': 65, 'low': 30}
        operational_factors['change_mgmt'] = change_scores.get(change_management, 65)
        
        # Weighted average
        weights = {
            'expertise': 0.25,
            'maintenance': 0.20,
            'compliance': 0.15,
            'backup': 0.15,
            'monitoring': 0.15,
            'change_mgmt': 0.10
        }
        
        operational_score = sum(operational_factors[factor] * weights[factor] 
                              for factor in operational_factors)
        
        return operational_score, operational_factors
    
    def calculate_strategic_score(self, inputs):
        """Calculate strategic factors score (0-100)."""
        strategic_factors = {}
        
        # 1. Innovation Requirements
        innovation_priority = inputs.get('innovation_priority', 'medium')  # high/medium/low
        innovation_scores = {'high': 90, 'medium': 70, 'low': 40}
        strategic_factors['innovation'] = innovation_scores.get(innovation_priority, 70)
        
        # 2. Time to Market
        time_to_market_importance = inputs.get('time_to_market_importance', 'medium')
        ttm_scores = {'high': 85, 'medium': 65, 'low': 45}
        strategic_factors['time_to_market'] = ttm_scores.get(time_to_market_importance, 65)
        
        # 3. Business Growth Projections
        growth_projection = inputs.get('business_growth_rate', 0.15)  # 15% default
        if growth_projection >= 0.30:
            strategic_factors['growth'] = 95
        elif growth_projection >= 0.20:
            strategic_factors['growth'] = 80
        elif growth_projection >= 0.10:
            strategic_factors['growth'] = 65
        else:
            strategic_factors['growth'] = 40
        
        # 4. Competitive Advantage
        cloud_competitive_advantage = inputs.get('cloud_competitive_advantage', 'medium')
        competitive_scores = {'high': 85, 'medium': 60, 'low': 30}
        strategic_factors['competitive'] = competitive_scores.get(cloud_competitive_advantage, 60)
        
        # 5. Digital Transformation Goals
        digital_transformation = inputs.get('digital_transformation_priority', 'medium')
        dt_scores = {'high': 90, 'medium': 70, 'low': 40}
        strategic_factors['digital_transformation'] = dt_scores.get(digital_transformation, 70)
        
        # 6. Vendor Lock-in Concerns
        vendor_lockin_concern = inputs.get('vendor_lockin_concern', 'medium')  # high/medium/low
        lockin_scores = {'high': 30, 'medium': 60, 'low': 85}  # High concern = lower cloud score
        strategic_factors['vendor_lockin'] = lockin_scores.get(vendor_lockin_concern, 60)
        
        # Weighted average
        weights = {
            'innovation': 0.20,
            'time_to_market': 0.18,
            'growth': 0.18,
            'competitive': 0.16,
            'digital_transformation': 0.16,
            'vendor_lockin': 0.12
        }
        
        strategic_score = sum(strategic_factors[factor] * weights[factor] 
                            for factor in strategic_factors)
        
        return strategic_score, strategic_factors
    
    def make_migration_decision(self, inputs, cloud_results):
        """
        Make comprehensive migration decision based on all factors.
        Returns decision recommendation, overall score, and detailed breakdown.
        """
        
        # Calculate scores for each category
        financial_score, financial_factors = self.calculate_financial_score(inputs, cloud_results)
        technical_score, technical_factors = self.calculate_technical_score(inputs, cloud_results)
        operational_score, operational_factors = self.calculate_operational_score(inputs)
        strategic_score, strategic_factors = self.calculate_strategic_score(inputs)
        
        # Calculate weighted overall score
        overall_score = (
            financial_score * self.decision_weights['financial'] +
            technical_score * self.decision_weights['technical'] +
            operational_score * self.decision_weights['operational'] +
            strategic_score * self.decision_weights['strategic']
        )
        
        # Determine recommendation
        if overall_score >= self.thresholds['strong_recommendation']:
            recommendation = "STRONG_MIGRATE"
            recommendation_text = "Strong Recommendation: Migrate to Cloud"
            confidence = "High"
        elif overall_score >= self.thresholds['moderate_recommendation']:
            recommendation = "MODERATE_MIGRATE" 
            recommendation_text = "Moderate Recommendation: Cloud Migration Beneficial"
            confidence = "Medium"
        elif overall_score >= self.thresholds['neutral']:
            recommendation = "NEUTRAL"
            recommendation_text = "Neutral: Evaluate Based on Priorities"
            confidence = "Medium"
        else:
            recommendation = "STAY_ON_PREMISES"
            recommendation_text = "Recommendation: Stay On-Premises"
            confidence = "Medium"
        
        # Generate key factors and risks
        key_factors = self._identify_key_factors(financial_factors, technical_factors, 
                                               operational_factors, strategic_factors)
        
        risks_and_considerations = self._identify_risks(recommendation, inputs, 
                                                      financial_factors, technical_factors)
        
        return {
            'recommendation': recommendation,
            'recommendation_text': recommendation_text,
            'overall_score': round(overall_score, 1),
            'confidence': confidence,
            'category_scores': {
                'financial': round(financial_score, 1),
                'technical': round(technical_score, 1), 
                'operational': round(operational_score, 1),
                'strategic': round(strategic_score, 1)
            },
            'detailed_factors': {
                'financial': financial_factors,
                'technical': technical_factors,
                'operational': operational_factors,
                'strategic': strategic_factors
            },
            'key_factors': key_factors,
            'risks_and_considerations': risks_and_considerations,
            'next_steps': self._generate_next_steps(recommendation)
        }
    
    def _identify_key_factors(self, financial_factors, technical_factors, 
                            operational_factors, strategic_factors):
        """Identify the most influential factors in the decision."""
        all_factors = []
        
        # Combine all factors with category labels
        for factor, score in financial_factors.items():
            all_factors.append(('Financial', factor, score))
        for factor, score in technical_factors.items():
            all_factors.append(('Technical', factor, score))
        for factor, score in operational_factors.items():
            all_factors.append(('Operational', factor, score))
        for factor, score in strategic_factors.items():
            all_factors.append(('Strategic', factor, score))
        
        # Sort by score (highest and lowest are most influential)
        all_factors.sort(key=lambda x: x[2])
        
        key_factors = {
            'top_drivers': all_factors[-3:],  # Top 3 scores (pro-cloud)
            'top_concerns': all_factors[:3]   # Bottom 3 scores (anti-cloud)
        }
        
        return key_factors
    
    def _identify_risks(self, recommendation, inputs, financial_factors, technical_factors):
        """Identify key risks based on the recommendation."""
        risks = []
        
        if recommendation in ['STRONG_MIGRATE', 'MODERATE_MIGRATE']:
            # Migration risks
            if financial_factors.get('migration_impact', 50) < 50:
                risks.append("High migration costs relative to savings")
            
            if technical_factors.get('compatibility', 80) < 60:
                risks.append("Potential application compatibility issues")
                
            if inputs.get('cloud_expertise_level') == 'low':
                risks.append("Limited cloud expertise - training required")
                
            if len(inputs.get('compliance_requirements', [])) > 2:
                risks.append("Complex compliance requirements need validation")
        
        elif recommendation == 'STAY_ON_PREMISES':
            # On-premises risks
            risks.append("Missing out on cloud innovation and agility benefits")
            risks.append("Continued infrastructure maintenance and upgrade costs")
            
            if inputs.get('infrastructure_age_years', 3) >= 4:
                risks.append("Aging infrastructure requires significant investment")
        
        return risks
    
    def _generate_next_steps(self, recommendation):
        """Generate recommended next steps based on the decision."""
        if recommendation == 'STRONG_MIGRATE':
            return [
                "Develop detailed migration roadmap and timeline",
                "Conduct pilot migration with non-critical workload",
                "Establish cloud center of excellence",
                "Begin staff training on cloud technologies",
                "Engage with AWS solutions architect for migration planning"
            ]
        elif recommendation == 'MODERATE_MIGRATE':
            return [
                "Conduct deeper cost-benefit analysis",
                "Perform proof of concept with representative workload",
                "Assess and develop cloud skills within team",
                "Evaluate specific security and compliance requirements",
                "Consider hybrid cloud approach as intermediate step"
            ]
        elif recommendation == 'NEUTRAL':
            return [
                "Define specific business objectives and priorities",
                "Gather more detailed current infrastructure costs",
                "Assess long-term business and technical strategy",
                "Consider starting with cloud-native new applications",
                "Evaluate hybrid cloud options"
            ]
        else:  # STAY_ON_PREMISES
            return [
                "Develop on-premises modernization plan",
                "Assess infrastructure refresh requirements",
                "Consider cloud-native development for new applications",
                "Evaluate specific use cases that might benefit from cloud",
                "Plan for future cloud readiness and skills development"
            ]

# END OF DECISION ENGINE CLASS INSERTION


class FirebaseAuthenticator:
    """Enhanced Firebase authentication manager with better debugging and fallback methods."""
    
    def __init__(self):
        self.firebase_app = None
        self.auth_client = None
        self.db = None
        self.initialized = False
        self.firebase_available = FIREBASE_AVAILABLE
        self.pyrebase_available = PYREBASE_AVAILABLE
        self.admin_auth_available = False
        self.debug_info = {}
        
    def debug_firebase_config(self):
        """Debug Firebase configuration and return detailed info."""
        debug_info = {
            'firebase_admin_available': self.firebase_available,
            'pyrebase_available': self.pyrebase_available,
            'secrets_available': 'firebase' in st.secrets if hasattr(st, 'secrets') else False,
            'server_config_complete': False,
            'client_config_complete': False,
            'missing_server_fields': [],
            'missing_client_fields': [],
            'admin_auth_ready': False,
            'client_auth_ready': False
        }
        
        if debug_info['secrets_available']:
            firebase_secrets = st.secrets["firebase"]
            
            # Check server-side fields
            server_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_server = [f for f in server_fields if f not in firebase_secrets or not firebase_secrets[f]]
            debug_info['missing_server_fields'] = missing_server
            debug_info['server_config_complete'] = len(missing_server) == 0
            
            # Check client-side fields
            client_fields = ['api_key', 'auth_domain', 'storage_bucket', 'messaging_sender_id', 'app_id']
            missing_client = [f for f in client_fields if f not in firebase_secrets or not firebase_secrets[f]]
            debug_info['missing_client_fields'] = missing_client
            debug_info['client_config_complete'] = len(missing_client) == 0
            
            # Determine what auth methods are ready
            debug_info['admin_auth_ready'] = (self.firebase_available and 
                                            debug_info['server_config_complete'])
            debug_info['client_auth_ready'] = (self.pyrebase_available and 
                                             debug_info['client_config_complete'] and
                                             debug_info['admin_auth_ready'])
        
        self.debug_info = debug_info
        return debug_info
    
    def initialize_firebase(self):
        """Initialize Firebase with comprehensive debugging."""
        if not self.firebase_available:
            return False
            
        if self.initialized:
            return True
            
        try:
            # Debug configuration first
            debug_info = self.debug_firebase_config()
            
            # Check if secrets are available
            if not debug_info['secrets_available']:
                return False
                
            firebase_secrets = st.secrets["firebase"]
            
            # Check for required fields for Firebase Admin SDK
            if not debug_info['server_config_complete']:
                return False
                
            # Get Firebase Admin config from Streamlit secrets
            firebase_config = {
                "type": firebase_secrets["type"],
                "project_id": firebase_secrets["project_id"],
                "private_key_id": firebase_secrets.get("private_key_id", ""),
                "private_key": firebase_secrets["private_key"].replace('\\n', '\n'),
                "client_email": firebase_secrets["client_email"],
                "client_id": firebase_secrets.get("client_id", ""),
                "auth_uri": firebase_secrets.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": firebase_secrets.get("token_uri", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": firebase_secrets.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": firebase_secrets.get("client_x509_cert_url", "")
            }
            
            # Initialize Firebase Admin
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                self.firebase_app = firebase_admin.initialize_app(cred)
            else:
                self.firebase_app = firebase_admin.get_app()
                
            # Initialize Firestore
            self.db = firestore.client()
            self.admin_auth_available = True
            
            # Try to initialize Pyrebase for client-side authentication
            if debug_info['client_config_complete'] and self.pyrebase_available:
                try:
                    pyrebase_config = {
                        "apiKey": firebase_secrets["api_key"],
                        "authDomain": firebase_secrets["auth_domain"],
                        "projectId": firebase_secrets["project_id"],
                        "storageBucket": firebase_secrets["storage_bucket"],
                        "messagingSenderId": firebase_secrets["messaging_sender_id"],
                        "appId": firebase_secrets["app_id"],
                        "databaseURL": ""  # Not using Realtime Database
                    }
                    
                    firebase_client = pyrebase.initialize_app(pyrebase_config)
                    self.auth_client = firebase_client.auth()
                    
                except Exception as e:
                    logger.warning(f"Pyrebase initialization failed: {e}")
                    self.auth_client = None
            else:
                self.auth_client = None
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            return False
    
    def sign_up_admin_only(self, email, password, display_name):
        """Create user using only Firebase Admin SDK (fallback method)."""
        if not self.firebase_available or not self.initialized or not self.admin_auth_available:
            return False, "Firebase Admin authentication not available."
            
        try:
            # Create user with Firebase Admin SDK
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=True  # Skip email verification for admin-created users
            )
            
            # Store additional user info in Firestore
            if self.db:
                user_data = {
                    'uid': user_record.uid,
                    'email': email,
                    'display_name': display_name,
                    'created_at': datetime.now(),
                    'role': 'user',
                    'last_login': datetime.now(),
                    'created_via': 'admin_sdk'
                }
                
                self.db.collection('users').document(user_record.uid).set(user_data)
            
            return True, f"Account created successfully for {email}! You can now sign in."
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message or "already exists" in error_message:
                return False, "Email already exists. Please use a different email or sign in."
            elif "WEAK_PASSWORD" in error_message:
                return False, "Password is too weak. Please use at least 6 characters."
            elif "INVALID_EMAIL" in error_message:
                return False, "Invalid email format."
            else:
                return False, f"Sign up failed: {error_message}"
    
    def sign_up(self, email, password, display_name):
        """Create a new user account with fallback to Admin SDK."""
        # Try client-side authentication first
        if self.firebase_available and self.initialized and self.auth_client:
            try:
                # Create user with email and password
                user = self.auth_client.create_user_with_email_and_password(email, password)
                
                # Send email verification
                self.auth_client.send_email_verification(user['idToken'])
                
                # Update profile with display name
                self.auth_client.update_profile(user['idToken'], display_name=display_name)
                
                # Store additional user info in Firestore (if available)
                if self.db:
                    user_data = {
                        'uid': user['localId'],
                        'email': email,
                        'display_name': display_name,
                        'created_at': datetime.now(),
                        'role': 'user',
                        'last_login': datetime.now(),
                        'created_via': 'client_sdk'
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
                    # Fall back to Admin SDK if client-side fails
                    return self.sign_up_admin_only(email, password, display_name)
        else:
            # Use Admin SDK fallback
            return self.sign_up_admin_only(email, password, display_name)
    
    def sign_in_admin_only(self, email, password):
        """Sign in using Firebase Admin SDK (verification only)."""
        if not self.firebase_available or not self.initialized or not self.admin_auth_available:
            return False, "Firebase Admin authentication not available.", None
            
        try:
            # Get user by email using Admin SDK
            user_record = auth.get_user_by_email(email)
            
            # For admin-only authentication, we create a custom token
            # Note: This is a simplified approach - in production, you'd want more secure verification
            custom_token = auth.create_custom_token(user_record.uid)
            
            # Get user data from Firestore
            user_data = {}
            if self.db:
                try:
                    user_doc = self.db.collection('users').document(user_record.uid).get()
                    user_data = user_doc.to_dict() if user_doc.exists else {}
                    
                    # Update last login
                    self.db.collection('users').document(user_record.uid).update({
                        'last_login': datetime.now()
                    })
                except Exception as e:
                    logger.warning(f"Firestore error: {e}")
            
            return True, "Sign in successful! (Admin SDK mode)", {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_data.get('display_name', user_record.display_name or ''),
                'role': user_data.get('role', 'user'),
                'id_token': custom_token.decode('utf-8'),
                'auth_method': 'admin_sdk'
            }
            
        except Exception as e:
            error_message = str(e)
            if "not found" in error_message.lower():
                return False, "Email not found. Please check your email or sign up.", None
            else:
                return False, f"Sign in failed: {error_message}", None
    
    def sign_in(self, email, password):
        """Sign in an existing user with fallback to Admin SDK."""
        # Try client-side authentication first
        if self.firebase_available and self.initialized and self.auth_client:
            try:
                user = self.auth_client.sign_in_with_email_and_password(email, password)
                
                # Get user info from Firebase Auth
                user_info = self.auth_client.get_account_info(user['idToken'])
                
                # Check if email is verified (skip for admin-created users)
                email_verified = user_info['users'][0].get('emailVerified', False)
                
                # Update last login in Firestore (if available)
                if self.db:
                    try:
                        user_doc_ref = self.db.collection('users').document(user['localId'])
                        user_doc = user_doc_ref.get()
                        
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            # If user was created via admin SDK, skip email verification
                            if user_data.get('created_via') == 'admin_sdk':
                                email_verified = True
                            
                            user_doc_ref.update({'last_login': datetime.now()})
                    except Exception as e:
                        logger.warning(f"Firestore error: {e}")
                
                if not email_verified:
                    return False, "Please verify your email before signing in.", None
                
                # Get user data from Firestore (if available)
                user_data = {}
                if self.db:
                    try:
                        user_doc = self.db.collection('users').document(user['localId']).get()
                        user_data = user_doc.to_dict() if user_doc.exists else {}
                    except Exception as e:
                        logger.warning(f"Firestore error: {e}")
                
                return True, "Sign in successful!", {
                    'uid': user['localId'],
                    'email': user_info['users'][0]['email'],
                    'display_name': user_data.get('display_name', ''),
                    'role': user_data.get('role', 'user'),
                    'id_token': user['idToken'],
                    'auth_method': 'client_sdk'
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
                    # Fall back to Admin SDK verification
                    logger.info("Client auth failed, attempting admin-only verification")
                    return self.sign_in_admin_only(email, password)
        else:
            # Use Admin SDK fallback
            return self.sign_in_admin_only(email, password)
    
    def reset_password(self, email):
        """Send password reset email."""
        if not self.firebase_available or not self.initialized or not self.auth_client:
            return False, "Password reset requires client-side authentication."
            
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

# Enhanced PDF Report Generator
class EnhancedPDFReportGenerator:
    """Enhanced PDF report generator with comprehensive enterprise features."""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab library required")
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for enterprise reports."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a365d'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#2d3748'),
        ))
    
    def generate_comprehensive_report(self, all_results):
        """Generate comprehensive PDF report with enterprise features."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
        story = []
        
        # Title page
        story.append(Paragraph("Enterprise AWS Migration Analysis Report", self.styles['CustomTitle']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.styles['Normal']))
        story.append(Spacer(1, 0.5 * inch))
        
        # Executive Summary
        if isinstance(all_results, dict):
            results_list = [all_results]
        else:
            results_list = all_results
        
        if results_list:
            story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
            
            total_workloads = len(results_list)
            total_monthly_cost = sum(
                result['recommendations']['PROD']['cost_breakdown']['total_costs'].get('on_demand', 0) 
                for result in results_list
            )
            
            # TCO Analysis
            total_migration_cost = sum(
                result['recommendations']['PROD']['tco_analysis'].get('migration_cost', 0)
                for result in results_list
            )
            
            total_annual_savings = sum(
                result['recommendations']['PROD']['tco_analysis'].get('monthly_savings', 0) * 12
                for result in results_list
            )
            
            summary_text = f"""
            This comprehensive analysis covers {total_workloads} enterprise workload(s) for AWS cloud migration.
            
            <b>Financial Summary:</b>
            • Total Monthly Cost (On-Demand): ${total_monthly_cost:,.2f}
            • Annual Cost Projection: ${total_monthly_cost * 12:,.2f}
            • Estimated Migration Cost: ${total_migration_cost:,.2f}
            • Potential Annual Savings: ${total_annual_savings:,.2f}
            
            <b>Key Recommendations:</b>
            • Consider Reserved Instances or Savings Plans for significant cost optimization
            • Implement comprehensive monitoring and auto-scaling strategies
            • Evaluate Graviton processors for compatible workloads
            • Plan migration in phases to minimize business disruption
            """
            
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(PageBreak())
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
def render_enhanced_workload_configuration():
    """Render enhanced workload configuration with enterprise features."""
    calculator = st.session_state.calculator
    st.markdown('<div class="section-header"><h3>🏗️ Enterprise Workload Configuration</h3></div>', unsafe_allow_html=True)
    
    # Basic Configuration
    with st.expander("📋 Basic Workload Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            calculator.inputs["workload_name"] = st.text_input(
                "Workload Name", 
                value=calculator.inputs["workload_name"],
                help="Descriptive name for this enterprise workload"
            )
            
            workload_options = list(calculator.WORKLOAD_PROFILES.keys())
            workload_labels = [calculator.WORKLOAD_PROFILES[k]["name"] for k in workload_options]
            current_workload_idx = workload_options.index(calculator.inputs["workload_type"])
            
            selected_workload_idx = st.selectbox(
                "Workload Type",
                range(len(workload_options)),
                index=current_workload_idx,
                format_func=lambda x: workload_labels[x],
                help="Select the primary workload pattern that best describes your application"
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
            
            # Enhanced region selection
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
                help="Select primary AWS region for deployment and pricing calculations"
            )
            calculator.inputs["region"] = region_options[selected_region_idx]
    
    selected_profile = calculator.WORKLOAD_PROFILES[calculator.inputs["workload_type"]]
    
    # Enhanced workload profile display
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"**{selected_profile['name']}**: {selected_profile['description']}")
    
    with col2:
        # Show compatibility badges
        badges = []
        if selected_profile["graviton_compatible"]:
            badges.append('<span class="sp-badge">Graviton Compatible</span>')
        if selected_profile["spot_suitable"]:
            badges.append('<span class="spot-badge">Spot Suitable</span>')
        
        if badges:
            st.markdown(f"**Compatibility:** {' '.join(badges)}", unsafe_allow_html=True)
    
    # Current Infrastructure Metrics
    with st.expander("🖥️ Current Infrastructure Metrics", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Compute Resources**")
            calculator.inputs["on_prem_cores"] = st.number_input(
                "CPU Cores", min_value=1, value=calculator.inputs["on_prem_cores"],
                help="Total number of CPU cores in your current infrastructure"
            )
            calculator.inputs["peak_cpu_percent"] = st.slider(
                "Peak CPU %", 0, 100, calculator.inputs["peak_cpu_percent"],
                help="Highest CPU utilization observed"
            )
            calculator.inputs["avg_cpu_percent"] = st.slider(
                "Average CPU %", 0, 100, calculator.inputs["avg_cpu_percent"],
                help="Typical CPU utilization"
            )
            
        with col2:
            st.markdown("**Memory Resources**")
            calculator.inputs["on_prem_ram_gb"] = st.number_input(
                "RAM (GB)", min_value=1, value=calculator.inputs["on_prem_ram_gb"],
                help="Total memory in gigabytes"
            )
            calculator.inputs["peak_ram_percent"] = st.slider(
                "Peak RAM %", 0, 100, calculator.inputs["peak_ram_percent"],
                help="Highest memory utilization observed"
            )
            calculator.inputs["avg_ram_percent"] = st.slider(
                "Average RAM %", 0, 100, calculator.inputs["avg_ram_percent"],
                help="Typical memory utilization"
            )
            
        with col3:
            st.markdown("**Storage & I/O**")
            calculator.inputs["storage_current_gb"] = st.number_input(
                "Storage (GB)", min_value=1, value=calculator.inputs["storage_current_gb"],
                help="Current total storage requirements"
            )
            calculator.inputs["peak_iops"] = st.number_input(
                "Peak IOPS", min_value=1, value=calculator.inputs["peak_iops"],
                help="Peak Input/Output Operations Per Second"
            )
            calculator.inputs["peak_throughput_mbps"] = st.number_input(
                "Peak Throughput (MB/s)", min_value=1, value=calculator.inputs["peak_throughput_mbps"],
                help="Peak data throughput in megabytes per second"
            )
    
    # Enhanced Enterprise Configuration
    with st.expander("🏢 Enterprise Configuration & Pricing Options", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💰 Pricing Strategy**")
            
            pricing_options = {
                "on_demand": "On-Demand (Pay as you go)",
                "ri_1y": "1-Year Reserved Instances",
                "ri_3y": "3-Year Reserved Instances", 
                "savings_plan_compute_1y": "1-Year Compute Savings Plan",
                "savings_plan_compute_3y": "3-Year Compute Savings Plan",
                "mixed": "Mixed Strategy (RI + On-Demand + Spot)"
            }
            
            calculator.inputs["pricing_model"] = st.selectbox(
                "Primary Pricing Model",
                list(pricing_options.keys()),
                format_func=lambda x: pricing_options[x],
                help="Choose your preferred AWS pricing strategy"
            )
            
            if selected_profile["spot_suitable"]:
                calculator.inputs["spot_percentage"] = st.slider(
                    "Spot Instance Percentage", 0, 80, calculator.inputs.get("spot_percentage", 0),
                    help="Percentage of workload suitable for Spot instances (up to 90% savings)"
                )
            
            st.markdown("**🏗️ Architecture Options**")
            calculator.inputs["enable_graviton"] = st.checkbox(
                "Enable Graviton Processors", 
                value=calculator.inputs.get("enable_graviton", True),
                help="AWS Graviton provides up to 20% better price-performance" if selected_profile["graviton_compatible"] else "Not compatible with selected workload",
                disabled=not selected_profile["graviton_compatible"]
            )
            
            calculator.inputs["prefer_amd"] = st.checkbox(
                "Prefer AMD Instances", 
                value=calculator.inputs["prefer_amd"],
                help="AMD instances typically offer 10-15% cost savings"
            )
            
        with col2:
            st.markdown("**🛡️ High Availability & Compliance**")
            calculator.inputs["multi_az"] = st.checkbox(
                "Multi-AZ Deployment", 
                value=calculator.inputs.get("multi_az", True),
                help="Deploy across multiple Availability Zones for high availability"
            )
            
            calculator.inputs["auto_scaling"] = st.checkbox(
                "Auto Scaling", 
                value=calculator.inputs.get("auto_scaling", True),
                help="Automatically scale instances based on demand"
            )
            
            # Load Balancer selection
            lb_options = {
                "alb": "Application Load Balancer (Layer 7)",
                "nlb": "Network Load Balancer (Layer 4)",
                "none": "No Load Balancer"
            }
            calculator.inputs["load_balancer"] = st.selectbox(
                "Load Balancer Type",
                list(lb_options.keys()),
                format_func=lambda x: lb_options[x],
                help="Choose appropriate load balancer for your workload"
            )
            
            # Compliance requirements
            compliance_options = list(calculator.COMPLIANCE_FRAMEWORKS.keys())
            calculator.inputs["compliance_requirements"] = st.multiselect(
                "Compliance Requirements",
                compliance_options,
                default=calculator.inputs.get("compliance_requirements", []),
                help="Select applicable compliance frameworks"
            )
    
    # Advanced Configuration
    with st.expander("⚙️ Advanced Enterprise Settings"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Growth & Scaling**")
            calculator.inputs["storage_growth_rate"] = st.number_input(
                "Annual Storage Growth Rate", min_value=0.0, max_value=1.0, 
                value=calculator.inputs["storage_growth_rate"], step=0.01, format="%.2f",
                help="Expected yearly growth in storage requirements"
            )
            calculator.inputs["years"] = st.slider(
                "Growth Projection (Years)", 1, 10, calculator.inputs["years"],
                help="Planning horizon for capacity growth"
            )
            calculator.inputs["seasonality_factor"] = st.number_input(
                "Seasonality Factor", min_value=1.0, max_value=3.0, 
                value=calculator.inputs["seasonality_factor"], step=0.1,
                help="Peak demand multiplier (1.0 = no seasonality, 2.0 = 100% peak)"
            )
            
        with col2:
            st.markdown("**🔒 Security & Monitoring**")
            monitoring_options = {
                "basic": "Basic CloudWatch",
                "detailed": "Detailed Monitoring",
                "enhanced": "Enhanced Monitoring + Custom Metrics"
            }
            calculator.inputs["monitoring_level"] = st.selectbox(
                "Monitoring Level",
                list(monitoring_options.keys()),
                format_func=lambda x: monitoring_options[x],
                help="Choose monitoring and observability level"
            )
            
            calculator.inputs["backup_retention_days"] = st.slider(
                "Backup Retention (Days)", 7, 365, 
                calculator.inputs.get("backup_retention_days", 30),
                help="Number of days to retain backups"
            )
            
            calculator.inputs["disaster_recovery"] = st.checkbox(
                "Disaster Recovery", 
                value=calculator.inputs.get("disaster_recovery", False),
                help="Enable cross-region disaster recovery capabilities"
            )
         
       
        with col3:
            st.markdown("**🌐 Network & Performance Configuration**")
            
            # VPC Configuration
            calculator.inputs["vpc_configuration"] = st.selectbox(
                "VPC Configuration",
                ["new_vpc", "existing_vpc", "default_vpc"],
                format_func=lambda x: {
                    "new_vpc": "Create New VPC",
                    "existing_vpc": "Use Existing VPC",
                    "default_vpc": "Use Default VPC"
                }.get(x, x),
                help="Choose VPC deployment strategy"
            )
            
            # Subnet Strategy
            calculator.inputs["subnet_strategy"] = st.selectbox(
                "Subnet Strategy",
                ["multi_az_private", "multi_az_public", "single_az", "hybrid"],
                format_func=lambda x: {
                    "multi_az_private": "Multi-AZ Private Subnets",
                    "multi_az_public": "Multi-AZ Public Subnets", 
                    "single_az": "Single AZ Deployment",
                    "hybrid": "Hybrid (Public + Private)"
                }.get(x, x),
                help="Select subnet deployment strategy"
            )
            
            # Internet Connectivity
            calculator.inputs["internet_connectivity"] = st.selectbox(
                "Internet Connectivity",
                ["internet_gateway", "nat_gateway", "nat_instance", "no_internet"],
                format_func=lambda x: {
                    "internet_gateway": "Internet Gateway (Direct)",
                    "nat_gateway": "NAT Gateway (Private)",
                    "nat_instance": "NAT Instance (Cost-Optimized)",
                    "no_internet": "No Internet Access"
                }.get(x, x),
                help="Choose internet connectivity method"
            )
            
            # Network Performance
            calculator.inputs["network_performance"] = st.selectbox(
                "Network Performance Requirements",
                ["standard", "enhanced", "sr_iov", "placement_group"],
                format_func=lambda x: {
                    "standard": "Standard Networking",
                    "enhanced": "Enhanced Networking",
                    "sr_iov": "SR-IOV Enabled",
                    "placement_group": "Cluster Placement Group"
                }.get(x, x),
                help="Select network performance optimization"
            )
            
            # Security Groups
            calculator.inputs["security_group_rules"] = st.number_input(
                "Estimated Security Group Rules",
                min_value=5, max_value=100,
                value=calculator.inputs.get("security_group_rules", 20),
                help="Approximate number of security group rules needed"
            )
            
            # VPC Endpoints
            vpc_endpoints = st.multiselect(
                "VPC Endpoints Required",
                ["s3", "dynamodb", "ec2", "ssm", "kms", "cloudwatch", "sns", "sqs"],
                default=calculator.inputs.get("vpc_endpoints", ["s3", "ec2"]),
                help="Select AWS services requiring VPC endpoints"
            )
            calculator.inputs["vpc_endpoints"] = vpc_endpoints
            
            # Advanced Network Features
            with st.expander("🔧 Advanced Network Features"):
                
                # Transit Gateway
                calculator.inputs["transit_gateway"] = st.checkbox(
                    "Transit Gateway Integration",
                    value=calculator.inputs.get("transit_gateway", False),
                    help="Connect to Transit Gateway for multi-VPC connectivity"
                )
                
                # Direct Connect
                calculator.inputs["direct_connect"] = st.checkbox(
                    "AWS Direct Connect",
                    value=calculator.inputs.get("direct_connect", False),
                    help="Dedicated network connection to AWS"
                )
                
                # VPN Connection
                calculator.inputs["vpn_connection"] = st.checkbox(
                    "Site-to-Site VPN",
                    value=calculator.inputs.get("vpn_connection", False),
                    help="VPN connection to on-premises network"
                )
                
                # CloudFront
                calculator.inputs["cloudfront_distribution"] = st.checkbox(
                    "CloudFront Distribution",
                    value=calculator.inputs.get("cloudfront_distribution", False),
                    help="Content delivery network for global performance"
                )
                
                # Route 53
                calculator.inputs["route53_hosted_zone"] = st.checkbox(
                    "Route 53 Hosted Zone",
                    value=calculator.inputs.get("route53_hosted_zone", False),
                    help="DNS management with Route 53"
                )
                
                # Network Load Balancer Features
                if calculator.inputs.get("load_balancer") in ["alb", "nlb"]:
                    calculator.inputs["lb_cross_zone"] = st.checkbox(
                        "Cross-Zone Load Balancing",
                        value=calculator.inputs.get("lb_cross_zone", True),
                        help="Distribute traffic evenly across AZs"
                    )
                    
                    calculator.inputs["lb_deletion_protection"] = st.checkbox(
                        "Load Balancer Deletion Protection",
                        value=calculator.inputs.get("lb_deletion_protection", True),
                        help="Prevent accidental load balancer deletion"
                    )
                
                # Network Monitoring
                calculator.inputs["vpc_flow_logs"] = st.checkbox(
                    "VPC Flow Logs",
                    value=calculator.inputs.get("vpc_flow_logs", False),
                    help="Enable VPC Flow Logs for network monitoring"
                )
                
                # Bandwidth Requirements
                calculator.inputs["bandwidth_requirements"] = st.selectbox(
                    "Bandwidth Requirements",
                    ["standard", "high", "very_high", "dedicated"],
                    format_func=lambda x: {
                        "standard": "Standard (Up to 5 Gbps)",
                        "high": "High (5-10 Gbps)",
                        "very_high": "Very High (10-25 Gbps)",
                        "dedicated": "Dedicated Tenancy"
                    }.get(x, x),
                    help="Expected network bandwidth requirements"
                )
                
                # Network Latency Requirements
                calculator.inputs["latency_requirements"] = st.selectbox(
                    "Latency Requirements",
                    ["standard", "low", "ultra_low"],
                    format_func=lambda x: {
                        "standard": "Standard (< 100ms)",
                        "low": "Low Latency (< 10ms)",
                        "ultra_low": "Ultra Low (< 1ms)"
                    }.get(x, x),
                    help="Application latency requirements"
                )

    # Network Cost Calculation Function (add this after the class definition)
    def calculate_network_costs(self, calculator_inputs):
        """Calculate network-related costs based on configuration."""
        network_costs = {}
        
        # VPC Costs (mostly free, but some components have costs)
        vpc_cost = 0.0
        
        # Internet Gateway (free)
        if calculator_inputs.get("internet_connectivity") == "internet_gateway":
            vpc_cost += 0.0
        
        # NAT Gateway costs
        elif calculator_inputs.get("internet_connectivity") == "nat_gateway":
            # NAT Gateway: $0.045/hour + $0.045/GB processed
            nat_gateway_cost = 0.045 * 24 * 30  # Monthly cost
            estimated_data_gb = 100  # Estimate based on workload
            nat_data_cost = estimated_data_gb * 0.045
            vpc_cost += nat_gateway_cost + nat_data_cost
        
        # NAT Instance costs (EC2 instance cost - handled separately)
        elif calculator_inputs.get("internet_connectivity") == "nat_instance":
            # t3.micro for NAT instance
            vpc_cost += 0.0104 * 24 * 30  # ~$7.50/month
        
        # VPC Endpoints
        vpc_endpoints = calculator_inputs.get("vpc_endpoints", [])
        if vpc_endpoints:
            # $0.01/hour per endpoint + data processing
            endpoint_cost = len(vpc_endpoints) * 0.01 * 24 * 30
            # Estimated data processing: $0.01/GB
            endpoint_data_cost = 50 * 0.01  # Assume 50GB/month
            vpc_cost += endpoint_cost + endpoint_data_cost
        
        network_costs["vpc_networking"] = round(vpc_cost, 2)
        
        # Transit Gateway costs
        if calculator_inputs.get("transit_gateway"):
            # $36/month per attachment + data processing
            tgw_cost = 36.0 + (100 * 0.02)  # Assume 100GB/month processing
            network_costs["transit_gateway"] = round(tgw_cost, 2)
        
        # Direct Connect costs
        if calculator_inputs.get("direct_connect"):
            # 1Gbps dedicated connection: ~$300/month
            network_costs["direct_connect"] = 300.0
        
        # Site-to-Site VPN costs
        if calculator_inputs.get("vpn_connection"):
            # $36/month per VPN connection
            network_costs["vpn_connection"] = 36.0
        
        # CloudFront costs
        if calculator_inputs.get("cloudfront_distribution"):
            # Estimate based on data transfer
            estimated_requests = 1000000  # 1M requests/month
            estimated_data_gb = 100       # 100GB/month
            
            request_cost = estimated_requests * 0.0000012  # $0.0000012 per request
            data_cost = estimated_data_gb * 0.085         # $0.085/GB
            network_costs["cloudfront"] = round(request_cost + data_cost, 2)
        
        # Route 53 costs
        if calculator_inputs.get("route53_hosted_zone"):
            # $0.50 per hosted zone + query costs
            hosted_zone_cost = 0.50
            query_cost = 1000000 * 0.0000004  # 1M queries at $0.0000004 each
            network_costs["route53"] = round(hosted_zone_cost + query_cost, 2)
        
        # VPC Flow Logs costs
        if calculator_inputs.get("vpc_flow_logs"):
            # Estimate based on instance count and data volume
            flow_logs_cost = 50 * 0.50  # Assume 50GB logs at $0.50/GB
            network_costs["vpc_flow_logs"] = round(flow_logs_cost, 2)
        
        return network_costs

    # Network Requirements Analysis Function
    def analyze_network_requirements(self, calculator_inputs, workload_profile):
        """Analyze and recommend network configuration based on workload."""
        recommendations = []
        
        workload_type = calculator_inputs.get("workload_type", "")
        multi_az = calculator_inputs.get("multi_az", False)
        compliance_reqs = calculator_inputs.get("compliance_requirements", [])
        
        # VPC Recommendations
        if workload_type == "database_server":
            recommendations.append("Private subnets recommended for database servers")
            recommendations.append("Consider VPC endpoints for S3 and other AWS services")
        
        if workload_type == "web_application":
            recommendations.append("Public subnets with Internet Gateway for web servers")
            recommendations.append("Consider CloudFront for global content delivery")
        
        # Multi-AZ recommendations
        if multi_az:
            recommendations.append("Deploy across multiple Availability Zones for high availability")
            recommendations.append("Use Application Load Balancer for cross-AZ traffic distribution")
        
        # Compliance recommendations
        if compliance_reqs:
            recommendations.append("Private subnets recommended for compliance requirements")
            recommendations.append("Enable VPC Flow Logs for audit and monitoring")
            recommendations.append("Consider AWS PrivateLink for secure service connectivity")
        
        # Performance recommendations
        bandwidth_req = calculator_inputs.get("bandwidth_requirements", "standard")
        if bandwidth_req in ["high", "very_high"]:
            recommendations.append("Consider Enhanced Networking for high bandwidth applications")
            recommendations.append("Use placement groups for low-latency communication")
        
        latency_req = calculator_inputs.get("latency_requirements", "standard")
        if latency_req in ["low", "ultra_low"]:
            recommendations.append("Deploy in single AZ or use placement groups for ultra-low latency")
            recommendations.append("Consider dedicated tenancy for consistent performance")
        
        # Security recommendations
        if len(calculator_inputs.get("vpc_endpoints", [])) > 0:
            recommendations.append("VPC endpoints reduce data transfer costs and improve security")
        
        return recommendations

    # Network Cost Optimization Function
    def optimize_network_costs(self, calculator_inputs, current_costs):
        """Provide network cost optimization recommendations."""
        optimizations = []
        
        # NAT Gateway optimization
        if calculator_inputs.get("internet_connectivity") == "nat_gateway":
            optimizations.append({
                "recommendation": "Consider NAT Instance for lower cost",
                "potential_savings": "Up to 80% reduction in NAT costs",
                "trade_off": "Requires more management overhead"
            })
        
        # VPC Endpoints optimization
        vpc_endpoints = calculator_inputs.get("vpc_endpoints", [])
        if not vpc_endpoints and calculator_inputs.get("workload_type") in ["database_server", "application_server"]:
            optimizations.append({
                "recommendation": "Add VPC endpoints for S3 and DynamoDB",
                "potential_savings": "Reduce data transfer charges",
                "trade_off": "Small hourly endpoint cost"
            })
        
        # CloudFront optimization
        if not calculator_inputs.get("cloudfront_distribution") and calculator_inputs.get("workload_type") == "web_application":
            optimizations.append({
                "recommendation": "Consider CloudFront for global content delivery",
                "potential_savings": "Reduce bandwidth costs and improve performance",
                "trade_off": "Additional complexity in cache management"
            })
        
        # Direct Connect vs VPN
        if calculator_inputs.get("vpn_connection") and not calculator_inputs.get("direct_connect"):
            optimizations.append({
                "recommendation": "Evaluate Direct Connect for high data transfer volumes",
                "potential_savings": "Significant savings on data transfer > 1TB/month",
                "trade_off": "Higher monthly fixed cost"
            })
        
        return optimizations
    # ADD MIGRATION DECISION INPUTS
    st.markdown("---")
    render_migration_decision_inputs()
    
    # ENHANCED ANALYSIS BUTTON
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Generate Enterprise Analysis", type="primary", key="generate_single"):
            with st.spinner("🔄 Analyzing workload with enterprise features..."):
                try:
                    results = {}
                    for env in calculator.ENV_MULTIPLIERS.keys():
                        results[env] = calculator.calculate_comprehensive_requirements(env)
                    
                    st.session_state.analysis_results = {
                        'inputs': calculator.inputs.copy(),
                        'recommendations': results
                    }
                    
                    st.success("✅ Enterprise analysis completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    import traceback
                    st.text(traceback.format_exc())
    
    with col2:
        if st.button("🎯 Complete Analysis with Migration Decision", type="primary", key="generate_with_decision"):
            with st.spinner("🔄 Analyzing workload and migration decision factors..."):
                try:
                    # Generate cloud analysis
                    results = {}
                    for env in calculator.ENV_MULTIPLIERS.keys():
                        results[env] = calculator.calculate_comprehensive_requirements(env)
                    
                    # Generate migration decision
                    decision_result = enhanced_migration_decision_analysis(
                        calculator.inputs, 
                        results['PROD']
                    )
                    
                    st.session_state.analysis_results = {
                        'inputs': calculator.inputs.copy(),
                        'recommendations': results,
                        'migration_decision': decision_result
                    }
                    
                    st.success("✅ Complete analysis with migration decision completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    import traceback
                    st.text(traceback.format_exc())

# END OF FUNCTION MODIFICATION

def render_enhanced_analysis_results(results):
    """Render enhanced analysis results with enterprise features."""
    st.markdown('<div class="section-header"><h3>📊 Enterprise Analysis Results</h3></div>', unsafe_allow_html=True)
    
    # Enterprise Summary Cards
    prod_results = results['PROD']
    tco_analysis = prod_results['tco_analysis']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Best Monthly Cost</div>
            <div class="metric-value">${tco_analysis['monthly_cost']:,.0f}</div>
            <div class="metric-description">{tco_analysis['best_pricing_option'].replace('_', ' ').title()}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Annual Savings</div>
            <div class="metric-value">${tco_analysis['monthly_savings'] * 12:,.0f}</div>
            <div class="metric-description">{tco_analysis['savings_percentage']}% vs On-Demand</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        roi_color = "green" if isinstance(tco_analysis['roi_3_years'], (int, float)) and tco_analysis['roi_3_years'] > 100 else "orange"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">3-Year ROI</div>
            <div class="metric-value" style="color: {roi_color}">{tco_analysis['roi_3_years']}%</div>
            <div class="metric-description">Return on Investment</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        break_even = tco_analysis['break_even_months']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Break-Even</div>
            <div class="metric-value">{break_even}</div>
            <div class="metric-description">Months to recover migration cost</div>
        </div>
        """, unsafe_allow_html=True)
    
    # TCO Savings Highlight
    if tco_analysis['monthly_savings'] > 0:
        st.markdown(f"""
        <div class="savings-highlight">
            💰 <strong>Potential Savings:</strong> ${tco_analysis['monthly_savings']:,.2f}/month 
            (${tco_analysis['monthly_savings'] * 12:,.2f}/year) by switching to {tco_analysis['best_pricing_option'].replace('_', ' ').title()}
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced Cost Breakdown
    st.subheader("💰 Comprehensive Cost Analysis")
    
    # Cost comparison across pricing models
    cost_breakdown = prod_results['cost_breakdown']
    total_costs = cost_breakdown['total_costs']
    
    # Create cost comparison chart
    cost_data = []
    for pricing_model, cost in total_costs.items():
        model_name = pricing_model.replace('_', ' ').title()
        savings = ((total_costs.get('on_demand', cost) - cost) / total_costs.get('on_demand', cost) * 100) if total_costs.get('on_demand', 0) > 0 else 0
        cost_data.append({
            'Pricing Model': model_name,
            'Monthly Cost': cost,
            'Savings %': round(savings, 1)
        })
    
    df_costs = pd.DataFrame(cost_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_costs = px.bar(df_costs, x='Pricing Model', y='Monthly Cost',
                          title='Cost Comparison by Pricing Model',
                          color='Monthly Cost', color_continuous_scale='RdYlGn_r')
        fig_costs.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_costs, use_container_width=True)
    
    with col2:
        fig_savings = px.bar(df_costs, x='Pricing Model', y='Savings %',
                           title='Savings Percentage vs On-Demand',
                           color='Savings %', color_continuous_scale='RdYlGn')
        fig_savings.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_savings, use_container_width=True)
    
    # Detailed cost breakdown
    st.subheader("🔍 Detailed Cost Breakdown")
    
    # Create detailed breakdown table
    breakdown_data = []
    for cost_category, costs in cost_breakdown.items():
        if cost_category == 'total_costs':
            continue
        if isinstance(costs, dict):
            for subcategory, amount in costs.items():
                breakdown_data.append({
                    'Category': cost_category.replace('_', ' ').title(),
                    'Service': subcategory.replace('_', ' ').title(),
                    'Monthly Cost': f"${amount:,.2f}",
                    'Annual Cost': f"${amount * 12:,.2f}"
                })
    
    if breakdown_data:
        df_breakdown = pd.DataFrame(breakdown_data)
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
    
    # Environment comparison
    st.subheader("🏢 Multi-Environment Analysis")
    
    env_data = []
    for env, env_results in results.items():
        instance_options = env_results['instance_options']
        primary_instance = instance_options.get('balanced', instance_options.get('cost_optimized', {}))
        
        env_data.append({
            'Environment': env,
            'Instance Type': primary_instance.get('type', 'N/A'),
            'vCPUs': env_results['requirements']['vCPUs'],
            'RAM (GB)': env_results['requirements']['RAM_GB'],
            'Storage (GB)': env_results['requirements']['storage_GB'],
            'Monthly Cost': f"${env_results['cost_breakdown']['total_costs'].get('on_demand', 0):,.2f}",
            'Multi-AZ': '✅' if env_results['requirements']['multi_az'] else '❌'
        })
    
    df_env = pd.DataFrame(env_data)
    st.dataframe(df_env, use_container_width=True, hide_index=True)
    
    # Instance recommendations
    st.subheader("🖥️ Instance Recommendations")
    
    instance_options = prod_results['instance_options']
    
    for scenario, instance in instance_options.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            processor_badge = ""
            if instance['processor'] == 'Graviton':
                processor_badge = '<span class="sp-badge">Graviton (ARM)</span>'
            elif instance['processor'] == 'AMD':
                processor_badge = '<span class="ri-badge">AMD</span>'
            else:
                processor_badge = '<span class="metric-description">Intel</span>'
            
            st.markdown(f"""
            <div class="cost-comparison-card">
                <h4>{scenario.replace('_', ' ').title()} Option</h4>
                <p><strong>Instance:</strong> {instance['type']} {processor_badge}</p>
                <p><strong>Specs:</strong> {instance['vCPU']} vCPUs, {instance['RAM']} GB RAM</p>
                <p><strong>Network:</strong> {instance['network']}</p>
                <p><strong>Family:</strong> {instance['family'].title()}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Show cost for this instance type
            instance_cost = cost_breakdown['instance_costs'].get('on_demand', 0)
            st.metric("Monthly Cost", f"${instance_cost:,.2f}")
    
    # Optimization Recommendations
    st.subheader("🎯 Optimization Recommendations")
    
    recommendations = prod_results['optimization_recommendations']
    
    for i, recommendation in enumerate(recommendations):
        st.markdown(f"**{i+1}.** {recommendation}")
    
    # Risk Assessment
    risk_assessment = prod_results['risk_assessment']
    
    st.subheader("⚠️ Migration Risk Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        risk_level = risk_assessment['overall_risk']
        risk_class = f"risk-{risk_level.lower()}"
        
        st.markdown(f"""
        <div class="risk-indicator {risk_class}">
            Overall Risk Level: {risk_level}
        </div>
        """, unsafe_allow_html=True)
        
        if risk_assessment['risk_factors']:
            st.markdown("**Risk Factors:**")
            for factor in risk_assessment['risk_factors']:
                st.markdown(f"• {factor}")
    
    with col2:
        if risk_assessment['mitigation_strategies']:
            st.markdown("**Mitigation Strategies:**")
            for strategy in risk_assessment['mitigation_strategies']:
                st.markdown(f"• {strategy}")
    
    # Compliance Information
    compliance = prod_results['compliance']
    if compliance['requirements']:
        st.subheader("🛡️ Compliance Requirements")
        
        for req in compliance['requirements']:
            if req in st.session_state.calculator.COMPLIANCE_FRAMEWORKS:
                framework = st.session_state.calculator.COMPLIANCE_FRAMEWORKS[req]
                
                with st.expander(f"{framework['name']} - {framework['description']}"):
                    st.markdown("**Requirements:**")
                    for requirement in framework['requirements']:
                        st.markdown(f"• {requirement}")
                    
                    cost_impact = (framework['additional_cost_factor'] - 1) * 100
                    st.markdown(f"**Cost Impact:** +{cost_impact:.1f}% additional cost")

def render_migration_planning():
    """Render migration planning interface."""
    st.markdown('<div class="section-header"><h3>🚀 Migration Planning & Timeline</h3></div>', unsafe_allow_html=True)
    
    if not st.session_state.analysis_results:
        st.info("💡 Please run a workload analysis first to access migration planning features.")
        return
    
    results = st.session_state.analysis_results['recommendations']
    
    # Migration phases
    phases = [
        {
            "name": "Assessment & Planning",
            "duration": "2-4 weeks",
            "description": "Infrastructure discovery, dependency mapping, and detailed migration planning",
            "tasks": [
                "Complete infrastructure inventory",
                "Map application dependencies",
                "Create detailed migration plan",
                "Set up AWS accounts and basic networking"
            ]
        },
        {
            "name": "Pilot Migration",
            "duration": "2-3 weeks", 
            "description": "Migrate non-critical workloads to validate approach and tooling",
            "tasks": [
                "Migrate development environment",
                "Test backup and restore procedures",
                "Validate monitoring and alerting",
                "Fine-tune security configurations"
            ]
        },
        {
            "name": "Production Migration",
            "duration": "4-8 weeks",
            "description": "Migrate production workloads with minimal downtime",
            "tasks": [
                "Execute production cutover",
                "Validate application functionality",
                "Optimize performance and costs",
                "Implement auto-scaling policies"
            ]
        },
        {
            "name": "Optimization",
            "duration": "2-4 weeks",
            "description": "Post-migration optimization and cost management",
            "tasks": [
                "Right-size instances based on actual usage",
                "Implement Reserved Instances/Savings Plans",
                "Optimize storage and networking",
                "Final security and compliance validation"
            ]
        }
    ]
    
    for i, phase in enumerate(phases):
        st.markdown(f"""
        <div class="migration-phase">
            <h4>Phase {i+1}: {phase['name']} ({phase['duration']})</h4>
            <p>{phase['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"Phase {i+1} Tasks"):
            for task in phase['tasks']:
                st.markdown(f"✓ {task}")
    
    # Timeline visualization
    st.subheader("📅 Migration Timeline")
    
    # Create Gantt chart data
    import datetime as dt
    start_date = dt.datetime.now()
    
    timeline_data = []
    current_date = start_date
    
    for i, phase in enumerate(phases):
        weeks = int(phase['duration'].split('-')[1].split()[0])  # Get max weeks
        end_date = current_date + timedelta(weeks=weeks)
        
        timeline_data.append({
            'Phase': phase['name'],
            'Start': current_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d'),
            'Duration': f"{weeks} weeks"
        })
        
        current_date = end_date
    
    df_timeline = pd.DataFrame(timeline_data)
    st.dataframe(df_timeline, use_container_width=True, hide_index=True)
    
    # Cost-benefit timeline
    st.subheader("💰 Cost-Benefit Timeline")
    
    tco_analysis = results['PROD']['tco_analysis']
    monthly_savings = tco_analysis['monthly_savings']
    migration_cost = tco_analysis['migration_cost']
    
    # Calculate cumulative savings over time
    months = list(range(0, 37))  # 3 years
    cumulative_savings = []
    cumulative_cost = [migration_cost]  # Start with migration cost
    
    for month in months:
        if month == 0:
            cumulative_savings.append(-migration_cost)
        else:
            cumulative_savings.append(cumulative_savings[-1] + monthly_savings)
        
        if month > 0:
            cumulative_cost.append(cumulative_cost[-1] + tco_analysis['monthly_cost'])
    
    # Create cost-benefit chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=months,
        y=cumulative_savings,
        mode='lines+markers',
        name='Cumulative Savings',
        line=dict(color='green', width=3)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="red", 
                  annotation_text="Break-even point")
    
    fig.update_layout(
        title="Cumulative Savings Over Time",
        xaxis_title="Months from Migration Start",
        yaxis_title="Cumulative Savings ($)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def initialize_session_state():
    """Initialize session state with enhanced features."""
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

def render_authentication():
    """Render enhanced authentication interface with detailed debugging."""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise AWS Workload Sizing Platform v4.0</h1>
        <span class="enterprise-badge">Enterprise Edition</span>
        <p>Advanced cloud migration planning with Reserved Instances, Savings Plans, and comprehensive TCO analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Firebase
    if 'firebase_auth' not in st.session_state:
        st.session_state.firebase_auth = FirebaseAuthenticator()
    
    firebase_auth = st.session_state.firebase_auth
    
    # Check if Firebase libraries are available
    if not firebase_auth.firebase_available:
        st.markdown("""
        <div class="demo-banner">
            🔧 <strong>Demo Mode</strong> - Firebase authentication libraries not available. You can use all enterprise features without authentication.
        </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 To enable full authentication, install Firebase dependencies: `pip install firebase-admin pyrebase4`")
        
        if st.button("🚀 Continue to Enterprise Platform", type="primary"):
            st.session_state.authenticated = True
            st.session_state.demo_mode = True
            st.session_state.user_info = {
                'display_name': 'Enterprise Demo User',
                'email': 'demo@enterprise.com',
                'role': 'demo'
            }
            st.rerun()
        return False
    
    # Try to initialize Firebase
    firebase_initialized = firebase_auth.initialize_firebase()
    
    if not firebase_initialized:
        st.markdown("""
        <div class="demo-banner">
            🔧 <strong>Demo Mode</strong> - Firebase configuration incomplete. You can use all enterprise features without authentication.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Continue to Enterprise Platform (Demo Mode)", type="primary"):
            st.session_state.authenticated = True
            st.session_state.demo_mode = True
            st.session_state.user_info = {
                'display_name': 'Enterprise Demo User',
                'email': 'demo@enterprise.com',
                'role': 'demo'
            }
            st.rerun()
        return False
    
    # Check if user is already authenticated
    if st.session_state.get('authenticated', False):
        return True
    
    # Authentication tabs with enhanced styling
    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔐 Sign In", "📝 Sign Up", "🚀 Demo Mode"])
    
    with auth_tab1:
        render_sign_in(firebase_auth)
    
    with auth_tab2:
        render_sign_up(firebase_auth)
        
    with auth_tab3:
        st.markdown("""
        <div class="auth-container">
            <h3 style="text-align: center; margin-bottom: 1rem;">Enterprise Demo Mode</h3>
            <p>Experience the full enterprise platform without authentication. All advanced features including Reserved Instances, Savings Plans, and TCO analysis are available.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Enter Enterprise Demo Mode", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.demo_mode = True
            st.session_state.user_info = {
                'display_name': 'Enterprise Demo User',
                'email': 'demo@enterprise.com',
                'role': 'demo'
            }
            st.success("Welcome to Enterprise Demo Mode!")
            time.sleep(1)
            st.rerun()
    
    return False

def render_sign_in(firebase_auth):
    """Render sign in form."""
    st.markdown("""
    <div class="auth-container">
        <h3 style="text-align: center; margin-bottom: 1rem;">Enterprise Sign In</h3>
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
                        if 'id_token' in user_data:
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
        <h3 style="text-align: center; margin-bottom: 1rem;">Create Enterprise Account</h3>
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
                    else:
                        st.error(message)

def render_user_info():
    """Render user information in sidebar."""
    if st.session_state.get('authenticated', False):
        user_info = st.session_state.get('user_info', {})
        is_demo = st.session_state.get('demo_mode', False)
        
        if is_demo:
            st.markdown(f"""
            <div class="user-info">
                <strong>👤 {user_info.get('display_name', 'Enterprise Demo User')}</strong><br>
                <small>{user_info.get('email', 'demo@enterprise.com')}</small><br>
                <span class="status-badge status-demo">Enterprise Demo</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            auth_method = user_info.get('auth_method', 'unknown')
            auth_badge = "🔐 Full Auth" if auth_method == "client_sdk" else "⚡ Admin Auth"
            
            st.markdown(f"""
            <div class="user-info">
                <strong>👤 {user_info.get('display_name', 'User')}</strong><br>
                <small>{user_info.get('email', '')}</small><br>
                <small>Role: {user_info.get('role', 'user').title()}</small><br>
                <small>{auth_badge}</small>
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

# Main application
def main():
    """Main application entry point with enhanced enterprise features."""
    initialize_session_state()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        if not render_authentication():
            return
    
    # Show demo mode banner if applicable
    if st.session_state.get('demo_mode', False):
        st.markdown("""
        <div class="demo-banner">
            🔧 <strong>Enterprise Demo Mode Active</strong> - Full functionality including Reserved Instances, Savings Plans, and advanced TCO analysis
        </div>
        """, unsafe_allow_html=True)
    
    # Main application header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise AWS Workload Sizing Platform v4.0</h1>
        <span class="enterprise-badge">Enterprise Edition</span>
        <p>Advanced cloud migration planning with Reserved Instances, Savings Plans, comprehensive TCO analysis, and enterprise-grade features</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🔧 Enterprise Configuration")
        
        # User info
        render_user_info()
        
        calculator = st.session_state.calculator
        
        # AWS Connection Status
        try:
            cred_status, cred_message = calculator.validate_aws_credentials()
        except:
            cred_status, cred_message = False, "❌ AWS credentials validation failed"
        
        if cred_status:
            st.markdown(f'<span class="status-badge status-success">AWS Connected</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="status-badge status-error">AWS Not Connected</span>', unsafe_allow_html=True)
        
        st.markdown(f"<small>{cred_message}</small>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Quick Enterprise Stats
        if st.session_state.analysis_results or st.session_state.bulk_results:
            st.markdown("### 📈 Enterprise Analytics")
            
            if st.session_state.bulk_results:
                total_workloads = len(st.session_state.bulk_results)
                total_cost = sum(r['recommendations']['PROD']['cost_breakdown']['total_costs'].get('on_demand', 0) for r in st.session_state.bulk_results)
                total_savings = sum(r['recommendations']['PROD']['tco_analysis']['monthly_savings'] for r in st.session_state.bulk_results)
            else:
                total_workloads = 1
                total_cost = st.session_state.analysis_results['recommendations']['PROD']['cost_breakdown']['total_costs'].get('on_demand', 0)
                total_savings = st.session_state.analysis_results['recommendations']['PROD']['tco_analysis']['monthly_savings']
            
            st.metric("Workloads Analyzed", total_workloads)
            st.metric("Monthly Cost (On-Demand)", f"${total_cost:,.2f}")
            st.metric("Potential Monthly Savings", f"${total_savings:,.2f}")
            st.metric("Annual Savings Potential", f"${total_savings * 12:,.2f}")
        
        st.markdown("---")
        st.markdown("""
        ### 🚀 Enterprise Features
        
        **Advanced Pricing:**
        - Reserved Instances (1Y & 3Y)
        - Savings Plans (Compute & EC2)
        - Spot Instance Integration
        - Mixed Pricing Strategies
        
        **Enterprise Architecture:**
        - Multi-AZ Deployments
        - Graviton Processor Support
        - Auto Scaling Integration
        - Load Balancer Optimization
        
        **Compliance & Security:**
        - SOC 2, PCI-DSS, HIPAA, FedRAMP
        - Enhanced Monitoring Options
        - Disaster Recovery Planning
        - Security Best Practices
        
        **Advanced Analytics:**
        - Total Cost of Ownership (TCO)
        - ROI Calculations
        - Migration Risk Assessment
        - Optimization Recommendations
        """)
    
    # Enhanced tab structure
    # FIND the main() function (around line 2100-2200)
# REPLACE the existing tab structure with this enhanced version:

def main():
    """Main application entry point with enhanced enterprise features."""
    initialize_session_state()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        if not render_authentication():
            return
    
    # Show demo mode banner if applicable
    if st.session_state.get('demo_mode', False):
        st.markdown("""
        <div class="demo-banner">
            🔧 <strong>Enterprise Demo Mode Active</strong> - Full functionality including Reserved Instances, Savings Plans, and advanced TCO analysis
        </div>
        """, unsafe_allow_html=True)
    
    # Main application header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise AWS Workload Sizing Platform v4.0</h1>
        <span class="enterprise-badge">Enterprise Edition</span>
        <p>Advanced cloud migration planning with Reserved Instances, Savings Plans, comprehensive TCO analysis, and intelligent migration decisions</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🔧 Enterprise Configuration")
        
        # User info
        render_user_info()
        
        calculator = st.session_state.calculator
        
        # AWS Connection Status
        try:
            cred_status, cred_message = calculator.validate_aws_credentials()
        except:
            cred_status, cred_message = False, "❌ AWS credentials validation failed"
        
        if cred_status:
            st.markdown(f'<span class="status-badge status-success">AWS Connected</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="status-badge status-error">AWS Not Connected</span>', unsafe_allow_html=True)
        
        st.markdown(f"<small>{cred_message}</small>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Quick Enterprise Stats
        if st.session_state.analysis_results or st.session_state.bulk_results:
            st.markdown("### 📈 Enterprise Analytics")
            
            if st.session_state.bulk_results:
                total_workloads = len(st.session_state.bulk_results)
                total_cost = sum(r['recommendations']['PROD']['cost_breakdown']['total_costs'].get('on_demand', 0) for r in st.session_state.bulk_results)
                total_savings = sum(r['recommendations']['PROD']['tco_analysis']['monthly_savings'] for r in st.session_state.bulk_results)
            else:
                total_workloads = 1
                total_cost = st.session_state.analysis_results['recommendations']['PROD']['cost_breakdown']['total_costs'].get('on_demand', 0)
                total_savings = st.session_state.analysis_results['recommendations']['PROD']['tco_analysis']['monthly_savings']
            
            st.metric("Workloads Analyzed", total_workloads)
            st.metric("Monthly Cost (On-Demand)", f"${total_cost:,.2f}")
            st.metric("Potential Monthly Savings", f"${total_savings:,.2f}")
            st.metric("Annual Savings Potential", f"${total_savings * 12:,.2f}")
            
            # Show migration decision if available
            if (st.session_state.analysis_results and 
                'migration_decision' in st.session_state.analysis_results):
                decision = st.session_state.analysis_results['migration_decision']
                recommendation = decision['recommendation']
                
                if recommendation == "STRONG_MIGRATE":
                    st.success(f"🚀 Strong Migration Recommendation ({decision['overall_score']}/100)")
                elif recommendation == "MODERATE_MIGRATE":
                    st.info(f"✅ Moderate Migration Recommendation ({decision['overall_score']}/100)")
                elif recommendation == "NEUTRAL":
                    st.warning(f"⚖️ Neutral Decision ({decision['overall_score']}/100)")
                else:
                    st.error(f"🏢 Stay On-Premises Recommended ({decision['overall_score']}/100)")
        
        st.markdown("---")
        st.markdown("""
        ### 🚀 Enterprise Features
        
        **Advanced Pricing:**
        - Reserved Instances (1Y & 3Y)
        - Savings Plans (Compute & EC2)
        - Spot Instance Integration
        - Mixed Pricing Strategies
        
        **Enterprise Architecture:**
        - Multi-AZ Deployments
        - Graviton Processor Support
        - Auto Scaling Integration
        - Load Balancer Optimization
        
        **Migration Decision Engine:**
        - Financial Analysis (35% weight)
        - Technical Assessment (25% weight)
        - Operational Factors (20% weight)
        - Strategic Alignment (20% weight)
        
        **Compliance & Security:**
        - SOC 2, PCI-DSS, HIPAA, FedRAMP
        - Enhanced Monitoring Options
        - Disaster Recovery Planning
        - Security Best Practices
        
        **Advanced Analytics:**
        - Total Cost of Ownership (TCO)
        - ROI Calculations
        - Migration Risk Assessment
        - Optimization Recommendations
        """)
    
    # ENHANCED TAB STRUCTURE WITH MIGRATION DECISION
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "⚙️ Workload Configuration", 
        "🎯 Migration Decision",
        "📁 Bulk Analysis", 
        "🚀 Migration Planning",
        "📋 Reports & Export",
        "💰 Cost Optimization"
    ])
    
    with tab1:
        render_enhanced_workload_configuration()
        
        if st.session_state.analysis_results:
            st.markdown("---")
            render_enhanced_analysis_results(st.session_state.analysis_results['recommendations'])
    
    # NEW MIGRATION DECISION TAB
    with tab2:
        st.markdown("### 🎯 Migration Decision Analysis")
        
        if not st.session_state.analysis_results:
            st.info("💡 Please run a complete workload analysis first to see migration decision analysis.")
            
            # Show preview of decision factors
            st.markdown("#### 📊 Decision Framework Preview")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **🏛️ Decision Categories:**
                - 💰 **Financial (35%)**: Cost savings, ROI, break-even analysis
                - 🏗️ **Technical (25%)**: Infrastructure age, scalability, performance
                - ⚙️ **Operational (20%)**: Skills, maintenance, compliance
                - 🎯 **Strategic (20%)**: Innovation, growth, competitive advantage
                """)
            
            with col2:
                st.markdown("""
                **📋 Decision Outcomes:**
                - 🚀 **Strong Migrate (75-100)**: Clear cloud benefits
                - ✅ **Moderate Migrate (60-74)**: Good benefits, pilot recommended
                - ⚖️ **Neutral (45-59)**: Depends on priorities
                - 🏢 **Stay On-Premises (0-44)**: Optimize current infrastructure
                """)
            
        elif 'migration_decision' not in st.session_state.analysis_results:
            st.info("💡 Please run analysis with migration decision factors to see results here.")
            st.markdown("Click the **🎯 Complete Analysis with Migration Decision** button in the Workload Configuration tab.")
        else:
            render_migration_decision_results(st.session_state.analysis_results['migration_decision'])
    
    with tab3:
        def render_bulk_upload_configuration():
            """Render bulk upload configuration interface."""
            st.markdown("### 📁 Enterprise Bulk Analysis")
                # Instructions and template download
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 Bulk Analysis Instructions:**
        
        1. Download the CSV template below
        2. Fill in your workload data
        3. Upload the completed CSV file
        4. Review and validate the data
        5. Execute bulk analysis
        
        **Required Columns:**
        - workload_name, workload_type, on_prem_cores, peak_cpu_percent, avg_cpu_percent
        - on_prem_ram_gb, peak_ram_percent, avg_ram_percent, storage_current_gb
        - peak_iops, peak_throughput_mbps, region, operating_system
        """)
    
    with col2:
        # Create template CSV
        template_data = {
            'workload_name': ['Web Server Cluster', 'Database Server', 'Application Server'],
            'workload_type': ['web_application', 'database_server', 'application_server'],
            'operating_system': ['linux', 'windows', 'linux'],
            'region': ['us-east-1', 'us-east-1', 'us-west-2'],
            'on_prem_cores': [8, 16, 12],
            'peak_cpu_percent': [75, 85, 70],
            'avg_cpu_percent': [45, 55, 40],
            'on_prem_ram_gb': [32, 128, 64],
            'peak_ram_percent': [80, 90, 75],
            'avg_ram_percent': [55, 65, 50],
            'storage_current_gb': [500, 2000, 1000],
            'storage_growth_rate': [0.15, 0.20, 0.10],
            'peak_iops': [5000, 15000, 8000],
            'peak_throughput_mbps': [250, 500, 300],
            'seasonality_factor': [1.2, 1.1, 1.3],
            'prefer_amd': [True, False, True],
            'enable_graviton': [True, False, True],
            'multi_az': [True, True, True],
            'auto_scaling': [True, False, True],
            'load_balancer': ['alb', 'none', 'alb'],
            'compliance_requirements': ['["SOC2"]', '["SOC2","PCI-DSS"]', '["SOC2"]'],
            'backup_retention_days': [30, 90, 30],
            'monitoring_level': ['enhanced', 'enhanced', 'basic'],
            'disaster_recovery': [False, True, False]
        }
        
        template_df = pd.DataFrame(template_data)
        csv_template = template_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download CSV Template",
            data=csv_template,
            file_name="workload_analysis_template.csv",
            mime="text/csv",
            key="download_template"
        )
        
        st.info("💡 Use this template to ensure all required fields are included")
    
    st.markdown("---")
    
    # File upload section
    st.subheader("📤 Upload Workload Data")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload a CSV file with your workload configurations"
    )
    
    if uploaded_file is not None:
        try:
            # Read and validate CSV
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} workloads.")
            
            # Validate required columns
            required_columns = [
                'workload_name', 'workload_type', 'on_prem_cores', 'peak_cpu_percent',
                'avg_cpu_percent', 'on_prem_ram_gb', 'peak_ram_percent', 'avg_ram_percent',
                'storage_current_gb', 'peak_iops', 'peak_throughput_mbps', 'region', 'operating_system'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                st.info("Please download the template and ensure all required columns are present.")
                return
            
            # Show data preview
            with st.expander("👀 Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
                
                if len(df) > 10:
                    st.info(f"Showing first 10 rows of {len(df)} total rows")
            
            # Validation summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Workloads", len(df))
            
            with col2:
                unique_types = df['workload_type'].nunique()
                st.metric("Workload Types", unique_types)
            
            with col3:
                unique_regions = df['region'].nunique()
                st.metric("AWS Regions", unique_regions)
            
            # Advanced bulk options
            st.subheader("⚙️ Bulk Analysis Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                bulk_pricing_model = st.selectbox(
                    "Default Pricing Model for All Workloads",
                    ["on_demand", "ri_1y", "ri_3y", "savings_plan_compute_1y", "savings_plan_compute_3y"],
                    format_func=lambda x: {
                        "on_demand": "On-Demand",
                        "ri_1y": "1-Year Reserved Instances",
                        "ri_3y": "3-Year Reserved Instances",
                        "savings_plan_compute_1y": "1-Year Compute Savings Plan",
                        "savings_plan_compute_3y": "3-Year Compute Savings Plan"
                    }.get(x, x)
                )
                
                bulk_environments = st.multiselect(
                    "Environments to Analyze",
                    ["PROD", "STAGING", "QA", "DEV", "DR"],
                    default=["PROD", "STAGING"],
                    help="Select which environments to include in bulk analysis"
                )
            
            with col2:
                generate_summary_report = st.checkbox(
                    "Generate Portfolio Summary Report", 
                    value=True,
                    help="Create a comprehensive summary across all workloads"
                )
                
                include_migration_decision = st.checkbox(
                    "Include Migration Decision Analysis",
                    value=False,
                    help="Run migration decision analysis for each workload (requires additional data)"
                )
                
                parallel_processing = st.checkbox(
                    "Enable Parallel Processing",
                    value=True,
                    help="Process multiple workloads simultaneously for faster analysis"
                )
            
            # Execute bulk analysis
            if st.button("🚀 Execute Bulk Analysis", type="primary", key="bulk_analysis"):
                
                # Validate data before processing
                validation_errors = []
                
                for idx, row in df.iterrows():
                    # Check for valid workload types
                    if row['workload_type'] not in st.session_state.calculator.WORKLOAD_PROFILES:
                        validation_errors.append(f"Row {idx+1}: Invalid workload_type '{row['workload_type']}'")
                    
                    # Check for valid regions
                    valid_regions = ["us-east-1", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1", 
                                   "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", 
                                   "ap-south-1", "ap-east-1"]
                    if row['region'] not in valid_regions:
                        validation_errors.append(f"Row {idx+1}: Invalid region '{row['region']}'")
                    
                    # Check for reasonable values
                    if row['on_prem_cores'] <= 0:
                        validation_errors.append(f"Row {idx+1}: on_prem_cores must be greater than 0")
                    
                    if not (0 <= row['peak_cpu_percent'] <= 100):
                        validation_errors.append(f"Row {idx+1}: peak_cpu_percent must be between 0 and 100")
                
                if validation_errors:
                    st.error("❌ Validation Errors Found:")
                    for error in validation_errors[:10]:  # Show first 10 errors
                        st.text(f"• {error}")
                    if len(validation_errors) > 10:
                        st.text(f"... and {len(validation_errors) - 10} more errors")
                    return
                
                # Process bulk analysis
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                bulk_results = []
                
                for idx, row in df.iterrows():
                    progress = (idx + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing workload {idx + 1} of {len(df)}: {row['workload_name']}")
                    
                    # Create calculator instance for this workload
                    workload_calculator = EnterpriseEC2WorkloadSizingCalculator()
                    
                    # Set inputs from CSV row
                    for col in df.columns:
                        if col in workload_calculator.inputs:
                            value = row[col]
                            # Handle special cases
                            if col == 'compliance_requirements':
                                try:
                                    value = eval(value) if isinstance(value, str) else value
                                except:
                                    value = []
                            workload_calculator.inputs[col] = value
                    
                    # Set bulk options
                    workload_calculator.inputs['pricing_model'] = bulk_pricing_model
                    
                    try:
                        # Calculate recommendations for selected environments
                        workload_results = {}
                        for env in bulk_environments:
                            workload_results[env] = workload_calculator.calculate_comprehensive_requirements(env)
                        
                        result = {
                            'inputs': workload_calculator.inputs.copy(),
                            'recommendations': workload_results
                        }
                        
                        # Add migration decision if requested
                        if include_migration_decision:
                            # This would require additional CSV columns for migration decision factors
                            # For now, we'll use defaults
                            decision_result = enhanced_migration_decision_analysis(
                                workload_calculator.inputs, 
                                workload_results.get('PROD', {})
                            )
                            result['migration_decision'] = decision_result
                        
                        bulk_results.append(result)
                        
                    except Exception as e:
                        st.error(f"❌ Error processing workload {row['workload_name']}: {str(e)}")
                        continue
                
                # Store results
                st.session_state.bulk_results = bulk_results
                
                progress_bar.progress(1.0)
                status_text.text("✅ Bulk analysis completed!")
                
                st.success(f"🎉 Successfully analyzed {len(bulk_results)} workloads!")
                
                # Show summary
                if bulk_results:
                    render_bulk_analysis_summary(bulk_results, bulk_environments)
        
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted and contains valid data.")

def render_bulk_analysis_summary(bulk_results, environments):
    """Render summary of bulk analysis results."""
    st.markdown("---")
    st.subheader("📊 Bulk Analysis Summary")
    
    # Calculate totals
    total_workloads = len(bulk_results)
    total_monthly_cost = 0
    total_annual_savings = 0
    
    for result in bulk_results:
        prod_results = result['recommendations'].get('PROD', {})
        if prod_results:
            total_monthly_cost += prod_results['cost_breakdown']['total_costs'].get('on_demand', 0)
            total_annual_savings += prod_results['tco_analysis'].get('monthly_savings', 0) * 12
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Workloads", total_workloads)
    
    with col2:
        st.metric("Total Monthly Cost", f"${total_monthly_cost:,.2f}")
    
    with col3:
        st.metric("Annual Savings Potential", f"${total_annual_savings:,.2f}")
    
    with col4:
        avg_savings_pct = (total_annual_savings / (total_monthly_cost * 12) * 100) if total_monthly_cost > 0 else 0
        st.metric("Average Savings %", f"{avg_savings_pct:.1f}%")
    
    # Workload breakdown table
    summary_data = []
    for result in bulk_results:
        workload_name = result['inputs']['workload_name']
        workload_type = result['inputs']['workload_type']
        
        prod_results = result['recommendations'].get('PROD', {})
        if prod_results:
            tco_analysis = prod_results['tco_analysis']
            requirements = prod_results['requirements']
            
            summary_data.append({
                'Workload': workload_name,
                'Type': workload_type.replace('_', ' ').title(),
                'vCPUs': requirements['vCPUs'],
                'RAM (GB)': requirements['RAM_GB'],
                'Storage (GB)': requirements['storage_GB'],
                'Monthly Cost': f"${tco_analysis['monthly_cost']:,.2f}",
                'Monthly Savings': f"${tco_analysis['monthly_savings']:,.2f}",
                'ROI (3Y)': f"{tco_analysis['roi_3_years']}%"
            })
    
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    # Portfolio visualization
    if len(bulk_results) > 1:
        st.subheader("📈 Portfolio Visualization")
        
        # Cost distribution by workload type
        workload_costs = {}
        for result in bulk_results:
            workload_type = result['inputs']['workload_type'].replace('_', ' ').title()
            prod_results = result['recommendations'].get('PROD', {})
            if prod_results:
                cost = prod_results['cost_breakdown']['total_costs'].get('on_demand', 0)
                workload_costs[workload_type] = workload_costs.get(workload_type, 0) + cost
        
        if workload_costs:
            fig_pie = px.pie(
                values=list(workload_costs.values()),
                names=list(workload_costs.keys()),
                title="Cost Distribution by Workload Type"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Export options for bulk results
    st.markdown("---")
    st.subheader("📤 Export Bulk Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Portfolio Excel"):
            excel_data = generate_bulk_excel_report(bulk_results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Portfolio_Analysis_{timestamp}.xlsx"
            
            st.download_button(
                label="⬇️ Download Portfolio Excel",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📄 Export Summary CSV"):
            csv_data = generate_bulk_csv_summary(bulk_results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Portfolio_Summary_{timestamp}.csv"
            
            st.download_button(
                label="⬇️ Download Summary CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
    
    with col3:
        if REPORTLAB_AVAILABLE and st.button("📑 Generate Portfolio Report"):
            # This would generate a comprehensive PDF report for all workloads
            st.info("Portfolio PDF report generation available - implement based on requirements")

def generate_bulk_excel_report(bulk_results):
    """Generate Excel report for bulk analysis results."""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Portfolio summary
        summary_data = []
        for result in bulk_results:
            workload_name = result['inputs']['workload_name']
            prod_results = result['recommendations'].get('PROD', {})
            if prod_results:
                tco_analysis = prod_results['tco_analysis']
                requirements = prod_results['requirements']
                
                summary_data.append({
                    'Workload': workload_name,
                    'Type': result['inputs']['workload_type'],
                    'Region': result['inputs']['region'],
                    'vCPUs': requirements['vCPUs'],
                    'RAM_GB': requirements['RAM_GB'],
                    'Storage_GB': requirements['storage_GB'],
                    'Monthly_Cost': tco_analysis['monthly_cost'],
                    'Monthly_Savings': tco_analysis['monthly_savings'],
                    'Annual_Savings': tco_analysis['monthly_savings'] * 12,
                    'ROI_3Y': tco_analysis['roi_3_years'],
                    'Break_Even_Months': tco_analysis['break_even_months']
                })
        
        portfolio_df = pd.DataFrame(summary_data)
        portfolio_df.to_excel(writer, sheet_name='Portfolio Summary', index=False)
        
        # Individual workload details
        for i, result in enumerate(bulk_results[:10]):  # Limit to first 10 workloads
            workload_name = result['inputs']['workload_name'][:20]  # Limit name length
            prod_results = result['recommendations'].get('PROD', {})
            
            if prod_results:
                cost_data = []
                total_costs = prod_results['cost_breakdown']['total_costs']
                
                for pricing_model, cost in total_costs.items():
                    cost_data.append({
                        'Pricing_Model': pricing_model,
                        'Monthly_Cost': cost,
                        'Annual_Cost': cost * 12
                    })
                
                cost_df = pd.DataFrame(cost_data)
                sheet_name = f"WL{i+1}_{workload_name}"
                cost_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()

def generate_bulk_csv_summary(bulk_results):
    """Generate CSV summary for bulk results."""
    summary_data = []
    for result in bulk_results:
        workload_name = result['inputs']['workload_name']
        prod_results = result['recommendations'].get('PROD', {})
        if prod_results:
            tco_analysis = prod_results['tco_analysis']
            requirements = prod_results['requirements']
            
            summary_data.append({
                'Workload': workload_name,
                'Type': result['inputs']['workload_type'],
                'Region': result['inputs']['region'],
                'vCPUs': requirements['vCPUs'],
                'RAM_GB': requirements['RAM_GB'],
                'Storage_GB': requirements['storage_GB'],
                'Monthly_Cost': tco_analysis['monthly_cost'],
                'Monthly_Savings': tco_analysis['monthly_savings'],
                'Annual_Savings': tco_analysis['monthly_savings'] * 12,
                'ROI_3Y': tco_analysis['roi_3_years'],
                'Break_Even_Months': tco_analysis['break_even_months']
            })
    
    df = pd.DataFrame(summary_data)
    return df.to_csv(index=False)
    
    with tab4:
        render_migration_planning() 
    
    with tab5:
        # EXISTING REPORTS TAB CODE (keep unchanged)
        st.markdown("### 📋 Enterprise Reports & Export")        
        if not st.session_state.analysis_results and not st.session_state.bulk_results:
            st.info("💡 Please run a workload analysis first to generate reports.")
        else:
            # Check if ReportLab is available
            if not REPORTLAB_AVAILABLE:
                st.error("📄 PDF generation requires ReportLab library. Install with: `pip install reportlab`")
                st.info("You can still export data as CSV and Excel formats.")
            
            # Report options
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Available Reports")
                
                report_options = []
                if st.session_state.analysis_results:
                    report_options.extend([
                        "Executive Summary",
                        "Detailed Cost Analysis", 
                        "Technical Specifications",
                        "Migration Plan",
                        "Risk Assessment"
                    ])
                    
                    # Add migration decision report if available
                    if 'migration_decision' in st.session_state.analysis_results:
                        report_options.append("Migration Decision Analysis")
                
                if st.session_state.bulk_results:
                    report_options.extend([
                        "Portfolio Overview",
                        "Bulk Cost Analysis"
                    ])
                
                selected_reports = st.multiselect(
                    "Select Report Sections",
                    report_options,
                    default=report_options[:3] if len(report_options) >= 3 else report_options
                )
            
            with col2:
                st.markdown("#### 🎨 Report Options")
                
                include_charts = st.checkbox("Include Charts and Graphs", value=True)
                include_raw_data = st.checkbox("Include Raw Data Tables", value=False)
                company_name = st.text_input("Company Name", value="Enterprise Corporation")
                report_title = st.text_input("Report Title", value="AWS Migration Analysis")
            
            st.markdown("---")
            
            # Export buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if REPORTLAB_AVAILABLE and st.button("📄 Generate PDF Report", type="primary"):
                    with st.spinner("🔄 Generating comprehensive PDF report..."):
                        try:
                            pdf_data = generate_comprehensive_pdf_report(
                                st.session_state.analysis_results or st.session_state.bulk_results,
                                selected_reports,
                                company_name,
                                report_title,
                                include_charts,
                                include_raw_data
                            )
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"AWS_Migration_Report_{timestamp}.pdf"
                            
                            st.download_button(
                                label="⬇️ Download PDF Report",
                                data=pdf_data,
                                file_name=filename,
                                mime="application/pdf",
                                key="download_pdf"
                            )
                            
                            st.success("✅ PDF report generated successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating PDF: {str(e)}")
                            import traceback
                            st.text(traceback.format_exc())
            
            with col2:
                if st.button("📊 Export to Excel"):
                    with st.spinner("🔄 Generating Excel report..."):
                        try:
                            excel_data = generate_excel_report(
                                st.session_state.analysis_results or st.session_state.bulk_results
                            )
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"AWS_Migration_Data_{timestamp}.xlsx"
                            
                            st.download_button(
                                label="⬇️ Download Excel File",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_excel"
                            )
                            
                            st.success("✅ Excel file generated successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating Excel: {str(e)}")
            
            with col3:
                if st.button("📄 Export to CSV"):
                    with st.spinner("🔄 Generating CSV export..."):
                        try:
                            csv_data = generate_csv_report(
                                st.session_state.analysis_results or st.session_state.bulk_results
                            )
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"AWS_Migration_Summary_{timestamp}.csv"
                            
                            st.download_button(
                                label="⬇️ Download CSV File",
                                data=csv_data,
                                file_name=filename,
                                mime="text/csv",
                                key="download_csv"
                            )
                            
                            st.success("✅ CSV file generated successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating CSV: {str(e)}")
            
            # Preview section
            if st.session_state.analysis_results:
                st.markdown("---")
                st.markdown("### 👀 Report Preview")
                
                with st.expander("Executive Summary Preview"):
                    results = st.session_state.analysis_results['recommendations']['PROD']
                    tco_analysis = results['tco_analysis']
                    
                    st.markdown(f"""
                    **Workload:** {st.session_state.analysis_results['inputs']['workload_name']}
                    
                    **Financial Summary:**
                    - Best Monthly Cost: ${tco_analysis['monthly_cost']:,.2f} ({tco_analysis['best_pricing_option'].replace('_', ' ').title()})
                    - Annual Savings vs On-Demand: ${tco_analysis['monthly_savings'] * 12:,.2f}
                    - 3-Year ROI: {tco_analysis['roi_3_years']}%
                    - Break-even: {tco_analysis['break_even_months']} months
                    
                    **Recommendations:**
                    """)
                    
                    for i, rec in enumerate(results['optimization_recommendations'][:3], 1):
                        st.markdown(f"{i}. {rec}")
                    
                    # Add migration decision preview if available
                    if 'migration_decision' in st.session_state.analysis_results:
                        decision = st.session_state.analysis_results['migration_decision']
                        st.markdown(f"""
                        
                        **Migration Decision:**
                        - Recommendation: {decision['recommendation_text']}
                        - Overall Score: {decision['overall_score']}/100
                        - Confidence: {decision['confidence']}
                        """)
    
    with tab6:
        st.markdown("### 🎯 Advanced Cost Optimization")
        
        if st.session_state.analysis_results:
            results = st.session_state.analysis_results['recommendations']['PROD']
            
            st.subheader("💰 Cost Optimization Dashboard")
            
            # Optimization opportunities
            cost_breakdown = results['cost_breakdown']
            total_costs = cost_breakdown['total_costs']
            
            # Create optimization comparison
            optimization_data = []
            base_cost = total_costs.get('on_demand', 0)
            
            for pricing_model, cost in total_costs.items():
                if pricing_model != 'on_demand':
                    savings = base_cost - cost
                    savings_pct = (savings / base_cost * 100) if base_cost > 0 else 0
                    
                    optimization_data.append({
                        'Strategy': pricing_model.replace('_', ' ').title(),
                        'Monthly Cost': cost,
                        'Monthly Savings': savings,
                        'Savings %': savings_pct,
                        'Annual Savings': savings * 12
                    })
            
            if optimization_data:
                df_opt = pd.DataFrame(optimization_data)
                df_opt = df_opt.sort_values('Monthly Savings', ascending=False)
                
                # Format currency columns
                df_opt['Monthly Cost'] = df_opt['Monthly Cost'].apply(lambda x: f"${x:,.2f}")
                df_opt['Monthly Savings'] = df_opt['Monthly Savings'].apply(lambda x: f"${x:,.2f}")
                df_opt['Annual Savings'] = df_opt['Annual Savings'].apply(lambda x: f"${x:,.2f}")
                df_opt['Savings %'] = df_opt['Savings %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(df_opt, use_container_width=True, hide_index=True)
                
            # Add migration decision insights to cost optimization
            if 'migration_decision' in st.session_state.analysis_results:
                st.markdown("---")
                st.subheader("🎯 Migration Decision Insights")
                
                decision = st.session_state.analysis_results['migration_decision']
                financial_score = decision['category_scores']['financial']
                
                if financial_score >= 70:
                    st.success(f"💰 Strong financial case for cloud migration (Score: {financial_score}/100)")
                elif financial_score >= 50:
                    st.info(f"💡 Moderate financial benefits from cloud migration (Score: {financial_score}/100)")
                else:
                    st.warning(f"⚠️ Limited financial benefits from cloud migration (Score: {financial_score}/100)")
                
                # Show top financial drivers
                financial_factors = decision['detailed_factors']['financial']
                st.markdown("**Top Financial Factors:**")
                for factor, score in sorted(financial_factors.items(), key=lambda x: x[1], reverse=True)[:3]:
                    factor_name = factor.replace('_', ' ').title()
                    st.markdown(f"• {factor_name}: {score:.0f}/100")
        else:
            st.info("💡 Run a workload analysis to access cost optimization features.")
    
    # Enhanced footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <strong>Enterprise AWS Workload Sizing Platform v4.0</strong><br>
        Advanced cloud migration planning with Reserved Instances, Savings Plans, TCO analysis, intelligent migration decisions, and enterprise-grade compliance features<br>
        <em>Built for Enterprise • Comprehensive • Secure • Scalable • Intelligent</em>
    </div>
    """, unsafe_allow_html=True)

# END OF MAIN FUNCTION MODIFICATION
    # Enhanced footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <strong>Enterprise AWS Workload Sizing Platform v4.0</strong><br>
        Advanced cloud migration planning with Reserved Instances, Savings Plans, TCO analysis, and enterprise-grade compliance features<br>
        <em>Built for Enterprise • Comprehensive • Secure • Scalable</em>
    </div>
    """, unsafe_allow_html=True)
# Add these functions to your streamlit_app.py file before the main() function

def generate_comprehensive_pdf_report(results_data, selected_sections, company_name, report_title, include_charts, include_raw_data):
    """Generate comprehensive PDF report with all selected sections."""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is required for PDF generation")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, leftMargin=1*inch, rightMargin=1*inch)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a365d'),
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor('#2d3748'),
    )
    
    # Title page
    story.append(Paragraph(report_title, title_style))
    story.append(Paragraph(company_name, styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 0.5 * inch))
    
    # Handle both single and bulk results
    if isinstance(results_data, dict) and 'recommendations' in results_data:
        # Single workload result
        results_list = [results_data]
    elif isinstance(results_data, list):
        # Bulk results
        results_list = results_data
    else:
        # Fallback
        results_list = [results_data]
    
    # Executive Summary
    if "Executive Summary" in selected_sections:
        story.append(Paragraph("Executive Summary", section_style))
        
        total_workloads = len(results_list)
        total_monthly_cost = sum(
            result['recommendations']['PROD']['cost_breakdown']['total_costs'].get('on_demand', 0) 
            for result in results_list
        )
        
        total_migration_cost = sum(
            result['recommendations']['PROD']['tco_analysis'].get('migration_cost', 0)
            for result in results_list
        )
        
        total_annual_savings = sum(
            result['recommendations']['PROD']['tco_analysis'].get('monthly_savings', 0) * 12
            for result in results_list
        )
        
        summary_text = f"""
        This comprehensive analysis covers {total_workloads} enterprise workload(s) for AWS cloud migration.
        <br/><br/>
        <b>Financial Summary:</b><br/>
        • Total Monthly Cost (On-Demand): ${total_monthly_cost:,.2f}<br/>
        • Annual Cost Projection: ${total_monthly_cost * 12:,.2f}<br/>
        • Estimated Migration Cost: ${total_migration_cost:,.2f}<br/>
        • Potential Annual Savings: ${total_annual_savings:,.2f}<br/>
        <br/>
        <b>Key Recommendations:</b><br/>
        • Consider Reserved Instances or Savings Plans for significant cost optimization<br/>
        • Implement comprehensive monitoring and auto-scaling strategies<br/>
        • Evaluate Graviton processors for compatible workloads<br/>
        • Plan migration in phases to minimize business disruption
        """
        
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(PageBreak())
    
    # Detailed sections for each workload
    for idx, result in enumerate(results_list):
        workload_name = result.get('inputs', {}).get('workload_name', f'Workload {idx + 1}')
        prod_results = result['recommendations']['PROD']
        
        story.append(Paragraph(f"Workload Analysis: {workload_name}", section_style))
        
        if "Technical Specifications" in selected_sections:
            story.append(Paragraph("Technical Specifications", styles['Heading3']))
            
            requirements = prod_results['requirements']
            instance_options = prod_results['instance_options']
            primary_instance = instance_options.get('balanced', instance_options.get('cost_optimized', {}))
            
            tech_text = f"""
            <b>Resource Requirements:</b><br/>
            • vCPUs: {requirements['vCPUs']}<br/>
            • RAM: {requirements['RAM_GB']} GB<br/>
            • Storage: {requirements['storage_GB']} GB<br/>
            • IOPS: {requirements['iops_required']}<br/>
            • Multi-AZ: {'Yes' if requirements['multi_az'] else 'No'}<br/>
            <br/>
            <b>Recommended Instance:</b><br/>
            • Type: {primary_instance.get('type', 'N/A')}<br/>
            • Processor: {primary_instance.get('processor', 'N/A')}<br/>
            • Family: {primary_instance.get('family', 'N/A').title()}<br/>
            • Architecture: {primary_instance.get('architecture', 'N/A')}
            """
            story.append(Paragraph(tech_text, styles['Normal']))
            story.append(Spacer(1, 12))
        
        if "Detailed Cost Analysis" in selected_sections:
            story.append(Paragraph("Cost Analysis", styles['Heading3']))
            
            cost_breakdown = prod_results['cost_breakdown']
            total_costs = cost_breakdown['total_costs']
            tco_analysis = prod_results['tco_analysis']
            
            # Create cost table
            cost_data = [['Pricing Model', 'Monthly Cost', 'Savings vs On-Demand']]
            on_demand_cost = total_costs.get('on_demand', 0)
            
            for pricing_model, cost in total_costs.items():
                savings = ((on_demand_cost - cost) / on_demand_cost * 100) if on_demand_cost > 0 else 0
                cost_data.append([
                    pricing_model.replace('_', ' ').title(),
                    f"${cost:,.2f}",
                    f"{savings:.1f}%"
                ])
            
            cost_table = Table(cost_data)
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(cost_table)
            story.append(Spacer(1, 12))
            
            # TCO Summary
            tco_text = f"""
            <b>Total Cost of Ownership (3 Years):</b><br/>
            • Best Option: {tco_analysis['best_pricing_option'].replace('_', ' ').title()}<br/>
            • Monthly Cost: ${tco_analysis['monthly_cost']:,.2f}<br/>
            • Annual Savings: ${tco_analysis['monthly_savings'] * 12:,.2f}<br/>
            • 3-Year ROI: {tco_analysis['roi_3_years']}%<br/>
            • Break-even: {tco_analysis['break_even_months']} months
            """
            story.append(Paragraph(tco_text, styles['Normal']))
        
        if "Risk Assessment" in selected_sections:
            story.append(Paragraph("Risk Assessment", styles['Heading3']))
            
            risk_assessment = prod_results['risk_assessment']
            
            risk_text = f"""
            <b>Overall Risk Level: {risk_assessment['overall_risk']}</b><br/>
            <br/>
            <b>Risk Factors:</b><br/>
            """
            
            for factor in risk_assessment['risk_factors']:
                risk_text += f"• {factor}<br/>"
            
            risk_text += "<br/><b>Mitigation Strategies:</b><br/>"
            
            for strategy in risk_assessment['mitigation_strategies'][:5]:  # Limit to top 5
                risk_text += f"• {strategy}<br/>"
            
            story.append(Paragraph(risk_text, styles['Normal']))
        
        if "Migration Plan" in selected_sections:
            story.append(Paragraph("Migration Plan", styles['Heading3']))
            
            migration_text = """
            <b>Recommended Migration Phases:</b><br/>
            <br/>
            <b>Phase 1: Assessment & Planning (2-4 weeks)</b><br/>
            • Complete infrastructure inventory<br/>
            • Map application dependencies<br/>
            • Create detailed migration plan<br/>
            • Set up AWS accounts and basic networking<br/>
            <br/>
            <b>Phase 2: Pilot Migration (2-3 weeks)</b><br/>
            • Migrate development environment<br/>
            • Test backup and restore procedures<br/>
            • Validate monitoring and alerting<br/>
            • Fine-tune security configurations<br/>
            <br/>
            <b>Phase 3: Production Migration (4-8 weeks)</b><br/>
            • Execute production cutover<br/>
            • Validate application functionality<br/>
            • Optimize performance and costs<br/>
            • Implement auto-scaling policies<br/>
            <br/>
            <b>Phase 4: Optimization (2-4 weeks)</b><br/>
            • Right-size instances based on actual usage<br/>
            • Implement Reserved Instances/Savings Plans<br/>
            • Optimize storage and networking<br/>
            • Final security and compliance validation
            """
            story.append(Paragraph(migration_text, styles['Normal']))
        
        if idx < len(results_list) - 1:  # Add page break between workloads
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_excel_report(results_data):
    """Generate Excel report with multiple sheets."""
    output = BytesIO()
    
    # Handle both single and bulk results
    if isinstance(results_data, dict) and 'recommendations' in results_data:
        results_list = [results_data]
    elif isinstance(results_data, list):
        results_list = results_data
    else:
        results_list = [results_data]
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = []
        for result in results_list:
            workload_name = result.get('inputs', {}).get('workload_name', 'Unknown')
            prod_results = result['recommendations']['PROD']
            tco_analysis = prod_results['tco_analysis']
            requirements = prod_results['requirements']
            
            summary_data.append({
                'Workload': workload_name,
                'vCPUs': requirements['vCPUs'],
                'RAM (GB)': requirements['RAM_GB'], 
                'Storage (GB)': requirements['storage_GB'],
                'Best Pricing': tco_analysis['best_pricing_option'],
                'Monthly Cost': tco_analysis['monthly_cost'],
                'Monthly Savings': tco_analysis['monthly_savings'],
                'Annual Savings': tco_analysis['monthly_savings'] * 12,
                'ROI (3Y)': tco_analysis['roi_3_years'],
                'Break-even (months)': tco_analysis['break_even_months']
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # Detailed cost breakdown for each workload
        for idx, result in enumerate(results_list):
            workload_name = result.get('inputs', {}).get('workload_name', f'Workload_{idx+1}')
            prod_results = result['recommendations']['PROD']
            
            # Cost breakdown sheet
            cost_data = []
            total_costs = prod_results['cost_breakdown']['total_costs']
            
            for pricing_model, cost in total_costs.items():
                cost_data.append({
                    'Pricing Model': pricing_model.replace('_', ' ').title(),
                    'Monthly Cost': cost,
                    'Annual Cost': cost * 12
                })
            
            cost_df = pd.DataFrame(cost_data)
            sheet_name = f"{workload_name[:20]}_Costs"  # Limit sheet name length
            cost_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()


def generate_csv_report(results_data):
    """Generate CSV summary report."""
    # Handle both single and bulk results
    if isinstance(results_data, dict) and 'recommendations' in results_data:
        results_list = [results_data]
    elif isinstance(results_data, list):
        results_list = results_data
    else:
        results_list = [results_data]
    
    summary_data = []
    for result in results_list:
        workload_name = result.get('inputs', {}).get('workload_name', 'Unknown')
        prod_results = result['recommendations']['PROD']
        tco_analysis = prod_results['tco_analysis']
        requirements = prod_results['requirements']
        
        summary_data.append({
            'Workload': workload_name,
            'vCPUs': requirements['vCPUs'],
            'RAM_GB': requirements['RAM_GB'],
            'Storage_GB': requirements['storage_GB'],
            'Best_Pricing_Model': tco_analysis['best_pricing_option'],
            'Monthly_Cost': tco_analysis['monthly_cost'],
            'Monthly_Savings': tco_analysis['monthly_savings'],
            'Annual_Savings': tco_analysis['monthly_savings'] * 12,
            'ROI_3_Years': tco_analysis['roi_3_years'],
            'Break_Even_Months': tco_analysis['break_even_months']
        })
    
    df = pd.DataFrame(summary_data)
    return df.to_csv(index=False)
# INSERT THESE FUNCTIONS RIGHT BEFORE THE main() FUNCTION
# (Around line 2000-2100, before def main():)

def render_migration_decision_inputs():
    """Render additional inputs needed for migration decision analysis."""
    
    st.markdown('<div class="section-header"><h3>🎯 Migration Decision Factors</h3></div>', unsafe_allow_html=True)
    
    calculator = st.session_state.calculator
    
    with st.expander("💰 Financial & Business Context", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            calculator.inputs["current_annual_cost"] = st.number_input(
                "Current Annual Infrastructure Cost ($)",
                min_value=0,
                value=calculator.inputs.get("current_annual_cost", 100000),
                step=5000,
                help="Total annual cost of current on-premises infrastructure including hardware, software, maintenance, and staff"
            )
            
            calculator.inputs["prefer_opex"] = st.checkbox(
                "Prefer Operational Expenditure (OpEx) over Capital Expenditure (CapEx)",
                value=calculator.inputs.get("prefer_opex", True),
                help="Cloud provides OpEx model vs traditional CapEx for infrastructure"
            )
            
            calculator.inputs["business_growth_rate"] = st.slider(
                "Expected Annual Business Growth Rate",
                min_value=0.0, max_value=1.0, 
                value=calculator.inputs.get("business_growth_rate", 0.15),
                step=0.05, format="%.0%",
                help="Expected annual growth rate affecting infrastructure needs"
            )
        
        with col2:
            calculator.inputs["innovation_priority"] = st.selectbox(
                "Innovation and Agility Priority",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("innovation_priority", "medium")),
                help="How important is rapid innovation and new technology adoption?"
            )
            
            calculator.inputs["time_to_market_importance"] = st.selectbox(
                "Time-to-Market Importance",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("time_to_market_importance", "medium")),
                help="How critical is fast deployment of new services/features?"
            )
            
            calculator.inputs["digital_transformation_priority"] = st.selectbox(
                "Digital Transformation Priority",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("digital_transformation_priority", "medium")),
                help="Priority level for digital transformation initiatives"
            )
    
    with st.expander("🏗️ Technical Assessment"):
        col1, col2 = st.columns(2)
        
        with col1:
            calculator.inputs["infrastructure_age_years"] = st.slider(
                "Current Infrastructure Age (Years)",
                min_value=1, max_value=10,
                value=calculator.inputs.get("infrastructure_age_years", 3),
                help="Average age of current servers and infrastructure"
            )
            
            calculator.inputs["scalability_importance"] = st.selectbox(
                "Scalability Requirements",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("scalability_importance", "medium")),
                help="How important is the ability to scale up/down quickly?"
            )
            
            calculator.inputs["performance_criticality"] = st.selectbox(
                "Performance Criticality",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("performance_criticality", "medium")),
                help="How performance-sensitive are your applications?"
            )
            
            calculator.inputs["security_level"] = st.selectbox(
                "Security Requirements Level",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("security_level", "medium")),
                help="Level of security requirements (high might favor on-premises)"
            )
        
        with col2:
            calculator.inputs["cloud_native_compatible"] = st.checkbox(
                "Applications are Cloud-Native Compatible",
                value=calculator.inputs.get("cloud_native_compatible", True),
                help="Can applications run effectively in cloud environment?"
            )
            
            calculator.inputs["multi_region_required"] = st.checkbox(
                "Multi-Region Deployment Required",
                value=calculator.inputs.get("multi_region_required", False),
                help="Need to deploy across multiple geographic regions?"
            )
            
            calculator.inputs["vendor_lockin_concern"] = st.selectbox(
                "Vendor Lock-in Concern Level",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("vendor_lockin_concern", "medium")),
                help="Level of concern about being locked into a cloud provider"
            )
            
            calculator.inputs["cloud_competitive_advantage"] = st.selectbox(
                "Cloud as Competitive Advantage",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("cloud_competitive_advantage", "medium")),
                help="How much competitive advantage would cloud provide?"
            )
    
    with st.expander("⚙️ Operational Factors"):
        col1, col2 = st.columns(2)
        
        with col1:
            calculator.inputs["cloud_expertise"] = st.selectbox(
                "Team's Cloud Expertise Level",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("cloud_expertise", "medium")),
                help="Current level of cloud knowledge and skills in your team"
            )
            
            calculator.inputs["maintenance_burden"] = st.selectbox(
                "Current Infrastructure Maintenance Burden",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("maintenance_burden", "high")),
                help="How much effort is spent on infrastructure maintenance?"
            )
            
            calculator.inputs["change_mgmt"] = st.selectbox(
                "Change Management Capability",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("change_mgmt", "medium")),
                help="Organization's ability to manage large technology changes"
            )
        
        with col2:
            calculator.inputs["backup_complexity"] = st.selectbox(
                "Current Backup/Recovery Complexity",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(calculator.inputs.get("backup_complexity", "medium")),
                help="Complexity of current backup and disaster recovery"
            )
            
            calculator.inputs["monitoring_quality"] = st.selectbox(
                "Current Monitoring Quality",
                ["poor", "medium", "excellent"],
                index=["poor", "medium", "excellent"].index(calculator.inputs.get("monitoring_quality", "medium")),
                help="Quality of current infrastructure monitoring and alerting"
            )

def render_migration_decision_results(decision_result):
    """Render the migration decision analysis results."""
    
    st.markdown('<div class="section-header"><h3>🎯 Migration Decision Analysis</h3></div>', unsafe_allow_html=True)
    
    # Overall Recommendation
    recommendation = decision_result['recommendation']
    overall_score = decision_result['overall_score']
    
    # Color coding based on recommendation
    if recommendation == "STRONG_MIGRATE":
        color = "#10b981"  # Green
        icon = "🚀"
    elif recommendation == "MODERATE_MIGRATE":
        color = "#3b82f6"  # Blue
        icon = "✅"
    elif recommendation == "NEUTRAL":
        color = "#f59e0b"  # Yellow
        icon = "⚖️"
    else:  # STAY_ON_PREMISES
        color = "#ef4444"  # Red
        icon = "🏢"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}20 0%, {color}10 100%); 
                border: 2px solid {color}; border-radius: 12px; padding: 2rem; 
                text-align: center; margin: 1rem 0;">
        <h2 style="color: {color}; margin: 0;">{icon} {decision_result['recommendation_text']}</h2>
        <p style="font-size: 1.2rem; margin: 0.5rem 0;">
            <strong>Overall Score: {overall_score}/100</strong> | 
            Confidence: {decision_result['confidence']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Category Scores
    st.subheader("📊 Decision Factor Breakdown")
    
    category_scores = decision_result['category_scores']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        financial_score = category_scores['financial']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💰 Financial</div>
            <div class="metric-value" style="color: {'#10b981' if financial_score >= 60 else '#f59e0b' if financial_score >= 40 else '#ef4444'}">{financial_score}</div>
            <div class="metric-description">Cost & ROI Analysis</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        technical_score = category_scores['technical']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🏗️ Technical</div>
            <div class="metric-value" style="color: {'#10b981' if technical_score >= 60 else '#f59e0b' if technical_score >= 40 else '#ef4444'}">{technical_score}</div>
            <div class="metric-description">Infrastructure & Performance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        operational_score = category_scores['operational']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⚙️ Operational</div>
            <div class="metric-value" style="color: {'#10b981' if operational_score >= 60 else '#f59e0b' if operational_score >= 40 else '#ef4444'}">{operational_score}</div>
            <div class="metric-description">Skills & Management</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        strategic_score = category_scores['strategic']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎯 Strategic</div>
            <div class="metric-value" style="color: {'#10b981' if strategic_score >= 60 else '#f59e0b' if strategic_score >= 40 else '#ef4444'}">{strategic_score}</div>
            <div class="metric-description">Business & Innovation</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Key Drivers (Pro-Cloud)")
        key_factors = decision_result['key_factors']
        
        for category, factor, score in reversed(key_factors['top_drivers']):
            factor_name = factor.replace('_', ' ').title()
            st.markdown(f"**{category}:** {factor_name} ({score:.0f}/100)")
    
    with col2:
        st.subheader("⚠️ Key Concerns")
        
        for category, factor, score in key_factors['top_concerns']:
            factor_name = factor.replace('_', ' ').title()
            st.markdown(f"**{category}:** {factor_name} ({score:.0f}/100)")
    
    # Risks and Considerations
    if decision_result['risks_and_considerations']:
        st.subheader("⚠️ Risks and Considerations")
        for risk in decision_result['risks_and_considerations']:
            st.markdown(f"• {risk}")
    
    # Next Steps
    st.subheader("📋 Recommended Next Steps")
    for i, step in enumerate(decision_result['next_steps'], 1):
        st.markdown(f"{i}. {step}")
    
    # Detailed Factor Analysis
    with st.expander("🔍 Detailed Factor Analysis"):
        detailed_factors = decision_result['detailed_factors']
        
        for category, factors in detailed_factors.items():
            st.markdown(f"### {category.title()} Factors")
            
            factor_data = []
            for factor, score in factors.items():
                factor_data.append({
                    'Factor': factor.replace('_', ' ').title(),
                    'Score': f"{score:.1f}/100",
                    'Impact': 'Positive' if score >= 60 else 'Neutral' if score >= 40 else 'Negative'
                })
            
            df_factors = pd.DataFrame(factor_data)
            st.dataframe(df_factors, use_container_width=True, hide_index=True)

def enhanced_migration_decision_analysis(calculator_inputs, cloud_results):
    """Enhanced function to integrate decision engine with existing calculator."""
    
    # Map calculator inputs to decision engine inputs
    decision_inputs = {
        # Financial factors
        'current_annual_cost': calculator_inputs.get('current_annual_cost', 0),
        'prefer_opex': calculator_inputs.get('prefer_opex', True),
        
        # Technical factors  
        'infrastructure_age_years': calculator_inputs.get('infrastructure_age_years', 3),
        'scalability_importance': calculator_inputs.get('scalability_importance', 'medium'),
        'performance_criticality': calculator_inputs.get('performance_criticality', 'medium'),
        'disaster_recovery_needs': calculator_inputs.get('disaster_recovery', False),
        'multi_region_required': calculator_inputs.get('multi_region_required', False),
        'cloud_native_compatible': calculator_inputs.get('cloud_native_compatible', True),
        'security_requirements': calculator_inputs.get('security_level', 'medium'),
        'compliance_requirements': calculator_inputs.get('compliance_requirements', []),
        
        # Operational factors
        'cloud_expertise_level': calculator_inputs.get('cloud_expertise', 'medium'),
        'maintenance_burden': calculator_inputs.get('maintenance_burden', 'high'),
        'backup_complexity': calculator_inputs.get('backup_complexity', 'medium'),
        'current_monitoring_quality': calculator_inputs.get('monitoring_quality', 'medium'),
        'change_management_capability': calculator_inputs.get('change_mgmt', 'medium'),
        
        # Strategic factors
        'innovation_priority': calculator_inputs.get('innovation_priority', 'medium'),
        'time_to_market_importance': calculator_inputs.get('time_to_market_importance', 'medium'),
        'business_growth_rate': calculator_inputs.get('business_growth_rate', 0.15),
        'cloud_competitive_advantage': calculator_inputs.get('cloud_competitive_advantage', 'medium'),
        'digital_transformation_priority': calculator_inputs.get('digital_transformation_priority', 'medium'),
        'vendor_lockin_concern': calculator_inputs.get('vendor_lockin_concern', 'medium')
    }
    
    # Initialize decision engine
    decision_engine = CloudMigrationDecisionEngine()
    
    # Make migration decision
    decision_result = decision_engine.make_migration_decision(decision_inputs, cloud_results)
    
    return decision_result

# END OF UI FUNCTIONS INSERTION

if __name__ == "__main__":
    main()