# Modify initialize_session_state to set RI/SP option
# Modify render_workload_configuration to integrate On-Premise details and remove its tab
# Modify main to change the tab structure to a radio button for selection between single workload and bulk analysis
# Add a prominent "Run Analysis" button for single workload analysis
# Ensure report generation is accessible

import streamlit as st
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
import zipfile

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

# Configure page
st.set_page_config(
    page_title="Enterprise AWS EC2 Workload Sizing Platform",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Enhanced custom CSS - Fixed Google Fonts URL
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #1a202c;
    }
    .stApp {
        background-color: #f7fafc;
    }
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(to right, #667eea, #764ba2);
        color: white;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #e2e8f0;
        font-size: 1.1rem;
    }
    .stButton>button {
        background-color: #4c51bf;
        color: white;
        font-weight: 600;
        border-radius: 0.5rem;
        border: none;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #5a67d8;
        transform: translateY(-2px);
        box_shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #e2e8f0;
        color: #4a5568;
        border-radius: 0.5rem 0.5rem 0 0;
        margin-right: 0.25rem;
        padding: 0.75rem 1.25rem;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: #cbd5e0;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #ffffff;
        color: #4c51bf;
        border-bottom: 3px solid #4c51bf;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0 0.5rem 0.5rem 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .stProgress > div > div > div > div {
        background-color: #4c51bf;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .status-success {
        background-color: #d1fae5;
        color: #065f46;
    }
    .status-error {
        background-color: #fee2e2;
        color: #991b1b;
    }
    .stAlert {
        border-radius: 0.5rem;
    }
    code {
        background-color: #edf2f7;
        padding: 0.2em 0.4em;
        border-radius: 0.2rem;
        font-family: 'Fira Code', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Constants for regions and OS for dropdowns
AWS_REGIONS = {
    "US East (N. Virginia)": "us-east-1",
    "US East (Ohio)": "us-east-2",
    "US West (N. California)": "us-west-1",
    "US West (Oregon)": "us-west-2",
    "Europe (Ireland)": "eu-west-1",
    "Europe (Frankfurt)": "eu-central-1",
    "Asia Pacific (Singapore)": "ap-southeast-1",
    "Asia Pacific (Sydney)": "ap-southeast-2",
    "Asia Pacific (Tokyo)": "ap-northeast-1",
    "Asia Pacific (Seoul)": "ap-northeast-2",
    "Asia Pacific (Mumbai)": "ap-south-1",
    "Asia Pacific (Hong Kong)": "ap-east-1"
}

OPERATING_SYSTEMS = {
    "Linux (RHEL)": "RHEL",
    "Linux (Ubuntu)": "Ubuntu Pro",
    "Linux (Amazon Linux 2)": "Linux",
    "Windows Server": "Windows"
}

WORKLOAD_TYPES = [
    "Web Application", "Application Server", "Database Server",
    "File Server", "Compute Intensive", "Other"
]

# Instance types to exclude from recommendations
EXCLUDE_INSTANCE_TYPES = [
    "t1.micro", "m1.small", "m1.medium", "m1.large", "m1.xlarge",
    "c1.medium", "c1.xlarge", "m2.xlarge", "m2.2xlarge", "m2.4xlarge",
    "m3.medium", "m3.large", "m3.xlarge", "m3.2xlarge", "c3.large",
    "c3.xlarge", "c3.2xlarge", "c3.4xlarge", "c3.8xlarge", "r3.large",
    "r3.xlarge", "r3.2xlarge", "r3.4xlarge", "r3.8xlarge",
    "i2.xlarge", "i2.2xlarge", "i2.4xlarge", "i2.8xlarge",
    "d2.xlarge", "d2.2xlarge", "d2.4xlarge", "d2.8xlarge",
    "t2.nano", "t2.micro", "t2.small", "t2.medium", "t2.large", "t2.xlarge", "t2.2xlarge",
    "c4.large", "c4.xlarge", "c4.2xlarge", "c4.4xlarge", "c4.8xlarge",
    "m4.large", "m4.xlarge", "m4.2xlarge", "m4.4xlarge", "m4.10xlarge", "m4.16xlarge",
    "r4.large", "r4.xlarge", "r4.2xlarge", "r4.4xlarge", "r4.8xlarge", "r4.16xlarge",
    "x1.16xlarge", "x1.32xlarge", "x1e.xlarge", "x1e.2xlarge", "x1e.4xlarge", "x1e.8xlarge", "x1e.16xlarge", "x1e.32xlarge",
    "p2.xlarge", "p2.8xlarge", "p2.16xlarge", "p3.2xlarge", "p3.8xlarge", "p3.16xlarge",
    "g3.4xlarge", "g3.8xlarge", "g3.16xlarge"
]

# Simplified RI/SP discount rates
RI_SP_DISCOUNTS = {
    "On-Demand": 0.0,
    "1-Year No Upfront RI/SP": 0.30,
    "3-Year No Upfront RI/SP": 0.50
}

# Region name mapping for AWS Pricing API
PRICING_REGION_NAMES = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "eu-west-1": "Europe (Ireland)",
    "eu-central-1": "Europe (Frankfurt)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-east-1": "Asia Pacific (Hong Kong)"
}

