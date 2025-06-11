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

# Enhanced custom CSS
st.markdown("""
<style>
    @import url('https://fonts.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #1a202c; /* Darker text for headers */
    }
    .stApp {
        background-color: #f7fafc; /* Light gray background */
    }
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(to right, #667eea, #764ba2); /* Gradient header */
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
        background-color: #4c51bf; /* Deeper primary color */
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
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #e2e8f0; /* Light tab background */
        color: #4a5568; /* Darker tab text */
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
        background-color: #ffffff; /* Active tab background */
        color: #4c51bf; /* Active tab text */
        border-bottom: 3px solid #4c51bf; /* Active tab underline */
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
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div > div {
        background-color: #4c51bf; /* Progress bar color */
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
        background-color: #d1fae5; /* Green light */
        color: #065f46; /* Green dark */
    }
    .status-error {
        background-color: #fee2e2; /* Red light */
        color: #991b1b; /* Red dark */
    }
    .stAlert {
        border-radius: 0.5rem;
    }
    code {
        background-color: #edf2f7;
        padding: 0.2em 0.4em;
        border-radius: 0.2rem;
        font-family: 'Fira Code', monospace; /* Monospaced font for code */
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

# Instance types to exclude from recommendations based on common deprecation/performance issues
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

# Simplified RI/SP discount rates (for demonstration purposes only)
# In a real application, you would fetch actual RI/SP pricing from AWS.
RI_SP_DISCOUNTS = {
    "On-Demand": 0.0,
    "1-Year No Upfront RI/SP": 0.30,  # 30% discount
    "3-Year No Upfront RI/SP": 0.50   # 50% discount
}

# --- AWS Price Fetching and Calculation Logic ---
class AWSCalculator:
    def __init__(self):
        self.pricing_client = None
        self.ec2_client = None
        self.all_ec2_prices = {}
        self.all_ebs_prices = {}
        self.inputs = {}

    @lru_cache(maxsize=1)
    def _get_pricing_client(self):
        """Initializes and caches the AWS Pricing client."""
        try:
            return boto3.client('pricing', region_name='us-east-1')
        except NoCredentialsError:
            st.error("AWS credentials not found. Please configure them.")
            return None
        except PartialCredentialsError:
            st.error("Partial AWS credentials found. Please ensure they are complete.")
            return None
        except Exception as e:
            st.error(f"Error initializing AWS Pricing client: {e}")
            return None

    @lru_cache(maxsize=1)
    def _get_ec2_client(self, region):
        """Initializes and caches the AWS EC2 client for a specific region."""
        try:
            return boto3.client('ec2', region_name=region)
        except NoCredentialsError:
            st.error("AWS credentials not found. Please configure them.")
            return None
        except PartialCredentialsError:
            st.error("Partial AWS credentials found. Please ensure they are complete.")
            return None
        except Exception as e:
            st.error(f"Error initializing AWS EC2 client for region {region}: {e}")
            return None

    def validate_aws_credentials(self):
        """Validates AWS credentials by trying to list EC2 regions."""
        try:
            ec2 = boto3.client('ec2', region_name='us-east-1')
            _ = ec2.describe_regions()
            return True, "Successfully connected to AWS."
        except (NoCredentialsError, PartialCredentialsError):
            return False, "AWS credentials not configured or incomplete."
        except ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                return False, "Authentication failed. Check your AWS credentials and permissions."
            return False, f"AWS Client Error: {e}"
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def fetch_current_prices(self):
        """Fetches EC2 and EBS prices for all regions."""
        self.pricing_client = self._get_pricing_client()
        if not self.pricing_client:
            return

        self.all_ec2_prices = {}
        self.all_ebs_prices = {}

        regions_to_fetch = list(AWS_REGIONS.values())
        progress_bar_text = st.empty()
        progress_bar = st.progress(0)
        total_regions = len(regions_to_fetch)

        for i, region in enumerate(regions_to_fetch):
            progress_bar_text.text(f"Fetching prices for region: {region} ({i+1}/{total_regions})...")
            progress_bar.progress((i + 1) / total_regions)
            try:
                # Fetch EC2 On-Demand Prices
                ec2_response_iterator = self.pricing_client.get_paginator('get_products').paginate(
                    ServiceCode='AmazonEC2',
                    Filters=[
                        {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                        {'Type': 'TERM_MATCH', 'Field': 'operation', 'Value': 'RunInstances'},
                        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Compute Instance'},
                        {'Type': 'TERM_MATCH', 'Field': 'usageType', 'Value': f'BoxUsage:{region}'},
                    ]
                )
                region_ec2_prices = {}
                for page in ec2_response_iterator:
                    for price_item in page['PriceList']:
                        attributes = json.loads(price_item['Product']['attributes'])
                        instance_type = attributes.get('instanceType')
                        operating_system = attributes.get('operatingSystem')
                        
                        # Handle varied OS naming from AWS Pricing API
                        if operating_system == 'Linux':
                            if 'RHEL' in attributes.get('softwareIncluded', ''):
                                operating_system = 'RHEL'
                            elif 'Ubuntu Pro' in attributes.get('softwareIncluded', ''):
                                operating_system = 'Ubuntu Pro'
                            else:
                                operating_system = 'Linux' # Default for Amazon Linux / other generic Linux
                        elif operating_system == 'Windows':
                            operating_system = 'Windows' # Simple Windows Server
                        
                        price_dimensions = price_item['PublicationPricingInfo']['terms']['OnDemand']
                        for term_key in price_dimensions:
                            for price_code in price_dimensions[term_key]['priceDimensions']:
                                price_per_unit = float(price_dimensions[term_key]['priceDimensions'][price_code]['pricePerUnit']['USD'])
                                if instance_type and operating_system and price_per_unit > 0:
                                    if instance_type not in region_ec2_prices:
                                        region_ec2_prices[instance_type] = {}
                                    region_ec2_prices[instance_type][operating_system] = price_per_unit
                self.all_ec2_prices[region] = region_ec2_prices

                # Fetch EBS Prices (gp2 for now, as gp3 has specific pricing attributes for throughput/IOPS)
                ebs_response_iterator = self.pricing_client.get_paginator('get_products').paginate(
                    ServiceCode='AmazonEC2',
                    Filters=[
                        {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': 'General Purpose'}, # This usually maps to gp2
                        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': next(k for k, v in AWS_REGIONS.items() if v == region)}, # Use location name
                        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
                        {'Type': 'TERM_MATCH', 'Field': 'usageType', 'Value': f'EBS:VolumeUsage.gp2'} # Ensure gp2 specifically
                    ]
                )
                region_ebs_prices = {}
                for page in ebs_response_iterator:
                    for price_item in page['PriceList']:
                        attributes = json.loads(price_item['Product']['attributes'])
                        volume_type = attributes.get('volumeType')
                        if volume_type == 'General Purpose': # Targeting gp2
                            price_dimensions = price_item['PublicationPricingInfo']['terms']['OnDemand']
                            for term_key in price_dimensions:
                                for price_code in price_dimensions[term_key]['priceDimensions']:
                                    price_per_unit = float(price_dimensions[term_key]['priceDimensions'][price_code]['pricePerUnit']['USD'])
                                    if price_per_unit > 0:
                                        # Assuming gp2 price per GB-month
                                        region_ebs_prices['gp2'] = price_per_unit
                                        break # Found price, no need to look further
                            if 'gp2' in region_ebs_prices:
                                break
                    if 'gp2' in region_ebs_prices:
                        break # Found price, no need to look further

                self.all_ebs_prices[region] = region_ebs_prices

            except Exception as e:
                logger.error(f"Error fetching prices for {region}: {e}")
                st.warning(f"Could not fetch all prices for {region}. Some recommendations might be incomplete. Error: {e}")
                self.all_ec2_prices[region] = {} # Ensure region is in dict even if empty
                self.all_ebs_prices[region] = {}

        progress_bar_text.empty()
        progress_bar.empty()
        logger.info("Finished fetching prices.")

    @lru_cache(maxsize=None) # Cache instance details
    def get_instance_details(self, region):
        """Fetches detailed instance information (vCPU, Mem) for a region."""
        self.ec2_client = self._get_ec2_client(region)
        if not self.ec2_client:
            return {}

        instance_types_details = {}
        try:
            paginator = self.ec2_client.get_paginator('describe_instance_types')
            response_iterator = paginator.paginate()
            for page in response_iterator:
                for instance_type_info in page['InstanceTypes']:
                    instance_type = instance_type_info['InstanceType']
                    # Filter out excluded types here to reduce processing
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
            st.error(f"Error fetching instance details for {region}: {e}")
        return instance_types_details

    def calculate_cost(self, instance_type, operating_system, region, storage_gb, ri_sp_option="On-Demand"):
        """Calculates the monthly cost for a given instance and storage, applying RI/SP discounts."""
        instance_price = self.all_ec2_prices.get(region, {}).get(instance_type, {}).get(operating_system, 0.0)
        ebs_price_per_gb = self.all_ebs_prices.get(region, {}).get('gp2', 0.0)

        if instance_price == 0.0:
            logger.warning(f"Instance price not found for {instance_type}/{operating_system} in {region}")
            return {'total_cost': float('inf'), 'instance_cost': float('inf'), 'ebs_cost': float('inf'), 'os_cost': 0}

        # Apply RI/SP discount (simplified)
        discount_factor = 1.0 - RI_SP_DISCOUNTS.get(ri_sp_option, 0.0)
        
        # Assume 730 hours in a month (24*365/12)
        monthly_instance_cost = instance_price * 730 * discount_factor
        monthly_ebs_cost = ebs_price_per_gb * storage_gb # EBS is typically per GB-month
        
        # This model doesn't explicitly separate OS cost from instance cost for Windows/RHEL.
        # It's generally baked into the instance price for billed OS.
        # If specific OS costs needed to be broken out, the pricing API parsing would need to be more granular.
        os_cost_component = 0 # Placeholder for now, assume baked into instance_price

        total_monthly_cost = monthly_instance_cost + monthly_ebs_cost

        return {
            'total_cost': total_monthly_cost,
            'instance_cost': monthly_instance_cost,
            'ebs_cost': monthly_ebs_cost,
            'os_cost': os_cost_component # Currently 0 as it's part of instance_cost
        }

    def generate_all_recommendations(self):
        """Generates recommendations for DEV, UAT, and PROD environments."""
        self.inputs = st.session_state.workload_inputs.copy()
        recommendations = {}

        environments = ['DEV', 'UAT', 'PROD']
        for env in environments:
            vcpus = self.inputs[f'{env}_vcpus']
            memory = self.inputs[f'{env}_memory_gb']
            storage = self.inputs[f'{env}_storage_gb']
            os = self.inputs[f'{env}_os']
            region = self.inputs[f'{env}_region']
            ri_sp_option = self.inputs['ri_sp_option']

            logger.info(f"Generating recommendations for {env}: vCPUs={vcpus}, Mem={memory}, Storage={storage}, OS={os}, Region={region}, RI/SP={ri_sp_option}")

            instance_details_in_region = self.get_instance_details(region)
            region_ec2_prices = self.all_ec2_prices.get(region, {})

            best_instance = None
            min_cost = float('inf')
            cost_details = {}

            # Filter instance types by OS and exclude list
            available_instance_types = [
                it for it, os_prices in region_ec2_prices.items()
                if os in os_prices and it in instance_details_in_region and it not in EXCLUDE_INSTANCE_TYPES
            ]

            # Sort by vCPUs and then Memory for more deterministic recommendations
            available_instance_types.sort(key=lambda x: (instance_details_in_region[x]['vCPUs'], instance_details_in_region[x]['MemoryGiB']))

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

        # Calculate projected costs for PROD environment
        growth_rate = self.inputs.get('growth_rate_annual', 0.0) / 100
        growth_years = self.inputs.get('growth_years', 0)

        prod_recommendation = recommendations.get('PROD', {})
        if prod_recommendation and prod_recommendation['total_cost'] != float('inf') and growth_rate > 0 and growth_years > 0:
            initial_prod_cost = prod_recommendation['total_cost']
            projected_costs = {}
            for year in range(1, growth_years + 1):
                projected_vcpus = prod_recommendation['vcpus'] * (1 + growth_rate)**year
                projected_memory = prod_recommendation['memory_gb'] * (1 + growth_rate)**year
                projected_storage = prod_recommendation['storage_gb'] * (1 + growth_rate)**year
                
                # Re-evaluate instance type for projected growth
                best_projected_instance = None
                min_projected_cost = float('inf')

                instance_details_in_region = self.get_instance_details(prod_recommendation['region'])
                region_ec2_prices = self.all_ec2_prices.get(prod_recommendation['region'], {})

                available_instance_types = [
                    it for it, os_prices in region_ec2_prices.items()
                    if prod_recommendation['os'] in os_prices and it in instance_details_in_region and it not in EXCLUDE_INSTANCE_TYPES
                ]
                available_instance_types.sort(key=lambda x: (instance_details_in_region[x]['vCPUs'], instance_details_in_region[x]['MemoryGiB']))

                for instance_type in available_instance_types:
                    details = instance_details_in_region.get(instance_type)
                    if not details:
                        continue
                    if details['vCPUs'] >= projected_vcpus and details['MemoryGiB'] >= projected_memory:
                        current_projected_cost_details = self.calculate_cost(instance_type, prod_recommendation['os'], prod_recommendation['region'], projected_storage, ri_sp_option)
                        current_projected_total_cost = current_projected_cost_details['total_cost']
                        if current_projected_total_cost < min_projected_cost:
                            min_projected_cost = current_projected_total_cost
                            best_projected_instance = instance_type

                projected_costs[f'Year {year}'] = {
                    'vcpus': math.ceil(projected_vcpus),
                    'memory_gb': math.ceil(projected_memory),
                    'storage_gb': math.ceil(projected_storage),
                    'estimated_cost': min_projected_cost if min_projected_cost != float('inf') else 'N/A',
                    'recommended_instance': best_projected_instance if best_projected_instance else 'N/A'
                }
            recommendations['PROD']['projected_costs'] = projected_costs

        return recommendations


# --- Streamlit UI Components ---

def initialize_session_state():
    """Initializes all necessary session state variables."""
    if 'workload_inputs' not in st.session_state:
        st.session_state.workload_inputs = {
            'workload_name': '',
            'workload_type': WORKLOAD_TYPES[0],
            'PROD_vcpus': 2, 'PROD_memory_gb': 4, 'PROD_storage_gb': 100, 'PROD_os': OPERATING_SYSTEMS["Linux (Amazon Linux 2)"], 'PROD_region': AWS_REGIONS["US East (N. Virginia)"],
            'UAT_vcpus': 1, 'UAT_memory_gb': 2, 'UAT_storage_gb': 50, 'UAT_os': OPERATING_SYSTEMS["Linux (Amazon Linux 2)"], 'UAT_region': AWS_REGIONS["US East (N. Virginia)"],
            'DEV_vcpus': 1, 'DEV_memory_gb': 2, 'DEV_storage_gb': 50, 'DEV_os': OPERATING_SYSTEMS["Linux (Amazon Linux 2)"], 'DEV_region': AWS_REGIONS["US East (N. Virginia)"],
            'ri_sp_option': "On-Demand", # New: RI/SP option
            'growth_rate_annual': 0,      # New: Annual growth rate
            'growth_years': 5,             # New: Number of years for projection
            
            # New On-Premise Metrics
            'onprem_cpu_cores': 2,
            'onprem_current_storage_gb': 100,
            'onprem_cpu_model': "Intel Xeon E5",
            'onprem_storage_type': "SSD",
            'onprem_cpu_speed_ghz': 2.5,
            'onprem_raid_level': "RAID 1",
            'onprem_total_ram_gb': 8,
            'onprem_ram_type': "DDR4",
            'onprem_ram_speed_mhz': 2400,
            'onprem_annual_growth_rate_percent': 10,
            'onprem_planning_horizon_years': 5,
            'onprem_peak_cpu_utilization_percent': 70,
            'onprem_average_cpu_utilization_percent': 40,
            'onprem_active_cpu_cores': 2,
            'onprem_peak_ram_utilization_percent': 60,
            'onprem_average_ram_utilization_percent': 30,
            'onprem_sga_buffer_pool_gb': 0,
            'onprem_peak_iops': 1000,
            'onprem_average_iops': 500,
            'onprem_peak_throughput_mbps': 100,
            'onprem_network_bandwidth_gbps': 10,
            'onprem_network_latency_ms': 1,
            'onprem_max_concurrent_connections': 1000,
            'onprem_average_concurrent_connections': 500,

            # New Advanced Settings
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
        st.session_state.workload_inputs['ri_sp_option'] = st.selectbox(
            "Pricing Model / Commitment",
            options=list(RI_SP_DISCOUNTS.keys()),
            help="Choose between On-Demand pricing or different Reserved Instance/Savings Plan commitments for potential discounts.",
            index=list(RI_SP_DISCOUNTS.keys()).index(st.session_state.workload_inputs['ri_sp_option'])
        )
    with col_growth_rate:
        st.session_state.workload_inputs['growth_rate_annual'] = st.number_input(
            "Annual Growth Rate (%)",
            min_value=0, max_value=50, value=st.session_state.workload_inputs['growth_rate_annual'], step=1,
            help="Estimate the percentage growth of your workload's resource requirements per year (e.g., 10 for 10%)."
        )
    with col_growth_years:
        st.session_state.workload_inputs['growth_years'] = st.number_input(
            "Projection Years",
            min_value=0, max_value=10, value=st.session_state.workload_inputs['growth_years'], step=1,
            help="Number of years to project future costs based on the annual growth rate."
        )

    st.markdown("---")

    env_tabs = st.tabs(["Production (PROD)", "User Acceptance Testing (UAT)", "Development (DEV)", "On-Premise Details", "Advanced Settings"])

    for i, env in enumerate(['PROD', 'UAT', 'DEV']):
        with env_tabs[i]:
            st.markdown(f"#### {env} Environment Requirements")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.workload_inputs[f'{env}_vcpus'] = st.number_input(
                    f"Required vCPUs ({env})",
                    min_value=1, max_value=128, value=st.session_state.workload_inputs[f'{env}_vcpus'], step=1, key=f'{env}_vcpus_input'
                )
                st.session_state.workload_inputs[f'{env}_storage_gb'] = st.number_input(
                    f"Required Storage (GB) ({env})",
                    min_value=1, max_value=16384, value=st.session_state.workload_inputs[f'{env}_storage_gb'], step=10, key=f'{env}_storage_gb_input',
                    help="Storage is estimated for EBS General Purpose SSD (gp2/gp3) volumes."
                )
            with col2:
                st.session_state.workload_inputs[f'{env}_memory_gb'] = st.number_input(
                    f"Required Memory (GiB) ({env})",
                    min_value=0.5, max_value=2048.0, value=float(st.session_state.workload_inputs[f'{env}_memory_gb']), step=0.5, key=f'{env}_memory_gb_input'
                )
                st.session_state.workload_inputs[f'{env}_os'] = st.selectbox(
                    f"Operating System ({env})",
                    options=list(OPERATING_SYSTEMS.values()),
                    index=list(OPERATING_SYSTEMS.values()).index(st.session_state.workload_inputs[f'{env}_os']), key=f'{env}_os_select'
                )
            st.session_state.workload_inputs[f'{env}_region'] = st.selectbox(
                f"Preferred AWS Region ({env})",
                options=list(AWS_REGIONS.keys()),
                format_func=lambda x: x,
                index=list(AWS_REGIONS.keys()).index(next(k for k, v in AWS_REGIONS.items() if v == st.session_state.workload_inputs[f'{env}_region'])), key=f'{env}_region_select'
            )
            st.markdown("---")
    
    with env_tabs[3]: # On-Premise Details Tab
        st.markdown("#### Existing On-Premise Workload Details")
        st.markdown("##### Compute")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.workload_inputs['onprem_cpu_cores'] = st.number_input("CPU Cores", min_value=1, max_value=256, value=st.session_state.workload_inputs['onprem_cpu_cores'], step=1, key="onprem_cpu_cores")
            st.session_state.workload_inputs['onprem_cpu_model'] = st.text_input("CPU Model", value=st.session_state.workload_inputs['onprem_cpu_model'], key="onprem_cpu_model")
        with col2:
            st.session_state.workload_inputs['onprem_current_storage_gb'] = st.number_input("Current Storage (GB)", min_value=1, max_value=65536, value=st.session_state.workload_inputs['onprem_current_storage_gb'], step=100, key="onprem_current_storage_gb")
            st.session_state.workload_inputs['onprem_storage_type'] = st.selectbox("Storage Type", options=["HDD", "SSD", "NVMe", "SAN", "NAS"], index=["HDD", "SSD", "NVMe", "SAN", "NAS"].index(st.session_state.workload_inputs['onprem_storage_type']), key="onprem_storage_type")
        with col3:
            st.session_state.workload_inputs['onprem_cpu_speed_ghz'] = st.number_input("CPU Speed (GHz)", min_value=0.1, max_value=5.0, value=st.session_state.workload_inputs['onprem_cpu_speed_ghz'], step=0.1, format="%.1f", key="onprem_cpu_speed_ghz")
            st.session_state.workload_inputs['onprem_raid_level'] = st.text_input("RAID Level (If Applicable)", value=st.session_state.workload_inputs['onprem_raid_level'], key="onprem_raid_level")

        st.markdown("##### Memory Resources")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.workload_inputs['onprem_total_ram_gb'] = st.number_input("Total RAM (GB)", min_value=1, max_value=4096, value=st.session_state.workload_inputs['onprem_total_ram_gb'], step=4, key="onprem_total_ram_gb")
        with col2:
            st.session_state.workload_inputs['onprem_ram_type'] = st.text_input("RAM Type", value=st.session_state.workload_inputs['onprem_ram_type'], key="onprem_ram_type")
        with col3:
            st.session_state.workload_inputs['onprem_ram_speed_mhz'] = st.number_input("RAM Speed (MHz)", min_value=1000, max_value=5000, value=st.session_state.workload_inputs['onprem_ram_speed_mhz'], step=100, key="onprem_ram_speed_mhz")

        st.markdown("##### Growth & Planning (On-Premise Baseline)")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.workload_inputs['onprem_annual_growth_rate_percent'] = st.number_input("Annual Growth Rate (%)", min_value=0, max_value=50, value=st.session_state.workload_inputs['onprem_annual_growth_rate_percent'], step=1, key="onprem_annual_growth_rate_percent")
        with col2:
            st.session_state.workload_inputs['onprem_planning_horizon_years'] = st.number_input("Planning Horizon (years)", min_value=0, max_value=10, value=st.session_state.workload_inputs['onprem_planning_horizon_years'], step=1, key="onprem_planning_horizon_years")

        st.markdown("##### CPU Performance")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.workload_inputs['onprem_peak_cpu_utilization_percent'] = st.number_input("Peak CPU Utilization (%)", min_value=0, max_value=100, value=st.session_state.workload_inputs['onprem_peak_cpu_utilization_percent'], step=1, key="onprem_peak_cpu_utilization_percent")
        with col2:
            st.session_state.workload_inputs['onprem_average_cpu_utilization_percent'] = st.number_input("Average CPU Utilization (%)", min_value=0, max_value=100, value=st.session_state.workload_inputs['onprem_average_cpu_utilization_percent'], step=1, key="onprem_average_cpu_utilization_percent")
        with col3:
            st.session_state.workload_inputs['onprem_active_cpu_cores'] = st.number_input("Active CPU Cores", min_value=0, max_value=256, value=st.session_state.workload_inputs['onprem_active_cpu_cores'], step=1, key="onprem_active_cpu_cores")

        st.markdown("##### RAM Utilization")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.workload_inputs['onprem_peak_ram_utilization_percent'] = st.number_input("Peak RAM Utilization (%)", min_value=0, max_value=100, value=st.session_state.workload_inputs['onprem_peak_ram_utilization_percent'], step=1, key="onprem_peak_ram_utilization_percent")
        with col2:
            st.session_state.workload_inputs['onprem_average_ram_utilization_percent'] = st.number_input("Average RAM Utilization (%)", min_value=0, max_value=100, value=st.session_state.workload_inputs['onprem_average_ram_utilization_percent'], step=1, key="onprem_average_ram_utilization_percent")
        with col3:
            st.session_state.workload_inputs['onprem_sga_buffer_pool_gb'] = st.number_input("SGA/Buffer Pool Size (GB)", min_value=0.0, max_value=1024.0, value=st.session_state.workload_inputs['onprem_sga_buffer_pool_gb'], step=0.1, format="%.1f", key="onprem_sga_buffer_pool_gb")
        
        st.markdown("##### I/O Performance")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.workload_inputs['onprem_peak_iops'] = st.number_input("Peak IOPS", min_value=0, max_value=1000000, value=st.session_state.workload_inputs['onprem_peak_iops'], step=100, key="onprem_peak_iops")
        with col2:
            st.session_state.workload_inputs['onprem_average_iops'] = st.number_input("Average IOPS", min_value=0, max_value=500000, value=st.session_state.workload_inputs['onprem_average_iops'], step=100, key="onprem_average_iops")
        with col3:
            st.session_state.workload_inputs['onprem_peak_throughput_mbps'] = st.number_input("Peak Throughput (MB/s)", min_value=0, max_value=10000, value=st.session_state.workload_inputs['onprem_peak_throughput_mbps'], step=10, key="onprem_peak_throughput_mbps")

        st.markdown("##### Network & Connection")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.workload_inputs['onprem_network_bandwidth_gbps'] = st.number_input("Network Bandwidth (Gbps)", min_value=0.1, max_value=100.0, value=st.session_state.workload_inputs['onprem_network_bandwidth_gbps'], step=0.1, format="%.1f", key="onprem_network_bandwidth_gbps")
            st.session_state.workload_inputs['onprem_max_concurrent_connections'] = st.number_input("Max Concurrent Connections", min_value=0, max_value=100000, value=st.session_state.workload_inputs['onprem_max_concurrent_connections'], step=100, key="onprem_max_concurrent_connections")
        with col2:
            st.session_state.workload_inputs['onprem_network_latency_ms'] = st.number_input("Network Latency (ms)", min_value=0.0, max_value=1000.0, value=st.session_state.workload_inputs['onprem_network_latency_ms'], step=0.1, format="%.1f", key="onprem_network_latency_ms")
            st.session_state.workload_inputs['onprem_average_concurrent_connections'] = st.number_input("Average Concurrent Connections", min_value=0, max_value=50000, value=st.session_state.workload_inputs['onprem_average_concurrent_connections'], step=100, key="onprem_average_concurrent_connections")
        st.markdown("---")

    with env_tabs[4]: # Advanced Settings Tab
        st.markdown("#### AWS Advanced Settings")
        st.session_state.workload_inputs['enable_encryption_at_rest'] = st.checkbox(
            "Enable Encryption at Rest (EBS)",
            value=st.session_state.workload_inputs['enable_encryption_at_rest'],
            help="Enables encryption for EBS volumes."
        )
        st.session_state.workload_inputs['enable_performance_insights'] = st.checkbox(
            "Enable Performance Insights (RDS/EC2)",
            value=st.session_state.workload_inputs['enable_performance_insights'],
            help="Enables database performance monitoring with Performance Insights."
        )
        st.session_state.workload_inputs['enable_enhanced_monitoring'] = st.checkbox(
            "Enable Enhanced Monitoring (RDS/EC2)",
            value=st.session_state.workload_inputs['enable_enhanced_monitoring'],
            help="Provides more detailed metrics for monitoring instances."
        )
        st.session_state.workload_inputs['monthly_data_transfer_gb'] = st.number_input(
            "Monthly Data Transfer Out (GB)",
            min_value=0, max_value=100000, value=st.session_state.workload_inputs['monthly_data_transfer_gb'], step=100,
            help="Estimated outbound data transfer in GB per month. This affects networking costs."
        )
        st.session_state.workload_inputs['backup_retention_days'] = st.number_input(
            "Backup Retention (days, 0=default)",
            min_value=0, max_value=365, value=st.session_state.workload_inputs['backup_retention_days'], step=1,
            help="Number of days to retain backups for RDS/EC2, 0 means default AWS retention."
        )
        st.markdown("---")

    col_save, col_load = st.columns(2)
    with col_save:
        if st.button("💾 Save Configuration", key="save_config"):
            try:
                # Remove calculator object which is not JSON serializable
                inputs_to_save = st.session_state.workload_inputs.copy()
                file_name = f"{inputs_to_save.get('workload_name', 'workload_config').replace(' ', '_').lower()}.json"
                st.download_button(
                    label="Download Configuration JSON",
                    data=json.dumps(inputs_to_save, indent=4),
                    file_name=file_name,
                    mime="application/json",
                    key="download_config_btn"
                )
                st.success("Configuration ready for download!")
            except Exception as e:
                st.error(f"Error saving configuration: {e}")
    with col_load:
        uploaded_file = st.file_uploader("📂 Load Configuration", type="json", key="load_config_uploader")
        if uploaded_file is not None:
            try:
                loaded_inputs = json.load(uploaded_file)
                # Validate loaded inputs against expected structure
                for key, default_value in st.session_state.workload_inputs.items():
                    if key not in loaded_inputs:
                        loaded_inputs[key] = default_value # Add missing keys with default values
                
                # Update session state, ensuring loaded_inputs doesn't have extra keys
                st.session_state.workload_inputs = {k: loaded_inputs.get(k,v) for k,v in st.session_state.workload_inputs.items()}
                st.session_state.analysis_results = None # Clear previous results
                st.success("Configuration loaded successfully! Click 'Generate Recommendations' to apply.")
                st.experimental_rerun() # Rerun to update UI with loaded values
            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please upload a valid configuration file.")
            except Exception as e:
                st.error(f"Error loading configuration: {e}")


def render_analysis_results(recommendations, key_suffix=""):
    """Renders the analysis results for a single workload.
    
    Args:
        recommendations (dict): The dictionary of recommendations.
        key_suffix (str): A suffix to ensure unique keys for Streamlit elements,
                          especially when called in loops (e.g., from bulk analysis).
    """
    st.markdown("## ✨ Analysis Results")

    if not recommendations or 'error' in recommendations:
        st.warning(f"No recommendations available or an error occurred during analysis: {recommendations.get('error', 'Unknown Error')}. Please configure your workload and generate recommendations.")
        return

    # Prepare data for display
    data = []
    for env, rec in recommendations.items():
        if rec['total_cost'] == float('inf'):
            cost_str = "N/A (No suitable instance)"
            instance_str = "No suitable instance found"
            instance_cost = "N/A"
            ebs_cost = "N/A"
            os_cost = "N/A"
        else:
            cost_str = f"${rec['total_cost']:,.2f}/month"
            instance_str = f"{rec['instance_type']} ({rec['vcpus']} vCPUs, {rec['memory_gb']:.1f} GiB)"
            instance_cost = f"${rec['instance_cost']:,.2f}"
            ebs_cost = f"${rec['ebs_cost']:,.2f}"
            os_cost = f"${rec['os_cost']:,.2f}" # Will be $0.00 for now based on current logic

        data.append({
            "Environment": env,
            "Recommended Instance": instance_str,
            "OS": rec['os'],
            "Region": next(k for k, v in AWS_REGIONS.items() if v == rec['region']),
            "Storage (GB)": rec['storage_gb'],
            "EC2 Instance Cost": instance_cost,
            "EBS Storage Cost": ebs_cost,
            "OS Cost": os_cost,
            "Total Monthly Cost": cost_str
        })

    df_results = pd.DataFrame(data)
    st.dataframe(df_results, hide_index=True, use_container_width=True)

    # Display On-Premise Details and Advanced Settings for context
    st.markdown("### Workload Configuration Summary (Inputs)")
    
    inputs_df_data = []
    inputs = st.session_state.workload_inputs # Get current inputs

    # General Workload Info
    inputs_df_data.append({"Category": "General", "Metric": "Workload Name", "Value": inputs.get('workload_name', 'N/A')})
    inputs_df_data.append({"Category": "General", "Metric": "Workload Type", "Value": inputs.get('workload_type', 'N/A')})
    inputs_df_data.append({"Category": "General", "Metric": "Pricing Model / Commitment", "Value": inputs.get('ri_sp_option', 'N/A')})
    inputs_df_data.append({"Category": "General", "Metric": "Annual Growth Rate (%)", "Value": f"{inputs.get('growth_rate_annual', 0)}%"})
    inputs_df_data.append({"Category": "General", "Metric": "Projection Years", "Value": inputs.get('growth_years', 0)})

    # On-Premise Details
    inputs_df_data.append({"Category": "On-Premise Compute", "Metric": "CPU Cores", "Value": inputs.get('onprem_cpu_cores', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Compute", "Metric": "Current Storage (GB)", "Value": inputs.get('onprem_current_storage_gb', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Compute", "Metric": "CPU Model", "Value": inputs.get('onprem_cpu_model', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Compute", "Metric": "Storage Type", "Value": inputs.get('onprem_storage_type', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Compute", "Metric": "CPU Speed (GHz)", "Value": inputs.get('onprem_cpu_speed_ghz', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Compute", "Metric": "RAID Level", "Value": inputs.get('onprem_raid_level', 'N/A')})

    inputs_df_data.append({"Category": "On-Premise Memory", "Metric": "Total RAM (GB)", "Value": inputs.get('onprem_total_ram_gb', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Memory", "Metric": "RAM Type", "Value": inputs.get('onprem_ram_type', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Memory", "Metric": "RAM Speed (MHz)", "Value": inputs.get('onprem_ram_speed_mhz', 'N/A')})

    inputs_df_data.append({"Category": "On-Premise CPU Perf", "Metric": "Peak CPU Utilization (%)", "Value": f"{inputs.get('onprem_peak_cpu_utilization_percent', 0)}%"})
    inputs_df_data.append({"Category": "On-Premise CPU Perf", "Metric": "Average CPU Utilization (%)", "Value": f"{inputs.get('onprem_average_cpu_utilization_percent', 0)}%"})
    inputs_df_data.append({"Category": "On-Premise CPU Perf", "Metric": "Active CPU Cores", "Value": inputs.get('onprem_active_cpu_cores', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise RAM Util", "Metric": "Peak RAM Utilization (%)", "Value": f"{inputs.get('onprem_peak_ram_utilization_percent', 0)}%"})
    inputs_df_data.append({"Category": "On-Premise RAM Util", "Metric": "Average RAM Utilization (%)", "Value": f"{inputs.get('onprem_average_ram_utilization_percent', 0)}%"})
    inputs_df_data.append({"Category": "On-Premise RAM Util", "Metric": "SGA/Buffer Pool Size (GB)", "Value": inputs.get('onprem_sga_buffer_pool_gb', 'N/A')})

    inputs_df_data.append({"Category": "On-Premise I/O Perf", "Metric": "Peak IOPS", "Value": inputs.get('onprem_peak_iops', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise I/O Perf", "Metric": "Average IOPS", "Value": inputs.get('onprem_average_iops', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise I/O Perf", "Metric": "Peak Throughput (MB/s)", "Value": inputs.get('onprem_peak_throughput_mbps', 'N/A')})

    inputs_df_data.append({"Category": "On-Premise Network", "Metric": "Network Bandwidth (Gbps)", "Value": inputs.get('onprem_network_bandwidth_gbps', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Network", "Metric": "Network Latency (ms)", "Value": inputs.get('onprem_network_latency_ms', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Network", "Metric": "Max Concurrent Connections", "Value": inputs.get('onprem_max_concurrent_connections', 'N/A')})
    inputs_df_data.append({"Category": "On-Premise Network", "Metric": "Average Concurrent Connections", "Value": inputs.get('onprem_average_concurrent_connections', 'N/A')})

    # Advanced Settings
    inputs_df_data.append({"Category": "Advanced Settings", "Metric": "Enable Encryption at Rest", "Value": "Yes" if inputs.get('enable_encryption_at_rest') else "No"})
    inputs_df_data.append({"Category": "Advanced Settings", "Metric": "Enable Performance Insights", "Value": "Yes" if inputs.get('enable_performance_insights') else "No"})
    inputs_df_data.append({"Category": "Advanced Settings", "Metric": "Enable Enhanced Monitoring", "Value": "Yes" if inputs.get('enable_enhanced_monitoring') else "No"})
    inputs_df_data.append({"Category": "Advanced Settings", "Metric": "Monthly Data Transfer (GB)", "Value": inputs.get('monthly_data_transfer_gb', 'N/A')})
    inputs_df_data.append({"Category": "Advanced Settings", "Metric": "Backup Retention (days)", "Value": inputs.get('backup_retention_days', 'N/A')})


    inputs_df = pd.DataFrame(inputs_df_data)
    st.dataframe(inputs_df, hide_index=True, use_container_width=True)

    # Cost Breakdown Chart (Pie Chart) for PROD
    st.markdown("### PROD Environment Cost Breakdown")
    prod_rec = recommendations.get('PROD')
    if prod_rec and prod_rec['total_cost'] != float('inf'):
        cost_breakdown_data = {
            'Component': ['EC2 Instance', 'EBS Storage', 'OS (included in EC2)'],
            'Cost': [prod_rec['instance_cost'], prod_rec['ebs_cost'], prod_rec['os_cost']]
        }
        df_costs = pd.DataFrame(cost_breakdown_data)
        # Filter out 0 cost components for better visualization if OS cost is always 0
        df_costs = df_costs[df_costs['Cost'] > 0]
        fig_costs = px.pie(df_costs, values='Cost', names='Component', title='PROD Monthly Cost Distribution', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_costs.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
        st.plotly_chart(fig_costs, use_container_width=True, key=f"prod_cost_chart_{key_suffix}")
    else:
        st.info("PROD environment recommendations not available for cost breakdown.")

    # Workload Growth Projection
    st.markdown("### Workload Growth Projections (PROD)")
    # Ensure st.session_state.workload_inputs is correctly populated for single workload,
    # or passed from the bulk item's inputs. For simplicity here, assuming single workload context
    # is generally what drives 'growth_years' and 'growth_rate_annual'
    current_growth_years = st.session_state.workload_inputs.get('growth_years', 0)
    current_growth_rate = st.session_state.workload_inputs.get('growth_rate_annual', 0)

    if 'projected_costs' in recommendations.get('PROD', {}) and current_growth_years > 0:
        proj_costs = recommendations['PROD']['projected_costs']
        proj_data = []
        for year_str, details in proj_costs.items():
            proj_data.append({
                "Year": int(year_str.split(' ')[1]),
                "Estimated Cost (Monthly)": details['estimated_cost'] if isinstance(details['estimated_cost'], (int, float)) else None,
                "Projected vCPUs": details['vcpus'],
                "Projected Memory (GiB)": details['memory_gb'],
                "Projected Storage (GB)": details['storage_gb'],
                "Recommended Instance": details['recommended_instance']
            })
        df_projected = pd.DataFrame(proj_data).set_index("Year")

        # Plot projected costs
        fig_proj = px.line(df_projected, y="Estimated Cost (Monthly)", title="Projected Monthly Cost Over Time (PROD)", markers=True, text="Estimated Cost (Monthly)")
        fig_proj.update_traces(texttemplate='%{text:$.2f}', textposition='top center')
        fig_proj.update_layout(hovermode="x unified", xaxis_title="Year", yaxis_title="Estimated Monthly Cost ($)")
        st.plotly_chart(fig_proj, use_container_width=True, key=f"proj_cost_chart_{key_suffix}")

        st.markdown(f"""
        <details>
        <summary>Detailed Growth Projection Table</summary>
        <p>This table shows the projected resource requirements and estimated costs for the PROD environment based on an annual growth rate of <b>{current_growth_rate}%</b> over <b>{current_growth_years}</b> years.</p>
        </details>
        """, unsafe_allow_html=True)
        st.dataframe(df_projected, use_container_width=True)
    else:
        st.info("No growth projection data available or growth rate not set.")


def render_bulk_analysis():
    """Renders the UI for bulk analysis."""
    st.markdown("## 📥 Bulk Workload Analysis")

    # Define CSV template
    csv_columns = [
        "Workload Name", "Workload Type",
        "PROD_vCPUs", "PROD_Memory_GiB", "PROD_Storage_GB", "PROD_OS", "PROD_Region",
        "UAT_vCPUs", "UAT_Memory_GiB", "UAT_Storage_GB", "UAT_OS", "UAT_Region",
        "DEV_vCPUs", "DEV_Memory_GiB", "DEV_Storage_GB", "DEV_OS", "DEV_Region",
        "RI_SP_Option", "Annual Growth Rate (%)", "Projection Years",
        # New On-Premise Metrics
        "OnPrem_CPU_Cores", "OnPrem_Current_Storage_GB", "OnPrem_CPU_Model", "OnPrem_Storage_Type",
        "OnPrem_CPU_Speed_GHz", "OnPrem_RAID_Level", "OnPrem_Total_RAM_GB", "OnPrem_RAM_Type",
        "OnPrem_RAM_Speed_MHz", "OnPrem_Annual_Growth_Rate_Percent", "OnPrem_Planning_Horizon_Years",
        "OnPrem_Peak_CPU_Utilization_Percent", "OnPrem_Average_CPU_Utilization_Percent",
        "OnPrem_Active_CPU_Cores", "OnPrem_Peak_RAM_Utilization_Percent",
        "OnPrem_Average_RAM_Utilization_Percent", "OnPrem_SGA_Buffer_Pool_GB", "OnPrem_Peak_IOPS",
        "OnPrem_Average_IOPS", "OnPrem_Peak_Throughput_MBPS", "OnPrem_Network_Bandwidth_Gbps",
        "OnPrem_Network_Latency_ms", "OnPrem_Max_Concurrent_Connections", "OnPrem_Average_Concurrent_Connections",
        # New Advanced Settings
        "Enable_Encryption_at_Rest", "Enable_Performance_Insights", "Enable_Enhanced_Monitoring",
        "Monthly_Data_Transfer_GB", "Backup_Retention_Days"
    ]
    sample_data = [
        ["Sample Workload 1", "Web Application", 4, 8.0, 100, "Linux (Amazon Linux 2)", "us-east-1",
         2, 4.0, 50, "Linux (Amazon Linux 2)", "us-east-1",
         1, 2.0, 25, "Linux (Amazon Linux 2)", "us-east-1",
         "On-Demand", 10, 5,
         # On-Premise Metrics
         2, 100, "Intel Xeon E5", "SSD", 2.5, "RAID 1", 8, "DDR4", 2400, 10, 5, 70, 40, 2, 60, 30, 0, 1000, 500, 100, 10, 1, 1000, 500,
         # Advanced Settings
         True, True, False, 500, 7],
        ["Sample Workload 2", "Database Server", 8, 32.0, 500, "Linux (RHEL)", "us-west-2",
         4, 16.0, 250, "Linux (RHEL)", "us-west-2",
         2, 8.0, 100, "Linux (RHEL)", "us-west-2",
         "1-Year No Upfront RI/SP", 5, 3,
         # On-Premise Metrics
         4, 500, "AMD EPYC", "NVMe", 3.0, "RAID 5", 32, "DDR4", 2933, 5, 3, 80, 50, 4, 70, 40, 10, 5000, 2000, 500, 25, 0.5, 5000, 2000,
         # Advanced Settings
         True, True, True, 1000, 14]
    ]
    df_template = pd.DataFrame(sample_data, columns=csv_columns)

    st.download_button(
        label="Download Bulk Upload Template (CSV)",
        data=df_template.to_csv(index=False).encode('utf-8'),
        file_name="bulk_workload_template.csv",
        mime="text/csv",
        help="Download a CSV template to fill in multiple workload requirements."
    )

    uploaded_file = st.file_uploader("Upload Workloads CSV", type="csv", key="bulk_csv_uploader")

    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            st.session_state.bulk_upload_df = df_uploaded
            st.success(f"Successfully uploaded {len(df_uploaded)} workloads.")
            st.dataframe(df_uploaded, use_container_width=True, hide_index=True)
            if st.button("🚀 Analyze All Workloads", key="analyze_bulk_btn"):
                analyze_bulk_workloads(df_uploaded)
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")

def analyze_bulk_workloads(df_workloads):
    """Processes multiple workloads from a DataFrame and generates recommendations."""
    st.session_state.bulk_results = []
    total_workloads = len(df_workloads)
    analysis_progress_text = st.empty()
    analysis_progress_bar = st.progress(0)

    for i, row in df_workloads.iterrows():
        workload_name = row.get("Workload Name", f"Workload {i+1}")
        analysis_progress_text.text(f"Analyzing workload: {workload_name} ({i+1}/{total_workloads})...")
        analysis_progress_bar.progress((i + 1) / total_workloads)

        # Map CSV columns to session state keys
        current_workload_inputs = {
            'workload_name': workload_name,
            'workload_type': row.get("Workload Type", WORKLOAD_TYPES[0]),
            'PROD_vcpus': row.get("PROD_vCPUs", 0),
            'PROD_memory_gb': row.get("PROD_Memory_GiB", 0.0),
            'PROD_storage_gb': row.get("PROD_Storage_GB", 0),
            'PROD_os': row.get("PROD_OS", OPERATING_SYSTEMS["Linux (Amazon Linux 2)"]),
            'PROD_region': AWS_REGIONS.get(row.get("PROD_Region", "US East (N. Virginia)"), row.get("PROD_Region", "us-east-1")), # Handle both name and value
            'UAT_vcpus': row.get("UAT_vCPUs", 0),
            'UAT_memory_gb': row.get("UAT_Memory_GiB", 0.0),
            'UAT_storage_gb': row.get("UAT_Storage_GB", 0),
            'UAT_os': row.get("UAT_OS", OPERATING_SYSTEMS["Linux (Amazon Linux 2)"]),
            'UAT_region': AWS_REGIONS.get(row.get("UAT_Region", "US East (N. Virginia)"), row.get("UAT_Region", "us-east-1")),
            'DEV_vcpus': row.get("DEV_vCPUs", 0),
            'DEV_memory_gb': row.get("DEV_Memory_GiB", 0.0),
            'DEV_storage_gb': row.get("DEV_Storage_GB", 0),
            'DEV_os': row.get("DEV_OS", OPERATING_SYSTEMS["Linux (Amazon Linux 2)"]),
            'DEV_region': AWS_REGIONS.get(row.get("DEV_Region", "US East (N. Virginia)"), row.get("DEV_Region", "us-east-1")),
            'ri_sp_option': row.get("RI_SP_Option", "On-Demand"),
            'growth_rate_annual': row.get("Annual Growth Rate (%)", 0),
            'growth_years': row.get("Projection Years", 5),
            
            # On-Premise Metrics from CSV
            'onprem_cpu_cores': row.get("OnPrem_CPU_Cores", 0),
            'onprem_current_storage_gb': row.get("OnPrem_Current_Storage_GB", 0),
            'onprem_cpu_model': row.get("OnPrem_CPU_Model", "N/A"),
            'onprem_storage_type': row.get("OnPrem_Storage_Type", "N/A"),
            'onprem_cpu_speed_ghz': row.get("OnPrem_CPU_Speed_GHz", 0.0),
            'onprem_raid_level': row.get("OnPrem_RAID_Level", "N/A"),
            'onprem_total_ram_gb': row.get("OnPrem_Total_RAM_GB", 0),
            'onprem_ram_type': row.get("OnPrem_RAM_Type", "N/A"),
            'onprem_ram_speed_mhz': row.get("OnPrem_RAM_Speed_MHz", 0),
            'onprem_annual_growth_rate_percent': row.get("OnPrem_Annual_Growth_Rate_Percent", 0),
            'onprem_planning_horizon_years': row.get("OnPrem_Planning_Horizon_Years", 0),
            'onprem_peak_cpu_utilization_percent': row.get("OnPrem_Peak_CPU_Utilization_Percent", 0),
            'onprem_average_cpu_utilization_percent': row.get("OnPrem_Average_CPU_Utilization_Percent", 0),
            'onprem_active_cpu_cores': row.get("OnPrem_Active_CPU_Cores", 0),
            'onprem_peak_ram_utilization_percent': row.get("OnPrem_Peak_RAM_Utilization_Percent", 0),
            'onprem_average_ram_utilization_percent': row.get("OnPrem_Average_RAM_Utilization_Percent", 0),
            'onprem_sga_buffer_pool_gb': row.get("OnPrem_SGA_Buffer_Pool_GB", 0.0),
            'onprem_peak_iops': row.get("OnPrem_Peak_IOPS", 0),
            'onprem_average_iops': row.get("OnPrem_Average_IOPS", 0),
            'onprem_peak_throughput_mbps': row.get("OnPrem_Peak_Throughput_MBPS", 0),
            'onprem_network_bandwidth_gbps': row.get("OnPrem_Network_Bandwidth_Gbps", 0.0),
            'onprem_network_latency_ms': row.get("OnPrem_Network_Latency_ms", 0.0),
            'onprem_max_concurrent_connections': row.get("OnPrem_Max_Concurrent_Connections", 0),
            'onprem_average_concurrent_connections': row.get("OnPrem_Average_Concurrent_Connections", 0),
            
            # Advanced Settings from CSV
            'enable_encryption_at_rest': row.get("Enable_Encryption_at_Rest", False),
            'enable_performance_insights': row.get("Enable_Performance_Insights", False),
            'enable_enhanced_monitoring': row.get("Enable_Enhanced_Monitoring", False),
            'monthly_data_transfer_gb': row.get("Monthly_Data_Transfer_GB", 0),
            'backup_retention_days': row.get("Backup_Retention_Days", 0)
        }
        
        # Save current_workload_inputs to session state calculator inputs
        st.session_state.calculator.inputs = current_workload_inputs
        
        try:
            results = st.session_state.calculator.generate_all_recommendations()
            st.session_state.bulk_results.append({
                'workload_name': workload_name,
                'inputs': current_workload_inputs, # Store inputs for reports if needed later
                'recommendations': results
            })
        except Exception as e:
            st.session_state.bulk_results.append({
                'workload_name': workload_name,
                'inputs': current_workload_inputs,
                'recommendations': {'error': f"Error processing workload: {e}"}
            })
            logger.error(f"Error processing bulk workload {workload_name}: {e}")

    analysis_progress_text.empty()
    analysis_progress_bar.empty()
    st.success("✅ Bulk analysis completed successfully!")


def display_bulk_analysis_results(bulk_results):
    """Displays the results of bulk analysis."""
    st.markdown("### Bulk Analysis Summary")
    summary_data = []
    for item in bulk_results:
        workload_name = item['workload_name']
        prod_rec = item['recommendations'].get('PROD', {})
        total_cost_prod = prod_rec.get('total_cost', float('inf'))
        
        if total_cost_prod == float('inf'):
            cost_str = "N/A (No suitable instance)"
            instance_str = "No suitable instance found"
        else:
            cost_str = f"${total_cost_prod:,.2f}/month"
            instance_str = f"{prod_rec.get('instance_type', 'N/A')} ({prod_rec.get('vcpus',0)} vCPUs, {prod_rec.get('memory_gb',0):.1f} GiB)"

        summary_data.append({
            "Workload Name": workload_name,
            "PROD Recommended Instance": instance_str,
            "PROD Monthly Cost": cost_str,
            "Status": "Success" if total_cost_prod != float('inf') else "Failed"
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    st.markdown("### Detailed Bulk Results")
    for i, item in enumerate(bulk_results):
        workload_name = item['workload_name']
        st.markdown(f"#### {workload_name}")
        # Pass the full inputs and recommendations to render_analysis_results
        # For bulk analysis, we might want to show the specific inputs that led to this result
        # For now, `render_analysis_results` takes `recommendations` and uses `st.session_state.workload_inputs` for detailed inputs.
        # This needs a slight adjustment if `render_analysis_results` is to be truly standalone for bulk.
        # For now, we will set session_state.workload_inputs temporarily to the inputs for the current bulk item
        # and then call render_analysis_results. This is a bit hacky but works for demonstration.
        
        # Store original inputs
        original_workload_inputs = st.session_state.workload_inputs.copy()
        # Set inputs for current bulk item
        st.session_state.workload_inputs = item['inputs']
        render_analysis_results(item['recommendations'], key_suffix=f"bulk_{i}")
        # Restore original inputs
        st.session_state.workload_inputs = original_workload_inputs
        
        st.markdown("---")


def generate_pdf_report(workload_name, inputs, recommendations):
    """Generates a PDF report for the given workload."""
    if not REPORTLAB_AVAILABLE:
        st.error("`reportlab` library not found. Please install it (`pip install reportlab`) to generate PDF reports.")
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(name='TitleStyle', fontSize=20, leading=24, alignment=TA_CENTER,
                              spaceAfter=20, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Heading1', fontSize=16, leading=18, spaceAfter=12,
                              fontName='Helvetica-Bold', textColor=colors.HexColor('#4c51bf')))
    styles.add(ParagraphStyle(name='Heading2', fontSize=14, leading=16, spaceAfter=8,
                              fontName='Helvetica-Bold', textColor=colors.HexColor('#2d3748')))
    styles.add(ParagraphStyle(name='Normal', fontSize=10, leading=12, spaceAfter=6,
                              fontName='Helvetica'))
    styles.add(ParagraphStyle(name='Small', fontSize=9, leading=10, spaceAfter=4,
                              fontName='Helvetica'))
    styles.add(ParagraphStyle(name='Code', fontSize=9, leading=10, spaceAfter=4,
                              fontName='Courier', backColor=colors.HexColor('#edf2f7'),
                              borderColor=colors.HexColor('#e2e8f0'), borderWidth=0.5,
                              leftIndent=6, rightIndent=6, firstLineIndent=6,
                              leadingOffset=2, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='TableCaption', fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=6, spaceAfter=6))


    story = []

    # Title
    story.append(Paragraph("Enterprise AWS EC2 Workload Sizing Report", styles['TitleStyle']))
    story.append(Paragraph(f"Workload Name: <b>{workload_name}</b>", styles['Heading1']))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # Workload Configuration
    story.append(Paragraph("1. Workload Configuration (Input Parameters)", styles['Heading1']))
    story.append(Paragraph(f"Workload Type: {inputs.get('workload_type', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Pricing Model / Commitment: {inputs.get('ri_sp_option', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Annual Growth Rate: {inputs.get('growth_rate_annual', 0)}%", styles['Normal']))
    story.append(Paragraph(f"Projection Years: {inputs.get('growth_years', 0)}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    # Environment Details
    for env in ['PROD', 'UAT', 'DEV']:
        story.append(Paragraph(f"<b>{env} Environment:</b>", styles['Normal']))
        story.append(Paragraph(f"  - Required vCPUs: {inputs.get(f'{env}_vcpus', 'N/A')}", styles['Small']))
        story.append(Paragraph(f"  - Required Memory (GiB): {inputs.get(f'{env}_memory_gb', 'N/A')}", styles['Small']))
        story.append(Paragraph(f"  - Required Storage (GB): {inputs.get(f'{env}_storage_gb', 'N/A')}", styles['Small']))
        story.append(Paragraph(f"  - Operating System: {inputs.get(f'{env}_os', 'N/A')}", styles['Small']))
        story.append(Paragraph(f"  - Preferred AWS Region: {next((k for k, v in AWS_REGIONS.items() if v == inputs.get(f'{env}_region')), 'N/A')}", styles['Small']))
        story.append(Spacer(1, 0.05 * inch))

    # On-Premise Details
    story.append(Paragraph("2. On-Premise Workload Details", styles['Heading1']))
    story.append(Paragraph("<b>Compute:</b>", styles['Heading2']))
    story.append(Paragraph(f"  - CPU Cores: {inputs.get('onprem_cpu_cores', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Current Storage (GB): {inputs.get('onprem_current_storage_gb', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - CPU Model: {inputs.get('onprem_cpu_model', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Storage Type: {inputs.get('onprem_storage_type', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - CPU Speed (GHz): {inputs.get('onprem_cpu_speed_ghz', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - RAID Level: {inputs.get('onprem_raid_level', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Memory Resources:</b>", styles['Heading2']))
    story.append(Paragraph(f"  - Total RAM (GB): {inputs.get('onprem_total_ram_gb', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - RAM Type: {inputs.get('onprem_ram_type', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - RAM Speed (MHz): {inputs.get('onprem_ram_speed_mhz', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Growth & Planning:</b>", styles['Heading2']))
    story.append(Paragraph(f"  - Annual Growth Rate (%): {inputs.get('onprem_annual_growth_rate_percent', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Planning Horizon (years): {inputs.get('onprem_planning_horizon_years', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>CPU Performance:</b>", styles['Heading2']))
    story.append(Paragraph(f"  - Peak CPU Utilization (%): {inputs.get('onprem_peak_cpu_utilization_percent', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Average CPU Utilization (%): {inputs.get('onprem_average_cpu_utilization_percent', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Active CPU Cores: {inputs.get('onprem_active_cpu_cores', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>RAM Utilization:</b>", styles['Heading2']))
    story.append(Paragraph(f"  - Peak RAM Utilization (%): {inputs.get('onprem_peak_ram_utilization_percent', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Average RAM Utilization (%): {inputs.get('onprem_average_ram_utilization_percent', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - SGA/Buffer Pool Size (GB): {inputs.get('onprem_sga_buffer_pool_gb', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>I/O Performance:</b>", styles['Heading2']))
    story.append(Paragraph(f"  - Peak IOPS: {inputs.get('onprem_peak_iops', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Average IOPS: {inputs.get('onprem_average_iops', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Peak Throughput (MB/s): {inputs.get('onprem_peak_throughput_mbps', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Network & Connection:</b>", styles['Heading2']))
    story.append(Paragraph(f"  - Network Bandwidth (Gbps): {inputs.get('onprem_network_bandwidth_gbps', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Network Latency (ms): {inputs.get('onprem_network_latency_ms', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Max Concurrent Connections: {inputs.get('onprem_max_concurrent_connections', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Average Concurrent Connections: {inputs.get('onprem_average_concurrent_connections', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # Advanced Settings
    story.append(Paragraph("3. AWS Advanced Settings", styles['Heading1']))
    story.append(Paragraph(f"  - Enable Encryption at Rest: {'Yes' if inputs.get('enable_encryption_at_rest') else 'No'}", styles['Normal']))
    story.append(Paragraph(f"  - Enable Performance Insights: {'Yes' if inputs.get('enable_performance_insights') else 'No'}", styles['Normal']))
    story.append(Paragraph(f"  - Enable Enhanced Monitoring: {'Yes' if inputs.get('enable_enhanced_monitoring') else 'No'}", styles['Normal']))
    story.append(Paragraph(f"  - Monthly Data Transfer (GB): {inputs.get('monthly_data_transfer_gb', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"  - Backup Retention (days): {inputs.get('backup_retention_days', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # Recommendations
    story.append(Paragraph("4. AWS Recommendations", styles['Heading1']))

    table_data = [['Environment', 'Recommended Instance', 'OS', 'Region', 'Storage (GB)', 'Monthly Cost']]
    for env, rec in recommendations.items():
        if rec['total_cost'] == float('inf'):
            cost_str = "N/A (No suitable instance)"
            instance_str = "No suitable instance found"
        else:
            cost_str = f"${rec['total_cost']:,.2f}"
            instance_str = f"{rec['instance_type']} ({rec['vcpus']} vCPUs, {rec['memory_gb']:.1f} GiB)"
        
        table_data.append([
            env,
            instance_str,
            rec['os'],
            next(k for k, v in AWS_REGIONS.items() if v == rec['region']),
            rec['storage_gb'],
            cost_str
        ])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4c51bf')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    table = Table(table_data)
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))

    # Cost Breakdown (PROD)
    prod_rec = recommendations.get('PROD')
    if prod_rec and prod_rec['total_cost'] != float('inf'):
        story.append(Paragraph("5. PROD Environment Cost Breakdown", styles['Heading1']))
        story.append(Paragraph(f"Monthly Instance Cost: ${prod_rec['instance_cost']:,.2f}", styles['Normal']))
        story.append(Paragraph(f"Monthly EBS Storage Cost: ${prod_rec['ebs_cost']:,.2f}", styles['Normal']))
        story.append(Paragraph(f"Monthly OS Cost (included): ${prod_rec['os_cost']:,.2f}", styles['Normal']))
        story.append(Paragraph(f"<b>Total PROD Monthly Cost: ${prod_rec['total_cost']:,.2f}</b>", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

    # Growth Projections
    if 'projected_costs' in recommendations.get('PROD', {}) and inputs.get('growth_years', 0) > 0:
        story.append(Paragraph("6. Workload Growth Projections (PROD)", styles['Heading1']))
        story.append(Paragraph(f"Based on an annual growth rate of {inputs.get('growth_rate_annual', 0)}% over {inputs.get('growth_years', 0)} years.", styles['Normal']))
        
        proj_table_data = [['Year', 'Projected vCPUs', 'Projected Memory (GiB)', 'Projected Storage (GB)', 'Estimated Monthly Cost', 'Recommended Instance']]
        for year_str, details in recommendations['PROD']['projected_costs'].items():
            proj_cost = details['estimated_cost'] if isinstance(details['estimated_cost'], (int, float)) else 'N/A'
            if isinstance(proj_cost, (int, float)):
                proj_cost_str = f"${proj_cost:,.2f}"
            else:
                proj_cost_str = proj_cost
            proj_table_data.append([
                year_str,
                details['vcpus'],
                details['memory_gb'],
                details['storage_gb'],
                proj_cost_str,
                details['recommended_instance']
            ])
        
        proj_table = Table(proj_table_data)
        proj_table.setStyle(table_style) # Re-use general table style
        story.append(proj_table)
        story.append(Spacer(1, 0.2 * inch))

    # Footer
    story.append(PageBreak())
    story.append(Paragraph("--- End of Report ---", styles['TableCaption']))
    story.append(Paragraph("Enterprise AWS Workload Sizing Platform v3.0", styles['Small']))
    story.append(Paragraph("Comprehensive cloud migration planning for enterprise infrastructure", styles['Small']))

    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

def render_reports_export():
    """Renders options to export reports."""
    st.markdown("## 📄 Reports & Export")

    # Single Workload Report
    st.markdown("### Single Workload Report")
    if st.session_state.analysis_results:
        workload_name = st.session_state.analysis_results['inputs'].get('workload_name', 'Single_Workload_Analysis')
        
        if st.button("Generate PDF Report (Current Workload)", key="generate_pdf_single"):
            with st.spinner("Generating PDF..."):
                pdf_buffer = generate_pdf_report(
                    workload_name=workload_name,
                    inputs=st.session_state.analysis_results['inputs'],
                    recommendations=st.session_state.analysis_results['recommendations']
                )
                if pdf_buffer:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=f"{workload_name}_AWS_Sizing_Report.pdf",
                        mime="application/pdf",
                        key="download_single_pdf"
                    )
                    st.success("PDF report generated!")
                else:
                    st.error("Failed to generate PDF report.")
    else:
        st.info("Please generate recommendations for a single workload first to enable PDF report generation.")

    # Bulk Workload Reports
    st.markdown("### Bulk Workload Reports")
    if st.session_state.bulk_results:
        # Option 1: Export all bulk results to a single CSV
        if st.button("Export Bulk Results to CSV", key="export_bulk_csv"):
            bulk_export_data = []
            for item in st.session_state.bulk_results:
                row_data = {
                    "Workload Name": item['workload_name'],
                    "Workload Type": item['inputs'].get('workload_type', ''),
                    "PROD_vCPUs_Req": item['inputs'].get('PROD_vcpus', 0),
                    "PROD_Memory_GiB_Req": item['inputs'].get('PROD_memory_gb', 0.0),
                    "PROD_Storage_GB_Req": item['inputs'].get('PROD_storage_gb', 0),
                    "PROD_OS_Req": item['inputs'].get('PROD_os', ''),
                    "PROD_Region_Req": next(k for k,v in AWS_REGIONS.items() if v == item['inputs'].get('PROD_region')),
                    "RI_SP_Option": item['inputs'].get('ri_sp_option', 'On-Demand'),
                    "Annual Growth Rate (%)": item['inputs'].get('growth_rate_annual', 0),
                    "Projection Years": item['inputs'].get('growth_years', 0),

                    # On-Premise Metrics for Export
                    "OnPrem_CPU_Cores": item['inputs'].get('onprem_cpu_cores', 0),
                    "OnPrem_Current_Storage_GB": item['inputs'].get('onprem_current_storage_gb', 0),
                    "OnPrem_CPU_Model": item['inputs'].get('onprem_cpu_model', ''),
                    "OnPrem_Storage_Type": item['inputs'].get('onprem_storage_type', ''),
                    "OnPrem_CPU_Speed_GHz": item['inputs'].get('onprem_cpu_speed_ghz', 0.0),
                    "OnPrem_RAID_Level": item['inputs'].get('onprem_raid_level', ''),
                    "OnPrem_Total_RAM_GB": item['inputs'].get('onprem_total_ram_gb', 0),
                    "OnPrem_RAM_Type": item['inputs'].get('onprem_ram_type', ''),
                    "OnPrem_RAM_Speed_MHz": item['inputs'].get('onprem_ram_speed_mhz', 0),
                    "OnPrem_Annual_Growth_Rate_Percent": item['inputs'].get('onprem_annual_growth_rate_percent', 0),
                    "OnPrem_Planning_Horizon_Years": item['inputs'].get('onprem_planning_horizon_years', 0),
                    "OnPrem_Peak_CPU_Utilization_Percent": item['inputs'].get('onprem_peak_cpu_utilization_percent', 0),
                    "OnPrem_Average_CPU_Utilization_Percent": item['inputs'].get('onprem_average_cpu_utilization_percent', 0),
                    "OnPrem_Active_CPU_Cores": item['inputs'].get('onprem_active_cpu_cores', 0),
                    "OnPrem_Peak_RAM_Utilization_Percent": item['inputs'].get('onprem_peak_ram_utilization_percent', 0),
                    "OnPrem_Average_RAM_Utilization_Percent": item['inputs'].get('onprem_average_ram_utilization_percent', 0),
                    "OnPrem_SGA_Buffer_Pool_GB": item['inputs'].get('onprem_sga_buffer_pool_gb', 0.0),
                    "OnPrem_Peak_IOPS": item['inputs'].get('onprem_peak_iops', 0),
                    "OnPrem_Average_IOPS": item['inputs'].get('onprem_average_iops', 0),
                    "OnPrem_Peak_Throughput_MBPS": item['inputs'].get('onprem_peak_throughput_mbps', 0),
                    "OnPrem_Network_Bandwidth_Gbps": item['inputs'].get('onprem_network_bandwidth_gbps', 0.0),
                    "OnPrem_Network_Latency_ms": item['inputs'].get('onprem_network_latency_ms', 0.0),
                    "OnPrem_Max_Concurrent_Connections": item['inputs'].get('onprem_max_concurrent_connections', 0),
                    "OnPrem_Average_Concurrent_Connections": item['inputs'].get('onprem_average_concurrent_connections', 0),

                    # Advanced Settings for Export
                    "Enable_Encryption_at_Rest": "Yes" if item['inputs'].get('enable_encryption_at_rest') else "No",
                    "Enable_Performance_Insights": "Yes" if item['inputs'].get('enable_performance_insights') else "No",
                    "Enable_Enhanced_Monitoring": "Yes" if item['inputs'].get('enable_enhanced_monitoring') else "No",
                    "Monthly_Data_Transfer_GB": item['inputs'].get('monthly_data_transfer_gb', 0),
                    "Backup_Retention_Days": item['inputs'].get('backup_retention_days', 0),

                    # AWS Recommendations Summary
                    "PROD_Recommended_Instance": item['recommendations'].get('PROD', {}).get('instance_type', 'N/A'),
                    "PROD_vCPUs_Rec": item['recommendations'].get('PROD', {}).get('vcpus', 0),
                    "PROD_Memory_GiB_Rec": item['recommendations'].get('PROD', {}).get('memory_gb', 0.0),
                    "PROD_Monthly_Cost_USD": item['recommendations'].get('PROD', {}).get('total_cost', float('inf'))
                }
                bulk_export_data.append(row_data)

            df_bulk_export = pd.DataFrame(bulk_export_data)
            csv_export = df_bulk_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download All Bulk Results as CSV",
                data=csv_export,
                file_name=f"bulk_aws_sizing_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_all_bulk_csv"
            )
            st.success("Bulk results CSV ready for download!")
        
        # Option 2: Generate individual PDF reports for each bulk workload (can be slow for many)
        if st.button("Generate Individual PDF Reports for Bulk Workloads (ZIP)", key="generate_bulk_pdfs"):
            if REPORTLAB_AVAILABLE:
                with st.spinner("Generating individual PDFs and zipping... This may take a while for many workloads."):
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for item in st.session_state.bulk_results:
                            workload_name = item['workload_name']
                            pdf_buffer = generate_pdf_report(
                                workload_name=workload_name,
                                inputs=item['inputs'],
                                recommendations=item['recommendations']
                            )
                            if pdf_buffer:
                                zf.writestr(f"{workload_name}_AWS_Sizing_Report.pdf", pdf_buffer.getvalue())
                    zip_buffer.seek(0)
                    st.download_button(
                        label="Download All PDF Reports (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"bulk_aws_sizing_reports_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                        mime="application/zip",
                        key="download_bulk_pdfs_zip"
                    )
                    st.success("All PDF reports generated and zipped!")
                else:
                    st.error("Failed to generate bulk PDF reports.")
            else:
                st.error("`reportlab` library not found. Cannot generate PDF reports.")
    else:
        st.info("No bulk analysis results available to export.")


# Main Application Logic
def main():
    initialize_session_state()

    st.markdown("""
    <div class="main-header">
        <h1>Enterprise AWS EC2 Workload Sizing Platform</h1>
        <p>Comprehensive cloud migration planning for enterprise infrastructure</p>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("⚙️ Re-fetch Latest AWS Prices", help="Click to refresh AWS pricing data from the AWS Pricing API. This may take a few minutes.", key="fetch_prices_btn"):
        st.session_state.calculator.fetch_current_prices()
        if st.session_state.calculator.all_ec2_prices and st.session_state.calculator.all_ebs_prices:
            st.sidebar.success("✅ Latest AWS prices fetched successfully!")
        else:
            st.sidebar.error("❌ Failed to fetch AWS prices. Check AWS credentials or network.")

    # Check AWS credentials status
    status, message = st.session_state.calculator.validate_aws_credentials()
    if status:
        st.sidebar.success(f"AWS Connection: {message}")
    else:
        st.sidebar.error(f"AWS Connection: {message} Please ensure AWS credentials are set up (e.g., via ~/.aws/credentials or environment variables).")
        st.info("AWS credentials are required to fetch real-time pricing and generate accurate recommendations. Please configure them to proceed.")

    tab1, tab2, tab3 = st.tabs(["Single Workload Analysis", "Bulk Analysis", "Reports & Export"])

    with tab1:
        render_workload_configuration()
        if st.button("✨ Generate Recommendations", type="primary", key="generate_single_recommendation"):
            if not status: # Re-check status before analysis
                st.error("Cannot generate recommendations. AWS credentials are not properly configured.")
            elif not st.session_state.calculator.all_ec2_prices:
                st.info("Fetching AWS prices for the first time or refresh needed. Please wait...")
                st.session_state.calculator.fetch_current_prices()
                if not st.session_state.calculator.all_ec2_prices:
                    st.error("Failed to fetch AWS prices. Cannot proceed with recommendations.")
                    return
            
            with st.spinner("Analyzing workload and generating recommendations..."):
                try:
                    # Pass inputs from session state
                    st.session_state.calculator.inputs = st.session_state.workload_inputs.copy() 
                    results = st.session_state.calculator.generate_all_recommendations()
                    st.session_state.analysis_results = {
                        'inputs': st.session_state.workload_inputs.copy(),
                        'recommendations': results
                    }

                    st.success("✅ Analysis completed successfully!")
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")

        # This block will now be the *only* place render_analysis_results is called for single analysis.
        if st.session_state.analysis_results:
            st.markdown("---")
            render_analysis_results(st.session_state.analysis_results['recommendations'], key_suffix="single_workload")

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
        <strong>Enterprise AWS Workload Sizing Platform v3.0</strong><br>
        Comprehensive cloud migration planning for enterprise infrastructure
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()