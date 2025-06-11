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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

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
            'growth_years': 5             # New: Number of years for projection
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

    env_tabs = st.tabs(["Production (PROD)", "User Acceptance Testing (UAT)", "Development (DEV)"])

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


def render_analysis_results(recommendations):
    """Renders the analysis results for a single workload."""
    st.markdown("## ✨ Analysis Results")

    if not recommendations:
        st.warning("No recommendations available. Please configure your workload and generate recommendations.")
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

        fig_costs = px.pie(df_costs, values='Cost', names='Component', title='PROD Monthly Cost Distribution',
                           hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_costs.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
        st.plotly_chart(fig_costs, use_container_width=True)
    else:
        st.info("PROD environment recommendations not available for cost breakdown.")


    # Workload Growth Projection
    st.markdown("### Workload Growth Projections (PROD)")
    if 'projected_costs' in recommendations.get('PROD', {}) and st.session_state.workload_inputs['growth_years'] > 0:
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
        fig_proj = px.line(df_projected, y="Estimated Cost (Monthly)", title="Projected Monthly Cost Over Time (PROD)",
                           markers=True, text="Estimated Cost (Monthly)")
        fig_proj.update_traces(texttemplate='%{text:$.2f}', textposition='top center')
        fig_proj.update_layout(hovermode="x unified", xaxis_title="Year", yaxis_title="Estimated Monthly Cost ($)")
        st.plotly_chart(fig_proj, use_container_width=True)

        st.markdown(f"""
        <details>
        <summary>Detailed Growth Projection Table</summary>
        <p>This table shows the projected resource requirements and estimated costs for the PROD environment based on an annual growth rate of <b>{st.session_state.workload_inputs['growth_rate_annual']}%</b> over <b>{st.session_state.workload_inputs['growth_years']}</b> years.</p>
        </details>
        """, unsafe_allow_html=True)
        st.dataframe(df_projected, use_container_width=True)

    else:
        st.info("No growth projection data available or growth rate not set.")


def render_bulk_analysis():
    """Renders the UI for bulk analysis."""
    st.markdown("## 📥 Bulk Workload Analysis")
    st.warning("""
        For bulk analysis, please ensure your CSV file has the following columns (case-sensitive):
        `Workload Name`, `Workload Type`, `PROD_vCPUs`, `PROD_Memory_GiB`, `PROD_Storage_GB`, `PROD_OS`, `PROD_Region`,
        `UAT_vCPUs`, `UAT_Memory_GiB`, `UAT_Storage_GB`, `UAT_OS`, `UAT_Region`,
        `DEV_vCPUs`, `DEV_Memory_GiB`, `DEV_Storage_GB`, `DEV_OS`, `DEV_Region`
        
        Optional columns: `RI_SP_Option` (e.g., 'On-Demand', '1-Year No Upfront RI/SP', '3-Year No Upfront RI/SP'), 
        `Annual Growth Rate (%)`, `Projection Years`
    """)

    uploaded_file = st.file_uploader("Upload CSV File", type="csv", key="bulk_upload_file")

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.bulk_upload_df = df
            st.success("File uploaded successfully!")
            st.dataframe(df.head())

            if st.button("🚀 Start Bulk Analysis", type="primary", key="start_bulk_analysis"):
                st.session_state.bulk_results = []
                total_workloads = len(df)
                progress_text = st.empty()
                progress_bar = st.progress(0)

                st.session_state.calculator.fetch_current_prices() # Fetch prices once for bulk

                for i, row in df.iterrows():
                    progress_text.text(f"Analyzing workload {i+1} of {total_workloads}...")
                    progress_bar.progress((i + 1) / total_workloads)

                    # Map CSV columns to workload_inputs structure
                    temp_inputs = {
                        'workload_name': row.get('Workload Name', f'Workload_{i+1}'),
                        'workload_type': row.get('Workload Type', 'Other'),
                        'PROD_vcpus': row.get('PROD_vCPUs', 1),
                        'PROD_memory_gb': row.get('PROD_Memory_GiB', 1.0),
                        'PROD_storage_gb': row.get('PROD_Storage_GB', 50),
                        'PROD_os': row.get('PROD_OS', OPERATING_SYSTEMS["Linux (Amazon Linux 2)"]),
                        'PROD_region': AWS_REGIONS.get(row.get('PROD_Region', "US East (N. Virginia)"), AWS_REGIONS["US East (N. Virginia)"]),
                        'UAT_vcpus': row.get('UAT_vCPUs', 1),
                        'UAT_memory_gb': row.get('UAT_Memory_GiB', 1.0),
                        'UAT_storage_gb': row.get('UAT_Storage_GB', 50),
                        'UAT_os': row.get('UAT_OS', OPERATING_SYSTEMS["Linux (Amazon Linux 2)"]),
                        'UAT_region': AWS_REGIONS.get(row.get('UAT_Region', "US East (N. Virginia)"), AWS_REGIONS["US East (N. Virginia)"]),
                        'DEV_vcpus': row.get('DEV_vCPUs', 1),
                        'DEV_memory_gb': row.get('DEV_Memory_GiB', 1.0),
                        'DEV_storage_gb': row.get('DEV_Storage_GB', 50),
                        'DEV_os': row.get('DEV_OS', OPERATING_SYSTEMS["Linux (Amazon Linux 2)"]),
                        'DEV_region': AWS_REGIONS.get(row.get('DEV_Region', "US East (N. Virginia)"), AWS_REGIONS["US East (N. Virginia)"]),
                        'ri_sp_option': row.get('RI_SP_Option', 'On-Demand'),
                        'growth_rate_annual': row.get('Annual Growth Rate (%)', 0),
                        'growth_years': row.get('Projection Years', 5)
                    }

                    # Temporarily set calculator's inputs for bulk processing
                    st.session_state.calculator.inputs = temp_inputs
                    
                    try:
                        results = st.session_state.calculator.generate_all_recommendations()
                        st.session_state.bulk_results.append({
                            'workload_name': temp_inputs['workload_name'],
                            'inputs': temp_inputs,
                            'recommendations': results
                        })
                    except Exception as e:
                        logger.error(f"Error processing workload {temp_inputs['workload_name']}: {e}")
                        st.session_state.bulk_results.append({
                            'workload_name': temp_inputs['workload_name'],
                            'inputs': temp_inputs,
                            'recommendations': {'error': str(e)}
                        })

                progress_text.empty()
                progress_bar.empty()
                st.success("Bulk analysis completed!")
                st.experimental_rerun() # Rerun to display results in next block

        except pd.errors.EmptyDataError:
            st.error("The uploaded CSV file is empty.")
            st.session_state.bulk_upload_df = None
        except Exception as e:
            st.error(f"Error reading CSV file: {e}. Please ensure it's a valid CSV.")
            st.session_state.bulk_upload_df = None

def display_bulk_analysis_results(bulk_results):
    """Displays results for bulk analysis."""
    st.markdown("## 📈 Bulk Analysis Results Summary")

    if not bulk_results:
        st.info("No bulk analysis results to display.")
        return

    summary_data = []
    for workload_result in bulk_results:
        name = workload_result['workload_name']
        prod_rec = workload_result['recommendations'].get('PROD', {})
        total_cost = prod_rec.get('total_cost', float('inf'))
        instance_type = prod_rec.get('instance_type', 'N/A')
        
        if total_cost == float('inf'):
            cost_str = "N/A"
        else:
            cost_str = f"${total_cost:,.2f}"

        summary_data.append({
            "Workload Name": name,
            "PROD Recommended Instance": instance_type,
            "PROD Monthly Cost": cost_str,
            "RI/SP Option": workload_result['inputs'].get('ri_sp_option', 'N/A')
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, hide_index=True, use_container_width=True)

    csv_data = df_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Summary CSV",
        data=csv_data,
        file_name="bulk_analysis_summary.csv",
        mime="text/csv",
        key="download_bulk_summary"
    )

    st.markdown("---")
    st.markdown("### Detailed Bulk Results")
    if st.button("Expand All Workloads", key="expand_all_bulk"):
        for workload_result in bulk_results:
            name = workload_result['workload_name']
            st.markdown(f"#### Workload: {name}")
            if 'error' in workload_result['recommendations']:
                st.error(f"Error for {name}: {workload_result['recommendations']['error']}")
            else:
                render_analysis_results(workload_result['recommendations'])
            st.markdown("---")
    
    # Allow selection for individual detailed view (if desired, can be added later)
    # selected_workload_name = st.selectbox("View detailed results for a specific workload:", 
    #                                       [res['workload_name'] for res in bulk_results])
    # if selected_workload_name:
    #     selected_workload = next((res for res in bulk_results if res['workload_name'] == selected_workload_name), None)
    #     if selected_workload and 'error' not in selected_workload['recommendations']:
    #         render_analysis_results(selected_workload['recommendations'])
    #     elif selected_workload:
    #         st.error(f"Error for {selected_workload_name}: {selected_workload['recommendations']['error']}")


def generate_pdf_report(analysis_results, workload_inputs, buffer):
    """Generates a PDF report for the analysis results."""
    if not REPORTLAB_AVAILABLE:
        st.error("ReportLab library not installed. Cannot generate PDF report. Please install with `pip install reportlab`.")
        return

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=inch/2, leftMargin=inch/2,
                            topMargin=inch/2, bottomMargin=inch/2)
    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(name='TitleStyle', fontSize=24, leading=28, alignment=TA_CENTER,
                              fontName='Helvetica-Bold', spaceAfter=24))
    styles.add(ParagraphStyle(name='Heading1', fontSize=18, leading=22, spaceAfter=12,
                              fontName='Helvetica-Bold', textColor=colors.HexColor('#4c51bf')))
    styles.add(ParagraphStyle(name='Heading2', fontSize=14, leading=18, spaceAfter=8,
                              fontName='Helvetica-Bold', textColor=colors.HexColor('#667eea')))
    styles.add(ParagraphStyle(name='BodyText', fontSize=10, leading=12, spaceAfter=6,
                              fontName='Helvetica'))
    styles.add(ParagraphStyle(name='SmallText', fontSize=8, leading=10, spaceAfter=4,
                              fontName='Helvetica'))
    styles.add(ParagraphStyle(name='TableHeading', fontSize=10, leading=12, alignment=TA_CENTER,
                              fontName='Helvetica-Bold', textColor=colors.white))
    styles.add(ParagraphStyle(name='TableData', fontSize=9, leading=10, alignment=TA_LEFT,
                              fontName='Helvetica'))
    
    story = []

    # Title Page
    story.append(Paragraph("Enterprise AWS Workload Sizing Report", styles['TitleStyle']))
    story.append(Paragraph(f"Workload Name: {workload_inputs.get('workload_name', 'N/A')}", styles['Heading1']))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['BodyText']))
    story.append(Spacer(0, 0.5*inch))
    
    story.append(Paragraph("Overview", styles['Heading2']))
    story.append(Paragraph("This report provides an analysis of recommended AWS EC2 instances and estimated monthly costs for various environments (Production, UAT, Development) based on your specified workload requirements.", styles['BodyText']))
    story.append(Spacer(0, 0.2*inch))

    story.append(Paragraph("Input Parameters", styles['Heading2']))
    input_data = [
        ["Parameter", "Value"],
        ["Workload Type", workload_inputs.get('workload_type', 'N/A')],
        ["Pricing Model/Commitment", workload_inputs.get('ri_sp_option', 'N/A')],
        ["Annual Growth Rate (%)", f"{workload_inputs.get('growth_rate_annual', 0)}%"],
        ["Projection Years", workload_inputs.get('growth_years', 0)]
    ]
    
    for env in ['PROD', 'UAT', 'DEV']:
        input_data.append([f"{env} vCPUs", workload_inputs.get(f'{env}_vcpus', 'N/A')])
        input_data.append([f"{env} Memory (GiB)", workload_inputs.get(f'{env}_memory_gb', 'N/A')])
        input_data.append([f"{env} Storage (GB)", workload_inputs.get(f'{env}_storage_gb', 'N/A')])
        input_data.append([f"{env} OS", workload_inputs.get(f'{env}_os', 'N/A')])
        region_code = workload_inputs.get(f'{env}_region', '')
        region_name = next((name for name, code in AWS_REGIONS.items() if code == region_code), region_code)
        input_data.append([f"{env} Region", region_name])
    
    input_table = Table(input_data, colWidths=[2.5*inch, 4*inch])
    input_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4c51bf')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('ALIGN', (1,1), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
    ]))
    story.append(input_table)
    story.append(PageBreak())

    # Recommendations Section
    story.append(Paragraph("Recommended AWS Instances and Costs", styles['Heading1']))
    story.append(Spacer(0, 0.2*inch))

    for env in ['PROD', 'UAT', 'DEV']:
        rec = analysis_results.get(env)
        if rec and rec['total_cost'] != float('inf'):
            story.append(Paragraph(f"**{env} Environment**", styles['Heading2']))
            
            rec_data = [
                ["Parameter", "Value"],
                ["Recommended Instance Type", rec.get('instance_type', 'N/A')],
                ["vCPUs", rec.get('vcpus', 'N/A')],
                ["Memory (GiB)", f"{rec.get('memory_gb', 'N/A'):.1f}"],
                ["Storage (GB)", rec.get('storage_gb', 'N/A')],
                ["Operating System", rec.get('os', 'N/A')],
                ["Region", next(k for k, v in AWS_REGIONS.items() if v == rec['region'])],
                ["Pricing Model", rec.get('ri_sp_option', 'N/A')],
                ["Monthly EC2 Instance Cost", f"${rec.get('instance_cost', 0):,.2f}"],
                ["Monthly EBS Storage Cost", f"${rec.get('ebs_cost', 0):,.2f}"],
                ["Monthly OS Cost", f"${rec.get('os_cost', 0):,.2f}"], # Still 0 in this simplified model
                ["Total Monthly Cost", f"${rec.get('total_cost', 0):,.2f}"]
            ]
            rec_table = Table(rec_data, colWidths=[2.5*inch, 4*inch])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f7fafc')),
                ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
                ('ALIGN', (0,1), (0,-1), 'LEFT'),
                ('ALIGN', (1,1), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,1), (-1,-1), 9),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            story.append(rec_table)
            story.append(Spacer(0, 0.4*inch))
        else:
            story.append(Paragraph(f"**{env} Environment:** No suitable instance found or error occurred.", styles['BodyText']))
            story.append(Spacer(0, 0.2*inch))

    # Growth Projection Section
    prod_rec = analysis_results.get('PROD', {})
    if 'projected_costs' in prod_rec and workload_inputs.get('growth_years', 0) > 0:
        story.append(PageBreak())
        story.append(Paragraph("Workload Growth Projections (PROD)", styles['Heading1']))
        story.append(Paragraph(f"Projected resource requirements and estimated monthly costs for the PROD environment based on an annual growth rate of {workload_inputs.get('growth_rate_annual', 0)}% over {workload_inputs.get('growth_years', 0)} years.", styles['BodyText']))
        story.append(Spacer(0, 0.2*inch))

        proj_headers = ["Year", "Projected vCPUs", "Projected Memory (GiB)", "Projected Storage (GB)", "Recommended Instance", "Estimated Monthly Cost"]
        proj_data = [proj_headers]

        for year_str, details in prod_rec['projected_costs'].items():
            cost_value = details['estimated_cost']
            cost_display = f"${cost_value:,.2f}" if isinstance(cost_value, (int, float)) else "N/A"
            proj_data.append([
                year_str,
                details['vcpus'],
                f"{details['memory_gb']:.1f}",
                details['storage_gb'],
                details['recommended_instance'],
                cost_display
            ])
        
        proj_table = Table(proj_data, colWidths=[1*inch, 1.2*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.6*inch])
        proj_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4c51bf')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('ALIGN', (0,1), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
        ]))
        story.append(proj_table)
        story.append(Spacer(0, 0.4*inch))
    else:
        story.append(Paragraph("No growth projection data available.", styles['BodyText']))
        story.append(Spacer(0, 0.2*inch))


    # Footer
    story.append(PageBreak())
    story.append(Paragraph("--- End of Report ---", styles['SmallText'], alignment=TA_CENTER))

    try:
        doc.build(story)
        logger.info("PDF report generated successfully.")
    except Exception as e:
        logger.error(f"Error building PDF: {e}")
        st.error(f"Error generating PDF report: {e}")

