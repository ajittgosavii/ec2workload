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
                "m6i.4xlarge": 0.4838, "m6i.8xlarge": 0.9677, "m6i.12xlarge": 1.4515, "m6i.16xlarge": 1.9354,
                
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