# --- AWS Price Fetching and Calculation Logic ---
class AWSCalculator:
    def __init__(self):
        self.pricing_client = None
        self.ec2_client = None
        self.all_ec2_prices = {}
        self.all_ebs_prices = {}
        self.inputs = {}
        self._instance_details_cache = {}

    def _get_pricing_client(self):
        """Initializes the AWS Pricing client."""
        try:
            return boto3.client('pricing', region_name='us-east-1')
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credentials error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error initializing AWS Pricing client: {e}")
            return None

    def _get_ec2_client(self, region):
        """Initializes the AWS EC2 client for a specific region."""
        try:
            return boto3.client('ec2', region_name=region)
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credentials error for region {region}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error initializing AWS EC2 client for region {region}: {e}")
            return None

    def validate_aws_credentials(self):
        """Validates AWS credentials by trying to list EC2 regions."""
        try:
            ec2 = boto3.client('ec2', region_name='us-east-1')
            ec2.describe_regions()
            return True, "Successfully connected to AWS."
        except (NoCredentialsError, PartialCredentialsError):
            return False, "AWS credentials not configured or incomplete."
        except ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                return False, "Authentication failed. Check your AWS credentials and permissions."
            return False, f"AWS Client Error: {e}"
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def fetch_current_prices(self, regions_to_fetch=None):
        """
        Fetches EC2 and EBS prices for specified regions.
        If regions_to_fetch is None, it fetches for all predefined regions.
        """
        self.pricing_client = self._get_pricing_client()
        if not self.pricing_client:
            st.error("Failed to initialize AWS Pricing client. Please check your credentials.")
            return

        if regions_to_fetch is None:
            regions_to_fetch = list(AWS_REGIONS.values())
        
        # Clear existing prices for the regions we are about to fetch, or clear all if fetching all
        if regions_to_fetch == list(AWS_REGIONS.values()):
            self.all_ec2_prices = {}
            self.all_ebs_prices = {}
            self._instance_details_cache = {} # Clear instance details cache too
        else:
            for region in regions_to_fetch:
                if region in self.all_ec2_prices:
                    del self.all_ec2_prices[region]
                if region in self.all_ebs_prices:
                    del self.all_ebs_prices[region]
                if region in self._instance_details_cache:
                    del self._instance_details_cache[region]


        progress_bar_text = st.empty()
        progress_bar = st.progress(0)
        total_regions = len(regions_to_fetch)

        for i, region in enumerate(regions_to_fetch):
            progress_bar_text.text(f"Fetching prices for region: {PRICING_REGION_NAMES.get(region, region)} ({i+1}/{total_regions})...")
            progress_bar.progress((i + 1) / total_regions)
            
            try:
                # Fetch EC2 On-Demand Prices
                self.all_ec2_prices[region] = self._fetch_ec2_prices_for_region(region)
                # Fetch EBS Prices
                self.all_ebs_prices[region] = self._fetch_ebs_prices_for_region(region)
                
            except Exception as e:
                logger.error(f"Error fetching prices for {region}: {e}")
                st.warning(f"Could not fetch all prices for {PRICING_REGION_NAMES.get(region, region)}. Error: {e}")
                self.all_ec2_prices[region] = {}
                self.all_ebs_prices[region] = {}

        progress_bar_text.empty()
        progress_bar.empty()
        logger.info(f"Finished fetching prices for {len(regions_to_fetch)} regions.")

    def _fetch_ec2_prices_for_region(self, region):
        """Fetch EC2 prices for a specific region."""
        region_ec2_prices = {}
        location_name = PRICING_REGION_NAMES.get(region, region)
        
        try:
            paginator = self.pricing_client.get_paginator('get_products')
            response_iterator = paginator.paginate(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location_name},
                    {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Compute Instance'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
                ]
            )
            
            for page in response_iterator:
                for price_item in page['PriceList']:
                    try:
                        product = json.loads(price_item)
                        attributes = product['product']['attributes']
                        
                        instance_type = attributes.get('instanceType')
                        operating_system = attributes.get('operatingSystem')
                        
                        if not instance_type or not operating_system:
                            continue
                            
                        # Normalize OS names
                        if operating_system.lower() == 'linux':
                            operating_system = 'Linux'
                        elif operating_system.lower() == 'rhel':
                            operating_system = 'RHEL'
                        elif 'ubuntu' in operating_system.lower():
                            operating_system = 'Ubuntu Pro'
                        elif operating_system.lower() == 'windows':
                            operating_system = 'Windows'
                        
                        # Extract pricing information
                        terms = product.get('terms', {})
                        on_demand = terms.get('OnDemand', {})
                        
                        for term_key, term_value in on_demand.items():
                            price_dimensions = term_value.get('priceDimensions', {})
                            for price_key, price_value in price_dimensions.items():
                                price_per_unit = price_value.get('pricePerUnit', {}).get('USD', '0')
                                try:
                                    price_float = float(price_per_unit)
                                    if price_float > 0:
                                        if instance_type not in region_ec2_prices:
                                            region_ec2_prices[instance_type] = {}
                                        region_ec2_prices[instance_type][operating_system] = price_float
                                        break
                                except (ValueError, TypeError):
                                    continue
                            break
                    except (json.JSONDecodeError, KeyError) as e:
                        continue
                        
        except Exception as e:
            logger.error(f"Error fetching EC2 prices for region {region}: {e}")
            
        return region_ec2_prices

    def _fetch_ebs_prices_for_region(self, region):
        """Fetch EBS prices for a specific region."""
        region_ebs_prices = {}
        location_name = PRICING_REGION_NAMES.get(region, region)
        
        try:
            paginator = self.pricing_client.get_paginator('get_products')
            response_iterator = paginator.paginate(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location_name},
                    {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
                    {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': 'General Purpose'}
                ]
            )
            
            for page in response_iterator:
                for price_item in page['PriceList']:
                    try:
                        product = json.loads(price_item)
                        attributes = product['product']['attributes']
                        
                        volume_type = attributes.get('volumeType')
                        if volume_type != 'General Purpose':
                            continue
                            
                        terms = product.get('terms', {})
                        on_demand = terms.get('OnDemand', {})
                        
                        for term_key, term_value in on_demand.items():
                            price_dimensions = term_value.get('priceDimensions', {})
                            for price_key, price_value in price_dimensions.items():
                                price_per_unit = price_value.get('pricePerUnit', {}).get('USD', '0')
                                try:
                                    price_float = float(price_per_unit)
                                    if price_float > 0:
                                        region_ebs_prices['gp2'] = price_float
                                        return region_ebs_prices
                                except (ValueError, TypeError):
                                    continue
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue
                        
        except Exception as e:
            logger.error(f"Error fetching EBS prices for region {region}: {e}")
            
        return region_ebs_prices

    def get_instance_details(self, region):
        """Fetches detailed instance information (vCPU, Mem) for a region."""
        # Only fetch if not already in cache and region is known to have prices
        if region in self._instance_details_cache and self._instance_details_cache[region]:
            return self._instance_details_cache[region]
            
        # Ensure prices for this region are fetched before trying to get instance details
        if region not in self.all_ec2_prices or not self.all_ec2_prices[region]:
             # Attempt to fetch prices for this specific region if not present
             # This might happen if user selects a region for display that wasn't part of initial fetch
             self.fetch_current_prices(regions_to_fetch=[region])
             if region not in self.all_ec2_prices or not self.all_ec2_prices[region]:
                 logger.warning(f"Could not fetch prices for {region}. Cannot get instance details.")
                 return {}

        ec2_client = self._get_ec2_client(region)
        if not ec2_client:
            return {}

        instance_types_details = {}
        try:
            paginator = ec2_client.get_paginator('describe_instance_types')
            response_iterator = paginator.paginate()
            
            for page in response_iterator:
                for instance_type_info in page['InstanceTypes']:
                    instance_type = instance_type_info['InstanceType']
                    if instance_type not in EXCLUDE_INSTANCE_TYPES:
                        vcpus = instance_type_info['VCpuInfo']['DefaultVCpus']
                        memory_mib = instance_type_info['MemoryInfo']['SizeInMiB']
                        memory_gib = memory_mib / 1024
                        instance_types_details[instance_type] = {
                            'vCPUs': vcpus,
                            'MemoryGiB': memory_gib
                        }
                        
        except Exception as e:
            logger.error(f"Error fetching instance details for {region}: {e}")
            
        self._instance_details_cache[region] = instance_types_details
        return instance_types_details

    def calculate_cost(self, instance_type, operating_system, region, storage_gb, ri_sp_option="On-Demand"):
        """Calculates the monthly cost for a given instance and storage."""
        instance_price = self.all_ec2_prices.get(region, {}).get(instance_type, {}).get(operating_system, 0.0)
        ebs_price_per_gb = self.all_ebs_prices.get(region, {}).get('gp2', 0.1)  # Default fallback

        if instance_price == 0.0:
            logger.warning(f"Instance price not found for {instance_type}/{operating_system} in {region}")
            return {'total_cost': float('inf'), 'instance_cost': float('inf'), 'ebs_cost': float('inf'), 'os_cost': 0}

        # Apply RI/SP discount
        discount_factor = 1.0 - RI_SP_DISCOUNTS.get(ri_sp_option, 0.0)
        
        # Calculate monthly costs (730 hours per month)
        monthly_instance_cost = instance_price * 730 * discount_factor
        monthly_ebs_cost = ebs_price_per_gb * storage_gb
        os_cost_component = 0  # Included in instance cost

        total_monthly_cost = monthly_instance_cost + monthly_ebs_cost

        return {
            'total_cost': total_monthly_cost,
            'instance_cost': monthly_instance_cost,
            'ebs_cost': monthly_ebs_cost,
            'os_cost': os_cost_component
        }

    def generate_all_recommendations(self):
        """Generates recommendations for DEV, UAT, and PROD environments."""
        recommendations = {}
        environments = ['DEV', 'UAT', 'PROD']
        
        for env in environments:
            try:
                vcpus = self.inputs.get(f'{env}_vcpus', 1)
                memory = self.inputs.get(f'{env}_memory_gb', 1.0)
                storage = self.inputs.get(f'{env}_storage_gb', 20)
                os = self.inputs.get(f'{env}_os', 'Linux')
                region = self.inputs.get(f'{env}_region', 'us-east-1')
                ri_sp_option = self.inputs.get('ri_sp_option', 'On-Demand')

                logger.info(f"Generating recommendations for {env}: vCPUs={vcpus}, Mem={memory}, Storage={storage}, OS={os}, Region={region}")

                # Ensure instance details and prices for this specific region are available
                instance_details_in_region = self.get_instance_details(region)
                region_ec2_prices = self.all_ec2_prices.get(region, {})

                best_instance = None
                min_cost = float('inf')
                cost_details = {}

                # Filter and sort instance types
                available_instance_types = [
                    it for it, os_prices in region_ec2_prices.items()
                    if os in os_prices and it in instance_details_in_region and it not in EXCLUDE_INSTANCE_TYPES
                ]

                available_instance_types.sort(key=lambda x: (
                    instance_details_in_region[x]['vCPUs'], 
                    instance_details_in_region[x]['MemoryGiB']
                ))

                for instance_type in available_instance_types:
                    details = instance_details_in_region.get(instance_type)
                    if not details:
                        continue

                    if details['vCPUs'] >= vcpus and details['MemoryGiB'] >= memory:
                        current_cost_details = self.calculate_cost(instance_type, os, region, storage, ri_sp_option)
                        current_total_cost = current_cost_details['total_cost']

                        if current_total_cost < min_cost:
                            min_cost = current_total_cost
                            best_instance = instance_type
                            cost_details = current_cost_details

                if best_instance:
                    recommendations[env] = {
                        'instance_type': best_instance,
                        'vcpus': instance_details_in_region[best_instance]['vCPUs'],
                        'memory_gb': instance_details_in_region[best_instance]['MemoryGiB'],
                        'storage_gb': storage,
                        'os': os,
                        'region': region,
                        'total_cost': min_cost,
                        'instance_cost': cost_details['instance_cost'],
                        'ebs_cost': cost_details['ebs_cost'],
                        'os_cost': cost_details['os_cost'],
                        'ri_sp_option': ri_sp_option
                    }
                else:
                    recommendations[env] = {
                        'instance_type': 'No suitable instance found',
                        'vcpus': 0, 'memory_gb': 0, 'storage_gb': storage,
                        'os': os, 'region': region, 'total_cost': float('inf'),
                        'instance_cost': float('inf'), 'ebs_cost': float('inf'), 'os_cost': 0,
                        'ri_sp_option': ri_sp_option
                    }
                    
            except Exception as e:
                logger.error(f"Error generating recommendations for {env}: {e}")
                recommendations[env] = {
                    'instance_type': f'Error: {str(e)}',
                    'vcpus': 0, 'memory_gb': 0, 'storage_gb': 0,
                    'os': '', 'region': '', 'total_cost': float('inf'),
                    'instance_cost': float('inf'), 'ebs_cost': float('inf'), 'os_cost': 0,
                    'ri_sp_option': ri_sp_option
                }

        # Calculate projected costs for PROD environment
        self._calculate_projected_costs(recommendations)
        
        return recommendations

    def _calculate_projected_costs(self, recommendations):
        """Calculate projected costs for PROD environment."""
        try:
            growth_rate = self.inputs.get('growth_rate_annual', 0.0) / 100
            growth_years = self.inputs.get('growth_years', 0)

            prod_recommendation = recommendations.get('PROD', {})
            if (prod_recommendation and 
                prod_recommendation['total_cost'] != float('inf') and 
                growth_rate > 0 and growth_years > 0):
                
                projected_costs = {}
                region = prod_recommendation['region']
                os = prod_recommendation['os']
                ri_sp_option = prod_recommendation['ri_sp_option']
                
                instance_details_in_region = self.get_instance_details(region)
                region_ec2_prices = self.all_ec2_prices.get(region, {})

                for year in range(1, growth_years + 1):
                    projected_vcpus = prod_recommendation['vcpus'] * (1 + growth_rate)**year
                    projected_memory = prod_recommendation['memory_gb'] * (1 + growth_rate)**year
                    projected_storage = prod_recommendation['storage_gb'] * (1 + growth_rate)**year
                    
                    # Find best instance for projected requirements
                    best_projected_instance = None
                    min_projected_cost = float('inf')

                    available_instance_types = [
                        it for it, os_prices in region_ec2_prices.items()
                        if os in os_prices and it in instance_details_in_region and it not in EXCLUDE_INSTANCE_TYPES
                    ]
                    
                    available_instance_types.sort(key=lambda x: (
                        instance_details_in_region[x]['vCPUs'], 
                        instance_details_in_region[x]['MemoryGiB']
                    ))

                    for instance_type in available_instance_types:
                        details = instance_details_in_region.get(instance_type)
                        if not details:
                            continue
                            
                        if details['vCPUs'] >= projected_vcpus and details['MemoryGiB'] >= projected_memory:
                            cost_details = self.calculate_cost(
                                instance_type, os, region, 
                                math.ceil(projected_storage), ri_sp_option
                            )
                            
                            if cost_details['total_cost'] < min_projected_cost:
                                min_projected_cost = cost_details['total_cost']
                                best_projected_instance = instance_type

                    projected_costs[f'Year {year}'] = {
                        'vcpus': math.ceil(projected_vcpus),
                        'memory_gb': math.ceil(projected_memory),
                        'storage_gb': math.ceil(projected_storage),
                        'estimated_cost': min_projected_cost if min_projected_cost != float('inf') else 'N/A',
                        'recommended_instance': best_projected_instance if best_projected_instance else 'N/A'
                    }
                    
                recommendations['PROD']['projected_costs'] = projected_costs
                
        except Exception as e:
            logger.error(f"Error calculating projected costs: {e}")