def render_reports_export():
    """Renders the UI for reports and export."""
    st.markdown("## 📋 Reports & Export")

    if st.session_state.analysis_results:
        st.markdown("### Single Workload Report")
        if REPORTLAB_AVAILABLE:
            pdf_buffer = BytesIO()
            generate_pdf_report(st.session_state.analysis_results, st.session_state.workload_inputs, pdf_buffer)
            st.download_button(
                label="Download PDF Report",
                data=pdf_buffer.getvalue(),
                file_name=f"workload_report_{st.session_state.workload_inputs.get('workload_name', 'single').replace(' ', '_').lower()}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Install `reportlab` to enable PDF report generation (`pip install reportlab`).")

        # Export to CSV
        csv_data = []
        for env, rec in st.session_state.analysis_results.items():
            if rec['total_cost'] != float('inf'):
                row = {
                    "Workload Name": st.session_state.workload_inputs.get('workload_name', 'Single Workload'),
                    "Environment": env,
                    "Recommended Instance": rec['instance_type'],
                    "vCPUs": rec['vcpus'],
                    "Memory (GiB)": rec['memory_gb'],
                    "Storage (GB)": rec['storage_gb'],
                    "OS": rec['os'],
                    "Region": next(k for k, v in AWS_REGIONS.items() if v == rec['region']),
                    "Pricing Model": rec['ri_sp_option'],
                    "Monthly EC2 Instance Cost": rec['instance_cost'],
                    "Monthly EBS Storage Cost": rec['ebs_cost'],
                    "Monthly OS Cost": rec['os_cost'],
                    "Total Monthly Cost": rec['total_cost']
                }
                csv_data.append(row)
        
        # Add growth projections to CSV if available
        prod_rec = st.session_state.analysis_results.get('PROD', {})
        if 'projected_costs' in prod_rec and st.session_state.workload_inputs['growth_years'] > 0:
            for year_str, details in prod_rec['projected_costs'].items():
                cost_value = details['estimated_cost']
                csv_data.append({
                    "Workload Name": st.session_state.workload_inputs.get('workload_name', 'Single Workload'),
                    "Environment": f"PROD - {year_str} Projection",
                    "Recommended Instance": details['recommended_instance'],
                    "vCPUs": details['vcpus'],
                    "Memory (GiB)": details['memory_gb'],
                    "Storage (GB)": details['storage_gb'],
                    "OS": prod_rec['os'],
                    "Region": next(k for k, v in AWS_REGIONS.items() if v == prod_rec['region']),
                    "Pricing Model": prod_rec['ri_sp_option'],
                    "Monthly EC2 Instance Cost": "N/A", # Not broken down in projections
                    "Monthly EBS Storage Cost": "N/A",
                    "Monthly OS Cost": "N/A",
                    "Total Monthly Cost": cost_value if isinstance(cost_value, (int, float)) else "N/A"
                })

        if csv_data:
            df_export = pd.DataFrame(csv_data)
            csv_export = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Single Workload CSV",
                data=csv_export,
                file_name=f"workload_details_{st.session_state.workload_inputs.get('workload_name', 'single').replace(' ', '_').lower()}.csv",
                mime="text/csv"
            )

    if st.session_state.bulk_results:
        st.markdown("### Bulk Analysis Export")
        
        # Prepare data for detailed bulk CSV
        bulk_detailed_data = []
        for workload_result in st.session_state.bulk_results:
            workload_name = workload_result['workload_name']
            inputs = workload_result['inputs']
            recs = workload_result['recommendations']

            if 'error' in recs:
                bulk_detailed_data.append({
                    "Workload Name": workload_name,
                    "Status": "Error",
                    "Error Message": recs['error'],
                    **{f"Input_{k}": v for k,v in inputs.items()} # Include inputs for error rows
                })
                continue

            for env, rec in recs.items():
                row = {
                    "Workload Name": workload_name,
                    "Environment": env,
                    "Status": "Success",
                    "Recommended Instance": rec.get('instance_type', 'N/A'),
                    "vCPUs": rec.get('vcpus', 'N/A'),
                    "Memory (GiB)": rec.get('memory_gb', 'N/A'),
                    "Storage (GB)": rec.get('storage_gb', 'N/A'),
                    "OS": rec.get('os', 'N/A'),
                    "Region": next((k for k, v in AWS_REGIONS.items() if v == rec.get('region')), rec.get('region', 'N/A')),
                    "Pricing Model": rec.get('ri_sp_option', 'N/A'),
                    "Monthly EC2 Instance Cost": rec.get('instance_cost', 'N/A'),
                    "Monthly EBS Storage Cost": rec.get('ebs_cost', 'N/A'),
                    "Monthly OS Cost": rec.get('os_cost', 'N/A'),
                    "Total Monthly Cost": rec.get('total_cost', 'N/A') if rec.get('total_cost', float('inf')) != float('inf') else 'N/A',
                    "Annual Growth Rate (%)": inputs.get('growth_rate_annual', 'N/A'),
                    "Projection Years": inputs.get('growth_years', 'N/A')
                }
                bulk_detailed_data.append(row)

                # Add projected costs for PROD if available
                if env == 'PROD' and 'projected_costs' in rec and inputs.get('growth_years', 0) > 0:
                    for year_str, proj_details in rec['projected_costs'].items():
                        proj_cost_value = proj_details['estimated_cost']
                        bulk_detailed_data.append({
                            "Workload Name": workload_name,
                            "Environment": f"PROD - {year_str} Projection",
                            "Status": "Success",
                            "Recommended Instance": proj_details['recommended_instance'],
                            "vCPUs": proj_details['vcpus'],
                            "Memory (GiB)": proj_details['memory_gb'],
                            "Storage (GB)": proj_details['storage_gb'],
                            "OS": rec['os'],
                            "Region": next((k for k, v in AWS_REGIONS.items() if v == rec.get('region')), rec.get('region', 'N/A')),
                            "Pricing Model": rec.get('ri_sp_option', 'N/A'),
                            "Monthly EC2 Instance Cost": "N/A",
                            "Monthly EBS Storage Cost": "N/A",
                            "Monthly OS Cost": "N/A",
                            "Total Monthly Cost": proj_cost_value if isinstance(proj_cost_value, (int, float)) else "N/A",
                            "Annual Growth Rate (%)": inputs.get('growth_rate_annual', 'N/A'),
                            "Projection Years": inputs.get('growth_years', 'N/A')
                        })

        if bulk_detailed_data:
            df_bulk_export = pd.DataFrame(bulk_detailed_data)
            bulk_csv_export = df_bulk_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Detailed Bulk Results CSV",
                data=bulk_csv_export,
                file_name="bulk_analysis_detailed_results.csv",
                mime="text/csv"
            )
        else:
            st.info("No bulk results to export.")