# --- Session State Management ---
def initialize_session_state():
    """Initializes all necessary session state variables."""
    if 'workload_inputs' not in st.session_state:
        st.session_state.workload_inputs = {
            'workload_name': '',
            'workload_type': WORKLOAD_TYPES[0],
            'PROD_vcpus': 2, 'PROD_memory_gb': 4, 'PROD_storage_gb': 100, 
            'PROD_os': OPERATING_SYSTEMS["Linux (Amazon Linux 2)"], 
            'PROD_region': AWS_REGIONS["US East (N. Virginia)"],
            'UAT_vcpus': 1, 'UAT_memory_gb': 2, 'UAT_storage_gb': 50, 
            'UAT_os': OPERATING_SYSTEMS["Linux (Amazon Linux 2)"], 
            'UAT_region': AWS_REGIONS["US East (N. Virginia)"],
            'DEV_vcpus': 1, 'DEV_memory_gb': 2, 'DEV_storage_gb': 50, 
            'DEV_os': OPERATING_SYSTEMS["Linux (Amazon Linux 2)"], 
            'DEV_region': AWS_REGIONS["US East (N. Virginia)"],
            'ri_sp_option': "3-Year No Upfront RI/SP",  # Changed default to "3-Year No Upfront RI/SP"
            'growth_rate_annual': 0,
            'growth_years': 5,
            
            # On-Premise Metrics (Updated)
            'onprem_total_cpu_cores': 2, 
            'onprem_total_ram_gb': 8,
            'onprem_total_storage_gb': 100, 
            'onprem_virtual_disk_count': 1, 
            'onprem_virtual_disk_size_gb': 100, 
            'onprem_peak_cpu_utilization_percent': 70, 
            'onprem_average_cpu_utilization_percent': 40, 
            'onprem_peak_ram_utilization_percent': 60, 
            'onprem_average_ram_utilization_percent': 30, 
            'onprem_peak_iops': 1000, 
            'onprem_peak_throughput_mbps': 100, 
            'onprem_network_max_usage_mbps': 1000, 
            
            # Advanced Settings
            'enable_encryption_at_rest': True,
            'enable_performance_insights': True,
            'enable_enhanced_monitoring': False,
            'monthly_data_transfer_gb': 500,
            'backup_retention_days': 7
        }
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'bulk_upload_df' not in st.session_state:
        st.session_state.bulk_upload_df = None
    if 'bulk_results' not in st.session_state:
        st.session_state.bulk_results = None
    if 'calculator' not in st.session_state:
        st.session_state.calculator = AWSCalculator()
    if 'selected_output_region' not in st.session_state:
        st.session_state.selected_output_region = list(AWS_REGIONS.values())[0]
    if 'selected_output_env' not in st.session_state:
        st.session_state.selected_output_env = 'PROD'
    if 'selected_main_option' not in st.session_state:
        st.session_state.selected_main_option = "Configure Single Workload"
    if 'run_analysis_flag' not in st.session_state:
        st.session_state.run_analysis_flag = False


# --- UI Rendering Functions ---

def render_on_premise_details():
    """Renders the UI for existing on-premise workload details."""
    st.markdown("#### Existing On-Premise Workload Details (Current Usage)")
    st.info("Provide current *peak* resource utilization and configuration to help size for AWS.")
    
    st.markdown("##### Compute & Memory")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.workload_inputs['onprem_total_cpu_cores'] = st.number_input(
            "Total Physical CPU Cores (On-Prem)", 
            min_value=1, max_value=256, 
            value=st.session_state.workload_inputs['onprem_total_cpu_cores'], 
            step=1, 
            key="onprem_total_cpu_cores"
        )
        st.session_state.workload_inputs['onprem_total_ram_gb'] = st.number_input(
            "Total RAM (GiB) (On-Prem)", 
            min_value=1, max_value=4096, 
            value=st.session_state.workload_inputs['onprem_total_ram_gb'], 
            step=4, 
            key="onprem_total_ram_gb"
        )
    with col2:
        st.session_state.workload_inputs['onprem_peak_cpu_utilization_percent'] = st.number_input(
            "Peak CPU Utilization (%)", 
            min_value=0, max_value=100, 
            value=st.session_state.workload_inputs['onprem_peak_cpu_utilization_percent'], 
            step=5, 
            help="Highest observed CPU utilization percentage."
        )
        st.session_state.workload_inputs['onprem_peak_ram_utilization_percent'] = st.number_input(
            "Peak RAM Utilization (%)", 
            min_value=0, max_value=100, 
            value=st.session_state.workload_inputs['onprem_peak_ram_utilization_percent'], 
            step=5, 
            help="Highest observed RAM utilization percentage."
        )
    
    st.markdown("##### Storage")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.workload_inputs['onprem_total_storage_gb'] = st.number_input(
            "Total Used Storage (GB) (On-Prem)", 
            min_value=1, max_value=65536, 
            value=st.session_state.workload_inputs['onprem_total_storage_gb'], 
            step=100, 
            key="onprem_total_storage_gb_input", 
            help="Total logical storage space consumed by this workload on-premise."
        )
        st.session_state.workload_inputs['onprem_virtual_disk_count'] = st.number_input(
            "Number of Virtual Disks",
            min_value=1, max_value=32,
            value=st.session_state.workload_inputs['onprem_virtual_disk_count'],
            step=1,
            key="onprem_virtual_disk_count"
        )
    with col2:
        st.session_state.workload_inputs['onprem_virtual_disk_size_gb'] = st.number_input(
            "Average Virtual Disk Size (GB)",
            min_value=1, max_value=16384,
            value=st.session_state.workload_inputs['onprem_virtual_disk_size_gb'],
            step=10,
            key="onprem_virtual_disk_size_gb"
        )
        st.session_state.workload_inputs['onprem_peak_iops'] = st.number_input(
            "Peak Storage IOPS", 
            min_value=0, max_value=200000, 
            value=st.session_state.workload_inputs['onprem_peak_iops'], 
            step=100, 
            help="Highest observed IOPS (Input/Output Operations Per Second)."
        )

    st.markdown("##### Network")
    st.session_state.workload_inputs['onprem_network_max_usage_mbps'] = st.number_input(
        "Peak Network Usage (Mbps)", 
        min_value=0, max_value=100000, 
        value=st.session_state.workload_inputs['onprem_network_max_usage_mbps'], 
        step=100, 
        help="Highest observed network throughput in Mbps."
    )
    
    st.markdown("---")