# Main application
def main():
    """Main application entry point."""
    initialize_session_state()

    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise AWS Workload Sizing Platform</h1>
        <p>Comprehensive infrastructure assessment and cloud migration planning for enterprise workloads</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🔧 Global Configuration")

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

            total_workloads = 0
            total_monthly_cost = 0.0

            if st.session_state.bulk_results:
                total_workloads += len(st.session_state.bulk_results)
                for res in st.session_state.bulk_results:
                    if 'PROD' in res['recommendations'] and 'total_cost' in res['recommendations']['PROD'] and res['recommendations']['PROD']['total_cost'] != float('inf'):
                        total_monthly_cost += res['recommendations']['PROD']['total_cost']
            
            if st.session_state.analysis_results and 'PROD' in st.session_state.analysis_results['recommendations'] and st.session_state.analysis_results['recommendations']['PROD']['total_cost'] != float('inf'):
                # If both single and bulk results exist, avoid double counting for 'total_workloads' if a single analysis is also active
                # For simplicity, if a single analysis is active, count it as 1 additional workload if not part of bulk.
                # A more robust solution might distinguish between 'single' and 'bulk' states explicitly.
                if not st.session_state.bulk_results: # Only add if no bulk results are active
                     total_workloads += 1 
                total_monthly_cost += st.session_state.analysis_results['recommendations']['PROD']['total_cost']

            st.metric("Workloads Analyzed", total_workloads)
            st.metric("Monthly Cost (PROD)", f"${total_monthly_cost:,.2f}")
            st.metric("Annual Cost (PROD)", f"${total_monthly_cost * 12:,.2f}")

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
                    st.session_state.calculator.fetch_current_prices()
                    # Ensure the calculator has the current inputs from session state
                    st.session_state.calculator.inputs = st.session_state.workload_inputs.copy() 
                    results = st.session_state.calculator.generate_all_recommendations()
                    st.session_state.analysis_results = {
                        'inputs': st.session_state.workload_inputs.copy(),
                        'recommendations': results
                    }

                    st.success("✅ Analysis completed successfully!")
                    # The results will be rendered when the tab refreshes based on st.session_state.analysis_results
                    # No need to call render_analysis_results here directly after setting session state
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")

        # This block will now be the *only* place render_analysis_results is called for single analysis.
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
        <strong>Enterprise AWS Workload Sizing Platform v3.0</strong><br>
        Comprehensive cloud migration planning for enterprise infrastructure
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()