def render_workload_configuration():
    """Renders the UI for configuring a single workload."""
    st.markdown("## 📊 Workload Requirements")

    st.session_state.workload_inputs['workload_name'] = st.text_input(
        "Workload Name (e.g., 'CRM Backend', 'Data Analytics')",
        value=st.session_state.workload_inputs['workload_name'],
        placeholder="Enter a descriptive name for your workload"
    )
    st.session_state.workload_inputs['workload_type'] = st.selectbox(
        "Workload Type",
        options=WORKLOAD_TYPES,
        index=WORKLOAD_TYPES.index(st.session_state.workload_inputs['workload_type'])
    )

    st.markdown("### Cost Optimization & Growth Projections")
    col_ri, col_growth_rate, col_growth_years = st.columns(3)
    with col_ri:
        # Default value is now set in initialize_session_state
        st.session_state.workload_inputs['ri_sp_option'] = st.selectbox(
            "Pricing Model / Commitment",
            options=list(RI_SP_DISCOUNTS.keys()),
            help="Choose between On-Demand pricing or different Reserved Instance/Savings Plan commitments.",
            index=list(RI_SP_DISCOUNTS.keys()).index(st.session_state.workload_inputs['ri_sp_option'])
        )
    with col_growth_rate:
        st.session_state.workload_inputs['growth_rate_annual'] = st.number_input(
            "Annual Growth Rate (%)",
            min_value=0, max_value=50, 
            value=st.session_state.workload_inputs['growth_rate_annual'], 
            step=1,
            help="Estimate the percentage growth of your workload's resource requirements per year."
        )
    with col_growth_years:
        st.session_state.workload_inputs['growth_years'] = st.number_input(
            "Projection Years",
            min_value=0, max_value=10, 
            value=st.session_state.workload_inputs['growth_years'], 
            step=1,
            help="Number of years to project future costs based on the annual growth rate."
        )

    st.markdown("---")
    
    # Render On-Premise Details directly here
    render_on_premise_details()

    env_tabs = st.tabs([
        "Production (PROD)", 
        "User Acceptance Testing (UAT)", 
        "Development (DEV)", 
        "Advanced Settings" # Removed "On-Premise Details" tab
    ])

    # Environment configuration tabs
    for i, env in enumerate(['PROD', 'UAT', 'DEV']):
        with env_tabs[i]:
            st.markdown(f"#### {env} Environment Requirements")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.workload_inputs[f'{env}_vcpus'] = st.number_input(
                    f"Required vCPUs ({env})", 
                    min_value=1, max_value=128, 
                    value=st.session_state.workload_inputs[f'{env}_vcpus'], 
                    step=1, 
                    key=f'{env}_vcpus_input'
                )
                st.session_state.workload_inputs[f'{env}_storage_gb'] = st.number_input(
                    f"Required Storage (GB) ({env})", 
                    min_value=1, max_value=16384, 
                    value=st.session_state.workload_inputs[f'{env}_storage_gb'], 
                    step=10, 
                    key=f'{env}_storage_gb_input', 
                    help="Storage is estimated for EBS General Purpose SSD (gp2/gp3) volumes."
                )
            with col2:
                st.session_state.workload_inputs[f'{env}_memory_gb'] = st.number_input(
                    f"Required Memory (GiB) ({env})", 
                    min_value=0.5, max_value=2048.0, 
                    value=float(st.session_state.workload_inputs[f'{env}_memory_gb']), 
                    step=0.5, 
                    key=f'{env}_memory_gb_input'
                )
                st.session_state.workload_inputs[f'{env}_os'] = st.selectbox(
                    f"Operating System ({env})", 
                    options=list(OPERATING_SYSTEMS.values()), 
                    index=list(OPERATING_SYSTEMS.values()).index(st.session_state.workload_inputs[f'{env}_os']), 
                    key=f'{env}_os_select'
                )
            
            # Region selection with error handling
            current_region_code = st.session_state.workload_inputs[f'{env}_region']
            default_region_key = "US East (N. Virginia)"
            try:
                current_region_name = next(k for k, v in AWS_REGIONS.items() if v == current_region_code)
            except StopIteration:
                logger.warning(f"Region code '{current_region_code}' not found for {env}. Defaulting to '{default_region_key}'.")
                current_region_name = default_region_key
                st.session_state.workload_inputs[f'{env}_region'] = AWS_REGIONS[default_region_key]

            selected_region_name = st.selectbox(
                f"Preferred AWS Region ({env})",
                options=list(AWS_REGIONS.keys()),
                index=list(AWS_REGIONS.keys()).index(current_region_name),
                key=f'{env}_region_select'
            )
            st.session_state.workload_inputs[f'{env}_region'] = AWS_REGIONS[selected_region_name]
            st.markdown("---")

    # Advanced Settings Tab
    with env_tabs[3]: # Index changed from 4 to 3
        st.markdown("#### Advanced Settings")
        col_enc, col_perf, col_mon = st.columns(3)
        with col_enc:
            st.session_state.workload_inputs['enable_encryption_at_rest'] = st.checkbox(
                "Enable Encryption at Rest",
                value=st.session_state.workload_inputs['enable_encryption_at_rest'],
                help="Encrypt EBS volumes and database storage."
            )
        with col_perf:
            st.session_state.workload_inputs['enable_performance_insights'] = st.checkbox(
                "Enable Performance Insights",
                value=st.session_state.workload_inputs['enable_performance_insights'],
                help="Monitor database performance with Performance Insights."
            )
        with col_mon:
            st.session_state.workload_inputs['enable_enhanced_monitoring'] = st.checkbox(
                "Enable Enhanced Monitoring",
                value=st.session_state.workload_inputs['enable_enhanced_monitoring'],
                help="Granular OS and process-level metrics for EC2 instances."
            )
        
        col_data_transfer, col_backup = st.columns(2)
        with col_data_transfer:
            st.session_state.workload_inputs['monthly_data_transfer_gb'] = st.number_input(
                "Estimated Monthly Data Transfer Out (GB)",
                min_value=0, max_value=100000, 
                value=st.session_state.workload_inputs['monthly_data_transfer_gb'], 
                step=100,
                help="Estimate outbound data transfer to the internet or other AWS regions."
            )
        with col_backup:
            st.session_state.workload_inputs['backup_retention_days'] = st.number_input(
                "Backup Retention (Days)",
                min_value=0, max_value=365, 
                value=st.session_state.workload_inputs['backup_retention_days'], 
                step=1,
                help="Number of days to retain automated backups."
            )
    
def render_analysis_results(recommendations, key_suffix=""):
    """Renders the analysis results in a user-friendly format."""
    st.markdown("## 📈 AWS Sizing Recommendations")

    # Check if recommendations are empty or contain only errors
    if not recommendations or all(rec.get('total_cost', float('inf')) == float('inf') for rec in recommendations.values()):
        st.warning("Could not generate recommendations. Please check your inputs and AWS credentials. Prices might not be available for the selected region/OS combination.")
        return

    # Data for the table
    data = []
    for env, rec in recommendations.items():
        data.append({
            "Environment": env,
            "Recommended Instance Type": rec['instance_type'],
            "vCPUs": rec['vcpus'],
            "Memory (GiB)": f"{rec['memory_gb']:.1f}",
            "Storage (GB)": rec['storage_gb'],
            "OS": rec['os'],
            "Region": PRICING_REGION_NAMES.get(rec['region'], rec['region']),
            "Pricing Model": rec['ri_sp_option'],
            "Estimated Monthly Cost": f"${rec['total_cost']:.2f}" if rec['total_cost'] != float('inf') else "N/A"
        })
    
    df_results = pd.DataFrame(data)
    st.dataframe(df_results, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Cost Breakdown by Environment")

    costs_data = []
    for env, rec in recommendations.items():
        if rec['total_cost'] != float('inf'):
            costs_data.append({
                "Environment": env,
                "Instance Cost": rec['instance_cost'],
                "EBS Cost": rec['ebs_cost'],
                "Total Cost": rec['total_cost']
            })
    df_costs = pd.DataFrame(costs_data)
    df_costs_melted = df_costs.melt(id_vars=["Environment"], var_name="Cost Type", value_name="Amount")

    if not df_costs_melted.empty:
        fig_bar = px.bar(
            df_costs_melted, 
            x="Environment", 
            y="Amount", 
            color="Cost Type", 
            title="Monthly Cost Breakdown by Environment",
            barmode='group',
            height=400,
            color_discrete_map={
                "Instance Cost": "#4c51bf",
                "EBS Cost": "#667eea",
                "Total Cost": "#a78bfa" 
            }
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No cost breakdown data available. Ensure recommendations were generated successfully.")

    prod_rec = recommendations.get('PROD', {})
    if 'projected_costs' in prod_rec and prod_rec['projected_costs']:
        st.markdown("---")
        st.markdown("### 📊 PROD Environment Projected Costs")
        projected_df = pd.DataFrame.from_dict(prod_rec['projected_costs'], orient='index')
        projected_df.index.name = "Year"
        st.dataframe(projected_df, use_container_width=True)

        # Plot projected costs
        if not projected_df.empty and 'estimated_cost' in projected_df.columns:
            projected_df['estimated_cost_numeric'] = pd.to_numeric(projected_df['estimated_cost'], errors='coerce')
            projected_df_filtered = projected_df.dropna(subset=['estimated_cost_numeric'])
            
            if not projected_df_filtered.empty:
                fig_proj = px.line(
                    projected_df_filtered, 
                    x=projected_df_filtered.index, 
                    y="estimated_cost_numeric", 
                    markers=True,
                    title="Projected PROD Environment Costs Over Time",
                    labels={"estimated_cost_numeric": "Estimated Monthly Cost ($)", "Year": "Projection Year"},
                    height=400
                )
                fig_proj.update_traces(line_color="#4c51bf", marker_color="#4c51bf")
                st.plotly_chart(fig_proj, use_container_width=True)
            else:
                st.warning("No valid projected cost data to plot.")
        else:
            st.info("No growth projection data available or configured.")

    st.markdown("---")

    # MODIFIED_CODE_BLOCK: Replaced Heatmap with Current vs. Projected Cost Comparison
    st.markdown("### Current vs. Projected Cost Comparison (PROD)")
    prod_rec = recommendations.get('PROD', {})
    if 'projected_costs' in prod_rec and prod_rec['projected_costs'] and prod_rec.get('total_cost', float('inf')) != float('inf'):
        
        # Prepare data for the comparison chart
        comparison_data = []
        
        # Add current cost (Year 0)
        comparison_data.append({
            'Year': 'Year 0',
            'Estimated Monthly Cost': prod_rec['total_cost'],
            'Type': 'Current'
        })
        
        # Add projected costs
        for year, details in prod_rec['projected_costs'].items():
            cost = details.get('estimated_cost')
            if cost != 'N/A' and isinstance(cost, (int, float)):
                comparison_data.append({
                    'Year': year,
                    'Estimated Monthly Cost': cost,
                    'Type': 'Projected'
                })

        if len(comparison_data) > 1: # Only show chart if there's something to compare
            df_comparison = pd.DataFrame(comparison_data)
            
            fig_comparison = px.bar(
                df_comparison,
                x='Year',
                y='Estimated Monthly Cost',
                color='Type',
                title='Current vs. Projected Monthly Cost for PROD Environment',
                labels={'Estimated Monthly Cost': 'Estimated Monthly Cost ($)'},
                height=450,
                color_discrete_map={'Current': '#667eea', 'Projected': '#a78bfa'}
            )
            fig_comparison.update_layout(
                xaxis_title='Year',
                yaxis_title='Estimated Monthly Cost ($)',
                legend_title='Cost Type'
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        else:
            st.info("Not enough data to generate a current vs. projected cost comparison chart.")
    else:
        st.info("No projected cost data available for the PROD environment to create a comparison chart.")


def render_bulk_analysis():
    """Renders the UI for bulk analysis."""
    st.markdown("## 📦 Bulk Workload Analysis")
    st.write("Upload a CSV file with multiple workload requirements to get recommendations for all of them at once.")

    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.bulk_upload_df = df
            st.success("CSV file uploaded successfully!")
            st.write("Preview of uploaded data:")
            st.dataframe(df.head(), use_container_width=True)

            required_columns = [
                'Workload Name', 'Workload Type', 
                'PROD_vcpus', 'PROD_memory_gb', 'PROD_storage_gb', 'PROD_os', 'PROD_region',
                'UAT_vcpus', 'UAT_memory_gb', 'UAT_storage_gb', 'UAT_os', 'UAT_region',
                'DEV_vcpus', 'DEV_memory_gb', 'DEV_storage_gb', 'DEV_os', 'DEV_region',
                'RI/SP Option', 'Growth Rate Annual (%)', 'Projection Years'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"Missing required columns in CSV: {', '.join(missing_columns)}. Please refer to the [sample template](#sample-csv-template) for the correct format.")
                st.session_state.bulk_upload_df = None
            else:
                st.info("All required columns found. Ready for analysis.")
                if st.button("Run Bulk Analysis", type="primary", use_container_width=True):
                    with st.spinner("Running bulk analysis... This might take a while for large files."):
                        bulk_results_list = []
                        total_workloads = len(df)
                        bulk_progress_bar = st.progress(0)
                        bulk_progress_text = st.empty()

                        for i, row in df.iterrows():
                            bulk_progress_text.text(f"Analyzing workload {i+1} of {total_workloads}...")
                            bulk_progress_bar.progress((i + 1) / total_workloads)

                            temp_inputs = {
                                'workload_name': row['Workload Name'],
                                'workload_type': row['Workload Type'],
                                'PROD_vcpus': row['PROD_vcpus'], 
                                'PROD_memory_gb': row['PROD_memory_gb'], 
                                'PROD_storage_gb': row['PROD_storage_gb'], 
                                'PROD_os': row['PROD_os'], 
                                'PROD_region': row['PROD_region'],
                                'UAT_vcpus': row['UAT_vcpus'], 
                                'UAT_memory_gb': row['UAT_memory_gb'], 
                                'UAT_storage_gb': row['UAT_storage_gb'], 
                                'UAT_os': row['UAT_os'], 
                                'UAT_region': row['UAT_region'],
                                'DEV_vcpus': row['DEV_vcpus'], 
                                'DEV_memory_gb': row['DEV_memory_gb'], 
                                'DEV_storage_gb': row['DEV_storage_gb'], 
                                'DEV_os': row['DEV_os'], 
                                'DEV_region': row['DEV_region'],
                                'ri_sp_option': row['RI/SP Option'],
                                'growth_rate_annual': row['Growth Rate Annual (%)'],
                                'growth_years': row['Projection Years']
                            }
                            st.session_state.calculator.inputs = temp_inputs
                            single_workload_recommendations = st.session_state.calculator.generate_all_recommendations()
                            
                            # Flatten recommendations for bulk display
                            flattened_rec = {'Workload Name': row['Workload Name']}
                            for env, rec_details in single_workload_recommendations.items():
                                for k, v in rec_details.items():
                                    if k != 'projected_costs': # Don't flatten projected costs directly
                                        flattened_rec[f'{env}_{k}'] = v
                            bulk_results_list.append(flattened_rec)
                            
                        st.session_state.bulk_results = pd.DataFrame(bulk_results_list)
                        bulk_progress_bar.empty()
                        bulk_progress_text.empty()
                        st.success("Bulk analysis completed!")
                        st.experimental_rerun() # Rerun to display results

        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            logger.error(f"CSV read error: {e}")

    st.markdown("---")
    st.markdown("### Sample CSV Template")
    st.write("You can download a sample CSV template to help you format your data correctly.")
    
    sample_data = {
        'Workload Name': ['CRM System', 'Internal Wiki'],
        'Workload Type': ['Web Application', 'Application Server'],
        'PROD_vcpus': [4, 2],
        'PROD_memory_gb': [8, 4],
        'PROD_storage_gb': [200, 100],
        'PROD_os': ['Linux', 'Windows'],
        'PROD_region': ['us-east-1', 'eu-west-1'],
        'UAT_vcpus': [2, 1],
        'UAT_memory_gb': [4, 2],
        'UAT_storage_gb': [100, 50],
        'UAT_os': ['Linux', 'Windows'],
        'UAT_region': ['us-east-1', 'eu-west-1'],
        'DEV_vcpus': [1, 1],
        'DEV_memory_gb': [2, 1],
        'DEV_storage_gb': [50, 20],
        'DEV_os': ['Linux', 'Windows'],
        'DEV_region': ['us-east-1', 'eu-west-1'],
        'RI/SP Option': ['3-Year No Upfront RI/SP', '1-Year No Upfront RI/SP'],
        'Growth Rate Annual (%)': [10, 5],
        'Projection Years': [3, 2]
    }
    sample_df = pd.DataFrame(sample_data)
    
    csv_buffer = io.StringIO()
    sample_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Sample CSV Template",
        data=csv_buffer.getvalue(),
        file_name="sample_workloads_template.csv",
        mime="text/csv",
        help="Click to download a CSV template with the expected column headers."
    )

def display_bulk_analysis_results(bulk_results_df):
    """Displays the results of a bulk analysis."""
    st.markdown("### Bulk Analysis Results")
    st.dataframe(bulk_results_df, use_container_width=True, hide_index=True)

    # Optional: Download bulk results
    csv_export = bulk_results_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Bulk Results as CSV",
        data=csv_export,
        file_name=f"bulk_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="download_bulk_csv"
    )

    excel_export = BytesIO()
    with pd.ExcelWriter(excel_export, engine='xlsxwriter') as writer:
        bulk_results_df.to_excel(writer, index=False, sheet_name='Bulk Analysis Results')
    st.download_button(
        label="Download Bulk Results as Excel",
        data=excel_export.getvalue(),
        file_name=f"bulk_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_bulk_excel"
    )

    st.markdown("---")

def create_pdf_report(recommendations, workload_inputs, bulk_results_df=None):
    """Generates a PDF report from the analysis results."""
    if not REPORTLAB_AVAILABLE:
        st.error("PDF generation library (reportlab) not found. Please install it to enable PDF exports (`pip install reportlab`).")
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch/2, leftMargin=inch/2,
                            topMargin=inch/2, bottomMargin=inch/2)
    styles = getSampleStyleSheet()
    
    # --- FIX ---
    # Define custom styles that are not present in the default stylesheet.
    # Modify existing styles for customization.
    styles.add(ParagraphStyle(name='Heading1Centered', alignment=TA_CENTER, fontSize=20, leading=24, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Small', fontSize=8, leading=10, fontName='Helvetica'))
    
    # Modify existing styles
    styles['h2'].fontName = 'Helvetica-Bold'
    styles['h2'].fontSize = 14
    styles['h2'].leading = 16
    styles['h2'].alignment = TA_LEFT
    
    story = []

    # Title Page
    story.append(Paragraph("Enterprise AWS Workload Sizing Platform", styles['Heading1Centered']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Cloud Migration Cost Analysis Report", styles['h2']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph("Generated by AWS Workload Sizing Platform v3.1", styles['Small']))
    story.append(PageBreak())

    # Workload Configuration Summary
    story.append(Paragraph("1. Workload Configuration Summary", styles['h2']))
    story.append(Paragraph(f"<b>Workload Name:</b> {workload_inputs.get('workload_name', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"<b>Workload Type:</b> {workload_inputs.get('workload_type', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"<b>Pricing Model:</b> {workload_inputs.get('ri_sp_option', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"<b>Annual Growth Rate:</b> {workload_inputs.get('growth_rate_annual', 0)}%", styles['Normal']))
    story.append(Paragraph(f"<b>Projection Years:</b> {workload_inputs.get('growth_years', 0)}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # On-Premise Details (if applicable)
    story.append(Paragraph("1.1 On-Premise Details", styles['h3']))
    onprem_data = [
        ['Metric', 'Value'],
        ['Total Physical CPU Cores', workload_inputs.get('onprem_total_cpu_cores', 'N/A')],
        ['Total RAM (GiB)', workload_inputs.get('onprem_total_ram_gb', 'N/A')],
        ['Total Used Storage (GB)', workload_inputs.get('onprem_total_storage_gb', 'N/A')],
        ['Peak CPU Utilization (%)', workload_inputs.get('onprem_peak_cpu_utilization_percent', 'N/A')],
        ['Peak RAM Utilization (%)', workload_inputs.get('onprem_peak_ram_utilization_percent', 'N/A')],
        ['Number of Virtual Disks', workload_inputs.get('onprem_virtual_disk_count', 'N/A')],
        ['Average Virtual Disk Size (GB)', workload_inputs.get('onprem_virtual_disk_size_gb', 'N/A')],
        ['Peak Storage IOPS', workload_inputs.get('onprem_peak_iops', 'N/A')],
        ['Peak Network Usage (Mbps)', workload_inputs.get('onprem_network_max_usage_mbps', 'N/A')]
    ]
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4c51bf')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ])
    table = Table(onprem_data)
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))
    story.append(PageBreak())

    # Recommendations Table
    story.append(Paragraph("2. AWS Sizing Recommendations", styles['h2']))
    
    # Prepare data for the table
    rec_table_data = [
        ["Environment", "Recommended Instance Type", "vCPUs", "Memory (GiB)", "Storage (GB)", "OS", "Region", "Estimated Monthly Cost"]
    ]
    for env, rec in recommendations.items():
        if rec['total_cost'] != float('inf'):
            rec_table_data.append([
                env,
                rec['instance_type'],
                str(rec['vcpus']),
                f"{rec['memory_gb']:.1f}",
                str(rec['storage_gb']),
                rec['os'],
                PRICING_REGION_NAMES.get(rec['region'], rec['region']),
                f"${rec['total_cost']:.2f}"
            ])
        else:
            rec_table_data.append([
                env, "N/A", "N/A", "N/A", str(rec['storage_gb']), rec['os'], 
                PRICING_REGION_NAMES.get(rec['region'], rec['region']), "N/A"
            ])

    # Table style for recommendations
    rec_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4c51bf')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ])
    
    rec_table = Table(rec_table_data, colWidths=[1.0*inch, 1.2*inch, 0.6*inch, 1.0*inch, 1.0*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    rec_table.setStyle(rec_table_style)
    story.append(rec_table)
    story.append(Spacer(1, 0.2 * inch))

    # Cost Breakdown Chart (placeholder - can't embed Plotly directly in ReportLab)
    story.append(Paragraph("2.1 Cost Breakdown by Environment (See application for interactive chart)", styles['h3']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("A detailed bar chart showing instance, EBS, and total costs per environment is available in the web application.", styles['Italic']))
    story.append(Spacer(1, 0.2 * inch))


    # Projected Costs (PROD Environment)
    prod_rec = recommendations.get('PROD', {})
    if 'projected_costs' in prod_rec and prod_rec['projected_costs']:
        story.append(Paragraph("2.2 PROD Environment Projected Costs", styles['h3']))
        projected_data = [
            ["Year", "vCPUs", "Memory (GiB)", "Storage (GB)", "Estimated Monthly Cost", "Recommended Instance"]
        ]
        for year, proj_details in prod_rec['projected_costs'].items():
            projected_data.append([
                year,
                str(proj_details['vcpus']),
                str(proj_details['memory_gb']),
                str(proj_details['storage_gb']),
                f"${proj_details['estimated_cost']:.2f}" if proj_details['estimated_cost'] != 'N/A' else 'N/A',
                proj_details['recommended_instance']
            ])
        
        proj_table = Table(projected_data)
        proj_table.setStyle(rec_table_style) # Re-use similar style
        story.append(proj_table)
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("A line chart illustrating projected costs over time is available in the web application.", styles['Italic']))
        story.append(PageBreak())

    # Bulk Analysis Results (if provided)
    if bulk_results_df is not None and not bulk_results_df.empty:
        story.append(Paragraph("3. Bulk Analysis Results", styles['h2']))
        story.append(Spacer(1, 0.1 * inch))

        # Convert DataFrame to list of lists for ReportLab Table
        bulk_data = [bulk_results_df.columns.tolist()] + bulk_results_df.values.tolist()
        
        # Determine column widths dynamically for bulk analysis table
        num_cols = len(bulk_results_df.columns)
        col_widths = [(letter[0] - inch) / num_cols] * num_cols # Divide available width evenly
        
        bulk_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4c51bf')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('FONTSIZE', (0,0), (-1,-1), 8), # Smaller font for bulk
        ])

        # Handle potential for too many columns in bulk results
        max_cols_per_page = 8 # Adjust as needed
        if num_cols > max_cols_per_page:
            st.warning(f"Bulk results have too many columns ({num_cols}) for a readable PDF. Only showing first {max_cols_per_page} columns.")
            bulk_data_truncated = [row[:max_cols_per_page] for row in bulk_data]
            col_widths_truncated = [(letter[0] - inch) / max_cols_per_page] * max_cols_per_page
            bulk_table = Table(bulk_data_truncated, colWidths=col_widths_truncated)
        else:
            bulk_table = Table(bulk_data, colWidths=col_widths)
            
        bulk_table.setStyle(bulk_table_style)
        story.append(bulk_table)
        story.append(PageBreak())

    # Footer
    story.append(Paragraph("--- End of Report ---", styles['Small'], alignment=TA_CENTER))

    try:
        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error building PDF: {e}")
        st.error(f"Failed to generate PDF report: {e}")
        return None

def render_reports_export():
    """Renders the reports and export options."""
    st.markdown("## 📥 Reports & Export")

    # Single Workload Report
    if st.session_state.analysis_results:
        st.markdown("### Single Workload Analysis Report")
        col_pdf, col_json = st.columns(2)
        with col_pdf:
            pdf_report = create_pdf_report(
                st.session_state.analysis_results['recommendations'], 
                st.session_state.analysis_results['inputs']
            )
            if pdf_report:
                st.download_button(
                    label="Download PDF Report (Single Workload)",
                    data=pdf_report,
                    file_name=f"aws_sizing_report_{st.session_state.analysis_results['inputs'].get('workload_name', 'single_workload').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
        with col_json:
            analysis_json = json.dumps(st.session_state.analysis_results, indent=2)
            st.download_button(
                label="Download JSON Results (Single Workload)",
                data=analysis_json.encode('utf-8'),
                file_name=f"aws_sizing_results_{st.session_state.analysis_results['inputs'].get('workload_name', 'single_workload').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("Run a single workload analysis first to generate a report.")

    st.markdown("---")
    
    # Bulk Analysis Report
    if st.session_state.bulk_results is not None and not st.session_state.bulk_results.empty:
        st.markdown("### Bulk Analysis Report Options")
        st.write("Bulk results are available for download in CSV/Excel format in the 'Bulk Analysis' section.")
        
        # Option to generate a single PDF for bulk, but this can be very large
        if REPORTLAB_AVAILABLE:
            if st.button("Generate Combined PDF Report (Bulk Results)", help="Generates a single PDF report containing all bulk analysis results. This may take time for large datasets and might be less readable.", key="bulk_pdf_gen_btn"):
                with st.spinner("Generating combined PDF for bulk results..."):
                    # For bulk PDF, we pass the bulk_results_df
                    bulk_pdf_report = create_pdf_report(
                        recommendations={}, # No single workload recommendations for bulk PDF
                        workload_inputs={}, # No single workload inputs for bulk PDF
                        bulk_results_df=st.session_state.bulk_results
                    )
                    if bulk_pdf_report:
                        st.download_button(
                            label="Download Combined PDF Report (Bulk)",
                            data=bulk_pdf_report,
                            file_name=f"aws_bulk_sizing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            key="download_combined_bulk_pdf"
                        )
    else:
        st.info("Run a bulk analysis first to generate bulk reports.")

# --- Main Application Logic ---
def main():
    initialize_session_state()

    st.markdown("""
        <div class="main-header">
            <h1>Enterprise AWS EC2 Workload Sizing Platform</h1>
            <p>Comprehensive cloud migration planning for enterprise infrastructure</p>
        </div>
    """, unsafe_allow_html=True)

    # AWS Credentials Check (can be in sidebar or an initial step)
    st.sidebar.markdown("### AWS Configuration")
    aws_access_key_id = st.sidebar.text_input("AWS Access Key ID", type="password", key="aws_access_key_id")
    aws_secret_access_key = st.sidebar.text_input("AWS Secret Access Key", type="password", key="aws_secret_access_key")
    
    os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key

    if st.sidebar.button("Validate AWS Credentials"):
        is_valid, message = st.session_state.calculator.validate_aws_credentials()
        if is_valid:
            st.sidebar.success(message)
            # Fetch prices only if credentials are valid and not already fetched
            if not st.session_state.calculator.all_ec2_prices:
                with st.spinner("Fetching latest AWS pricing data... This may take a moment."):
                    st.session_state.calculator.fetch_current_prices()
                    st.sidebar.success("AWS pricing data fetched successfully!")
        else:
            st.sidebar.error(message)

    if not st.session_state.calculator.all_ec2_prices:
        st.warning("Please validate AWS credentials and fetch pricing data to proceed with analysis.")
    
    st.markdown("---")

    # Main option selection: Single Workload vs Bulk Analysis
    st.session_state.selected_main_option = st.radio(
        "Choose an analysis type:",
        ("Configure Single Workload", "Perform Bulk Analysis"),
        index=0 if st.session_state.selected_main_option == "Configure Single Workload" else 1,
        help="Select whether to analyze a single workload or upload a CSV for multiple workloads."
    )

    if st.session_state.selected_main_option == "Configure Single Workload":
        render_workload_configuration()
        
        st.markdown("---")
        
        # Analyze Workload button
        if st.button("Analyze Workload", type="primary", use_container_width=True, key="single_workload_analyze_btn"):
            if not st.session_state.calculator.all_ec2_prices:
                st.error("Please fetch AWS pricing data first via the sidebar.")
            else:
                st.session_state.run_analysis_flag = True
                st.session_state.analysis_results = None # Clear previous results
                st.session_state.calculator.inputs = st.session_state.workload_inputs.copy()
                with st.spinner("Analyzing workload and generating recommendations..."):
                    try:
                        results = st.session_state.calculator.generate_all_recommendations()
                        st.session_state.analysis_results = {
                            'inputs': st.session_state.workload_inputs.copy(),
                            'recommendations': results
                        }
                        st.success("✅ Analysis completed successfully!")
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
                        logger.error(f"Analysis error: {e}")
        
        # Display analysis results if available
        if st.session_state.analysis_results:
            st.markdown("---")
            render_analysis_results(
                st.session_state.analysis_results['recommendations'], 
                key_suffix="single_workload"
            )

    elif st.session_state.selected_main_option == "Perform Bulk Analysis":
        render_bulk_analysis()
        if st.session_state.bulk_results:
            st.markdown("---")
            display_bulk_analysis_results(st.session_state.bulk_results)
    
    st.markdown("---")
    # Reports & Export section always visible at the end
    render_reports_export()

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <strong>Enterprise AWS Workload Sizing Platform v3.1</strong><br>
        Comprehensive cloud migration planning for enterprise infrastructure
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()