# Complete Enhanced AWS Migration Analysis Platform v7.0
# Requirements: streamlit>=1.28.0, pandas>=1.5.0, plotly>=5.0.0, reportlab>=3.6.0, anthropic>=0.8.0, openpyxl>=3.1.0

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import boto3
import json
import logging
from datetime import datetime, timedelta
import io
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import anthropic
import requests
import csv
from io import StringIO

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="Enhanced AWS Migration Platform v7.0",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Try to import openpyxl for Excel generation
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .env-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem;
        text-align: center;
        transition: all 0.3s ease;
        min-height: 120px;
    }
    
    .env-dev { border-left: 4px solid #3b82f6; }
    .env-qa { border-left: 4px solid #8b5cf6; }
    .env-uat { border-left: 4px solid #f59e0b; }
    .env-preprod { border-left: 4px solid #ef4444; }
    .env-prod { border-left: 4px solid #10b981; }
</style>
""", unsafe_allow_html=True)

class ClaudeAIMigrationAnalyzer:
    """Real Claude AI powered migration complexity analyzer using Anthropic API."""
    
    def __init__(self):
        self.complexity_factors = {
            'application_architecture': {'weight': 0.25},
            'technical_stack': {'weight': 0.20},
            'operational_complexity': {'weight': 0.20},
            'business_impact': {'weight': 0.20},
            'organizational_readiness': {'weight': 0.15}
        }

    def analyze_workload_complexity(self, workload_inputs: Dict, environment: str) -> Dict[str, Any]:
        """Analyze migration complexity using real Claude AI API."""
        
        try:
            # Get Claude API key from Streamlit secrets or environment
            api_key = self._get_claude_api_key()
            
            if not api_key:
                logger.warning("Claude API key not found, using fallback analysis")
                return self._get_fallback_analysis()
            
            # Initialize Claude client
            client = anthropic.Anthropic(api_key=api_key)
            
            # Prepare the prompt for Claude
            analysis_prompt = self._create_analysis_prompt(workload_inputs, environment)
            
            # Make API call to Claude
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                temperature=0.1,
                system="You are an expert AWS migration architect. Analyze the provided workload information and provide detailed migration recommendations in JSON format.",
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )
            
            # Parse Claude's response
            analysis_result = self._parse_claude_response(response.content[0].text)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in Claude AI analysis: {e}")
            return self._get_fallback_analysis()

    def _get_claude_api_key(self) -> Optional[str]:
        """Get Claude API key from Streamlit secrets or environment variables."""
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
                return str(st.secrets['ANTHROPIC_API_KEY'])
            
            # Try environment variable
            import os
            return os.getenv('ANTHROPIC_API_KEY')
            
        except Exception:
            return None

    def _create_analysis_prompt(self, workload_inputs: Dict, environment: str) -> str:
        """Create a detailed prompt for Claude to analyze the workload."""
        
        prompt = f"""
        Please analyze the following workload for AWS migration and provide a comprehensive assessment in JSON format.

        **Workload Information:**
        - Name: {workload_inputs.get('workload_name', 'Unknown')}
        - Type: {workload_inputs.get('workload_type', 'web_application')}
        - Operating System: {workload_inputs.get('operating_system', 'linux')}
        - Environment: {environment}
        - Region: {workload_inputs.get('region', 'us-east-1')}

        **Current Infrastructure:**
        - CPU Cores: {workload_inputs.get('on_prem_cores', 8)}
        - Peak CPU Usage: {workload_inputs.get('peak_cpu_percent', 70)}%
        - RAM: {workload_inputs.get('on_prem_ram_gb', 32)} GB
        - Peak RAM Usage: {workload_inputs.get('peak_ram_percent', 80)}%
        - Storage: {workload_inputs.get('storage_current_gb', 500)} GB
        - Peak IOPS: {workload_inputs.get('peak_iops', 5000)}
        - Peak Throughput: {workload_inputs.get('peak_throughput_mbps', 250)} MB/s
        - Infrastructure Age: {workload_inputs.get('infrastructure_age_years', 3)} years
        - Business Criticality: {workload_inputs.get('business_criticality', 'medium')}

        Please provide your analysis in the following JSON structure:
        
        {{
            "complexity_score": <number 0-100>,
            "complexity_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
            "complexity_color": "<low|medium|high|critical>",
            "migration_strategy": {{
                "approach": "<migration approach>",
                "methodology": "<migration methodology>",
                "timeline": "<estimated timeline>",
                "risk_level": "<risk assessment>"
            }},
            "migration_steps": [
                {{
                    "phase": "<phase name>",
                    "duration": "<duration>",
                    "tasks": ["<task1>", "<task2>", "<task3>"],
                    "deliverables": ["<deliverable1>", "<deliverable2>"]
                }}
            ],
            "risk_factors": [
                {{
                    "category": "<risk category>",
                    "risk": "<risk description>",
                    "probability": "<Low|Medium|High>",
                    "impact": "<Low|Medium|High|Critical>",
                    "mitigation": "<mitigation strategy>"
                }}
            ],
            "estimated_timeline": {{
                "min_weeks": <number>,
                "max_weeks": <number>,
                "confidence": "<Low|Medium|High>"
            }},
            "recommendations": [
                "<recommendation1>",
                "<recommendation2>",
                "<recommendation3>"
            ],
            "success_factors": [
                "<factor1>",
                "<factor2>",
                "<factor3>"
            ]
        }}

        Consider the environment type ({environment}) when assessing complexity, risk, and timeline. Production environments should have higher complexity scores and longer timelines due to stricter requirements.

        Base your complexity score on:
        - Technical complexity (40%)
        - Operational requirements (25%)
        - Business impact (20%)
        - Migration risk (15%)

        Provide specific, actionable recommendations based on AWS best practices.
        """
        
        return prompt

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response and validate it."""
        try:
            # Try to extract JSON from the response
            import re
            
            # Look for JSON block in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                parsed_response = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['complexity_score', 'complexity_level', 'migration_strategy']
                
                for field in required_fields:
                    if field not in parsed_response:
                        logger.warning(f"Missing required field: {field}")
                        return self._get_fallback_analysis()
                
                # Ensure complexity_color is set
                if 'complexity_color' not in parsed_response:
                    level = parsed_response.get('complexity_level', 'MEDIUM').lower()
                    parsed_response['complexity_color'] = level.lower()
                
                return parsed_response
            
            else:
                logger.warning("No JSON found in Claude response")
                return self._get_fallback_analysis()
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            return self._get_fallback_analysis()
        except Exception as e:
            logger.error(f"Error parsing Claude response: {e}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when Claude API is not available."""
        return {
            'complexity_score': 50,
            'complexity_level': 'MEDIUM',
            'complexity_color': 'medium',
            'migration_strategy': {
                'approach': 'Standard Migration with Optimization',
                'methodology': 'Lift and shift with selective modernization',
                'timeline': '6-10 weeks',
                'risk_level': 'Medium'
            },
            'migration_steps': [
                {
                    'phase': 'Discovery & Assessment',
                    'duration': '1-2 weeks',
                    'tasks': [
                        'Infrastructure inventory and dependency mapping',
                        'Performance baseline establishment',
                        'Security and compliance assessment'
                    ],
                    'deliverables': ['Migration plan', 'Risk assessment', 'Architecture design']
                },
                {
                    'phase': 'Migration Execution',
                    'duration': '3-6 weeks',
                    'tasks': [
                        'Environment setup and configuration',
                        'Application migration and testing',
                        'Performance optimization'
                    ],
                    'deliverables': ['Migrated workload', 'Test results', 'Documentation']
                },
                {
                    'phase': 'Validation & Go-Live',
                    'duration': '1-2 weeks',
                    'tasks': [
                        'End-to-end testing',
                        'Production cutover',
                        'Post-migration optimization'
                    ],
                    'deliverables': ['Production workload', 'Support procedures']
                }
            ],
            'risk_factors': [
                {
                    'category': 'Technical',
                    'risk': 'Application compatibility issues',
                    'probability': 'Medium',
                    'impact': 'High',
                    'mitigation': 'Comprehensive testing in staging environment'
                },
                {
                    'category': 'Operational',
                    'risk': 'Extended downtime during cutover',
                    'probability': 'Low',
                    'impact': 'High',
                    'mitigation': 'Blue-green deployment strategy'
                }
            ],
            'estimated_timeline': {'min_weeks': 6, 'max_weeks': 10, 'confidence': 'Medium'},
            'recommendations': [
                'Implement comprehensive backup and rollback procedures',
                'Conduct thorough security and compliance validation',
                'Plan for adequate testing and validation phases',
                'Establish clear success criteria and KPIs'
            ],
            'success_factors': [
                'Strong project leadership and governance',
                'Clear communication with all stakeholders',
                'Adequate resource allocation and timeline',
                'Comprehensive testing strategy'
            ]
        }

class AWSCostCalculator:
    """AWS service cost calculator with detailed pricing breakdown."""
    
    def __init__(self, region='us-east-1'):
        # Initialize AWS Pricing client
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.region = region
        
        # Initialize pricing data structure
        self.pricing = {
            'compute': {
                'ec2_instances': {},
                'elastic_ip': 0.005  # per hour
            },
            'network': {
                'alb': 0.0225,  # per ALB per hour
                'nlb': 0.0225,  # per NLB per hour
                'nat_gateway': 0.045,  # per NAT per hour
                'cloudfront': {'per_gb': 0.085},
                'route53': {'hosted_zone': 0.50},
                'data_transfer': {'out_to_internet_up_to_10tb': 0.09},
                'vpn_gateway': 0.05  # per hour
            },
            'storage': {
                'ebs': {
                    'gp3': 0.08,  # per GB-month
                    'io2': 0.125,  # per GB-month
                    'io2_iops': 0.065,  # per provisioned IOPS
                    'snapshots': 0.05  # per GB-month
                },
                's3': {
                    'standard': 0.023,  # per GB-month
                    'standard_ia': 0.0125,  # per GB-month
                    'glacier': 0.004  # per GB-month
                }
            },
            'database': {
                'aurora_mysql': {
                    'db.r6g.large': 0.274,  # per hour
                    'db.r6g.xlarge': 0.548
                },
                'rds_mysql': {
                    'db.r6g.large': 0.252,  # per hour
                    'db.r6g.xlarge': 0.504
                },
                'storage': {
                    'aurora_storage': 0.10,  # per GB-month
                    'aurora_io': 0.20,  # per million requests
                    'rds_gp2': 0.115  # per GB-month
                },
                'backup_storage': 0.095,  # per GB-month
                'rds_proxy': 0.015  # per vCPU-hour
            },
            'security': {
                'secrets_manager': 0.40,  # per secret per month
                'kms': 1.00,  # per key per month
                'config': 0.003,  # per configuration item
                'cloudtrail': 0.10,  # per 100,000 events
                'guardduty': 0.10,  # per GB analyzed
                'security_hub': 0.0010,  # per security check
                'waf': 0.60  # per web ACL per month
            },
            'monitoring': {
                'cloudwatch': {
                    'metrics': 0.30,  # per custom metric
                    'dashboards': 3.00,  # per dashboard
                    'alarms': 0.10,  # per alarm
                    'logs_ingestion': 0.50,  # per GB
                    'logs_storage': 0.03  # per GB-month
                },
                'xray': 0.000005,  # per trace
                'synthetics': 0.0012  # per canary run
            }
        }

    def get_real_pricing(self, service_code: str, filters: list) -> list:
        """Get real pricing from AWS Pricing API."""
        try:
            response = self.pricing_client.get_products(
                ServiceCode=service_code,
                Filters=filters,
                MaxResults=100
            )
            return response['PriceList']
        except Exception as e:
            logger.error(f"Error getting real pricing: {e}")
            return []
        
    def _get_ec2_pricing(self, instance_type: str) -> dict:
        """Get EC2 pricing from AWS Pricing API."""
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_region_name(self.region)},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
        ]
        
        price_list = self.get_real_pricing('AmazonEC2', filters)
        pricing = {}
        
        for price in price_list:
            data = json.loads(price)
            terms = data.get('terms', {})
            on_demand = terms.get('OnDemand', {})
            
            for term_id, term_data in on_demand.items():
                price_dimensions = term_data.get('priceDimensions', {})
                for dim_id, dim_data in price_dimensions.items():
                    if 'USD' in dim_data.get('pricePerUnit', {}):
                        usd_price = dim_data['pricePerUnit']['USD']
                        pricing['on_demand'] = float(usd_price)
                        break
                if 'on_demand' in pricing:
                    break
                    
        # Fallback if no pricing found
        if not pricing:
            logger.warning(f"Using fallback pricing for {instance_type}")
            fallback_prices = {
                'm6i.large': {'on_demand': 0.0864, 'ri_1y': 0.0605, 'ri_3y': 0.0432, 'spot': 0.0259},
                'm6i.xlarge': {'on_demand': 0.1728, 'ri_1y': 0.1210, 'ri_3y': 0.0864, 'spot': 0.0518},
                'm6i.2xlarge': {'on_demand': 0.3456, 'ri_1y': 0.2419, 'ri_3y': 0.1728, 'spot': 0.1037},
                'm6i.4xlarge': {'on_demand': 0.6912, 'ri_1y': 0.4838, 'ri_3y': 0.3456, 'spot': 0.2074},
                'r6i.large': {'on_demand': 0.1008, 'ri_1y': 0.0706, 'ri_3y': 0.0504, 'spot': 0.0302},
                'r6i.xlarge': {'on_demand': 0.2016, 'ri_1y': 0.1411, 'ri_3y': 0.1008, 'spot': 0.0605}
            }
            return fallback_prices.get(instance_type, {'on_demand': 0.1, 'ri_1y': 0.07, 'ri_3y': 0.05, 'spot': 0.03})
        
        return pricing

    # ... rest of the class remains the same ...
    
    def _get_region_name(self, region_code: str) -> str:
        """Map AWS region code to full name."""
        region_map = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'eu-west-2': 'EU (London)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
        }
        return region_map.get(region_code, region_code)
    
    def calculate_service_costs(self, env: str, tech_recs: Dict, requirements: Dict) -> Dict[str, Any]:
        """Calculate detailed costs for all AWS services."""
        
        costs = {
            'compute': self._calculate_compute_costs(env, tech_recs['compute'], requirements),
            'network': self._calculate_network_costs(env, tech_recs['network'], requirements),
            'storage': self._calculate_storage_costs(env, tech_recs['storage'], requirements),
            'database': self._calculate_database_costs(env, tech_recs['database'], requirements),
            'security': self._calculate_security_costs(env, tech_recs['security'], requirements),
            'monitoring': self._calculate_monitoring_costs(env, tech_recs['monitoring'], requirements)
        }
        
        # Calculate totals
        total_monthly = sum(category['total'] for category in costs.values())
        total_annual = total_monthly * 12
        
        costs['summary'] = {
            'total_monthly': total_monthly,
            'total_annual': total_annual,
            'largest_cost_category': max(costs.keys(), key=lambda k: costs[k]['total'] if k != 'summary' else 0)
        }
        
        return costs
    
    # Remaining methods same as before but using real pricing API
    # ... (rest of the AWSCostCalculator methods) ...
    def _calculate_compute_costs(self, env: str, compute_recs: Dict, requirements: Dict) -> Dict[str, Any]:
        """Calculate compute-related costs."""
        
        instance_type = compute_recs['primary_instance']['type']
        instance_count = self._get_instance_count(env)
        
        # EC2 instance costs
        instance_pricing = self.pricing['compute']['ec2_instances'].get(instance_type, {
        'on_demand': 0.1, 'ri_1y': 0.07, 'ri_3y': 0.05, 'spot': 0.03
    })
        
        # Determine pricing model
        pricing_model = 'on_demand'
        if env in ['PROD', 'PREPROD']:
            pricing_model = 'ri_1y'
        
        monthly_instance_cost = instance_pricing[pricing_model] * instance_count
        
        # Auto Scaling (no additional cost, but affects instance count)
        scaling_info = compute_recs.get('scaling', {})
        max_instances = scaling_info.get('max_instances', instance_count)
        
        # Elastic IP costs (if needed)
        eip_cost = self.pricing['compute']['elastic_ip'] * instance_count if env in ['PROD', 'PREPROD'] else 0
        
        total_compute = monthly_instance_cost + eip_cost
        
        return {
            'ec2_instances': {
                'cost': monthly_instance_cost,
                'details': f"{instance_count}x {instance_type} ({pricing_model})",
                'breakdown': {
                    'instance_type': instance_type,
                    'instance_count': instance_count,
                    'pricing_model': pricing_model,
                    'unit_cost': instance_pricing[pricing_model],
                    'max_instances_scaling': max_instances
                }
            },
            'elastic_ip': {
                'cost': eip_cost,
                'details': f"{instance_count} Elastic IPs" if eip_cost > 0 else "No Elastic IPs"
            },
            'auto_scaling': {
                'cost': 0,
                'details': "No additional cost - scales existing instances"
            },
            'total': total_compute,
            'optimization_notes': self._get_compute_optimization_notes(env, instance_type, pricing_model)
        }
    
    def _calculate_network_costs(self, env: str, network_recs: Dict, requirements: Dict) -> Dict[str, Any]:
        """Calculate network-related costs."""
        
        # Load Balancer costs
        lb_cost = 0
        lb_type = network_recs.get('load_balancer', '')
        if 'ALB' in lb_type:
            lb_cost = self.pricing['network']['alb']
        elif 'NLB' in lb_type:
            lb_cost = self.pricing['network']['nlb']
        
        # NAT Gateway costs
        nat_cost = 0
        if network_recs.get('nat_gateway') == 'Required':
            nat_count = 2 if env in ['PROD', 'PREPROD'] else 1
            nat_cost = self.pricing['network']['nat_gateway'] * nat_count
        
        # CloudFront costs (estimated)
        cdn_cost = 0
        if network_recs.get('cdn') == 'CloudFront':
            estimated_gb_month = self._estimate_cdn_usage(env)
            cdn_cost = estimated_gb_month * self.pricing['network']['cloudfront']['per_gb']
        
        # Route 53 costs
        dns_cost = self.pricing['network']['route53']['hosted_zone']
        if 'health checks' in network_recs.get('dns', ''):
            dns_cost += 0.50 * 2
        
        # Data transfer costs (estimated)
        data_transfer_cost = self._estimate_data_transfer_costs(env)
        
        # VPN costs
        vpn_cost = 0
        if 'VPN' in network_recs.get('vpn', ''):
            vpn_cost = self.pricing['network']['vpn_gateway']
        
        total_network = lb_cost + nat_cost + cdn_cost + dns_cost + data_transfer_cost + vpn_cost
        
        return {
            'load_balancer': {
                'cost': lb_cost,
                'details': f"{lb_type}" if lb_cost > 0 else "No load balancer"
            },
            'nat_gateway': {
                'cost': nat_cost,
                'details': f"{int(nat_cost / self.pricing['network']['nat_gateway'])} NAT Gateways" if nat_cost > 0 else "No NAT Gateway"
            },
            'cloudfront_cdn': {
                'cost': cdn_cost,
                'details': f"~{self._estimate_cdn_usage(env)} GB/month" if cdn_cost > 0 else "No CDN"
            },
            'route53_dns': {
                'cost': dns_cost,
                'details': "Hosted zone + health checks" if dns_cost > 1 else "Basic hosted zone"
            },
            'data_transfer': {
                'cost': data_transfer_cost,
                'details': f"Estimated data transfer costs"
            },
            'vpn_gateway': {
                'cost': vpn_cost,
                'details': "Site-to-site VPN" if vpn_cost > 0 else "No VPN"
            },
            'total': total_network,
            'optimization_notes': self._get_network_optimization_notes(env)
        }
    
    def _calculate_storage_costs(self, env: str, storage_recs: Dict, requirements: Dict) -> Dict[str, Any]:
        """Calculate storage-related costs."""
        
        # Primary EBS storage
        storage_gb = requirements.get('storage_GB', 100)
        
        # EBS volume costs
        primary_storage_type = storage_recs.get('primary_storage', 'gp3')
        if 'gp3' in primary_storage_type:
            ebs_cost = storage_gb * self.pricing['storage']['ebs']['gp3']
        elif 'io2' in primary_storage_type:
            ebs_cost = storage_gb * self.pricing['storage']['ebs']['io2']
            # Add IOPS costs for io2
            iops = self._extract_iops_from_recommendation(storage_recs.get('iops_recommendation', ''))
            if iops > 3000:
                additional_iops = iops - 3000
                ebs_cost += additional_iops * self.pricing['storage']['ebs']['io2_iops']
        else:
            ebs_cost = storage_gb * self.pricing['storage']['ebs']['gp3']
        
        # Snapshot costs (for backup)
        snapshot_frequency = self._get_snapshot_frequency(storage_recs.get('backup_strategy', ''))
        snapshot_retention_gb = storage_gb * snapshot_frequency * 0.3
        snapshot_cost = snapshot_retention_gb * self.pricing['storage']['ebs']['snapshots']
        
        # S3 costs for long-term backup/archival
        s3_cost = 0
        if env in ['PROD', 'PREPROD']:
            s3_storage_gb = storage_gb * 2
            s3_cost = s3_storage_gb * self.pricing['storage']['s3']['standard_ia']
        
        total_storage = ebs_cost + snapshot_cost + s3_cost
        
        return {
            'ebs_primary': {
                'cost': ebs_cost,
                'details': f"{storage_gb} GB {primary_storage_type}",
                'breakdown': {
                    'volume_cost': storage_gb * (self.pricing['storage']['ebs']['io2'] if 'io2' in primary_storage_type else self.pricing['storage']['ebs']['gp3']),
                    'iops_cost': ebs_cost - (storage_gb * (self.pricing['storage']['ebs']['io2'] if 'io2' in primary_storage_type else self.pricing['storage']['ebs']['gp3']))
                }
            },
            'ebs_snapshots': {
                'cost': snapshot_cost,
                'details': f"~{snapshot_retention_gb:.0f} GB snapshot storage"
            },
            's3_backup': {
                'cost': s3_cost,
                'details': f"~{s3_storage_gb if s3_cost > 0 else 0} GB S3 IA storage" if s3_cost > 0 else "No S3 backup"
            },
            'total': total_storage,
            'optimization_notes': self._get_storage_optimization_notes(env, storage_recs)
        }
    
    def _calculate_database_costs(self, env: str, db_recs: Dict, requirements: Dict) -> Dict[str, Any]:
        """Calculate database-related costs."""
        
        # RDS instance costs
        instance_class = db_recs.get('instance_class', 'db.r6g.large')
        engine = db_recs.get('engine', 'RDS MySQL')
        
        # Determine pricing based on engine
        if 'Aurora' in engine:
            db_instance_cost = self.pricing['database']['aurora_mysql'].get(instance_class, self.pricing['database']['aurora_mysql']['db.r6g.large'])
        else:
            db_instance_cost = self.pricing['database']['rds_mysql'].get(instance_class, self.pricing['database']['rds_mysql']['db.r6g.large'])
        
        # Multi-AZ costs (double the instance cost)
        if db_recs.get('multi_az'):
            db_instance_cost *= 2
        
        # Storage costs
        db_storage_gb = max(requirements.get('storage_GB', 100), 20)
        
        if 'Aurora' in engine:
            storage_cost = db_storage_gb * self.pricing['database']['storage']['aurora_storage']
            io_cost = 1000000 * self.pricing['database']['storage']['aurora_io']
            storage_cost += io_cost
        else:
            storage_cost = db_storage_gb * self.pricing['database']['storage']['rds_gp2']
        
        # Backup storage costs
        backup_retention = self._extract_backup_days(db_recs.get('backup_retention', '7 days'))
        backup_storage_gb = db_storage_gb * (backup_retention / 30) * 0.2
        backup_cost = backup_storage_gb * self.pricing['database']['backup_storage']
        
        # Read replica costs
        read_replica_cost = 0
        read_replicas = self._extract_read_replica_count(db_recs.get('read_replicas', 'No read replicas'))
        if read_replicas > 0:
            read_replica_cost = db_instance_cost * read_replicas * 0.8
        
        # RDS Proxy costs (if used)
        proxy_cost = 0
        if 'RDS Proxy' in db_recs.get('connection_pooling', ''):
            vcpus = requirements.get('vCPUs', 2)
            proxy_cost = vcpus * self.pricing['database']['rds_proxy'] * 730
        
        total_database = db_instance_cost + storage_cost + backup_cost + read_replica_cost + proxy_cost
        
        return {
            'db_instance': {
                'cost': db_instance_cost,
                'details': f"{instance_class} ({engine}) {'Multi-AZ' if db_recs.get('multi_az') else 'Single-AZ'}"
            },
            'db_storage': {
                'cost': storage_cost,
                'details': f"{db_storage_gb} GB {'Aurora' if 'Aurora' in engine else 'RDS'} storage"
            },
            'backup_storage': {
                'cost': backup_cost,
                'details': f"~{backup_storage_gb:.0f} GB backup retention ({backup_retention} days)"
            },
            'read_replicas': {
                'cost': read_replica_cost,
                'details': f"{read_replicas} read replicas" if read_replicas > 0 else "No read replicas"
            },
            'rds_proxy': {
                'cost': proxy_cost,
                'details': f"RDS Proxy for {vcpus} vCPUs" if proxy_cost > 0 else "No RDS Proxy"
            },
            'total': total_database,
            'optimization_notes': self._get_database_optimization_notes(env, db_recs)
        }
    
    def _calculate_security_costs(self, env: str, security_recs: Dict, requirements: Dict) -> Dict[str, Any]:
        """Calculate security-related costs."""
        
        # Secrets Manager
        secrets_count = self._estimate_secrets_count(env)
        secrets_cost = secrets_count * self.pricing['security']['secrets_manager']
        
        # KMS keys
        kms_keys = self._estimate_kms_keys(env, security_recs)
        kms_cost = kms_keys * self.pricing['security']['kms']
        
        # Config
        config_items = self._estimate_config_items(env)
        config_cost = config_items * self.pricing['security']['config']
        
        # CloudTrail
        cloudtrail_cost = self.pricing['security']['cloudtrail']
        
        # GuardDuty (production environments)
        guardduty_cost = 0
        if env in ['PROD', 'PREPROD']:
            guardduty_cost = self.pricing['security']['guardduty']
        
        # Security Hub
        security_hub_cost = 0
        if env in ['PROD', 'PREPROD']:
            findings_per_month = 1000
            security_hub_cost = findings_per_month * self.pricing['security']['security_hub']
        
        # WAF (if web application)
        waf_cost = 0
        if env in ['PROD', 'PREPROD']:
            waf_cost = self.pricing['security']['waf']
        
        total_security = secrets_cost + kms_cost + config_cost + cloudtrail_cost + guardduty_cost + security_hub_cost + waf_cost
        
        return {
            'secrets_manager': {
                'cost': secrets_cost,
                'details': f"{secrets_count} secrets"
            },
            'kms': {
                'cost': kms_cost,
                'details': f"{kms_keys} customer managed keys"
            },
            'config': {
                'cost': config_cost,
                'details': f"~{config_items} configuration items"
            },
            'cloudtrail': {
                'cost': cloudtrail_cost,
                'details': "Management events trail"
            },
            'guardduty': {
                'cost': guardduty_cost,
                'details': "Threat detection" if guardduty_cost > 0 else "Not enabled"
            },
            'security_hub': {
                'cost': security_hub_cost,
                'details': f"~{1000 if security_hub_cost > 0 else 0} findings/month" if security_hub_cost > 0 else "Not enabled"
            },
            'waf': {
                'cost': waf_cost,
                'details': "Web Application Firewall" if waf_cost > 0 else "Not enabled"
            },
            'total': total_security,
            'optimization_notes': self._get_security_optimization_notes(env)
        }
    
    def _calculate_monitoring_costs(self, env: str, monitoring_recs: Dict, requirements: Dict) -> Dict[str, Any]:
        """Calculate monitoring-related costs."""
        
        # CloudWatch metrics
        custom_metrics = self._estimate_custom_metrics(env)
        metrics_cost = custom_metrics * self.pricing['monitoring']['cloudwatch']['metrics']
        
        # CloudWatch dashboards
        dashboards = self._estimate_dashboards(env)
        dashboard_cost = dashboards * self.pricing['monitoring']['cloudwatch']['dashboards']
        
        # CloudWatch alarms
        alarms = self._estimate_alarms(env)
        alarm_cost = alarms * self.pricing['monitoring']['cloudwatch']['alarms']
        
        # CloudWatch logs
        log_ingestion_gb = self._estimate_log_volume(env)
        log_cost = log_ingestion_gb * self.pricing['monitoring']['cloudwatch']['logs_ingestion']
        log_storage_cost = log_ingestion_gb * self.pricing['monitoring']['cloudwatch']['logs_storage']
        
        # X-Ray (if enabled)
        xray_cost = 0
        if monitoring_recs.get('apm') == 'X-Ray':
            trace_volume = 1
            xray_cost = trace_volume * self.pricing['monitoring']['xray']
        
        # Synthetics (if enabled)
        synthetics_cost = 0
        if monitoring_recs.get('synthetic_monitoring') == 'Required':
            canary_runs = 30 * 24 * 12
            synthetics_cost = canary_runs * self.pricing['monitoring']['synthetics']
        
        total_monitoring = metrics_cost + dashboard_cost + alarm_cost + log_cost + log_storage_cost + xray_cost + synthetics_cost
        
        return {
            'cloudwatch_metrics': {
                'cost': metrics_cost,
                'details': f"{custom_metrics} custom metrics"
            },
            'cloudwatch_dashboards': {
                'cost': dashboard_cost,
                'details': f"{dashboards} dashboards"
            },
            'cloudwatch_alarms': {
                'cost': alarm_cost,
                'details': f"{alarms} alarms"
            },
            'cloudwatch_logs': {
                'cost': log_cost + log_storage_cost,
                'details': f"~{log_ingestion_gb} GB/month ingestion + storage",
                'breakdown': {
                    'ingestion': log_cost,
                    'storage': log_storage_cost
                }
            },
            'xray': {
                'cost': xray_cost,
                'details': "Application tracing" if xray_cost > 0 else "Not enabled"
            },
            'synthetics': {
                'cost': synthetics_cost,
                'details': f"~{canary_runs if synthetics_cost > 0 else 0} canary runs/month" if synthetics_cost > 0 else "Not enabled"
            },
            'total': total_monitoring,
            'optimization_notes': self._get_monitoring_optimization_notes(env)
        }
    
    # Helper methods for cost calculations
    def _get_instance_count(self, env: str) -> int:
        """Get instance count based on environment."""
        counts = {'DEV': 1, 'QA': 1, 'UAT': 2, 'PREPROD': 2, 'PROD': 3}
        return counts.get(env, 2)
    
    def _estimate_cdn_usage(self, env: str) -> float:
        """Estimate CDN data transfer in GB."""
        usage = {'DEV': 0, 'QA': 0, 'UAT': 50, 'PREPROD': 100, 'PROD': 500}
        return usage.get(env, 100)
    
    def _estimate_data_transfer_costs(self, env: str) -> float:
        """Estimate data transfer costs."""
        transfer_gb = {'DEV': 10, 'QA': 20, 'UAT': 50, 'PREPROD': 100, 'PROD': 500}
        gb = transfer_gb.get(env, 50)
        return gb * self.pricing['network']['data_transfer']['out_to_internet_up_to_10tb']
    
    def _extract_iops_from_recommendation(self, iops_rec: str) -> int:
        """Extract IOPS number from recommendation string."""
        import re
        match = re.search(r'(\d+)', iops_rec)
        return int(match.group(1)) if match else 3000
    
    def _get_snapshot_frequency(self, backup_strategy: str) -> float:
        """Get snapshot frequency multiplier."""
        if 'Daily' in backup_strategy:
            return 30
        elif 'Twice daily' in backup_strategy:
            return 60
        elif 'Continuous' in backup_strategy:
            return 365
        return 30
    
    def _extract_backup_days(self, retention: str) -> int:
        """Extract backup retention days."""
        import re
        match = re.search(r'(\d+)', retention)
        return int(match.group(1)) if match else 7
    
    def _extract_read_replica_count(self, replica_config: str) -> int:
        """Extract read replica count."""
        if 'No read replicas' in replica_config:
            return 0
        elif '1 read replica' in replica_config:
            return 1
        elif '1-2 read replicas' in replica_config:
            return 2
        elif '2-3 read replicas' in replica_config:
            return 3
        elif '3+ read replicas' in replica_config:
            return 3
        return 0
    
    def _estimate_secrets_count(self, env: str) -> int:
        """Estimate number of secrets."""
        counts = {'DEV': 3, 'QA': 5, 'UAT': 8, 'PREPROD': 12, 'PROD': 15}
        return counts.get(env, 8)
    
    def _estimate_kms_keys(self, env: str, security_recs: Dict) -> int:
        """Estimate KMS keys needed."""
        base_keys = {'DEV': 1, 'QA': 2, 'UAT': 3, 'PREPROD': 4, 'PROD': 5}
        return base_keys.get(env, 3)
    
    def _estimate_config_items(self, env: str) -> int:
        """Estimate AWS Config items."""
        counts = {'DEV': 10, 'QA': 20, 'UAT': 50, 'PREPROD': 100, 'PROD': 200}
        return counts.get(env, 50)
    
    def _estimate_custom_metrics(self, env: str) -> int:
        """Estimate custom CloudWatch metrics."""
        counts = {'DEV': 5, 'QA': 10, 'UAT': 25, 'PREPROD': 50, 'PROD': 100}
        return counts.get(env, 25)
    
    def _estimate_dashboards(self, env: str) -> int:
        """Estimate CloudWatch dashboards."""
        counts = {'DEV': 1, 'QA': 1, 'UAT': 2, 'PREPROD': 3, 'PROD': 5}
        return counts.get(env, 2)
    
    def _estimate_alarms(self, env: str) -> int:
        """Estimate CloudWatch alarms."""
        counts = {'DEV': 5, 'QA': 10, 'UAT': 20, 'PREPROD': 40, 'PROD': 80}
        return counts.get(env, 20)
    
    def _estimate_log_volume(self, env: str) -> float:
        """Estimate log volume in GB per month."""
        volumes = {'DEV': 1, 'QA': 2, 'UAT': 5, 'PREPROD': 15, 'PROD': 50}
        return volumes.get(env, 10)
    
    # Optimization notes methods
    def _get_compute_optimization_notes(self, env: str, instance_type: str, pricing_model: str) -> List[str]:
        """Get compute optimization recommendations."""
        notes = []
        if pricing_model == 'on_demand' and env in ['PROD', 'PREPROD']:
            notes.append("💡 Consider Reserved Instances for 20-40% cost savings")
        if 'large' in instance_type and env == 'DEV':
            notes.append("💡 Consider smaller instances for development environment")
        notes.append("💡 Monitor CPU utilization to right-size instances")
        return notes
    
    def _get_network_optimization_notes(self, env: str) -> List[str]:
        """Get network optimization recommendations."""
        notes = [
            "💡 Use CloudFront to reduce data transfer costs",
            "💡 Implement VPC endpoints to avoid NAT Gateway costs for AWS services"
        ]
        if env in ['DEV', 'QA']:
            notes.append("💡 Single NAT Gateway sufficient for non-production")
        return notes
    
    def _get_storage_optimization_notes(self, env: str, storage_recs: Dict) -> List[str]:
        """Get storage optimization recommendations."""
        notes = [
            "💡 Use gp3 volumes for better price-performance ratio",
            "💡 Implement lifecycle policies for S3 backup storage"
        ]
        if env in ['PROD', 'PREPROD']:
            notes.append("💡 Consider EBS snapshots cross-region replication")
        return notes
    
    def _get_database_optimization_notes(self, env: str, db_recs: Dict) -> List[str]:
        """Get database optimization recommendations."""
        notes = [
            "💡 Use Aurora for better price-performance at scale",
            "💡 Monitor database utilization for right-sizing"
        ]
        if env not in ['PROD']:
            notes.append("💡 Single-AZ deployment sufficient for non-production")
        return notes
    
    def _get_security_optimization_notes(self, env: str) -> List[str]:
        """Get security optimization recommendations."""
        notes = [
            "💡 Use AWS managed keys where possible to reduce costs",
            "💡 Implement proper log retention policies"
        ]
        if env in ['DEV', 'QA']:
            notes.append("💡 Reduce security tooling for development environments")
        return notes
    
    def _get_monitoring_optimization_notes(self, env: str) -> List[str]:
        """Get monitoring optimization recommendations."""
        notes = [
            "💡 Use metric filters to reduce custom metric costs",
            "💡 Implement log retention policies to control storage costs"
        ]
        if env in ['DEV', 'QA']:
            notes.append("💡 Reduce monitoring frequency for development environments")
        return notes
        
class EnhancedEnvironmentAnalyzer:
    """Enhanced environment analyzer with detailed complexity explanations."""
    
    def __init__(self):
        self.environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
        self.cost_calculator = AWSCostCalculator()
        
    # ... (rest of the EnhancedEnvironmentAnalyzer methods) ...

    def get_detailed_complexity_explanation(self, env: str, env_results: Dict) -> Dict[str, Any]:
        """Get detailed explanation of environment complexity."""
        
        claude_analysis = env_results.get('claude_analysis', {})
        complexity_score = claude_analysis.get('complexity_score', 50)
        requirements = env_results.get('requirements', {})
        
        # Calculate specific complexity factors
        factors = {
            'Resource Intensity': self._calculate_resource_intensity(requirements),
            'Migration Risk': self._calculate_migration_risk(env, claude_analysis),
            'Operational Complexity': self._calculate_operational_complexity(env),
            'Compliance Requirements': self._calculate_compliance_complexity(env),
            'Integration Dependencies': self._calculate_integration_complexity(env)
        }
        
        return {
            'overall_score': complexity_score,
            'complexity_level': claude_analysis.get('complexity_level', 'MEDIUM'),
            'factors': factors,
            'detailed_reasons': self._generate_detailed_reasons(env, factors, complexity_score),
            'specific_challenges': self._identify_specific_challenges(env, factors),
            'mitigation_strategies': self._generate_mitigation_strategies(env, factors)
        }
    
    def _calculate_resource_intensity(self, requirements: Dict) -> Dict[str, Any]:
        """Calculate resource intensity factor."""
        vcpus = requirements.get('vCPUs', 2)
        ram_gb = requirements.get('RAM_GB', 8)
        storage_gb = requirements.get('storage_GB', 100)
        
        cpu_intensity = min(vcpus / 2, 10) * 10
        memory_intensity = min(ram_gb / 8, 10) * 10
        storage_intensity = min(storage_gb / 100, 10) * 10
        
        overall_score = (cpu_intensity + memory_intensity + storage_intensity) / 3
        
        return {
            'score': overall_score,
            'cpu_intensity': cpu_intensity,
            'memory_intensity': memory_intensity,
            'storage_intensity': storage_intensity,
            'description': self._get_resource_description(overall_score)
        }
    
    def _calculate_migration_risk(self, env: str, claude_analysis: Dict) -> Dict[str, Any]:
        """Calculate migration risk factor."""
        base_risks = {'DEV': 20, 'QA': 30, 'UAT': 50, 'PREPROD': 70, 'PROD': 90}
        base_score = base_risks.get(env, 50)
        
        complexity_multiplier = claude_analysis.get('complexity_score', 50) / 50
        final_score = min(base_score * complexity_multiplier, 100)
        
        return {
            'score': final_score,
            'base_risk': base_score,
            'risk_level': self._get_risk_level(final_score),
            'description': self._get_migration_risk_description(env, final_score)
        }
    
    def _calculate_operational_complexity(self, env: str) -> Dict[str, Any]:
        """Calculate operational complexity."""
        complexity_factors = {
            'DEV': {
                'score': 25,
                'factors': ['Minimal SLA requirements', 'Simple monitoring', 'Basic security'],
                'description': 'Low operational complexity - development environment'
            },
            'QA': {
                'score': 35,
                'factors': ['Automated testing integration', 'Test data management'],
                'description': 'Low-medium complexity - automated testing requirements'
            },
            'UAT': {
                'score': 55,
                'factors': ['User access management', 'Performance validation'],
                'description': 'Medium complexity - user acceptance validation'
            },
            'PREPROD': {
                'score': 75,
                'factors': ['Production-like configuration', 'Advanced monitoring'],
                'description': 'High complexity - production simulation requirements'
            },
            'PROD': {
                'score': 90,
                'factors': ['24/7 availability', 'Advanced monitoring & alerting', 'Disaster recovery'],
                'description': 'Very high complexity - business-critical operations'
            }
        }
        return complexity_factors.get(env, {'score': 50, 'factors': [], 'description': 'Medium complexity'})
    
    def _calculate_compliance_complexity(self, env: str) -> Dict[str, Any]:
        """Calculate compliance complexity."""
        compliance_scores = {'DEV': 10, 'QA': 20, 'UAT': 40, 'PREPROD': 70, 'PROD': 95}
        score = compliance_scores.get(env, 50)
        
        return {
            'score': score,
            'level': self._get_compliance_level(score),
            'requirements': self._get_compliance_requirements(env),
            'description': f'{env} environment compliance requirements'
        }
    
    def _calculate_integration_complexity(self, env: str) -> Dict[str, Any]:
        """Calculate integration complexity."""
        integration_scores = {'DEV': 30, 'QA': 45, 'UAT': 60, 'PREPROD': 80, 'PROD': 95}
        score = integration_scores.get(env, 50)
        
        return {
            'score': score,
            'complexity_level': self._get_integration_level(score),
            'integration_points': self._get_integration_points(env),
            'description': f'{env} environment integration requirements'
        }
    
    def _generate_detailed_reasons(self, env: str, factors: Dict, overall_score: float) -> List[str]:
        """Generate detailed reasons for complexity score."""
        reasons = []
        
        resource_factor = factors['Resource Intensity']
        if resource_factor['score'] > 70:
            reasons.append(f"High resource requirements: {resource_factor['description']}")
        elif resource_factor['score'] > 40:
            reasons.append(f"Moderate resource requirements: {resource_factor['description']}")
        else:
            reasons.append(f"Light resource requirements: {resource_factor['description']}")
        
        migration_factor = factors['Migration Risk']
        if migration_factor['score'] > 70:
            reasons.append(f"High migration risk due to {env} environment criticality")
        
        ops_factor = factors['Operational Complexity']
        if ops_factor['score'] > 60:
            reasons.append(f"Complex operational requirements: {', '.join(ops_factor['factors'][:2])}")
        
        compliance_factor = factors['Compliance Requirements']
        if compliance_factor['score'] > 50:
            reasons.append(f"Significant compliance requirements for {env} environment")
        
        return reasons
    
    def _identify_specific_challenges(self, env: str, factors: Dict) -> List[str]:
        """Identify specific challenges for the environment."""
        env_challenges = {
            'DEV': [
                'Frequent code deployments and updates',
                'Developer access and permissions management',
                'Integration with development tools and CI/CD'
            ],
            'QA': [
                'Automated testing integration',
                'Test data management and refresh',
                'Performance and load testing capabilities'
            ],
            'UAT': [
                'User acceptance testing coordination',
                'Business stakeholder access management',
                'Production-like data simulation'
            ],
            'PREPROD': [
                'Production parity maintenance',
                'Disaster recovery testing',
                'Performance validation under load'
            ],
            'PROD': [
                'Zero-downtime deployment requirements',
                'Business continuity and disaster recovery',
                'Advanced monitoring and alerting',
                'Compliance and audit requirements'
            ]
        }
        return env_challenges.get(env, ['Standard migration challenges'])
    
    def _generate_mitigation_strategies(self, env: str, factors: Dict) -> List[str]:
        """Generate mitigation strategies."""
        env_strategies = {
            'DEV': [
                'Implement Infrastructure as Code for consistent deployments',
                'Use containerization for development environment isolation',
                'Establish automated backup and restore procedures'
            ],
            'QA': [
                'Implement automated testing pipelines',
                'Use data masking for sensitive test data',
                'Establish performance baselines and monitoring'
            ],
            'UAT': [
                'Create detailed user acceptance testing plans',
                'Implement role-based access controls',
                'Establish change management procedures'
            ],
            'PREPROD': [
                'Maintain production parity through automation',
                'Implement comprehensive disaster recovery testing',
                'Use blue-green deployment strategies'
            ],
            'PROD': [
                'Implement zero-downtime deployment strategies',
                'Establish comprehensive monitoring and alerting',
                'Create detailed disaster recovery plans',
                'Implement advanced security and compliance controls'
            ]
        }
        return env_strategies.get(env, ['Follow standard migration best practices'])
    
    def get_technical_recommendations(self, env: str, env_results: Dict) -> Dict[str, Any]:
        """Get comprehensive technical recommendations."""
        
        requirements = env_results.get('requirements', {})
        cost_breakdown = env_results.get('cost_breakdown', {})
        selected_instance = cost_breakdown.get('selected_instance', {})
        
        return {
            'compute': self._get_compute_recommendations(env, selected_instance, requirements),
            'network': self._get_network_recommendations(env, requirements),
            'storage': self._get_storage_recommendations(env, requirements),
            'database': self._get_database_recommendations(env, requirements),
            'security': self._get_security_recommendations(env),
            'monitoring': self._get_monitoring_recommendations(env),
            'backup': self._get_backup_recommendations(env),
            'scaling': self._get_scaling_recommendations(env, requirements)
        }
    
    def _get_compute_recommendations(self, env: str, selected_instance: Dict, requirements: Dict) -> Dict[str, Any]:
        """Get compute recommendations."""
        instance_type = selected_instance.get('type', 'N/A')
        vcpus = selected_instance.get('vCPU', requirements.get('vCPUs', 2))
        ram_gb = selected_instance.get('RAM', requirements.get('RAM_GB', 8))
        
        return {
            'primary_instance': {
                'type': instance_type,
                'vcpus': vcpus,
                'memory_gb': ram_gb,
                'rationale': f'Selected {instance_type} for {env} environment based on performance requirements'
            },
            'alternative_instances': [
                {'type': 'm6a.large', 'rationale': 'AMD-based cost optimization'},
                {'type': 'c6i.xlarge', 'rationale': 'Compute-optimized alternative'}
            ],
            'placement_strategy': self._get_placement_strategy(env),
            'auto_scaling': self._get_auto_scaling_config(env),
            'pricing_optimization': self._get_pricing_optimization(env)
        }
    
    def _get_network_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get network recommendations."""
        network_configs = {
            'DEV': {
                'vpc_design': 'Single AZ, basic VPC',
                'subnets': 'Public and private subnets',
                'security_groups': 'Development-focused security groups',
                'load_balancer': 'Application Load Balancer (if needed)',
                'cdn': 'Optional',
                'dns': 'Route 53 basic',
                'nat_gateway': 'Optional',
                'vpn': 'Site-to-site VPN for secure access'
            },
            'QA': {
                'vpc_design': 'Single AZ with testing isolation',
                'subnets': 'Isolated testing subnets',
                'security_groups': 'Testing-specific security groups',
                'load_balancer': 'ALB for load testing',
                'cdn': 'Optional',
                'dns': 'Route 53 basic',
                'nat_gateway': 'Optional',
                'vpn': 'Site-to-site VPN for secure access'
            },
            'UAT': {
                'vpc_design': 'Multi-AZ for availability testing',
                'subnets': 'Production-like subnet design',
                'security_groups': 'Production-like security',
                'load_balancer': 'ALB with SSL termination',
                'cdn': 'Optional',
                'dns': 'Route 53 basic',
                'nat_gateway': 'Optional',
                'vpn': 'Site-to-site VPN for secure access'
            },
            'PREPROD': {
                'vpc_design': 'Full multi-AZ production design',
                'subnets': 'Production mirror subnet design',
                'security_groups': 'Production security groups',
                'load_balancer': 'ALB/NLB with full features',
                'cdn': 'CloudFront',
                'dns': 'Route 53 with health checks',
                'nat_gateway': 'Required',
                'vpn': 'Site-to-site VPN for secure access'
            },
            'PROD': {
                'vpc_design': 'Multi-AZ with disaster recovery',
                'subnets': 'Highly available subnet design',
                'security_groups': 'Strict production security',
                'load_balancer': 'ALB/NLB with advanced features',
                'cdn': 'CloudFront',
                'dns': 'Route 53 with health checks',
                'nat_gateway': 'Required',
                'vpn': 'Site-to-site VPN for secure access'
            }
        }
        return network_configs.get(env, network_configs['UAT'])
    
    def _get_storage_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get storage recommendations."""
        storage_gb = requirements.get('storage_GB', 100)
        
        storage_configs = {
            'DEV': {
                'primary_storage': 'gp3 (General Purpose SSD)',
                'backup_strategy': 'Daily snapshots, 7-day retention',
                'encryption': 'EBS encryption enabled',
                'performance': 'Standard performance'
            },
            'QA': {
                'primary_storage': 'gp3 (General Purpose SSD)',
                'backup_strategy': 'Daily snapshots, 14-day retention',
                'encryption': 'EBS encryption enabled',
                'performance': 'Enhanced performance for testing'
            },
            'UAT': {
                'primary_storage': 'gp3 with provisioned IOPS',
                'backup_strategy': 'Twice daily snapshots, 30-day retention',
                'encryption': 'EBS encryption with customer keys',
                'performance': 'Production-like performance'
            },
            'PREPROD': {
                'primary_storage': 'io2 (Provisioned IOPS SSD)',
                'backup_strategy': 'Continuous backup, 90-day retention',
                'encryption': 'EBS encryption with customer keys',
                'performance': 'High performance, production parity'
            },
            'PROD': {
                'primary_storage': 'io2 (Provisioned IOPS SSD)',
                'backup_strategy': 'Continuous backup, cross-region replication',
                'encryption': 'EBS encryption with customer managed keys',
                'performance': 'Maximum performance optimization'
            }
        }
        
        config = storage_configs.get(env, storage_configs['UAT'])
        config.update({
            'recommended_size': f"{storage_gb * self._get_storage_multiplier(env)} GB",
            'iops_recommendation': self._get_iops_recommendation(env, storage_gb),
            'throughput_recommendation': self._get_throughput_recommendation(env),
            'lifecycle_policy': self._get_lifecycle_policy(env)
        })
        return config
    
    def _get_database_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get database recommendations."""
        db_configs = {
            'DEV': {
                'engine': 'RDS MySQL/PostgreSQL',
                'instance_class': 'db.t4g.micro or db.t4g.small',
                'multi_az': False,
                'backup_retention': '7 days',
                'encryption': 'Enabled',
                'monitoring': 'Basic CloudWatch'
            },
            'QA': {
                'engine': 'RDS MySQL/PostgreSQL',
                'instance_class': 'db.t4g.small or db.t4g.medium',
                'multi_az': False,
                'backup_retention': '14 days',
                'encryption': 'Enabled',
                'monitoring': 'Enhanced monitoring'
            },
            'UAT': {
                'engine': 'RDS MySQL/PostgreSQL',
                'instance_class': 'db.r6g.large',
                'multi_az': True,
                'backup_retention': '30 days',
                'encryption': 'Enabled with customer keys',
                'monitoring': 'Performance Insights'
            },
            'PREPROD': {
                'engine': 'RDS MySQL/PostgreSQL/Aurora',
                'instance_class': 'db.r6g.xlarge',
                'multi_az': True,
                'backup_retention': '35 days',
                'encryption': 'Enabled with customer managed keys',
                'monitoring': 'Performance Insights + Enhanced monitoring'
            },
            'PROD': {
                'engine': 'Aurora MySQL/PostgreSQL',
                'instance_class': 'db.r6g.xlarge or higher',
                'multi_az': True,
                'backup_retention': '35 days with cross-region backup',
                'encryption': 'Enabled with customer managed keys',
                'monitoring': 'Full Performance Insights + Enhanced monitoring'
            }
        }
        
        config = db_configs.get(env, db_configs['UAT'])
        config.update({
            'read_replicas': self._get_read_replica_config(env),
            'connection_pooling': 'RDS Proxy' if env in ['PREPROD', 'PROD'] else 'Application-level',
            'maintenance_window': self._get_maintenance_window(env)
        })
        return config
    
    def _get_security_recommendations(self, env: str) -> Dict[str, Any]:
        """Get security recommendations."""
        security_configs = {
            'DEV': {
                'iam_roles': 'Developer access with resource restrictions',
                'encryption': 'Standard EBS and S3 encryption',
                'network_security': 'Basic security groups and NACLs',
                'compliance': 'Basic security standards',
                'monitoring': 'CloudTrail for audit logging',
                'secrets_management': 'AWS Secrets Manager',
                'certificate_management': 'ACM with auto-renewal'
            },
            'PROD': {
                'iam_roles': 'Least privilege production access',
                'encryption': 'Customer-managed keys with rotation',
                'network_security': 'Maximum security controls',
                'compliance': 'Full regulatory compliance',
                'monitoring': 'Complete security and compliance monitoring',
                'secrets_management': 'AWS Secrets Manager',
                'certificate_management': 'ACM with auto-renewal'
            }
        }
        return security_configs.get(env, security_configs['DEV'])
    
    def _get_monitoring_recommendations(self, env: str) -> Dict[str, Any]:
        """Get monitoring recommendations."""
        monitoring_configs = {
            'DEV': {
                'cloudwatch': 'Basic metrics and logs',
                'alerting': 'Development team notifications',
                'dashboards': 'Basic development dashboard',
                'log_retention': '30 days',
                'apm': 'Optional',
                'synthetic_monitoring': 'Not required',
                'cost_monitoring': 'Cost Explorer + Budgets',
                'health_checks': 'Basic'
            },
            'PROD': {
                'cloudwatch': 'Premium monitoring with custom metrics',
                'alerting': '24/7 operations with escalation',
                'dashboards': 'Executive and operations dashboards',
                'log_retention': 'Long-term retention (3+ years)',
                'apm': 'X-Ray',
                'synthetic_monitoring': 'Required',
                'cost_monitoring': 'Cost Explorer + Budgets',
                'health_checks': 'Route 53 health checks'
            }
        }
        return monitoring_configs.get(env, monitoring_configs['DEV'])
    
    def _get_backup_recommendations(self, env: str) -> Dict[str, Any]:
        """Get backup recommendations."""
        backup_configs = {
            'DEV': {'frequency': 'Daily', 'retention': '7 days', 'cross_region': False, 'testing': 'Monthly'},
            'QA': {'frequency': 'Daily', 'retention': '14 days', 'cross_region': False, 'testing': 'Bi-weekly'},
            'UAT': {'frequency': 'Twice daily', 'retention': '30 days', 'cross_region': False, 'testing': 'Weekly'},
            'PREPROD': {'frequency': 'Every 6 hours', 'retention': '90 days', 'cross_region': True, 'testing': 'Weekly'},
            'PROD': {'frequency': 'Continuous (point-in-time recovery)', 'retention': '7 years (compliance)', 'cross_region': True, 'testing': 'Daily'}
        }
        return backup_configs.get(env, backup_configs['UAT'])
    
    def _get_scaling_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get scaling recommendations."""
        scaling_configs = {
            'DEV': {'auto_scaling': 'Basic scaling for cost optimization', 'min_instances': 1, 'max_instances': 2, 'target_utilization': '70%'},
            'QA': {'auto_scaling': 'Load testing optimized scaling', 'min_instances': 1, 'max_instances': 4, 'target_utilization': '60%'},
            'UAT': {'auto_scaling': 'User load optimized scaling', 'min_instances': 2, 'max_instances': 6, 'target_utilization': '65%'},
            'PREPROD': {'auto_scaling': 'Production-like scaling', 'min_instances': 2, 'max_instances': 10, 'target_utilization': '70%'},
            'PROD': {'auto_scaling': 'High availability scaling', 'min_instances': 3, 'max_instances': 20, 'target_utilization': '75%'}
        }
        return scaling_configs.get(env, scaling_configs['UAT'])
    
    # Helper methods
    def _get_resource_description(self, score: float) -> str:
        if score > 70:
            return "High resource intensity requiring powerful instances"
        elif score > 40:
            return "Moderate resource requirements"
        else:
            return "Light resource requirements suitable for smaller instances"
    
    def _get_risk_level(self, score: float) -> str:
        if score > 80: return "Very High"
        elif score > 60: return "High"
        elif score > 40: return "Medium"
        elif score > 20: return "Low"
        else: return "Very Low"
    
    def _get_migration_risk_description(self, env: str, score: float) -> str:
        risk_descriptions = {
            'DEV': "Development environment - can be rebuilt if needed",
            'QA': "Testing environment - important for development process",
            'UAT': "User acceptance environment - critical for business validation",
            'PREPROD': "Pre-production environment - high business impact",
            'PROD': "Production environment - maximum business criticality"
        }
        return risk_descriptions.get(env, "Standard environment risk")
    
    def _get_compliance_level(self, score: float) -> str:
        if score > 80: return "Full Compliance"
        elif score > 60: return "High Compliance"
        elif score > 40: return "Medium Compliance"
        else: return "Basic Compliance"
    
    def _get_compliance_requirements(self, env: str) -> List[str]:
        requirements = {
            'DEV': ['Basic security standards', 'Data protection'],
            'QA': ['Testing data compliance', 'Security standards'],
            'UAT': ['User data protection', 'Business compliance'],
            'PREPROD': ['Production-like compliance', 'Security validation'],
            'PROD': ['Full regulatory compliance', 'Audit requirements', 'Data sovereignty']
        }
        return requirements.get(env, ['Standard compliance'])
    
    def _get_integration_level(self, score: float) -> str:
        if score > 80: return "Complex"
        elif score > 60: return "Moderate"
        else: return "Simple"
    
    def _get_integration_points(self, env: str) -> List[str]:
        integrations = {
            'DEV': ['CI/CD systems', 'Development tools', 'Version control'],
            'QA': ['Testing frameworks', 'Test data systems', 'Reporting tools'],
            'UAT': ['Business applications', 'User directories', 'Approval systems'],
            'PREPROD': ['Production integrations', 'Monitoring systems', 'External APIs'],
            'PROD': ['All business systems', 'External partners', 'Real-time integrations']
        }
        return integrations.get(env, ['Standard integrations'])
    
    def _get_placement_strategy(self, env: str) -> str:
        strategies = {
            'DEV': 'Single AZ placement for cost optimization',
            'QA': 'Single AZ with availability considerations',
            'UAT': 'Multi-AZ for availability testing',
            'PREPROD': 'Multi-AZ production-like placement',
            'PROD': 'Multi-AZ with placement groups for performance'
        }
        return strategies.get(env, 'Standard placement')
    
    def _get_auto_scaling_config(self, env: str) -> str:
        configs = {
            'DEV': 'Cost-optimized scaling',
            'QA': 'Load testing optimized',
            'UAT': 'User load optimized',
            'PREPROD': 'Production-like scaling',
            'PROD': 'High availability scaling'
        }
        return configs.get(env, 'Standard scaling')
    
    def _get_pricing_optimization(self, env: str) -> str:
        optimizations = {
            'DEV': 'Spot instances recommended for cost savings',
            'QA': 'Mix of on-demand and spot instances',
            'UAT': 'On-demand with some reserved instances',
            'PREPROD': 'Reserved instances for predictable costs',
            'PROD': 'Reserved instances with savings plans'
        }
        return optimizations.get(env, 'Standard pricing')
    
    def _get_storage_multiplier(self, env: str) -> float:
        multipliers = {'DEV': 1.0, 'QA': 1.2, 'UAT': 1.3, 'PREPROD': 1.4, 'PROD': 1.5}
        return multipliers.get(env, 1.2)
    
    def _get_iops_recommendation(self, env: str, storage_gb: int) -> str:
        if env in ['PREPROD', 'PROD']:
            return f"{max(storage_gb * 3, 1000)} IOPS (Provisioned)"
        else:
            return f"{storage_gb * 3} IOPS (Baseline gp3)"
    
    def _get_throughput_recommendation(self, env: str) -> str:
        throughput = {
            'DEV': '125 MB/s (gp3 baseline)',
            'QA': '250 MB/s (enhanced)',
            'UAT': '500 MB/s (production-like)',
            'PREPROD': '1000 MB/s (high performance)',
            'PROD': '1000+ MB/s (maximum performance)'
        }
        return throughput.get(env, '250 MB/s')
    
    def _get_lifecycle_policy(self, env: str) -> str:
        policies = {
            'DEV': 'Move to IA after 30 days, archive after 90 days',
            'QA': 'Move to IA after 60 days, archive after 180 days',
            'UAT': 'Move to IA after 90 days, archive after 365 days',
            'PREPROD': 'Move to IA after 180 days, archive after 2 years',
            'PROD': 'Move to IA after 365 days, archive after 3 years'
        }
        return policies.get(env, 'Standard lifecycle policy')
    
    def _get_read_replica_config(self, env: str) -> str:
        configs = {
            'DEV': 'No read replicas needed',
            'QA': '1 read replica for testing',
            'UAT': '1-2 read replicas for user load',
            'PREPROD': '2-3 read replicas for production testing',
            'PROD': '3+ read replicas across AZs'
        }
        return configs.get(env, '1 read replica')
    
    def _get_maintenance_window(self, env: str) -> str:
        windows = {
            'DEV': 'Any time (flexible)',
            'QA': 'Off-hours testing window',
            'UAT': 'Business off-hours',
            'PREPROD': 'Coordinated with production',
            'PROD': 'Strict maintenance windows'
        }
        return windows.get(env, 'Standard maintenance window')
    
class EnhancedEnterpriseEC2Calculator:
    """Enhanced calculator with comprehensive instance types and environment support."""
    
    def __init__(self):
        try:
            self.claude_analyzer = ClaudeAIMigrationAnalyzer()
            
            # Comprehensive instance types
            self.INSTANCE_TYPES = [
                {
                    "type": "m6i.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750,
                    "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True
                },
                # ... other instance types ...
                {
                    "type": "m6i.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500,
                    "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True
                },
                {
                    "type": "m6i.2xlarge", "vCPU": 8, "RAM": 32, "max_ebs_bandwidth": 19000,
                    "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True
                },
                {
                    "type": "m6i.4xlarge", "vCPU": 16, "RAM": 64, "max_ebs_bandwidth": 38000,
                    "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True
                },
                {
                    "type": "r6i.large", "vCPU": 2, "RAM": 16, "max_ebs_bandwidth": 4750,
                    "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True
                },
                {
                    "type": "r6i.xlarge", "vCPU": 4, "RAM": 32, "max_ebs_bandwidth": 9500,
                    "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True
                }
            ]
                   
            
            # Environment multipliers
            self.ENV_MULTIPLIERS = {
                "PROD": {"cpu_ram": 1.0, "storage": 1.0, "description": "Production environment"},
                "PREPROD": {"cpu_ram": 0.9, "storage": 0.9, "description": "Pre-production environment"},
                "UAT": {"cpu_ram": 0.7, "storage": 0.7, "description": "User acceptance testing"},
                "QA": {"cpu_ram": 0.6, "storage": 0.6, "description": "Quality assurance"},
                "DEV": {"cpu_ram": 0.4, "storage": 0.4, "description": "Development environment"}
            }
            
            # Default inputs
            self.inputs = {
                "workload_name": "Sample Enterprise Workload",
                "workload_type": "web_application",
                "operating_system": "linux",
                "region": "us-east-1",
                "on_prem_cores": 8,
                "peak_cpu_percent": 70,
                "on_prem_ram_gb": 32,
                "peak_ram_percent": 80,
                "storage_current_gb": 500,
                "storage_growth_rate": 0.15,
                "peak_iops": 5000,
                "peak_throughput_mbps": 250,
                "infrastructure_age_years": 3,
                "business_criticality": "medium"
            }
            
            logger.info("Enhanced calculator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing calculator: {e}")
            raise

    # ... (rest of the EnhancedEnterpriseEC2Calculator methods) ...
    def calculate_enhanced_requirements(self, env: str) -> Dict[str, Any]:
        """Calculate requirements with Claude AI analysis."""
        
        try:
            # Standard requirements calculation
            requirements = self._calculate_standard_requirements(env)
            
            # Claude AI migration analysis
            claude_analysis = self.claude_analyzer.analyze_workload_complexity(self.inputs, env)
            
            # Enhanced results
            enhanced_results = {
                **requirements,
                'claude_analysis': claude_analysis,
                'environment': env
            }
            
            return enhanced_results
        except Exception as e:
            logger.error(f"Error in enhanced requirements calculation: {e}")
            return self._get_fallback_requirements(env)

    def _calculate_standard_requirements(self, env: str) -> Dict[str, Any]:
        """Calculate standard infrastructure requirements."""
        try:
            env_mult = self.ENV_MULTIPLIERS[env]
            
            required_vcpus = max(math.ceil(self.inputs["on_prem_cores"] * 1.2 * env_mult["cpu_ram"]), 2)
            required_ram = max(math.ceil(self.inputs["on_prem_ram_gb"] * 1.3 * env_mult["cpu_ram"]), 4)
            required_storage = math.ceil(self.inputs["storage_current_gb"] * 1.2 * env_mult["storage"])
            
            return {
                "requirements": {
                    "vCPUs": required_vcpus,
                    "RAM_GB": required_ram,
                    "storage_GB": required_storage,
                    "multi_az": env in ["PROD", "PREPROD"]
                },
                "cost_breakdown": self._calculate_basic_costs(required_vcpus, required_ram, required_storage, env),
                "tco_analysis": self._calculate_tco(required_vcpus, required_ram, env)
            }
        except Exception as e:
            logger.error(f"Error calculating standard requirements: {e}")
            return self._get_fallback_requirements(env)

    def _calculate_basic_costs(self, vcpus: int, ram_gb: int, storage_gb: int, env: str) -> Dict[str, Any]:
        """Calculate basic costs with realistic EC2 pricing."""
        try:
            selected_instance = self._select_best_instance(vcpus, ram_gb)
            instance_type = selected_instance['type']
            
            pricing = self._get_fallback_pricing(instance_type)
            
            monthly_instance_cost = {
                'on_demand': pricing['on_demand'] * 730,
                'ri_1y_no_upfront': pricing['ri_1y_no_upfront'] * 730,
                'ri_3y_no_upfront': pricing['ri_3y_no_upfront'] * 730,
                'spot': pricing['spot'] * 730
            }
            
            storage_cost_per_gb = 0.08
            monthly_storage_cost = storage_gb * storage_cost_per_gb
            monthly_network_cost = 50
            
            total_costs = {}
            for pricing_model, instance_cost in monthly_instance_cost.items():
                total_costs[pricing_model] = instance_cost + monthly_storage_cost + monthly_network_cost
            
            return {
                "total_costs": total_costs,
                "instance_costs": monthly_instance_cost,
                "storage_costs": {"primary_storage": monthly_storage_cost},
                "network_costs": {"data_transfer": monthly_network_cost},
                "selected_instance": selected_instance
            }
        except Exception as e:
            logger.error(f"Error calculating basic costs: {e}")
            return {
                "total_costs": {"on_demand": 1000, "ri_1y_no_upfront": 700},
                "selected_instance": {'type': 'm6i.large', 'vCPU': 2, 'RAM': 8}
            }

    def _select_best_instance(self, required_vcpus: int, required_ram_gb: int) -> Dict[str, Any]:
        """Select the best matching instance type."""
        try:
            best_instance = None
            best_score = 0
            
            for instance in self.INSTANCE_TYPES:
                if instance['vCPU'] >= required_vcpus and instance['RAM'] >= required_ram_gb:
                    cpu_efficiency = required_vcpus / instance['vCPU']
                    ram_efficiency = required_ram_gb / instance['RAM']
                    overall_efficiency = (cpu_efficiency + ram_efficiency) / 2
                    
                    if overall_efficiency > best_score:
                        best_score = overall_efficiency
                        best_instance = instance.copy()
                        best_instance['efficiency_score'] = overall_efficiency
            
            if best_instance is None:
                best_instance = {
                    'type': 'm6i.large',
                    'vCPU': 2,
                    'RAM': 8,
                    'family': 'general',
                    'efficiency_score': 0.5
                }
            
            return best_instance
        except Exception as e:
            logger.error(f"Error selecting best instance: {e}")
            return {'type': 'm6i.large', 'vCPU': 2, 'RAM': 8, 'family': 'general'}

    def _calculate_tco(self, vcpus: int, ram_gb: int, env: str) -> Dict[str, Any]:
        """Calculate TCO analysis."""
        try:
            selected_instance = self._select_best_instance(vcpus, ram_gb)
            pricing = self._get_fallback_pricing(selected_instance['type'])
            
            on_demand_monthly = pricing['on_demand'] * 730
            ri_1y_monthly = pricing['ri_1y_no_upfront'] * 730
            ri_3y_monthly = pricing['ri_3y_no_upfront'] * 730
            
            storage_monthly = max(self.inputs.get('storage_current_gb', 500), 100) * 0.08
            network_monthly = 50
            
            total_on_demand = on_demand_monthly + storage_monthly + network_monthly
            total_ri_1y = ri_1y_monthly + storage_monthly + network_monthly
            total_ri_3y = ri_3y_monthly + storage_monthly + network_monthly
            
            costs = {
                'on_demand': total_on_demand,
                'ri_1y_no_upfront': total_ri_1y,
                'ri_3y_no_upfront': total_ri_3y
            }
            
            best_option = min(costs.keys(), key=lambda k: costs[k])
            best_cost = costs[best_option]
            savings = total_on_demand - best_cost
            
            return {
                "monthly_cost": best_cost,
                "monthly_savings": savings,
                "best_pricing_option": best_option,
                "roi_3_years": (savings * 36 / total_on_demand) * 100 if total_on_demand > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating TCO: {e}")
            return {"monthly_cost": 1000, "monthly_savings": 200, "best_pricing_option": "ri_1y_no_upfront"}

    def _get_fallback_pricing(self, instance_type: str) -> Dict[str, float]:
        """Fallback pricing data."""
        fallback_prices = {
            'm6i.large': {'on_demand': 0.0864, 'ri_1y_no_upfront': 0.0605, 'ri_3y_no_upfront': 0.0432, 'spot': 0.0259},
            'm6i.xlarge': {'on_demand': 0.1728, 'ri_1y_no_upfront': 0.1210, 'ri_3y_no_upfront': 0.0864, 'spot': 0.0518},
            'm6i.2xlarge': {'on_demand': 0.3456, 'ri_1y_no_upfront': 0.2419, 'ri_3y_no_upfront': 0.1728, 'spot': 0.1037},
            'm6i.4xlarge': {'on_demand': 0.6912, 'ri_1y_no_upfront': 0.4838, 'ri_3y_no_upfront': 0.3456, 'spot': 0.2074},
            'r6i.large': {'on_demand': 0.1008, 'ri_1y_no_upfront': 0.0706, 'ri_3y_no_upfront': 0.0504, 'spot': 0.0302},
            'r6i.xlarge': {'on_demand': 0.2016, 'ri_1y_no_upfront': 0.1411, 'ri_3y_no_upfront': 0.1008, 'spot': 0.0605}
        }
        return fallback_prices.get(instance_type, {'on_demand': 0.1, 'ri_1y_no_upfront': 0.07, 'ri_3y_no_upfront': 0.05, 'spot': 0.03})

    def _get_fallback_requirements(self, env: str) -> Dict[str, Any]:
        """Fallback requirements."""
        return {
            'requirements': {'vCPUs': 2, 'RAM_GB': 8, 'storage_GB': 100},
            'cost_breakdown': {'total_costs': {'on_demand': 500}},
            'tco_analysis': {'monthly_cost': 500, 'monthly_savings': 150},
            'claude_analysis': self.claude_analyzer._get_fallback_analysis(),
            'environment': env
        }
    
    
class EnvironmentHeatMapGenerator:
    """Generate environment heat maps for workload analysis."""
    
    def __init__(self):
        self.environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
        self.metrics = ['Cost', 'Complexity', 'Risk', 'Timeline', 'Resources']

    # ... (rest of the EnvironmentHeatMapGenerator methods) ...
    def generate_heat_map_data(self, workload_results: Dict) -> pd.DataFrame:
        """Generate heat map data for environments."""
        try:
            heat_data = []
            
            for env in self.environments:
                env_results = workload_results.get(env, {})
                
                cost_score = self._calculate_cost_score(env_results)
                complexity_score = self._calculate_complexity_score(env_results)
                risk_score = self._calculate_risk_score(env_results)
                timeline_score = self._calculate_timeline_score(env_results)
                resource_score = self._calculate_resource_score(env_results)
                
                heat_data.append({
                    'Environment': env,
                    'Cost': cost_score,
                    'Complexity': complexity_score,
                    'Risk': risk_score,
                    'Timeline': timeline_score,
                    'Resources': resource_score
                })
            
            return pd.DataFrame(heat_data)
        except Exception as e:
            logger.error(f"Error generating heat map data: {e}")
            return pd.DataFrame()

    def _calculate_cost_score(self, env_results: Dict) -> float:
        """Calculate cost score for heat map."""
        try:
            if not env_results:
                return 50
            
            cost_breakdown = env_results.get('cost_breakdown', {})
            total_costs = cost_breakdown.get('total_costs', {})
            monthly_cost = total_costs.get('on_demand', 1000)
            
            if monthly_cost < 500: return 20
            elif monthly_cost < 1500: return 50
            elif monthly_cost < 3000: return 75
            else: return 95
        except Exception:
            return 50

    def _calculate_complexity_score(self, env_results: Dict) -> float:
        """Calculate complexity score for heat map."""
        try:
            claude_analysis = env_results.get('claude_analysis', {})
            return claude_analysis.get('complexity_score', 50)
        except Exception:
            return 50

    def _calculate_risk_score(self, env_results: Dict) -> float:
        """Calculate risk score for heat map."""
        try:
            claude_analysis = env_results.get('claude_analysis', {})
            complexity_score = claude_analysis.get('complexity_score', 50)
            return min(complexity_score * 1.2, 100)
        except Exception:
            return 50

    def _calculate_timeline_score(self, env_results: Dict) -> float:
        """Calculate timeline score for heat map."""
        try:
            claude_analysis = env_results.get('claude_analysis', {})
            timeline = claude_analysis.get('estimated_timeline', {})
            max_weeks = timeline.get('max_weeks', 8)
            
            if max_weeks < 4: return 20
            elif max_weeks < 8: return 40
            elif max_weeks < 16: return 70
            else: return 90
        except Exception:
            return 50

    def _calculate_resource_score(self, env_results: Dict) -> float:
        """Calculate resource score for heat map."""
        try:
            requirements = env_results.get('requirements', {})
            vcpus = requirements.get('vCPUs', 2)
            ram_gb = requirements.get('RAM_GB', 8)
            
            resource_intensity = (vcpus * 10) + (ram_gb * 2)
            
            if resource_intensity < 50: return 25
            elif resource_intensity < 150: return 50
            elif resource_intensity < 300: return 75
            else: return 95
        except Exception:
            return 50

    def create_heat_map_visualization(self, heat_data: pd.DataFrame) -> go.Figure:
        """Create Plotly heat map visualization."""
        try:
            if heat_data.empty:
                fig = go.Figure()
                fig.add_annotation(text="No data available for heat map", 
                                 xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
                return fig
            
            environments = heat_data['Environment'].tolist()
            metrics = ['Cost', 'Complexity', 'Risk', 'Timeline', 'Resources']
            
            z_data = []
            for metric in metrics:
                if metric in heat_data.columns:
                    z_data.append(heat_data[metric].tolist())
                else:
                    z_data.append([50] * len(environments))
            
            fig = go.Figure(data=go.Heatmap(
                z=z_data,
                x=environments,
                y=metrics,
                colorscale='RdYlGn_r',
                zmin=0,
                zmax=100,
                colorbar=dict(
                    title="Impact Level",
                    tickvals=[0, 25, 50, 75, 100],
                    ticktext=["Very Low", "Low", "Medium", "High", "Very High"]
                ),
                text=[[f"{val:.0f}" for val in row] for row in z_data],
                texttemplate="%{text}",
                textfont={"size": 12},
                hoverongaps=False
            ))
            
            fig.update_layout(
                title="Environment Impact Heat Map",
                xaxis_title="Environment",
                yaxis_title="Impact Metrics",
                width=800,
                height=400
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating heat map visualization: {e}")
            fig = go.Figure()
            fig.add_annotation(text=f"Error creating heat map: {str(e)}", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig    
    
class BulkWorkloadAnalyzer:
    """Handle bulk workload analysis from uploaded files."""
    
    def __init__(self):
        self.claude_analyzer = ClaudeAIMigrationAnalyzer()
        self.calculator = EnhancedEnterpriseEC2Calculator()
        
    # ... (rest of the BulkWorkloadAnalyzer methods) ...
    def process_bulk_upload(self, uploaded_file, file_type: str) -> Dict[str, Any]:
        """Process bulk upload file and return analysis results."""
        try:
            if file_type == 'csv':
                return self._process_csv_file(uploaded_file)
            elif file_type == 'excel':
                return self._process_excel_file(uploaded_file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error processing bulk upload: {e}")
            return {'error': str(e), 'workloads': []}
    
    def _process_csv_file(self, uploaded_file) -> Dict[str, Any]:
        """Process CSV file."""
        try:
            # Read CSV content
            content = uploaded_file.read().decode('utf-8')
            csv_data = list(csv.DictReader(StringIO(content)))
            
            return self._analyze_workloads(csv_data)
            
        except Exception as e:
            return {'error': f"CSV processing error: {str(e)}", 'workloads': []}
    
    def _process_excel_file(self, uploaded_file) -> Dict[str, Any]:
        """Process Excel file."""
        try:
            if not OPENPYXL_AVAILABLE:
                return {'error': 'openpyxl not available for Excel processing', 'workloads': []}
                
            # Read Excel content
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            workloads_data = df.to_dict('records')
            
            return self._analyze_workloads(workloads_data)
            
        except Exception as e:
            return {'error': f"Excel processing error: {str(e)}", 'workloads': []}
    
    def _analyze_workloads(self, workloads_data: List[Dict]) -> Dict[str, Any]:
        """Analyze multiple workloads."""
        results = {
            'total_workloads': len(workloads_data),
            'successful_analyses': 0,
            'failed_analyses': 0,
            'workloads': [],
            'summary': {}
        }
        
        for i, workload_data in enumerate(workloads_data):
            try:
                # Validate and normalize workload data
                normalized_workload = self._normalize_workload_data(workload_data)
                
                # Analyze for all environments
                workload_results = {}
                for env in ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']:
                    env_analysis = self._analyze_single_workload(normalized_workload, env)
                    workload_results[env] = env_analysis
                
                results['workloads'].append({
                    'index': i + 1,
                    'workload_name': normalized_workload.get('workload_name', f'Workload {i+1}'),
                    'status': 'success',
                    'analysis': workload_results
                })
                
                results['successful_analyses'] += 1
                
            except Exception as e:
                results['workloads'].append({
                    'index': i + 1,
                    'workload_name': workload_data.get('workload_name', f'Workload {i+1}'),
                    'status': 'failed',
                    'error': str(e)
                })
                results['failed_analyses'] += 1
        
        # Generate summary
        results['summary'] = self._generate_bulk_summary(results['workloads'])
        
        return results
    
    def _normalize_workload_data(self, workload_data: Dict) -> Dict:
        """Normalize and validate workload data."""
        # Define field mappings (CSV column -> internal field)
        field_mappings = {
            'workload_name': 'workload_name',
            'name': 'workload_name',
            'application_name': 'workload_name',
            'workload_type': 'workload_type',
            'type': 'workload_type',
            'application_type': 'workload_type',
            'operating_system': 'operating_system',
            'os': 'operating_system',
            'cpu_cores': 'on_prem_cores',
            'cores': 'on_prem_cores',
            'on_prem_cores': 'on_prem_cores',
            'peak_cpu_percent': 'peak_cpu_percent',
            'peak_cpu': 'peak_cpu_percent',
            'cpu_utilization': 'peak_cpu_percent',
            'ram_gb': 'on_prem_ram_gb',
            'memory_gb': 'on_prem_ram_gb',
            'on_prem_ram_gb': 'on_prem_ram_gb',
            'peak_ram_percent': 'peak_ram_percent',
            'peak_ram': 'peak_ram_percent',
            'memory_utilization': 'peak_ram_percent',
            'storage_gb': 'storage_current_gb',
            'storage_current_gb': 'storage_current_gb',
            'disk_gb': 'storage_current_gb',
            'peak_iops': 'peak_iops',
            'iops': 'peak_iops',
            'peak_throughput_mbps': 'peak_throughput_mbps',
            'throughput_mbps': 'peak_throughput_mbps',
            'infrastructure_age_years': 'infrastructure_age_years',
            'age_years': 'infrastructure_age_years',
            'business_criticality': 'business_criticality',
            'criticality': 'business_criticality',
            'region': 'region'
        }
        
        normalized = {}
        
        # Normalize field names (case-insensitive)
        for csv_field, value in workload_data.items():
            csv_field_lower = csv_field.lower().strip()
            
            if csv_field_lower in field_mappings:
                internal_field = field_mappings[csv_field_lower]
                normalized[internal_field] = value
        
        # Set defaults for missing fields
        defaults = {
            'workload_name': 'Unknown Workload',
            'workload_type': 'web_application',
            'operating_system': 'linux',
            'region': 'us-east-1',
            'on_prem_cores': 2,
            'peak_cpu_percent': 70,
            'on_prem_ram_gb': 8,
            'peak_ram_percent': 80,
            'storage_current_gb': 100,
            'peak_iops': 3000,
            'peak_throughput_mbps': 100,
            'infrastructure_age_years': 3,
            'business_criticality': 'medium'
        }
        
        for field, default_value in defaults.items():
            if field not in normalized or normalized[field] is None or normalized[field] == '':
                normalized[field] = default_value
            else:
                # Convert numeric fields
                if field in ['on_prem_cores', 'peak_cpu_percent', 'on_prem_ram_gb', 
                           'peak_ram_percent', 'storage_current_gb', 'peak_iops', 
                           'peak_throughput_mbps', 'infrastructure_age_years']:
                    try:
                        normalized[field] = float(normalized[field])
                    except (ValueError, TypeError):
                        normalized[field] = default_value
        
        return normalized
    
    def _analyze_single_workload(self, workload_inputs: Dict, environment: str) -> Dict[str, Any]:
        """Analyze a single workload for a specific environment."""
        
        # Update calculator inputs
        self.calculator.inputs.update(workload_inputs)
        
        # Calculate enhanced requirements
        return self.calculator.calculate_enhanced_requirements(environment)
    
    def _generate_bulk_summary(self, workloads: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics from bulk analysis."""
        successful_workloads = [w for w in workloads if w['status'] == 'success']
        
        if not successful_workloads:
            return {'error': 'No successful analyses to summarize'}
        
        # Aggregate statistics
        total_monthly_costs = []
        complexity_scores = []
        instance_types = {}
        
        for workload in successful_workloads:
            try:
                prod_analysis = workload['analysis']['PROD']
                
                # Cost data
                tco = prod_analysis.get('tco_analysis', {})
                monthly_cost = tco.get('monthly_cost', 0)
                if monthly_cost > 0:
                    total_monthly_costs.append(monthly_cost)
                
                # Complexity data
                claude_analysis = prod_analysis.get('claude_analysis', {})
                complexity = claude_analysis.get('complexity_score', 0)
                if complexity > 0:
                    complexity_scores.append(complexity)
                
                # Instance types
                cost_breakdown = prod_analysis.get('cost_breakdown', {})
                selected_instance = cost_breakdown.get('selected_instance', {})
                instance_type = selected_instance.get('type', 'Unknown')
                instance_types[instance_type] = instance_types.get(instance_type, 0) + 1
                
            except Exception as e:
                logger.warning(f"Error processing workload summary: {e}")
                continue
        
        # Calculate summary statistics
        summary = {
            'total_workloads_analyzed': len(successful_workloads),
            'total_monthly_cost': sum(total_monthly_costs),
            'total_annual_cost': sum(total_monthly_costs) * 12,
            'average_monthly_cost': sum(total_monthly_costs) / len(total_monthly_costs) if total_monthly_costs else 0,
            'average_complexity_score': sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0,
            'most_common_instance_type': max(instance_types.items(), key=lambda x: x[1])[0] if instance_types else 'N/A',
            'instance_type_distribution': instance_types,
            'cost_range': {
                'min': min(total_monthly_costs) if total_monthly_costs else 0,
                'max': max(total_monthly_costs) if total_monthly_costs else 0
            },
            'complexity_range': {
                'min': min(complexity_scores) if complexity_scores else 0,
                'max': max(complexity_scores) if complexity_scores else 0
            }
        }
        
        return summary
# Enhanced Streamlit Functions
def initialize_enhanced_session_state():
    """Initialize enhanced session state."""
    try:
        if 'enhanced_calculator' not in st.session_state:
            st.session_state.enhanced_calculator = EnhancedEnterpriseEC2Calculator()
        if 'enhanced_results' not in st.session_state:
            st.session_state.enhanced_results = None
        if 'bulk_results' not in st.session_state:
            st.session_state.bulk_results = None
            
        logger.info("Session state initialized successfully")
        
    except Exception as e:
        st.error(f"Error initializing session state: {str(e)}")
        logger.error(f"Error initializing session state: {e}")
        st.session_state.enhanced_calculator = None
        st.session_state.enhanced_results = None

def render_enhanced_configuration():
    """Render enhanced configuration."""
    
    st.markdown("### ⚙️ Enhanced Enterprise Workload Single Workload")
    
    # Check if calculator exists
    if 'enhanced_calculator' not in st.session_state or st.session_state.enhanced_calculator is None:
        st.error("⚠️ Calculator not initialized. Please refresh the page.")
        return
        
    calculator = st.session_state.enhanced_calculator
    
    # Basic workload information
    with st.expander("📋 Workload Information", expanded=True):
        # ... (workload configuration inputs) ...
        col1, col2 = st.columns(2)
        
        with col1:
            calculator.inputs["workload_name"] = st.text_input(
                "Workload Name",
                value=calculator.inputs["workload_name"],
                help="Descriptive name for this workload"
            )
            
            workload_types = {
                'web_application': 'Web Application (Frontend, CDN)',
                'application_server': 'Application Server (APIs, Middleware)',
                'database_server': 'Database Server (RDBMS, NoSQL)',
                'file_server': 'File Server (Storage, Backup)',
                'compute_intensive': 'Compute Intensive (HPC, Analytics)',
                'analytics_workload': 'Analytics Workload (BI, Data Processing)'
            }
            
            calculator.inputs["workload_type"] = st.selectbox(
                "Workload Type",
                list(workload_types.keys()),
                format_func=lambda x: workload_types[x],
                help="Select the primary workload pattern"
            )
        
        with col2:
            calculator.inputs["region"] = st.selectbox(
                "Primary AWS Region",
                ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
                help="Primary AWS region for deployment"
            )
            
            calculator.inputs["operating_system"] = st.selectbox(
                "Operating System",
                ["linux", "windows"],
                format_func=lambda x: "Linux (Amazon Linux, Ubuntu, RHEL)" if x == "linux" else "Windows Server"
            )
    # Infrastructure metrics
    with st.expander("🖥️ Current Infrastructure Metrics", expanded=True):
        # ... (infrastructure inputs) ...
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Compute Resources**")
            calculator.inputs["on_prem_cores"] = st.number_input(
                "CPU Cores", min_value=1, max_value=128, value=calculator.inputs["on_prem_cores"]
            )
            calculator.inputs["peak_cpu_percent"] = st.slider(
                "Peak CPU %", 0, 100, calculator.inputs["peak_cpu_percent"]
            )
        
        with col2:
            st.markdown("**Memory Resources**")
            calculator.inputs["on_prem_ram_gb"] = st.number_input(
                "RAM (GB)", min_value=1, max_value=1024, value=calculator.inputs["on_prem_ram_gb"]
            )
            calculator.inputs["peak_ram_percent"] = st.slider(
                "Peak RAM %", 0, 100, calculator.inputs["peak_ram_percent"]
            )
        
        with col3:
            st.markdown("**Storage & I/O**")
            calculator.inputs["storage_current_gb"] = st.number_input(
                "Storage (GB)", min_value=1, value=calculator.inputs["storage_current_gb"]
            )
            calculator.inputs["peak_iops"] = st.number_input(
                "Peak IOPS", min_value=1, value=calculator.inputs["peak_iops"]
            )
    
    # Analysis buttons
    st.markdown("---")
    if st.button("🚀 Run Enhanced Analysis", type="primary", key="main_enhanced_analysis_button"):
        run_enhanced_analysis()
        
    # Report generation section
    if st.session_state.enhanced_results:
        st.markdown("---")
        st.markdown("### 📋 Report Generation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Generate PDF Report", key="config_pdf_report"):
                generate_enhanced_pdf_report()
        with col2:
            if st.button("📊 Export to Excel", key="config_excel_report"):
                generate_enhanced_excel_report()

def run_enhanced_analysis():
    """Run enhanced analysis."""
    
    with st.spinner("🔄 Running enhanced analysis with Claude AI..."):
        try:
            calculator = st.session_state.enhanced_calculator
            
            if calculator is None:
                st.error("Calculator not available. Please refresh the page.")
                return
            
            # Calculate for all environments
            results = {}
            for env in calculator.ENV_MULTIPLIERS.keys():
                results[env] = calculator.calculate_enhanced_requirements(env)
            
            # Generate heat map data
            heat_map_generator = EnvironmentHeatMapGenerator()
            heat_map_data = heat_map_generator.generate_heat_map_data(results)
            heat_map_fig = heat_map_generator.create_heat_map_visualization(heat_map_data)
            
            # Store results
            st.session_state.enhanced_results = {
                'inputs': calculator.inputs.copy(),
                'recommendations': results,
                'heat_map_data': heat_map_data,
                'heat_map_fig': heat_map_fig
            }
            
            st.success("✅ Enhanced analysis completed successfully!")
            
        except Exception as e:
            st.error(f"❌ Error during enhanced analysis: {str(e)}")
            logger.error(f"Error in enhanced analysis: {e}")

def render_enhanced_results():
    """Render enhanced analysis results."""
    
    if 'enhanced_results' not in st.session_state or st.session_state.enhanced_results is None:
        st.info("💡 Run an enhanced analysis to see results here.")
        return
    
    try:
        results = st.session_state.enhanced_results
        st.markdown("### 📊 Enhanced Analysis Results")
        
        recommendations = results.get('recommendations', {})
        if not recommendations or 'PROD' not in recommendations:
            st.warning("⚠️ Analysis results incomplete. Please run the analysis again.")
            return
        
        prod_results = recommendations['PROD']
        claude_analysis = prod_results.get('claude_analysis', {})
        tco_analysis = prod_results.get('tco_analysis', {})
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            complexity_score = claude_analysis.get('complexity_score', 50)
            complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">🤖 Migration Complexity</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{complexity_score:.0f}/100</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">{complexity_level}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            monthly_cost = tco_analysis.get('monthly_cost', 0)
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">☁️ AWS Monthly Cost</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">${monthly_cost:,.0f}</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">Optimized Pricing</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            timeline = claude_analysis.get('estimated_timeline', {})
            max_weeks = timeline.get('max_weeks', 8)
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">⏱️ Migration Timeline</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{max_weeks}</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">Weeks (Estimated)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">🖥️ Instance Type</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">
                    {prod_results.get('cost_breakdown', {}).get('selected_instance', {}).get('type', 'N/A')}
                </div>
                <div style="font-size: 0.75rem; color: #9ca3af;">Recommended</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Claude AI Analysis
        st.markdown("### 🤖 Claude AI Migration Analysis")
        
        if claude_analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Migration Strategy**")
                strategy = claude_analysis.get('migration_strategy', {})
                if strategy:
                    st.markdown(f"**Approach:** {strategy.get('approach', 'N/A')}")
                    st.markdown(f"**Methodology:** {strategy.get('methodology', 'N/A')}")
                    st.markdown(f"**Timeline:** {strategy.get('timeline', 'N/A')}")
                    st.markdown(f"**Risk Level:** {strategy.get('risk_level', 'N/A')}")
            
            with col2:
                st.markdown("**Migration Steps**")
                migration_steps = claude_analysis.get('migration_steps', [])
                
                for i, step in enumerate(migration_steps[:3], 1):
                    if isinstance(step, dict):
                        with st.expander(f"Phase {i}: {step.get('phase', 'N/A')}", expanded=False):
                            st.markdown(f"**Duration:** {step.get('duration', 'N/A')}")
                            
                            tasks = step.get('tasks', [])
                            if tasks:
                                st.markdown("**Key Tasks:**")
                                for task in tasks[:3]:
                                    st.markdown(f"• {task}")
        
        # Cost Analysis
        st.markdown("### 💰 Cost Analysis")
        
        cost_breakdown = prod_results.get('cost_breakdown', {})
        total_costs = cost_breakdown.get('total_costs', {})
        
        if total_costs:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Instance Pricing Comparison**")
                cost_data = []
                for pricing_model, cost in total_costs.items():
                    cost_data.append({
                        'Pricing Model': pricing_model.replace('_', ' ').title(),
                        'Monthly Cost': f"${cost:,.2f}",
                        'Annual Cost': f"${cost*12:,.2f}"
                    })
                
                df_costs = pd.DataFrame(cost_data)
                st.dataframe(df_costs, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**AWS Service Cost Breakdown (PROD)**")
                
                # Calculate detailed service costs if available
                try:
                    # Actual implementation added here
                    analyzer = EnhancedEnvironmentAnalyzer()
                    tech_recs = analyzer.get_technical_recommendations('PROD', prod_results)
                    cost_calculator = AWSCostCalculator()
                    service_costs = cost_calculator.calculate_service_costs(
                        'PROD', tech_recs, prod_results.get('requirements', {}))
                    
                    service_cost_data = []
                    categories = ['compute', 'network', 'storage', 'database', 'security', 'monitoring']
                    for cat in categories:
                        if cat in service_costs:
                            service_cost_data.append({
                                'Service Category': cat.title(),
                                'Monthly Cost': f"${service_costs[cat]['total']:.2f}"
                            })
                    
                    if service_cost_data:
                        df_service_costs = pd.DataFrame(service_cost_data)
                        st.dataframe(df_service_costs, use_container_width=True, hide_index=True)
                        
                        # Show total from service breakdown
                        total_services = sum(service_costs[cat]['total'] for cat in categories if cat in service_costs)
                        st.markdown(f"**Total Monthly AWS Services Cost: ${total_services:.2f}**")
                    else:
                        # Fallback to basic cost display
                        basic_cost_data = [
                            {'Cost Component': 'Instance Costs', 'Monthly Cost': f"${cost_breakdown.get('instance_costs', {}).get('on_demand', 0):.2f}"},
                            {'Cost Component': 'Storage Costs', 'Monthly Cost': f"${cost_breakdown.get('storage_costs', {}).get('primary_storage', 0):.2f}"},
                            {'Cost Component': 'Network Costs', 'Monthly Cost': f"${cost_breakdown.get('network_costs', {}).get('data_transfer', 0):.2f}"}
                        ]
                        
                        df_basic_costs = pd.DataFrame(basic_cost_data)
                        st.dataframe(df_basic_costs, use_container_width=True, hide_index=True)
                
                except Exception as e:
                    logger.error(f"Error calculating detailed service costs: {e}")
                    # Fallback to basic cost display
                    basic_cost_data = [
                        {'Cost Component': 'Instance Costs', 'Monthly Cost': f"${cost_breakdown.get('instance_costs', {}).get('on_demand', 0):.2f}"},
                        {'Cost Component': 'Storage Costs', 'Monthly Cost': f"${cost_breakdown.get('storage_costs', {}).get('primary_storage', 0):.2f}"},
                        {'Cost Component': 'Network Costs', 'Monthly Cost': f"${cost_breakdown.get('network_costs', {}).get('data_transfer', 0):.2f}"}
                    ]
                    
                    df_basic_costs = pd.DataFrame(basic_cost_data)
                    st.dataframe(df_basic_costs, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Error displaying results: {str(e)}")
        logger.error(f"Error in render_enhanced_results: {e}")

def render_enhanced_environment_heatmap_tab():
    """Render enhanced environment heat map tab with detailed explanations."""
    
    # ... (heat map rendering) ...
    """Render enhanced environment heat map tab with detailed explanations."""
    
    st.markdown("### 🌡️ Environment Impact Analysis with Detailed Explanations")
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.info("💡 Run an enhanced analysis to see detailed environment heat maps and explanations.")
        return
    
    results = st.session_state.enhanced_results
    analyzer = EnhancedEnvironmentAnalyzer()
    
    # Environment overview cards
    st.markdown("#### Environment Complexity Overview")
    
    cols = st.columns(5)
    environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
    
    for i, env in enumerate(environments):
        with cols[i]:
            env_results = results['recommendations'].get(env, {})
            claude_analysis = env_results.get('claude_analysis', {})
            complexity = claude_analysis.get('complexity_score', 50)
            complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
            
            # Get detailed explanation
            complexity_explanation = analyzer.get_detailed_complexity_explanation(env, env_results)
            
            # Create expandable card
            with st.expander(f"{env} - {complexity:.0f}/100 ({complexity_level})", expanded=False):
                
                st.markdown(f"**Overall Complexity Score:** {complexity:.0f}/100")
                st.markdown(f"**Complexity Level:** {complexity_level}")
                
                st.markdown("**Key Complexity Factors:**")
                factors = complexity_explanation['factors']
                
                # Display factor scores
                factor_data = []
                for factor_name, factor_details in factors.items():
                    if isinstance(factor_details, dict):
                        score = factor_details.get('score', 0)
                        factor_data.append({'Factor': factor_name, 'Score': f"{score:.0f}/100"})
                
                if factor_data:
                    df_factors = pd.DataFrame(factor_data)
                    st.dataframe(df_factors, use_container_width=True, hide_index=True)
                
                st.markdown("**Why This Environment is Complex:**")
                for reason in complexity_explanation['detailed_reasons']:
                    st.markdown(f"• {reason}")
                
                st.markdown("**Specific Challenges:**")
                for challenge in complexity_explanation['specific_challenges'][:3]:
                    st.markdown(f"• {challenge}")
                
                st.markdown("**Mitigation Strategies:**")
                for strategy in complexity_explanation['mitigation_strategies'][:3]:
                    st.markdown(f"• {strategy}")
    
    # Heat map visualization
    st.markdown("#### Impact Heat Map Visualization")
    
    if 'heat_map_fig' in results:
        st.plotly_chart(results['heat_map_fig'], use_container_width=True)
    
    # Detailed complexity breakdown table
    st.markdown("#### Detailed Complexity Breakdown by Environment")
    
    detailed_data = []
    
    for env in environments:
        env_results = results['recommendations'].get(env, {})
        complexity_explanation = analyzer.get_detailed_complexity_explanation(env, env_results)
        
        factors = complexity_explanation['factors']
        
        detailed_data.append({
            'Environment': env,
            'Overall Score': f"{complexity_explanation['overall_score']:.0f}/100",
            'Complexity Level': complexity_explanation['complexity_level'],
            'Resource Intensity': f"{factors['Resource Intensity']['score']:.0f}/100",
            'Migration Risk': f"{factors['Migration Risk']['score']:.0f}/100",
            'Operational Complexity': f"{factors['Operational Complexity']['score']:.0f}/100",
            'Primary Reason': complexity_explanation['detailed_reasons'][0] if complexity_explanation['detailed_reasons'] else 'N/A'
        })
    
    df_detailed = pd.DataFrame(detailed_data)
    st.dataframe(df_detailed, use_container_width=True, hide_index=True)

    
def render_technical_recommendations_tab():
    """Render comprehensive technical recommendations tab with cost details."""
    
    # ... (technical recommendations) ...
    st.markdown("### 🔧 Comprehensive Technical Recommendations by Environment")
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.info("💡 Run an enhanced analysis to see detailed technical recommendations.")
        return
    
    results = st.session_state.enhanced_results
    analyzer = EnhancedEnvironmentAnalyzer()
    cost_calculator = AWSCostCalculator()
    
    # Environment selector
    selected_env = st.selectbox(
        "Select Environment for Detailed Technical Recommendations:",
        ['PROD', 'PREPROD', 'UAT', 'QA', 'DEV'],
        help="Choose an environment to see comprehensive technical specifications and costs"
    )
    
    env_results = results['recommendations'].get(selected_env, {})
    
    if not env_results:
        st.warning(f"No analysis results available for {selected_env} environment.")
        return
    
    # Get technical recommendations and costs
    tech_recs = analyzer.get_technical_recommendations(selected_env, env_results)
    requirements = env_results.get('requirements', {})
    service_costs = cost_calculator.calculate_service_costs(selected_env, tech_recs, requirements)
    
    st.markdown(f"## {selected_env} Environment - Technical Specifications & Costs")
    
    # Cost summary at the top
    st.markdown("### 💰 Cost Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_monthly = service_costs['summary']['total_monthly']
        st.metric("Total Monthly Cost", f"${total_monthly:,.2f}")
    
    with col2:
        total_annual = service_costs['summary']['total_annual']
        st.metric("Total Annual Cost", f"${total_annual:,.2f}")
    
    with col3:
        largest_category = service_costs['summary']['largest_cost_category']
        largest_cost = service_costs[largest_category]['total']
        st.metric("Largest Cost Driver", f"{largest_category.title()}: ${largest_cost:.2f}")
    
    with col4:
        # Calculate cost per vCPU
        vcpus = requirements.get('vCPUs', 2)
        cost_per_vcpu = total_monthly / vcpus if vcpus > 0 else 0
        st.metric("Cost per vCPU/month", f"${cost_per_vcpu:.2f}")
    
    # Cost breakdown chart
    st.markdown("#### Cost Breakdown by Service Category")
    
    categories = ['compute', 'network', 'storage', 'database', 'security', 'monitoring']
    costs = [service_costs[cat]['total'] for cat in categories]
    
    # Filter out zero costs to avoid clutter
    filtered_data = [(cat.title(), cost) for cat, cost in zip(categories, costs) if cost > 0]
    
    if filtered_data:
        labels, values = zip(*filtered_data)
        
        # Create a more visually appealing pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,  # Donut chart
            textinfo='label+percent+value',
            textposition='auto',
            textfont=dict(size=14),
            marker=dict(
                colors=['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4'],
                line=dict(color='#FFFFFF', width=2)
            ),
            hovertemplate='<b>%{label}</b><br>' +
                         'Cost: $%{value:.2f}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>',
            pull=[0.05 if max(values) == val else 0 for val in values]  # Pull out the largest slice
        )])
        
        fig_pie.update_layout(
            title=dict(
                text="Monthly Cost Distribution",
                x=0.5,
                font=dict(size=18, color='#1f2937')
            ),
            height=500,
            width=700,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05,
                font=dict(size=12)
            ),
            margin=dict(l=20, r=120, t=60, b=20),
            annotations=[
                dict(
                    text=f"Total<br>${sum(values):.2f}/month",
                    x=0.5, y=0.5,
                    font_size=16,
                    font_color='#1f2937',
                    showarrow=False
                )
            ]
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("No cost data available for visualization.")
    
    # Create tabs for different technical areas with costs
    tabs = st.tabs(["Single Workload", "Bulk Upload"])
    
    # Compute tab with costs
    with tech_tabs[0]:
        sw_subtabs = st.tabs(["Single Workload", "Heat Map", "Technical Recommendation"])
        st.markdown("#### 💻 Compute Single Workload & Costs")
        
        compute_recs = tech_recs['compute']
        compute_costs = service_costs['compute']
        
        # Cost overview
        st.markdown(f"**Monthly Compute Cost: ${compute_costs['total']:.2f}**")
        
        col1, col2 = st.columns(2)
        
    with col1:
            st.markdown("**Primary Instance Recommendation**")
            
            primary_instance = compute_recs['primary_instance']
            instance_data = [
                {'Specification': 'Instance Type', 'Value': primary_instance['type']},
                {'Specification': 'vCPUs', 'Value': str(primary_instance['vcpus'])},
                {'Specification': 'Memory (GB)', 'Value': str(primary_instance['memory_gb'])},
                {'Specification': 'Rationale', 'Value': primary_instance['rationale']}
            ]
            
            df_instance = pd.DataFrame(instance_data)
            st.dataframe(df_instance, use_container_width=True, hide_index=True)
        
    with col2:
            st.markdown("**Compute Cost Breakdown**")
            
            cost_breakdown_data = []
            for service, details in compute_costs.items():
                if service != 'total' and service != 'optimization_notes':
                    cost_breakdown_data.append({
                        'Service': service.replace('_', ' ').title(),
                        'Monthly Cost': f"${details['cost']:.2f}",
                        'Details': details['details']
                    })
            
            df_compute_costs = pd.DataFrame(cost_breakdown_data)
            st.dataframe(df_compute_costs, use_container_width=True, hide_index=True)
        
        # Deployment configuration
            st.markdown("**Deployment Single Workload**")        
            deployment_data = [
                {'Single Workload': 'Placement Strategy', 'Recommendation': compute_recs['placement_strategy']},
                {'Single Workload': 'Auto Scaling', 'Recommendation': compute_recs['auto_scaling']},
                {'Single Workload': 'Pricing Optimization', 'Recommendation': compute_recs['pricing_optimization']}
        ]
        
            df_deployment = pd.DataFrame(deployment_data)
            st.dataframe(df_deployment, use_container_width=True, hide_index=True)
        
        # Cost optimization notes
            st.markdown("**💡 Cost Optimization Recommendations**")
            for note in compute_costs.get('optimization_notes', []):
            st.markdown(note)
    
        # Network tab with costs
    with tech_tabs[1]:
        bu_subtabs = st.tabs(["Single Workload", "Heat Map", "Technical Recommendation"])
        st.markdown("#### 🌐 Network Single Workload & Costs")
        
        network_recs = tech_recs['network']
        network_costs = service_costs['network']
        
        # Cost overview
        st.markdown(f"**Monthly Network Cost: ${network_costs['total']:.2f}**")
        
        col1, col2 = st.columns(2)
        
    with col1:
            st.markdown("**Core Network Components**")
            
            core_network_data = [
                {'Component': 'VPC Design', 'Single Workload': network_recs['vpc_design']},
                {'Component': 'Subnets', 'Single Workload': network_recs['subnets']},
                {'Component': 'Security Groups', 'Single Workload': network_recs['security_groups']},
                {'Component': 'Load Balancer', 'Single Workload': network_recs['load_balancer']}
            ]
            
            df_core_network = pd.DataFrame(core_network_data)
            st.dataframe(df_core_network, use_container_width=True, hide_index=True)
        
    with col2:
            st.markdown("**Network Cost Breakdown**")
            
            network_cost_data = []
            for service, details in network_costs.items():
                if service != 'total' and service != 'optimization_notes':
                    network_cost_data.append({
                        'Service': service.replace('_', ' ').title(),
                        'Monthly Cost': f"${details['cost']:.2f}",
                        'Details': details['details']
                    })
            
            df_network_costs = pd.DataFrame(network_cost_data)
            st.dataframe(df_network_costs, use_container_width=True, hide_index=True)
        
        # Advanced network services
        st.markdown("**Advanced Network Services**")
        
        advanced_network_data = [
            {'Service': 'CDN', 'Single Workload': network_recs['cdn']},
            {'Service': 'DNS', 'Single Workload': network_recs['dns']},
            {'Service': 'NAT Gateway', 'Single Workload': network_recs['nat_gateway']},
            {'Service': 'VPN', 'Single Workload': network_recs['vpn']}
        ]
        
        df_advanced_network = pd.DataFrame(advanced_network_data)
        st.dataframe(df_advanced_network, use_container_width=True, hide_index=True)
        
        # Cost optimization notes
        st.markdown("**💡 Network Cost Optimization**")
        for note in network_costs.get('optimization_notes', []):
            st.markdown(note)
    
    # Storage tab with costs
    with tech_tabs[2]:
        st.markdown("#### 💾 Storage Single Workload & Costs")
        
        storage_recs = tech_recs['storage']
        storage_costs = service_costs['storage']
        
        # Cost overview
        st.markdown(f"**Monthly Storage Cost: ${storage_costs['total']:.2f}**")
        
        col1, col2 = st.columns(2)
        
    with col1:
            st.markdown("**Primary Storage Single Workload**")
            
            storage_config_data = [
                {'Setting': 'Storage Type', 'Value': storage_recs['primary_storage']},
                {'Setting': 'Recommended Size', 'Value': storage_recs['recommended_size']},
                {'Setting': 'IOPS', 'Value': storage_recs['iops_recommendation']},
                {'Setting': 'Throughput', 'Value': storage_recs['throughput_recommendation']}
            ]
            
            df_storage_config = pd.DataFrame(storage_config_data)
            st.dataframe(df_storage_config, use_container_width=True, hide_index=True)
        
    with col2:
            st.markdown("**Storage Cost Breakdown**")
            
            storage_cost_data = []
            for service, details in storage_costs.items():
                if service != 'total' and service != 'optimization_notes':
                    storage_cost_data.append({
                        'Storage Type': service.replace('_', ' ').title(),
                        'Monthly Cost': f"${details['cost']:.2f}",
                        'Details': details['details']
                    })
            
            df_storage_costs = pd.DataFrame(storage_cost_data)
            st.dataframe(df_storage_costs, use_container_width=True, hide_index=True)
        
        # Data protection
        st.markdown("**Data Protection & Management**")
        
        protection_data = [
            {'Feature': 'Backup Strategy', 'Single Workload': storage_recs['backup_strategy']},
            {'Feature': 'Encryption', 'Single Workload': storage_recs['encryption']},
            {'Feature': 'Performance', 'Single Workload': storage_recs['performance']},
            {'Feature': 'Lifecycle Policy', 'Single Workload': storage_recs['lifecycle_policy']}
        ]
        
        df_protection = pd.DataFrame(protection_data)
        st.dataframe(df_protection, use_container_width=True, hide_index=True)
        
        # Cost optimization notes
        st.markdown("**💡 Storage Cost Optimization**")
        for note in storage_costs.get('optimization_notes', []):
            st.markdown(note)
    
    # Database tab with costs
    with tech_tabs[3]:
        st.markdown("#### 🗄️ Database Single Workload & Costs")
        
        db_recs = tech_recs['database']
        db_costs = service_costs['database']
        
        # Cost overview
        st.markdown(f"**Monthly Database Cost: ${db_costs['total']:.2f}**")
        
        col1, col2 = st.columns(2)
        
    with col1:
            st.markdown("**Database Engine & Instance**")
            
            db_config_data = [
                {'Setting': 'Database Engine', 'Value': db_recs['engine']},
                {'Setting': 'Instance Class', 'Value': db_recs['instance_class']},
                {'Setting': 'Multi-AZ', 'Value': 'Yes' if db_recs['multi_az'] else 'No'},
                {'Setting': 'Backup Retention', 'Value': db_recs['backup_retention']}
            ]
            
            df_db_config = pd.DataFrame(db_config_data)
            st.dataframe(df_db_config, use_container_width=True, hide_index=True)
        
    with col2:
            st.markdown("**Database Cost Breakdown**")
            
            db_cost_data = []
            for service, details in db_costs.items():
                if service != 'total' and service != 'optimization_notes':
                    db_cost_data.append({
                        'Database Component': service.replace('_', ' ').title(),
                        'Monthly Cost': f"${details['cost']:.2f}",
                        'Details': details['details']
                    })
            
            df_db_costs = pd.DataFrame(db_cost_data)
            st.dataframe(df_db_costs, use_container_width=True, hide_index=True)
        
        # Advanced database features
        st.markdown("**Advanced Database Features**")
        
        db_advanced_data = [
            {'Feature': 'Read Replicas', 'Single Workload': db_recs['read_replicas']},
            {'Feature': 'Connection Pooling', 'Single Workload': db_recs['connection_pooling']},
            {'Feature': 'Maintenance Window', 'Single Workload': db_recs['maintenance_window']},
            {'Feature': 'Monitoring', 'Single Workload': db_recs['monitoring']}
        ]
        
        df_db_advanced = pd.DataFrame(db_advanced_data)
        st.dataframe(df_db_advanced, use_container_width=True, hide_index=True)
        
        # Cost optimization notes
        st.markdown("**💡 Database Cost Optimization**")
        for note in db_costs.get('optimization_notes', []):
            st.markdown(note)
    
    # Security tab with costs
    with tech_tabs[4]:
        st.markdown("#### 🔒 Security Single Workload & Costs")
        
        security_recs = tech_recs['security']
        security_costs = service_costs['security']
        
        # Cost overview
        st.markdown(f"**Monthly Security Cost: ${security_costs['total']:.2f}**")
        
        col1, col2 = st.columns(2)
        
    with col1:
            st.markdown("**Security Services Single Workload**")
            
            security_data = []
            for key, value in security_recs.items():
                security_data.append({'Security Area': key.replace('_', ' ').title(), 'Single Workload': value})
            
            df_security = pd.DataFrame(security_data)
            st.dataframe(df_security, use_container_width=True, hide_index=True)
        
    with col2:
            st.markdown("**Security Cost Breakdown**")
            
            security_cost_data = []
            for service, details in security_costs.items():
                if service != 'total' and service != 'optimization_notes':
                    security_cost_data.append({
                        'Security Service': service.replace('_', ' ').title(),
                        'Monthly Cost': f"${details['cost']:.2f}",
                        'Details': details['details']
                    })
            
            df_security_costs = pd.DataFrame(security_cost_data)
            st.dataframe(df_security_costs, use_container_width=True, hide_index=True)
        
        # Security best practices
        st.markdown("**Security Best Practices for this Environment:**")
        
        security_practices = [
            "🔐 Implement least privilege access principles",
            "🔍 Enable comprehensive audit logging",
            "🛡️ Use AWS Config for compliance monitoring",
            "🚨 Set up GuardDuty for threat detection",
            "📊 Regular security assessments and penetration testing"
        ]
        
    for practice in security_practices:
            st.markdown(practice)
        
        # Cost optimization notes
        st.markdown("**💡 Security Cost Optimization**")
    for note in security_costs.get('optimization_notes', []):
            st.markdown(note)
    
    # Monitoring tab with costs
    with tech_tabs[5]:
        st.markdown("#### 📊 Monitoring Single Workload & Costs")
        
        monitoring_recs = tech_recs['monitoring']
        monitoring_costs = service_costs['monitoring']
        
        # Cost overview
        st.markdown(f"**Monthly Monitoring Cost: ${monitoring_costs['total']:.2f}**")
        
        col1, col2 = st.columns(2)
        
    with col1:
            st.markdown("**Core Monitoring Setup**")
            
            monitoring_core_data = [
                {'Component': 'CloudWatch', 'Single Workload': monitoring_recs['cloudwatch']},
                {'Component': 'Alerting', 'Single Workload': monitoring_recs['alerting']},
                {'Component': 'Dashboards', 'Single Workload': monitoring_recs['dashboards']},
                {'Component': 'Log Retention', 'Single Workload': monitoring_recs['log_retention']}
            ]
            
            df_monitoring_core = pd.DataFrame(monitoring_core_data)
            st.dataframe(df_monitoring_core, use_container_width=True, hide_index=True)
        
    with col2:
            st.markdown("**Monitoring Cost Breakdown**")
            
            monitoring_cost_data = []
            for service, details in monitoring_costs.items():
                if service != 'total' and service != 'optimization_notes':
                    monitoring_cost_data.append({
                        'Monitoring Service': service.replace('_', ' ').title(),
                        'Monthly Cost': f"${details['cost']:.2f}",
                        'Details': details['details']
                    })
            
            df_monitoring_costs = pd.DataFrame(monitoring_cost_data)
            st.dataframe(df_monitoring_costs, use_container_width=True, hide_index=True)
        
        # Advanced monitoring services
        st.markdown("**Advanced Monitoring Services**")
        
        monitoring_advanced_data = [
            {'Service': 'APM (X-Ray)', 'Single Workload': monitoring_recs['apm']},
            {'Service': 'Synthetic Monitoring', 'Single Workload': monitoring_recs['synthetic_monitoring']},
            {'Service': 'Cost Monitoring', 'Single Workload': monitoring_recs['cost_monitoring']},
            {'Service': 'Health Checks', 'Single Workload': monitoring_recs['health_checks']}
        ]
        
        df_monitoring_advanced = pd.DataFrame(monitoring_advanced_data)
        st.dataframe(df_monitoring_advanced, use_container_width=True, hide_index=True)
        
        # Cost optimization notes
        st.markdown("**💡 Monitoring Cost Optimization**")
    for note in monitoring_costs.get('optimization_notes', []):
            st.markdown(note)
    
    # Cost comparison across environments
    st.markdown("---")
    st.markdown("### 📊 Cost Comparison Across Environments")
    
    # Calculate costs for all environments
    all_env_costs = []
    
    for env in ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']:
        env_results_temp = results['recommendations'].get(env, {})
        if env_results_temp:
            tech_recs_temp = analyzer.get_technical_recommendations(env, env_results_temp)
            requirements_temp = env_results_temp.get('requirements', {})
            costs_temp = cost_calculator.calculate_service_costs(env, tech_recs_temp, requirements_temp)
            
            all_env_costs.append({
                'Environment': env,
                'Compute': costs_temp['compute']['total'],
                'Network': costs_temp['network']['total'],
                'Storage': costs_temp['storage']['total'],
                'Database': costs_temp['database']['total'],
                'Security': costs_temp['security']['total'],
                'Monitoring': costs_temp['monitoring']['total'],
                'Total Monthly': costs_temp['summary']['total_monthly']
            })
    
    if all_env_costs:
        df_env_costs = pd.DataFrame(all_env_costs)
        
        # Create stacked bar chart
        fig_bar = go.Figure()
        
        categories = ['Compute', 'Network', 'Storage', 'Database', 'Security', 'Monitoring']
        colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4']
        
        for i, category in enumerate(categories):
            fig_bar.add_trace(go.Bar(
                name=category,
                x=df_env_costs['Environment'],
                y=df_env_costs[category],
                marker_color=colors[i]
            ))
        
        fig_bar.update_layout(
            title="Monthly Cost Comparison Across Environments",
            barmode='stack',
            xaxis_title="Environment",
            yaxis_title="Monthly Cost ($)",
            height=500
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Show detailed comparison table
        st.dataframe(df_env_costs, use_container_width=True, hide_index=True)
        
        # Cost insights
        st.markdown("**💡 Cost Insights:**")
        total_costs = df_env_costs['Total Monthly'].tolist()
        if len(total_costs) >= 2:
            prod_cost = df_env_costs[df_env_costs['Environment'] == 'PROD']['Total Monthly'].iloc[0] if 'PROD' in df_env_costs['Environment'].values else 0
            dev_cost = df_env_costs[df_env_costs['Environment'] == 'DEV']['Total Monthly'].iloc[0] if 'DEV' in df_env_costs['Environment'].values else 0
            
            if prod_cost > 0 and dev_cost > 0:
                cost_ratio = prod_cost / dev_cost
                st.markdown(f"• Production environment costs {cost_ratio:.1f}x more than Development")
            
            total_all_envs = sum(total_costs)
            st.markdown(f"• Total monthly cost across all environments: ${total_all_envs:,.2f}")
            st.markdown(f"• Annual cost across all environments: ${total_all_envs * 12:,.2f}")
    
    # Summary recommendations for the environment
    st.markdown("---")
    st.markdown(f"### 📋 {selected_env} Environment Implementation Summary")
    
    total_cost = service_costs['summary']['total_monthly']
    annual_cost = service_costs['summary']['total_annual']
    
    summary_recommendations = [
        f"🏗️ **Architecture:** Deploy using {tech_recs['compute']['placement_strategy'].lower()}",
        f"🔧 **Compute:** Use {tech_recs['compute']['primary_instance']['type']} instances (${compute_costs['total']:.2f}/month)",
        f"🌐 **Network:** Implement {tech_recs['network']['vpc_design'].lower()} (${network_costs['total']:.2f}/month)",
        f"💾 **Storage:** Configure {tech_recs['storage']['primary_storage']} (${storage_costs['total']:.2f}/month)",
        f"🗄️ **Database:** Deploy {tech_recs['database']['engine']} (${db_costs['total']:.2f}/month)",
        f"🔒 **Security:** Implement {len([k for k, v in security_costs.items() if isinstance(v, dict) and v.get('cost', 0) > 0])} security services (${security_costs['total']:.2f}/month)",
        f"📊 **Monitoring:** Set up comprehensive monitoring (${monitoring_costs['total']:.2f}/month)",
        f"💰 **Total Cost:** ${total_cost:.2f}/month (${annual_cost:,.2f}/year)"
    ]
    
    for rec in summary_recommendations:
        st.markdown(rec)

def generate_enhanced_excel_report():
    """Generate comprehensive Excel report with multiple sheets."""
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.warning("No analysis results available for Excel generation.")
        return
    
    if not OPENPYXL_AVAILABLE:
        st.error("📊 openpyxl not available. Please install with: `pip install openpyxl`")
        return
    
    try:
        results = st.session_state.enhanced_results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        data_font = Font(size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Sheet 1: Executive Summary
        ws_summary = wb.create_sheet("Executive Summary")
        
        # Add title
        ws_summary['A1'] = "AWS Migration Analysis - Executive Summary"
        ws_summary['A1'].font = Font(bold=True, size=16)
        ws_summary.merge_cells('A1:E1')
        
        # Add generation date
        ws_summary['A2'] = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        ws_summary['A2'].font = Font(size=12, italic=True)
        ws_summary.merge_cells('A2:E2')
        
        # Summary data
        prod_results = results['recommendations']['PROD']
        claude_analysis = prod_results.get('claude_analysis', {})
        tco_analysis = prod_results.get('tco_analysis', {})
        
        summary_data = [
            ["Metric", "Value"],
            ["Workload Name", results['inputs']['workload_name']],
            ["Workload Type", results['inputs']['workload_type']],
            ["Migration Complexity Level", claude_analysis.get('complexity_level', 'MEDIUM')],
            ["Complexity Score", f"{claude_analysis.get('complexity_score', 50):.0f}/100"],
            ["Estimated Timeline (weeks)", f"{claude_analysis.get('estimated_timeline', {}).get('max_weeks', 8)}"],
            ["Monthly Cost (Production)", f"${tco_analysis.get('monthly_cost', 0):,.2f}"],
            ["Annual Cost (Production)", f"${tco_analysis.get('monthly_cost', 0) * 12:,.2f}"],
            ["Best Pricing Option", tco_analysis.get('best_pricing_option', 'N/A').replace('_', ' ').title()],
            ["Migration Strategy", claude_analysis.get('migration_strategy', {}).get('approach', 'N/A')]
        ]
        
        # Write summary data
        start_row = 4
        for row_idx, (metric, value) in enumerate(summary_data, start_row):
            ws_summary[f'A{row_idx}'] = metric
            ws_summary[f'B{row_idx}'] = value
            
            if row_idx == start_row:  # Header row
                ws_summary[f'A{row_idx}'].font = header_font
                ws_summary[f'A{row_idx}'].fill = header_fill
                ws_summary[f'B{row_idx}'].font = header_font
                ws_summary[f'B{row_idx}'].fill = header_fill
            else:
                ws_summary[f'A{row_idx}'].font = data_font
                ws_summary[f'B{row_idx}'].font = data_font
            
            ws_summary[f'A{row_idx}'].border = border
            ws_summary[f'B{row_idx}'].border = border
        
        # Auto-adjust column widths
        ws_summary.column_dimensions['A'].width = 25
        ws_summary.column_dimensions['B'].width = 30
        
        # Sheet 2: Environment Comparison
        ws_env = wb.create_sheet("Environment Comparison")
        
        env_headers = ["Environment", "Complexity Score", "Instance Type", "Monthly Cost", "vCPUs", "RAM (GB)", "Storage (GB)"]
        
        # Write headers
        for col_idx, header in enumerate(env_headers, 1):
            cell = ws_env.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        # Write environment data
        for row_idx, env in enumerate(['DEV', 'QA', 'UAT', 'PREPROD', 'PROD'], 2):
            env_results = results['recommendations'].get(env, {})
            env_claude_analysis = env_results.get('claude_analysis', {})
            cost_breakdown = env_results.get('cost_breakdown', {})
            selected_instance = cost_breakdown.get('selected_instance', {})
            total_costs = cost_breakdown.get('total_costs', {})
            requirements = env_results.get('requirements', {})
            
            env_data = [
                env,
                f"{env_claude_analysis.get('complexity_score', 50):.0f}",
                selected_instance.get('type', 'N/A'),
                f"${total_costs.get('on_demand', 0):,.2f}",
                str(requirements.get('vCPUs', 'N/A')),
                str(requirements.get('RAM_GB', 'N/A')),
                str(requirements.get('storage_GB', 'N/A'))
            ]
            
            for col_idx, value in enumerate(env_data, 1):
                cell = ws_env.cell(row=row_idx, column=col_idx, value=value)
                cell.font = data_font
                cell.border = border
                if col_idx > 1:  # Center align numeric data
                    cell.alignment = Alignment(horizontal='center')
        
        # Auto-adjust column widths
        for col_idx in range(1, len(env_headers) + 1):
            ws_env.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 15
        
        # Sheet 3: Cost Analysis by Environment
        ws_cost = wb.create_sheet("Cost Analysis")
        
        analyzer = EnhancedEnvironmentAnalyzer()
        cost_calculator = AWSCostCalculator()
        
        cost_headers = ["Environment", "Compute", "Network", "Storage", "Database", "Security", "Monitoring", "Total Monthly"]
        
        # Write headers
        for col_idx, header in enumerate(cost_headers, 1):
            cell = ws_cost.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        # Calculate and write cost data for all environments
        for row_idx, env in enumerate(['DEV', 'QA', 'UAT', 'PREPROD', 'PROD'], 2):
            env_results_temp = results['recommendations'].get(env, {})
            if env_results_temp:
                tech_recs_temp = analyzer.get_technical_recommendations(env, env_results_temp)
                requirements_temp = env_results_temp.get('requirements', {})
                costs_temp = cost_calculator.calculate_service_costs(env, tech_recs_temp, requirements_temp)
                
                cost_data = [
                    env,
                    f"${costs_temp['compute']['total']:.2f}",
                    f"${costs_temp['network']['total']:.2f}",
                    f"${costs_temp['storage']['total']:.2f}",
                    f"${costs_temp['database']['total']:.2f}",
                    f"${costs_temp['security']['total']:.2f}",
                    f"${costs_temp['monitoring']['total']:.2f}",
                    f"${costs_temp['summary']['total_monthly']:.2f}"
                ]
            else:
                cost_data = [env] + ["N/A"] * 7
            
            for col_idx, value in enumerate(cost_data, 1):
                cell = ws_cost.cell(row=row_idx, column=col_idx, value=value)
                cell.font = data_font
                cell.border = border
                if col_idx > 1:  # Center align cost data
                    cell.alignment = Alignment(horizontal='center')
        
        # Auto-adjust column widths
        for col_idx in range(1, len(cost_headers) + 1):
            ws_cost.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 12
        
        # Sheet 4: Migration Recommendations
        ws_recs = wb.create_sheet("Migration Recommendations")
        
        ws_recs['A1'] = "Migration Recommendations"
        ws_recs['A1'].font = Font(bold=True, size=14)
        ws_recs.merge_cells('A1:C1')
        
        # Migration strategy
        strategy = claude_analysis.get('migration_strategy', {})
        strategy_data = [
            ["Migration Strategy", ""],
            ["Approach", strategy.get('approach', 'N/A')],
            ["Methodology", strategy.get('methodology', 'N/A')],
            ["Timeline", strategy.get('timeline', 'N/A')],
            ["Risk Level", strategy.get('risk_level', 'N/A')],
            ["", ""],
            ["Key Recommendations", ""]
        ]
        
        # Add recommendations
        recommendations = claude_analysis.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            strategy_data.append([f"{i}.", rec])
        
        # Write recommendations data
        for row_idx, (label, value) in enumerate(strategy_data, 3):
            ws_recs[f'A{row_idx}'] = label
            ws_recs[f'B{row_idx}'] = value
            
            if "Strategy" in label or "Recommendations" in label:
                ws_recs[f'A{row_idx}'].font = Font(bold=True, size=12)
                ws_recs[f'B{row_idx}'].font = Font(bold=True, size=12)
            else:
                ws_recs[f'A{row_idx}'].font = data_font
                ws_recs[f'B{row_idx}'].font = data_font
        
        # Auto-adjust column widths
        ws_recs.column_dimensions['A'].width = 20
        ws_recs.column_dimensions['B'].width = 60
        
        # Sheet 5: Technical Specifications (Production)
        ws_tech = wb.create_sheet("Technical Specifications")
        
        if prod_results:
            tech_recs = analyzer.get_technical_recommendations('PROD', prod_results)
            requirements = prod_results.get('requirements', {})
            service_costs = cost_calculator.calculate_service_costs('PROD', tech_recs, requirements)
            
            ws_tech['A1'] = "Production Environment Technical Specifications"
            ws_tech['A1'].font = Font(bold=True, size=14)
            ws_tech.merge_cells('A1:D1')
            
            tech_sections = [
                ("Compute Single Workload", tech_recs['compute']),
                ("Network Single Workload", tech_recs['network']),
                ("Storage Single Workload", tech_recs['storage']),
                ("Database Single Workload", tech_recs['database']),
                ("Security Single Workload", tech_recs['security']),
                ("Monitoring Single Workload", tech_recs['monitoring'])
            ]
            
            current_row = 3
            for section_name, section_data in tech_sections:
                # Section header
                ws_tech[f'A{current_row}'] = section_name
                ws_tech[f'A{current_row}'].font = Font(bold=True, size=12)
                ws_tech.merge_cells(f'A{current_row}:D{current_row}')
                current_row += 1
                
                # Section data
                if isinstance(value, (str, int, float, bool)): # ensure value is scalar
                    for key, value in section_data.items():
                        ws_tech[f'A{current_row}'] = key.replace('_', ' ').title()
                        ws_tech[f'B{current_row}'] = str(value)
                        ws_tech[f'A{current_row}'].font = data_font
                        ws_tech[f'B{current_row}'].font = data_font
                        current_row += 1
                
                current_row += 1  # Add space between sections
            
            # Auto-adjust column widths
            ws_tech.column_dimensions['A'].width = 25
            ws_tech.column_dimensions['B'].width = 40
        
        # Save to BytesIO buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        filename = f"Enhanced_AWS_Migration_Analysis_{timestamp}.xlsx"
        
        st.download_button(
            label="⬇️ Download Excel Report",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="excel_report_download"
        )
        
        st.success("✅ Enhanced Excel report generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating Excel report: {str(e)}")
        logger.error(f"Error in Excel generation: {e}")

def generate_enhanced_pdf_report():
    """Generate enhanced PDF report."""
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.warning("No analysis results available for PDF generation.")
        return
    
    if not REPORTLAB_AVAILABLE:
        st.warning("📄 ReportLab not available. Please install with: `pip install reportlab`")
        return
    
    try:
        results = st.session_state.enhanced_results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create PDF content
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, leftMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f2937'),
            fontName='Helvetica-Bold'
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Enhanced AWS Migration Analysis", title_style))
        story.append(Paragraph("Enterprise Corporation", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        prod_results = results['recommendations']['PROD']
        claude_analysis = prod_results.get('claude_analysis', {})
        tco_analysis = prod_results.get('tco_analysis', {})
        
        story.append(Paragraph("Executive Summary", styles['Heading1']))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Workload Name', results['inputs']['workload_name']],
            ['Migration Complexity', f"{claude_analysis.get('complexity_level', 'MEDIUM')} ({claude_analysis.get('complexity_score', 50):.0f}/100)"],
            ['Estimated Timeline', f"{claude_analysis.get('estimated_timeline', {}).get('max_weeks', 8)} weeks"],
            ['Monthly Cost', f"${tco_analysis.get('monthly_cost', 0):,.2f}"],
            ['Best Pricing Option', tco_analysis.get('best_pricing_option', 'N/A').replace('_', ' ').title()]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        
        story.append(summary_table)
        story.append(PageBreak())
        
        # Environment Analysis Section
        story.append(Paragraph("Environment Analysis Overview", styles['Heading1']))
        
        analyzer = EnhancedEnvironmentAnalyzer()
        
        # Environment comparison table
        env_data = [['Environment', 'Complexity Score', 'Instance Type', 'Monthly Cost', 'Key Characteristics']]
        
        for env in ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']:
            env_results = results['recommendations'].get(env, {})
            claude_env_analysis = env_results.get('claude_analysis', {})
            cost_breakdown = env_results.get('cost_breakdown', {})
            selected_instance = cost_breakdown.get('selected_instance', {})
            total_costs = cost_breakdown.get('total_costs', {})
            
            characteristics = get_env_characteristics(env)
            
            env_data.append([
                env,
                f"{claude_env_analysis.get('complexity_score', 50):.0f}/100",
                selected_instance.get('type', 'N/A'),
                f"${total_costs.get('on_demand', 0):,.0f}",
                characteristics
            ])
        
        env_table = Table(env_data, colWidths=[1*inch, 1*inch, 1.2*inch, 1*inch, 2.8*inch])
        env_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#93c5fd')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(env_table)
        story.append(PageBreak())
        
        # Migration Strategy
        story.append(Paragraph("Migration Strategy", styles['Heading1']))
        
        strategy = claude_analysis.get('migration_strategy', {})
        if strategy:
            strategy_text = f"""
            <b>Approach:</b> {strategy.get('approach', 'N/A')}<br/>
            <b>Methodology:</b> {strategy.get('methodology', 'N/A')}<br/>
            <b>Timeline:</b> {strategy.get('timeline', 'N/A')}<br/>
            <b>Risk Level:</b> {strategy.get('risk_level', 'N/A')}
            """
            story.append(Paragraph(strategy_text, styles['Normal']))
        
        # Migration Steps
        migration_steps = claude_analysis.get('migration_steps', [])
        if migration_steps:
            story.append(Paragraph("Migration Implementation Plan", styles['Heading2']))
            
            for i, step in enumerate(migration_steps, 1):
                if isinstance(step, dict):
                    story.append(Paragraph(f"Phase {i}: {step.get('phase', 'N/A')} ({step.get('duration', 'N/A')})", styles['Heading3']))
                    
                    tasks = step.get('tasks', [])
                    if tasks:
                        tasks_text = "<b>Key Tasks:</b><br/>" + "<br/>".join([f"• {task}" for task in tasks])
                        story.append(Paragraph(tasks_text, styles['Normal']))
                    
                    deliverables = step.get('deliverables', [])
                    if deliverables:
                        deliverables_text = f"<b>Deliverables:</b> {', '.join(deliverables)}"
                        story.append(Paragraph(deliverables_text, styles['Normal']))
                    
                    story.append(Spacer(1, 0.1*inch))
        
        # Technical Recommendations Section
        story.append(PageBreak())
        story.append(Paragraph("Technical Recommendations & Cost Analysis", styles['Heading1']))
        
        # Production environment technical specs
        prod_env_results = results['recommendations'].get('PROD', {})
        if prod_env_results:
            tech_recs = analyzer.get_technical_recommendations('PROD', prod_env_results)
            requirements = prod_env_results.get('requirements', {})
            service_costs = cost_calculator.calculate_service_costs('PROD', tech_recs, requirements)
            
            # Cost Summary Section
            story.append(Paragraph("Production Environment Cost Summary", styles['Heading2']))
            
            cost_summary_data = [
                ['Service Category', 'Monthly Cost', 'Annual Cost', 'Key Components'],
                ['Compute', f"${service_costs['compute']['total']:.2f}", f"${service_costs['compute']['total'] * 12:.2f}", 'EC2 instances, Auto Scaling'],
                ['Network', f"${service_costs['network']['total']:.2f}", f"${service_costs['network']['total'] * 12:.2f}", 'Load balancers, NAT Gateway, CloudFront'],
                ['Storage', f"${service_costs['storage']['total']:.2f}", f"${service_costs['storage']['total'] * 12:.2f}", 'EBS volumes, Snapshots, S3'],
                ['Database', f"${service_costs['database']['total']:.2f}", f"${service_costs['database']['total'] * 12:.2f}", 'RDS/Aurora, Backup storage'],
                ['Security', f"${service_costs['security']['total']:.2f}", f"${service_costs['security']['total'] * 12:.2f}", 'KMS, Secrets Manager, GuardDuty'],
                ['Monitoring', f"${service_costs['monitoring']['total']:.2f}", f"${service_costs['monitoring']['total'] * 12:.2f}", 'CloudWatch, X-Ray, Synthetics'],
                ['TOTAL', f"${service_costs['summary']['total_monthly']:.2f}", f"${service_costs['summary']['total_annual']:.2f}", 'All AWS services']
            ]
            
            cost_summary_table = Table(cost_summary_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 2.1*inch])
            cost_summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor('#059669')),
                ('TEXTCOLOR', (-1, -1), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#6b7280')),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            story.append(cost_summary_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        recommendations = claude_analysis.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Key Recommendations", styles['Heading2']))
            recs_text = "<br/>".join([f"{i}. {rec}" for i, rec in enumerate(recommendations, 1)])
            story.append(Paragraph(recs_text, styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"Report generated by Enhanced AWS Migration Platform v7.0 with Real Claude AI on {datetime.now().strftime('%B %d, %Y')}"
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#6b7280'))
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        filename = f"Enhanced_AWS_Migration_Report_{timestamp}.pdf"
        
        st.download_button(
            label="⬇️ Download Enhanced PDF Report",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/pdf",
            key="pdf_report_download"
        )
        
        st.success("✅ Enhanced PDF report generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
# Add these functions AFTER generate_enhanced_pdf_report() and BEFORE get_env_characteristics()
def generate_bulk_template():
    """Downloadable CSV template for bulk upload."""
    import io

    sample_data = {
        "workload_name": ["App 1", "DB 1"],
        "cpu_cores": [4, 8],
        "ram_gb": [16, 32],
        "storage_gb": [200, 500],
        "workload_type": ["web_application", "database_server"],
        "operating_system": ["linux", "windows"],
        "peak_cpu_percent": [70, 85],
        "peak_ram_percent": [75, 90],
        "peak_iops": [3000, 6000],
        "business_criticality": ["medium", "high"],
        "region": ["us-east-1", "us-east-1"]
    }

    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    st.download_button(
        label="⬇️ Click to Download CSV Template",
        data=output,
        file_name="bulk_upload_template.csv",
        mime="text/csv"
    )

        
def render_bulk_upload_tab():
    """Render bulk upload tab."""
    st.markdown("### 📁 Bulk Workload Upload & Analysis")
    
    st.markdown("""
    Upload multiple workloads at once using CSV or Excel files. This feature allows you to:
    - Analyze dozens of workloads simultaneously
    - Get comprehensive cost and complexity analysis for all environments
    - Export consolidated reports
    - Compare workloads side-by-side
    """)
    
    # File upload section
    st.markdown("#### 📤 Upload Workloads File")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload a file containing multiple workloads to analyze"
        )
    
    with col2:
        # Create a button to trigger template download
        if st.button("📋 Download Template", key="bulk_template_download"):
            # Call the template generation function
            generate_bulk_template()
    
    # Show file format requirements
    with st.expander("📋 File Format Requirements", expanded=False):
        st.markdown("""
        **Required Columns** (case-insensitive):
        - `workload_name` or `name` - Name of the workload
        - `cpu_cores` or `cores` - Number of CPU cores
        - `ram_gb` or `memory_gb` - RAM in GB
        - `storage_gb` or `disk_gb` - Storage in GB
        
        **Optional Columns:**
        - `workload_type` - web_application, database_server, etc.
        - `operating_system` - linux, windows
        - `peak_cpu_percent` - Peak CPU utilization %
        - `peak_ram_percent` - Peak RAM utilization %
        - `peak_iops` - Peak IOPS
        - `business_criticality` - low, medium, high, critical
        - `region` - AWS region (default: us-east-1)
        
        **Example CSV:**
        ```
        workload_name,cpu_cores,ram_gb,storage_gb,workload_type,peak_cpu_percent
        Web App 1,4,16,200,web_application,75
        Database 1,8,32,500,database_server,85
        API Service,2,8,100,application_server,60
        ```
        """)
    
    # Process uploaded file
    if uploaded_file is not None:
        file_type = 'csv' if uploaded_file.name.endswith('.csv') else 'excel'
        
        if st.button("🚀 Analyze All Workloads", type="primary", key="bulk_analyze_button"):
            with st.spinner("🔄 Processing bulk workload analysis..."):
                bulk_analyzer = BulkWorkloadAnalyzer()
                results = bulk_analyzer.process_bulk_upload(uploaded_file, file_type)
                
                # Store results in session state
                st.session_state.bulk_results = results
                
                if 'error' in results:
                    st.error(f"❌ Error processing file: {results['error']}")
                else:
                    st.success(f"✅ Successfully analyzed {results['successful_analyses']} out of {results['total_workloads']} workloads!")
    
    # Display results
    if 'bulk_results' in st.session_state and st.session_state.bulk_results:
        render_bulk_results()
    
    # Add report generation section
    if 'bulk_results' in st.session_state and st.session_state.bulk_results:
        st.markdown("---")
        st.markdown("### 📋 Bulk Report Generation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Export to Excel", key="bulk_excel_export"):
                export_bulk_results_to_excel(st.session_state.bulk_results)
        with col2:
            if st.button("📄 Generate PDF Report", key="bulk_pdf_export"):
                export_bulk_results_to_pdf(st.session_state.bulk_results)

def render_bulk_results():
    """Render bulk analysis results."""
    results = st.session_state.bulk_results
    
    # ... (bulk results rendering) ...
    if 'error' in results:
        st.error(f"Error: {results['error']}")
        return
    
    st.markdown("---")
    st.markdown("### 📊 Bulk Analysis Results")    
    
    # Add detailed tabs for bulk workloads
    if results['successful_analyses'] > 0:
        st.markdown("#### 🔍 Detailed Workload Analysis")
        selected_workload = st.selectbox(
            "Select Workload for Detailed View",
            [w['workload_name'] for w in results['workloads'] if w['status'] == 'success']
        )
        
        if selected_workload:
            workload_data = next(w for w in results['workloads'] 
                             if w['workload_name'] == selected_workload and w['status'] == 'success')
            
            # Create tabs for detailed analysis
tabs = st.tabs(["Single Workload", "Bulk Upload"])
            
            with tab1:
                render_workload_analysis(workload_data)
                
            with tab2:
                render_workload_heatmaps(workload_data)
                
            with tab3:
                render_workload_recommendations(workload_data)

def render_workload_analysis(workload_data):
    """Render analysis for a specific workload."""
    st.markdown(f"### 📊 Analysis for {workload_data['workload_name']}")
    
    prod_analysis = workload_data['analysis']['PROD']
    claude_analysis = prod_analysis.get('claude_analysis', {})
           
    try:
        prod_results = workload_data['analysis']['PROD']
        claude_analysis = prod_results.get('claude_analysis', {})
        tco_analysis = prod_results.get('tco_analysis', {})
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            complexity_score = claude_analysis.get('complexity_score', 50)
            complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">🤖 Migration Complexity</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{complexity_score:.0f}/100</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">{complexity_level}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            monthly_cost = tco_analysis.get('monthly_cost', 0)
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">☁️ AWS Monthly Cost</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">${monthly_cost:,.0f}</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">Optimized Pricing</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            timeline = claude_analysis.get('estimated_timeline', {})
            max_weeks = timeline.get('max_weeks', 8)
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">⏱️ Migration Timeline</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{max_weeks}</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">Weeks (Estimated)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">🖥️ Instance Type</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">
                    {prod_results.get('cost_breakdown', {}).get('selected_instance', {}).get('type', 'N/A')}
                </div>
                <div style="font-size: 0.75rem; color: #9ca3af;">Recommended</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Claude AI Analysis
        st.markdown("### 🤖 Claude AI Migration Analysis")
        
        if claude_analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Migration Strategy**")
                strategy = claude_analysis.get('migration_strategy', {})
                if strategy:
                    st.markdown(f"**Approach:** {strategy.get('approach', 'N/A')}")
                    st.markdown(f"**Methodology:** {strategy.get('methodology', 'N/A')}")
                    st.markdown(f"**Timeline:** {strategy.get('timeline', 'N/A')}")
                    st.markdown(f"**Risk Level:** {strategy.get('risk_level', 'N/A')}")
            
            with col2:
                st.markdown("**Migration Steps**")
                migration_steps = claude_analysis.get('migration_steps', [])
                
                for i, step in enumerate(migration_steps[:3], 1):
                    if isinstance(step, dict):
                        with st.expander(f"Phase {i}: {step.get('phase', 'N/A')}", expanded=False):
                            st.markdown(f"**Duration:** {step.get('duration', 'N/A')}")
                            
                            tasks = step.get('tasks', [])
                            if tasks:
                                st.markdown("**Key Tasks:**")
                                for task in tasks[:3]:
                                    st.markdown(f"• {task}")
        
        # Risk Analysis
        st.markdown("### ⚠️ Risk Analysis")
        
        risk_factors = claude_analysis.get('risk_factors', [])
        if risk_factors:
            risk_data = []
            for risk in risk_factors[:5]:
                if isinstance(risk, dict):
                    risk_data.append({
                        'Category': risk.get('category', 'N/A'),
                        'Risk': risk.get('risk', 'N/A'),
                        'Probability': risk.get('probability', 'N/A'),
                        'Impact': risk.get('impact', 'N/A'),
                        'Mitigation': risk.get('mitigation', 'N/A')
                    })
            
            if risk_data:
                df_risks = pd.DataFrame(risk_data)
                st.dataframe(df_risks, use_container_width=True, hide_index=True)
        
        # Recommendations
        st.markdown("### 💡 Key Recommendations")
        
        recommendations = claude_analysis.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations[:7], 1):
                st.markdown(f"{i}. {rec}")
        
        # Success Factors
        st.markdown("### ✅ Success Factors")
        
        success_factors = claude_analysis.get('success_factors', [])
        if success_factors:
            for i, factor in enumerate(success_factors[:5], 1):
                st.markdown(f"• {factor}")
        
        # Cost Analysis
        st.markdown("### 💰 Cost Analysis")
        
        cost_breakdown = prod_results.get('cost_breakdown', {})
        total_costs = cost_breakdown.get('total_costs', {})
        
        if total_costs:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Instance Pricing Comparison**")
                cost_data = []
                for pricing_model, cost in total_costs.items():
                    cost_data.append({
                        'Pricing Model': pricing_model.replace('_', ' ').title(),
                        'Monthly Cost': f"${cost:,.2f}",
                        'Annual Cost': f"${cost*12:,.2f}"
                    })
                
                df_costs = pd.DataFrame(cost_data)
                st.dataframe(df_costs, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**AWS Service Cost Breakdown (PROD)**")
                
                # Calculate detailed service costs
                try:
                    analyzer = EnhancedEnvironmentAnalyzer()
                    tech_recs = analyzer.get_technical_recommendations('PROD', prod_results)
                    cost_calculator = AWSCostCalculator()
                    service_costs = cost_calculator.calculate_service_costs('PROD', tech_recs, prod_results.get('requirements', {}))
                    
                    service_cost_data = []
                    categories = ['compute', 'network', 'storage', 'database', 'security', 'monitoring']
                    for cat in categories:
                        if cat in service_costs:
                            service_cost_data.append({
                                'Service Category': cat.title(),
                                'Monthly Cost': f"${service_costs[cat]['total']:.2f}"
                            })
                    
                    if service_cost_data:
                        df_service_costs = pd.DataFrame(service_cost_data)
                        st.dataframe(df_service_costs, use_container_width=True, hide_index=True)
                        
                        # Show total from service breakdown
                        total_services = sum(service_costs[cat]['total'] for cat in categories if cat in service_costs)
                        st.markdown(f"**Total Monthly AWS Services Cost: ${total_services:.2f}**")
                    else:
                        # Fallback to basic cost display
                        basic_cost_data = [
                            {'Cost Component': 'Instance Costs', 'Monthly Cost': f"${cost_breakdown.get('instance_costs', {}).get('on_demand', 0):.2f}"},
                            {'Cost Component': 'Storage Costs', 'Monthly Cost': f"${cost_breakdown.get('storage_costs', {}).get('primary_storage', 0):.2f}"},
                            {'Cost Component': 'Network Costs', 'Monthly Cost': f"${cost_breakdown.get('network_costs', {}).get('data_transfer', 0):.2f}"}
                        ]
                        
                        df_basic_costs = pd.DataFrame(basic_cost_data)
                        st.dataframe(df_basic_costs, use_container_width=True, hide_index=True)
                
                except Exception as e:
                    logger.error(f"Error calculating detailed service costs: {e}")
                    # Fallback to basic cost display
                    basic_cost_data = [
                        {'Cost Component': 'Instance Costs', 'Monthly Cost': f"${cost_breakdown.get('instance_costs', {}).get('on_demand', 0):.2f}"},
                        {'Cost Component': 'Storage Costs', 'Monthly Cost': f"${cost_breakdown.get('storage_costs', {}).get('primary_storage', 0):.2f}"},
                        {'Cost Component': 'Network Costs', 'Monthly Cost': f"${cost_breakdown.get('network_costs', {}).get('data_transfer', 0):.2f}"}
                    ]
                    
                    df_basic_costs = pd.DataFrame(basic_cost_data)
                    st.dataframe(df_basic_costs, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Error displaying workload analysis: {str(e)}")
        logger.error(f"Error in render_workload_analysis: {e}")

def render_workload_heatmaps(workload_data):
    """Render heatmaps for a specific workload."""
    st.markdown(f"### 🌡️ Environment Heat Map for {workload_data['workload_name']}")
    
    # Generate heat map data
    heat_map_generator = EnvironmentHeatMapGenerator()
    heat_map_data = heat_map_generator.generate_heat_map_data(workload_data['analysis'])
    heat_map_fig = heat_map_generator.create_heat_map_visualization(heat_map_data)
    
    st.plotly_chart(heat_map_fig, use_container_width=True)

def render_workload_recommendations(workload_data):
    """Render recommendations for a specific workload."""
    st.markdown(f"### 🔧 Technical Recommendations for {workload_data['workload_name']}")
    
    analyzer = EnhancedEnvironmentAnalyzer()
    env = 'PROD'  # Focus on production environment
    env_results = workload_data['analysis'][env]
    tech_recs = analyzer.get_technical_recommendations(env, env_results)
    
    # ... (recommendations rendering similar to single workload) ...

def render_workload_recommendations(workload_data):
    """Render comprehensive technical recommendations for a specific workload."""
    st.markdown(f"### 🔧 Technical Recommendations for {workload_data['workload_name']}")
    
    try:
        analyzer = EnhancedEnvironmentAnalyzer()
        env = 'PROD'  # Focus on production environment
        env_results = workload_data['analysis'][env]
        tech_recs = analyzer.get_technical_recommendations(env, env_results)
        cost_calculator = AWSCostCalculator()
        requirements = env_results.get('requirements', {})
        service_costs = cost_calculator.calculate_service_costs(env, tech_recs, requirements)
        
        # Cost summary at the top
        st.markdown("### 💰 Cost Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_monthly = service_costs['summary']['total_monthly']
            st.metric("Total Monthly Cost", f"${total_monthly:,.2f}")
        
        with col2:
            total_annual = service_costs['summary']['total_annual']
            st.metric("Total Annual Cost", f"${total_annual:,.2f}")
        
        with col3:
            largest_category = service_costs['summary']['largest_cost_category']
            largest_cost = service_costs[largest_category]['total']
            st.metric("Largest Cost Driver", f"{largest_category.title()}: ${largest_cost:.2f}")
        
        with col4:
            # Calculate cost per vCPU
            vcpus = requirements.get('vCPUs', 2)
            cost_per_vcpu = total_monthly / vcpus if vcpus > 0 else 0
            st.metric("Cost per vCPU/month", f"${cost_per_vcpu:.2f}")
        
        # Create tabs for different technical areas with costs
tabs = st.tabs(["Single Workload", "Bulk Upload"])
        
        # Compute tab with costs
    with tech_tabs[0]:
    sw_subtabs = st.tabs(["Single Workload", "Heat Map", "Technical Recommendation"])
            st.markdown("#### 💻 Compute Single Workload & Costs")
            
            compute_recs = tech_recs['compute']
            compute_costs = service_costs['compute']
            
            # Cost overview
            st.markdown(f"**Monthly Compute Cost: ${compute_costs['total']:.2f}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Primary Instance Recommendation**")
                
                primary_instance = compute_recs['primary_instance']
                instance_data = [
                    {'Specification': 'Instance Type', 'Value': primary_instance['type']},
                    {'Specification': 'vCPUs', 'Value': str(primary_instance['vcpus'])},
                    {'Specification': 'Memory (GB)', 'Value': str(primary_instance['memory_gb'])},
                    {'Specification': 'Rationale', 'Value': primary_instance['rationale']}
                ]
                
                df_instance = pd.DataFrame(instance_data)
                st.dataframe(df_instance, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Compute Cost Breakdown**")
                
                cost_breakdown_data = []
                for service, details in compute_costs.items():
                    if service != 'total' and service != 'optimization_notes':
                        cost_breakdown_data.append({
                            'Service': service.replace('_', ' ').title(),
                            'Monthly Cost': f"${details['cost']:.2f}",
                            'Details': details['details']
                        })
                
                df_compute_costs = pd.DataFrame(cost_breakdown_data)
                st.dataframe(df_compute_costs, use_container_width=True, hide_index=True)
            
            # Deployment configuration
            st.markdown("**Deployment Single Workload**")
            
            deployment_data = [
                {'Single Workload': 'Placement Strategy', 'Recommendation': compute_recs['placement_strategy']},
                {'Single Workload': 'Auto Scaling', 'Recommendation': compute_recs['auto_scaling']},
                {'Single Workload': 'Pricing Optimization', 'Recommendation': compute_recs['pricing_optimization']}
            ]
            
            df_deployment = pd.DataFrame(deployment_data)
            st.dataframe(df_deployment, use_container_width=True, hide_index=True)
            
            # Cost optimization notes
            st.markdown("**💡 Cost Optimization Recommendations**")
            for note in compute_costs.get('optimization_notes', []):
                st.markdown(note)
        
        # Network tab with costs
        with tech_tabs[1]:
    bu_subtabs = st.tabs(["Single Workload", "Heat Map", "Technical Recommendation"])
            st.markdown("#### 🌐 Network Single Workload & Costs")
            
            network_recs = tech_recs['network']
            network_costs = service_costs['network']
            
            # Cost overview
            st.markdown(f"**Monthly Network Cost: ${network_costs['total']:.2f}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Core Network Components**")
                
                core_network_data = [
                    {'Component': 'VPC Design', 'Single Workload': network_recs['vpc_design']},
                    {'Component': 'Subnets', 'Single Workload': network_recs['subnets']},
                    {'Component': 'Security Groups', 'Single Workload': network_recs['security_groups']},
                    {'Component': 'Load Balancer', 'Single Workload': network_recs['load_balancer']}
                ]
                
                df_core_network = pd.DataFrame(core_network_data)
                st.dataframe(df_core_network, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Network Cost Breakdown**")
                
                network_cost_data = []
                for service, details in network_costs.items():
                    if service != 'total' and service != 'optimization_notes':
                        network_cost_data.append({
                            'Service': service.replace('_', ' ').title(),
                            'Monthly Cost': f"${details['cost']:.2f}",
                            'Details': details['details']
                        })
                
                df_network_costs = pd.DataFrame(network_cost_data)
                st.dataframe(df_network_costs, use_container_width=True, hide_index=True)
            
            # Advanced network services
            st.markdown("**Advanced Network Services**")
            
            advanced_network_data = [
                {'Service': 'CDN', 'Single Workload': network_recs['cdn']},
                {'Service': 'DNS', 'Single Workload': network_recs['dns']},
                {'Service': 'NAT Gateway', 'Single Workload': network_recs['nat_gateway']},
                {'Service': 'VPN', 'Single Workload': network_recs['vpn']}
            ]
            
            df_advanced_network = pd.DataFrame(advanced_network_data)
            st.dataframe(df_advanced_network, use_container_width=True, hide_index=True)
            
            # Cost optimization notes
            st.markdown("**💡 Network Cost Optimization**")
            for note in network_costs.get('optimization_notes', []):
                st.markdown(note)
        
        # Storage tab with costs
        with tech_tabs[2]:
            st.markdown("#### 💾 Storage Single Workload & Costs")
            
            storage_recs = tech_recs['storage']
            storage_costs = service_costs['storage']
            
            # Cost overview
            st.markdown(f"**Monthly Storage Cost: ${storage_costs['total']:.2f}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Primary Storage Single Workload**")
                
                storage_config_data = [
                    {'Setting': 'Storage Type', 'Value': storage_recs['primary_storage']},
                    {'Setting': 'Recommended Size', 'Value': storage_recs['recommended_size']},
                    {'Setting': 'IOPS', 'Value': storage_recs['iops_recommendation']},
                    {'Setting': 'Throughput', 'Value': storage_recs['throughput_recommendation']}
                ]
                
                df_storage_config = pd.DataFrame(storage_config_data)
                st.dataframe(df_storage_config, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Storage Cost Breakdown**")
                
                storage_cost_data = []
                for service, details in storage_costs.items():
                    if service != 'total' and service != 'optimization_notes':
                        storage_cost_data.append({
                            'Storage Type': service.replace('_', ' ').title(),
                            'Monthly Cost': f"${details['cost']:.2f}",
                            'Details': details['details']
                        })
                
                df_storage_costs = pd.DataFrame(storage_cost_data)
                st.dataframe(df_storage_costs, use_container_width=True, hide_index=True)
            
            # Data protection
            st.markdown("**Data Protection & Management**")
            
            protection_data = [
                {'Feature': 'Backup Strategy', 'Single Workload': storage_recs['backup_strategy']},
                {'Feature': 'Encryption', 'Single Workload': storage_recs['encryption']},
                {'Feature': 'Performance', 'Single Workload': storage_recs['performance']},
                {'Feature': 'Lifecycle Policy', 'Single Workload': storage_recs['lifecycle_policy']}
            ]
            
            df_protection = pd.DataFrame(protection_data)
            st.dataframe(df_protection, use_container_width=True, hide_index=True)
            
            # Cost optimization notes
            st.markdown("**💡 Storage Cost Optimization**")
            for note in storage_costs.get('optimization_notes', []):
                st.markdown(note)
        
        # Database tab with costs
        with tech_tabs[3]:
            st.markdown("#### 🗄️ Database Single Workload & Costs")
            
            db_recs = tech_recs['database']
            db_costs = service_costs['database']
            
            # Cost overview
            st.markdown(f"**Monthly Database Cost: ${db_costs['total']:.2f}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Database Engine & Instance**")
                
                db_config_data = [
                    {'Setting': 'Database Engine', 'Value': db_recs['engine']},
                    {'Setting': 'Instance Class', 'Value': db_recs['instance_class']},
                    {'Setting': 'Multi-AZ', 'Value': 'Yes' if db_recs['multi_az'] else 'No'},
                    {'Setting': 'Backup Retention', 'Value': db_recs['backup_retention']}
                ]
                
                df_db_config = pd.DataFrame(db_config_data)
                st.dataframe(df_db_config, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Database Cost Breakdown**")
                
                db_cost_data = []
                for service, details in db_costs.items():
                    if service != 'total' and service != 'optimization_notes':
                        db_cost_data.append({
                            'Database Component': service.replace('_', ' ').title(),
                            'Monthly Cost': f"${details['cost']:.2f}",
                            'Details': details['details']
                        })
                
                df_db_costs = pd.DataFrame(db_cost_data)
                st.dataframe(df_db_costs, use_container_width=True, hide_index=True)
            
            # Advanced database features
            st.markdown("**Advanced Database Features**")
            
            db_advanced_data = [
                {'Feature': 'Read Replicas', 'Single Workload': db_recs['read_replicas']},
                {'Feature': 'Connection Pooling', 'Single Workload': db_recs['connection_pooling']},
                {'Feature': 'Maintenance Window', 'Single Workload': db_recs['maintenance_window']},
                {'Feature': 'Monitoring', 'Single Workload': db_recs['monitoring']}
            ]
            
            df_db_advanced = pd.DataFrame(db_advanced_data)
            st.dataframe(df_db_advanced, use_container_width=True, hide_index=True)
            
            # Cost optimization notes
            st.markdown("**💡 Database Cost Optimization**")
            for note in db_costs.get('optimization_notes', []):
                st.markdown(note)
        
        # Security tab with costs
        with tech_tabs[4]:
            st.markdown("#### 🔒 Security Single Workload & Costs")
            
            security_recs = tech_recs['security']
            security_costs = service_costs['security']
            
            # Cost overview
            st.markdown(f"**Monthly Security Cost: ${security_costs['total']:.2f}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Security Services Single Workload**")
                
                security_data = []
                for key, value in security_recs.items():
                    security_data.append({'Security Area': key.replace('_', ' ').title(), 'Single Workload': value})
                
                df_security = pd.DataFrame(security_data)
                st.dataframe(df_security, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Security Cost Breakdown**")
                
                security_cost_data = []
                for service, details in security_costs.items():
                    if service != 'total' and service != 'optimization_notes':
                        security_cost_data.append({
                            'Security Service': service.replace('_', ' ').title(),
                            'Monthly Cost': f"${details['cost']:.2f}",
                            'Details': details['details']
                        })
                
                df_security_costs = pd.DataFrame(security_cost_data)
                st.dataframe(df_security_costs, use_container_width=True, hide_index=True)
            
            # Security best practices
            st.markdown("**Security Best Practices for this Environment:**")
            
            security_practices = [
                "🔐 Implement least privilege access principles",
                "🔍 Enable comprehensive audit logging",
                "🛡️ Use AWS Config for compliance monitoring",
                "🚨 Set up GuardDuty for threat detection",
                "📊 Regular security assessments and penetration testing"
            ]
            
            for practice in security_practices:
                st.markdown(practice)
            
            # Cost optimization notes
            st.markdown("**💡 Security Cost Optimization**")
            for note in security_costs.get('optimization_notes', []):
                st.markdown(note)
        
        # Monitoring tab with costs
        with tech_tabs[5]:
            st.markdown("#### 📊 Monitoring Single Workload & Costs")
            
            monitoring_recs = tech_recs['monitoring']
            monitoring_costs = service_costs['monitoring']
            
            # Cost overview
            st.markdown(f"**Monthly Monitoring Cost: ${monitoring_costs['total']:.2f}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Core Monitoring Setup**")
                
                monitoring_core_data = [
                    {'Component': 'CloudWatch', 'Single Workload': monitoring_recs['cloudwatch']},
                    {'Component': 'Alerting', 'Single Workload': monitoring_recs['alerting']},
                    {'Component': 'Dashboards', 'Single Workload': monitoring_recs['dashboards']},
                    {'Component': 'Log Retention', 'Single Workload': monitoring_recs['log_retention']}
                ]
                
                df_monitoring_core = pd.DataFrame(monitoring_core_data)
                st.dataframe(df_monitoring_core, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Monitoring Cost Breakdown**")
                
                monitoring_cost_data = []
                for service, details in monitoring_costs.items():
                    if service != 'total' and service != 'optimization_notes':
                        monitoring_cost_data.append({
                            'Monitoring Service': service.replace('_', ' ').title(),
                            'Monthly Cost': f"${details['cost']:.2f}",
                            'Details': details['details']
                        })
                
                df_monitoring_costs = pd.DataFrame(monitoring_cost_data)
                st.dataframe(df_monitoring_costs, use_container_width=True, hide_index=True)
            
            # Advanced monitoring services
            st.markdown("**Advanced Monitoring Services**")
            
            monitoring_advanced_data = [
                {'Service': 'APM (X-Ray)', 'Single Workload': monitoring_recs['apm']},
                {'Service': 'Synthetic Monitoring', 'Single Workload': monitoring_recs['synthetic_monitoring']},
                {'Service': 'Cost Monitoring', 'Single Workload': monitoring_recs['cost_monitoring']},
                {'Service': 'Health Checks', 'Single Workload': monitoring_recs['health_checks']}
            ]
            
            df_monitoring_advanced = pd.DataFrame(monitoring_advanced_data)
            st.dataframe(df_monitoring_advanced, use_container_width=True, hide_index=True)
            
            # Cost optimization notes
            st.markdown("**💡 Monitoring Cost Optimization**")
            for note in monitoring_costs.get('optimization_notes', []):
                st.markdown(note)
        
        # Summary recommendations
        st.markdown("---")
        st.markdown("### 📋 Implementation Summary")
        
        total_cost = service_costs['summary']['total_monthly']
        annual_cost = service_costs['summary']['total_annual']
        
        summary_recommendations = [
            f"🏗️ **Architecture:** Deploy using {tech_recs['compute']['placement_strategy'].lower()}",
            f"🔧 **Compute:** Use {tech_recs['compute']['primary_instance']['type']} instances (${compute_costs['total']:.2f}/month)",
            f"🌐 **Network:** Implement {tech_recs['network']['vpc_design'].lower()} (${network_costs['total']:.2f}/month)",
            f"💾 **Storage:** Configure {tech_recs['storage']['primary_storage']} (${storage_costs['total']:.2f}/month)",
            f"🗄️ **Database:** Deploy {tech_recs['database']['engine']} (${db_costs['total']:.2f}/month)",
            f"🔒 **Security:** Implement {len([k for k, v in security_costs.items() if isinstance(v, dict) and v.get('cost', 0) > 0])} security services (${security_costs['total']:.2f}/month)",
            f"📊 **Monitoring:** Set up comprehensive monitoring (${monitoring_costs['total']:.2f}/month)",
            f"💰 **Total Cost:** ${total_cost:.2f}/month (${annual_cost:,.2f}/year)"
        ]
        
        for rec in summary_recommendations:
            st.markdown(rec)
            
    except Exception as e:
        st.error(f"❌ Error displaying technical recommendations: {str(e)}")
        logger.error(f"Error in render_workload_recommendations: {e}")

def generate_enhanced_excel_report():
    """Generate comprehensive Excel report with multiple sheets for enhanced analysis."""
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.warning("No analysis results available for Excel generation.")
        return
    
    if not OPENPYXL_AVAILABLE:
        st.error("📊 openpyxl not available. Please install with: `pip install openpyxl`")
        return
    
    try:
        results = st.session_state.enhanced_results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        title_font = Font(bold=True, size=14)
        data_font = Font(size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        center_alignment = Alignment(horizontal='center')
        
        # Sheet 1: Executive Summary
        ws_summary = wb.create_sheet("Executive Summary")
        
        # Add title
        ws_summary['A1'] = "AWS Migration Analysis - Executive Summary"
        ws_summary['A1'].font = title_font
        ws_summary.merge_cells('A1:E1')
        
        # Add generation date
        ws_summary['A2'] = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        ws_summary['A2'].font = Font(size=11, italic=True)
        ws_summary.merge_cells('A2:E2')
        ws_summary.append([])  # Empty row
        
        # Workload information
        inputs = results['inputs']
        ws_summary.append(["Workload Information", ""])
        ws_summary.append(["Workload Name", inputs.get('workload_name', 'Unknown')])
        ws_summary.append(["Workload Type", inputs.get('workload_type', 'web_application')])
        ws_summary.append(["Operating System", inputs.get('operating_system', 'linux')])
        ws_summary.append(["AWS Region", inputs.get('region', 'us-east-1')])
        ws_summary.append([])  # Empty row
        
        # Summary data from analysis
        prod_results = results['recommendations']['PROD']
        claude_analysis = prod_results.get('claude_analysis', {})
        tco_analysis = prod_results.get('tco_analysis', {})
        
        ws_summary.append(["Analysis Summary", ""])
        ws_summary.append(["Migration Complexity", 
                          f"{claude_analysis.get('complexity_level', 'MEDIUM')} ({claude_analysis.get('complexity_score', 50):.0f}/100)"])
        ws_summary.append(["Estimated Timeline", 
                          f"{claude_analysis.get('estimated_timeline', {}).get('max_weeks', 8)} weeks"])
        ws_summary.append(["Monthly Cost (PROD)", f"${tco_analysis.get('monthly_cost', 0):,.2f}"])
        ws_summary.append(["Annual Cost (PROD)", f"${tco_analysis.get('monthly_cost', 0) * 12:,.2f}"])
        ws_summary.append(["Best Pricing Option", 
                          tco_analysis.get('best_pricing_option', 'N/A').replace('_', ' ').title()])
        ws_summary.append([])  # Empty row
        
        # Migration strategy
        strategy = claude_analysis.get('migration_strategy', {})
        ws_summary.append(["Migration Strategy", ""])
        ws_summary.append(["Approach", strategy.get('approach', 'N/A')])
        ws_summary.append(["Methodology", strategy.get('methodology', 'N/A')])
        ws_summary.append(["Risk Level", strategy.get('risk_level', 'N/A')])
        
        # Apply styles
        for row in ws_summary.iter_rows():
            for cell in row:
                cell.border = border
                if cell.row == 1:
                    cell.font = title_font
                elif cell.row in [3, 9, 17]:  # Section headers
                    cell.font = Font(bold=True)
        
        # Auto-adjust column widths
        ws_summary.column_dimensions['A'].width = 25
        ws_summary.column_dimensions['B'].width = 40
        
        # Sheet 2: Environment Comparison
        ws_env = wb.create_sheet("Environment Comparison")
        
        # Add title
        ws_env['A1'] = "Environment Comparison"
        ws_env['A1'].font = title_font
        ws_env.merge_cells('A1:G1')
        
        # Headers
        headers = ["Environment", "Complexity Score", "Instance Type", "Monthly Cost", "vCPUs", "RAM (GB)", "Storage (GB)"]
        ws_env.append(headers)
        
        # Data rows
        for env in ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']:
            env_results = results['recommendations'].get(env, {})
            claude_env_analysis = env_results.get('claude_analysis', {})
            cost_breakdown = env_results.get('cost_breakdown', {})
            selected_instance = cost_breakdown.get('selected_instance', {})
            total_costs = cost_breakdown.get('total_costs', {})
            requirements = env_results.get('requirements', {})
            
            ws_env.append([
                env,
                claude_env_analysis.get('complexity_score', 50),
                selected_instance.get('type', 'N/A'),
                total_costs.get('on_demand', 0),
                requirements.get('vCPUs', 'N/A'),
                requirements.get('RAM_GB', 'N/A'),
                requirements.get('storage_GB', 'N/A')
            ])
        
        # Apply styles
        for row in ws_env.iter_rows():
            for cell in row:
                cell.border = border
                if cell.row == 1:
                    cell.font = title_font
                elif cell.row == 2:  # Header row
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center_alignment
                elif cell.column in [2, 4]:  # Numeric columns
                    cell.number_format = '#,##0.00'
        
        # Auto-adjust column widths
        for col in range(1, len(headers) + 1):
            ws_env.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
        
        # Sheet 3: Cost Analysis
        ws_cost = wb.create_sheet("Cost Analysis")
        
        # Add title
        ws_cost['A1'] = "Cost Analysis by Environment"
        ws_cost['A1'].font = title_font
        ws_cost.merge_cells('A1:H1')
        
        # Headers
        cost_headers = ["Environment", "Compute", "Network", "Storage", "Database", "Security", "Monitoring", "Total Monthly"]
        ws_cost.append(cost_headers)
        
        # Get analyzer and calculator
        analyzer = EnhancedEnvironmentAnalyzer()
        cost_calculator = AWSCostCalculator()
        
        # Calculate costs for all environments
        for env in ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']:
            env_results = results['recommendations'].get(env, {})
            if env_results:
                tech_recs = analyzer.get_technical_recommendations(env, env_results)
                requirements = env_results.get('requirements', {})
                service_costs = cost_calculator.calculate_service_costs(env, tech_recs, requirements)
                
                ws_cost.append([
                    env,
                    service_costs['compute']['total'],
                    service_costs['network']['total'],
                    service_costs['storage']['total'],
                    service_costs['database']['total'],
                    service_costs['security']['total'],
                    service_costs['monitoring']['total'],
                    service_costs['summary']['total_monthly']
                ])
            else:
                ws_cost.append([env] + ["N/A"] * 7)
        
        # Apply styles
        for row in ws_cost.iter_rows():
            for cell in row:
                cell.border = border
                if cell.row == 1:
                    cell.font = title_font
                elif cell.row == 2:  # Header row
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center_alignment
                elif cell.row > 2 and cell.column > 1:  # Numeric columns
                    cell.number_format = '"$"#,##0.00'
        
        # Auto-adjust column widths
        for col in range(1, len(cost_headers) + 1):
            ws_cost.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
        
        # Sheet 4: Migration Recommendations
        ws_recs = wb.create_sheet("Migration Recommendations")
        
        # Add title
        ws_recs['A1'] = "Migration Recommendations"
        ws_recs['A1'].font = title_font
        ws_recs.merge_cells('A1:C1')
        
        # Migration strategy
        strategy = claude_analysis.get('migration_strategy', {})
        ws_recs.append(["Migration Strategy", ""])
        ws_recs.append(["Approach", strategy.get('approach', 'N/A')])
        ws_recs.append(["Methodology", strategy.get('methodology', 'N/A')])
        ws_recs.append(["Timeline", strategy.get('timeline', 'N/A')])
        ws_recs.append(["Risk Level", strategy.get('risk_level', 'N/A')])
        ws_recs.append([])  # Empty row
        
        # Migration steps
        migration_steps = claude_analysis.get('migration_steps', [])
        ws_recs.append(["Migration Implementation Plan", "", ""])
        ws_recs.append(["Phase", "Duration", "Key Tasks"])
        
        for step in migration_steps:
            if isinstance(step, dict):
                tasks = "\n".join(step.get('tasks', ['']))
                ws_recs.append([
                    step.get('phase', 'N/A'),
                    step.get('duration', 'N/A'),
                    tasks
                ])
        
        ws_recs.append([])  # Empty row
        
        # Recommendations
        recommendations = claude_analysis.get('recommendations', [])
        ws_recs.append(["Key Recommendations", ""])
        for i, rec in enumerate(recommendations, 1):
            ws_recs.append([f"{i}.", rec])
        
        # Apply styles and word wrap
        for row in ws_recs.iter_rows():
            for cell in row:
                cell.border = border
                if cell.row == 1:
                    cell.font = title_font
                elif cell.row in [2, 8, 8 + len(migration_steps) + 1]:  # Section headers
                    cell.font = Font(bold=True)
                if cell.column == 3:  # Tasks column
                    cell.alignment = Alignment(wrap_text=True)
        
        # Auto-adjust column widths
        ws_recs.column_dimensions['A'].width = 20
        ws_recs.column_dimensions['B'].width = 15
        ws_recs.column_dimensions['C'].width = 60
        ws_recs.row_dimensions[1].height = 30  # Title row height
        
        # Sheet 5: Technical Specifications (Production)
        ws_tech = wb.create_sheet("Technical Specifications")
        
        # Add title
        ws_tech['A1'] = "Production Environment Technical Specifications"
        ws_tech['A1'].font = title_font
        ws_tech.merge_cells('A1:D1')
        
        # Get technical recommendations
        analyzer = EnhancedEnvironmentAnalyzer()
        tech_recs = analyzer.get_technical_recommendations('PROD', prod_results)
        
        # Technical sections
        sections = [
            ("Compute Single Workload", tech_recs['compute']),
            ("Network Single Workload", tech_recs['network']),
            ("Storage Single Workload", tech_recs['storage']),
            ("Database Single Workload", tech_recs['database']),
            ("Security Single Workload", tech_recs['security']),
            ("Monitoring Single Workload", tech_recs['monitoring'])
        ]
        
        current_row = 3
        for section_name, section_data in sections:
            # Section header
            ws_tech.cell(row=current_row, column=1, value=section_name).font = Font(bold=True, size=12)
            ws_tech.merge_cells(f'A{current_row}:D{current_row}')
            current_row += 1
            
            # Section data
            for key, value in section_data.items():
                if isinstance(value, dict):
                    # Handle nested dictionaries
                    for subkey, subvalue in value.items():
                        ws_tech.cell(row=current_row, column=1, value=f"{key} - {subkey}")
                        ws_tech.cell(row=current_row, column=2, value=str(subvalue))
                        current_row += 1
                else:
                    ws_tech.cell(row=current_row, column=1, value=key)
                    ws_tech.cell(row=current_row, column=2, value=str(value))
                    current_row += 1
            
            current_row += 1  # Add space between sections
        
        # Apply borders
        for row in ws_tech.iter_rows(min_row=1, max_row=current_row-1, min_col=1, max_col=4):
            for cell in row:
                cell.border = border
        
        # Auto-adjust column widths
        ws_tech.column_dimensions['A'].width = 30
        ws_tech.column_dimensions['B'].width = 40
        
        # Save to BytesIO buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        filename = f"Enhanced_AWS_Migration_Analysis_{timestamp}.xlsx"
        
        st.download_button(
            label="⬇️ Download Excel Report",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="excel_report_download"
        )
        
        st.success("✅ Enhanced Excel report generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating Excel report: {str(e)}")
        logger.error(f"Error in Excel generation: {e}")

def export_bulk_results_to_excel(results):
    """Export bulk results to Excel."""
    if not OPENPYXL_AVAILABLE:
        st.error("📊 openpyxl not available. Please install with: `pip install openpyxl`")
        return
    
    try:
        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws_summary = wb.active
        ws_summary.title = "Summary"
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        data_font = Font(size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Add summary data
        ws_summary['A1'] = "Bulk Workload Analysis Summary"
        ws_summary['A1'].font = Font(bold=True, size=16)
        ws_summary.merge_cells('A1:D1')
        
        summary = results.get('summary', {})
        if 'error' in summary:
            ws_summary['A3'] = "Error: " + summary['error']
            ws_summary['A3'].font = Font(color="FF0000")
        else:
            # Summary metrics
            summary_data = [
                ["Total Workloads", summary.get('total_workloads_analyzed', 0)],
                ["Successful Analyses", summary.get('successful_analyses', 0)],
                ["Failed Analyses", summary.get('failed_analyses', 0)],
                ["Total Monthly Cost", f"${summary.get('total_monthly_cost', 0):,.2f}"],
                ["Total Annual Cost", f"${summary.get('total_annual_cost', 0):,.2f}"],
                ["Average Monthly Cost", f"${summary.get('average_monthly_cost', 0):,.2f}"],
                ["Average Complexity Score", f"{summary.get('average_complexity_score', 0):.1f}/100"],
                ["Most Common Instance", summary.get('most_common_instance_type', 'N/A')]
            ]
            
            # Write summary data
            for i, (metric, value) in enumerate(summary_data, 3):
                ws_summary[f'A{i}'] = metric
                ws_summary[f'B{i}'] = value
                
                if i == 3:  # Header row
                    ws_summary[f'A{i}'].font = header_font
                    ws_summary[f'A{i}'].fill = header_fill
                    ws_summary[f'B{i}'].font = header_font
                    ws_summary[f'B{i}'].fill = header_fill
                else:
                    ws_summary[f'A{i}'].font = data_font
                    ws_summary[f'B{i}'].font = data_font
                
                ws_summary[f'A{i}'].border = border
                ws_summary[f'B{i}'].border = border
        
        # Workloads sheet
        ws_workloads = wb.create_sheet("Workloads")
        
        # Headers
        headers = ["Workload", "Status", "Complexity", "Monthly Cost", "Instance Type", "Timeline (weeks)", "Migration Strategy"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws_workloads.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        # Workload data
        for row_idx, workload in enumerate(results.get('workloads', []), 2):
            if workload['status'] == 'success':
                prod_analysis = workload['analysis']['PROD']
                claude_analysis = prod_analysis.get('claude_analysis', {})
                tco_analysis = prod_analysis.get('tco_analysis', {})
                cost_breakdown = prod_analysis.get('cost_breakdown', {})
                selected_instance = cost_breakdown.get('selected_instance', {})
                
                ws_workloads.cell(row=row_idx, column=1, value=workload['workload_name'])
                ws_workloads.cell(row=row_idx, column=2, value="✅ Success")
                ws_workloads.cell(row=row_idx, column=3, value=f"{claude_analysis.get('complexity_score', 0):.0f}/100")
                ws_workloads.cell(row=row_idx, column=4, value=f"${tco_analysis.get('monthly_cost', 0):,.2f}")
                ws_workloads.cell(row=row_idx, column=5, value=selected_instance.get('type', 'N/A'))
                ws_workloads.cell(row=row_idx, column=6, value=claude_analysis.get('estimated_timeline', {}).get('max_weeks', 'N/A'))
                ws_workloads.cell(row=row_idx, column=7, value=claude_analysis.get('migration_strategy', {}).get('approach', 'N/A'))
            else:
                ws_workloads.cell(row=row_idx, column=1, value=workload['workload_name'])
                ws_workloads.cell(row=row_idx, column=2, value="❌ Failed")
                ws_workloads.cell(row=row_idx, column=3, value="N/A")
                ws_workloads.cell(row=row_idx, column=4, value="N/A")
                ws_workloads.cell(row=row_idx, column=5, value="N/A")
                ws_workloads.cell(row=row_idx, column=6, value="N/A")
                ws_workloads.cell(row=row_idx, column=7, value=workload.get('error', 'Analysis failed'))
            
            # Apply formatting
            for col_idx in range(1, len(headers) + 1):
                cell = ws_workloads.cell(row=row_idx, column=col_idx)
                cell.font = data_font
                cell.border = border
        
        # Auto-adjust column widths
        for sheet in wb:
            for column in sheet.columns:
                max_length = 0
                column_letter = openpyxl.utils.get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                sheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bulk_workload_analysis_{timestamp}.xlsx"
        
        st.download_button(
            label="⬇️ Download Excel Report",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="bulk_excel_report_download"
        )
        
        st.success("✅ Bulk Excel report generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating Excel report: {str(e)}")
        logger.error(f"Error in bulk Excel generation: {e}")

def export_bulk_results_to_pdf(results):
    """Export bulk results to PDF."""
    if not REPORTLAB_AVAILABLE:
        st.error("📄 ReportLab not available. Please install with: `pip install reportlab`")
        return
    
    try:
        # Create PDF content
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, leftMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f2937'),
            fontName='Helvetica-Bold'
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Bulk Workload Analysis Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Summary
        story.append(Paragraph("Analysis Summary", styles['Heading1']))
        
        summary = results.get('summary', {})
        if 'error' in summary:
            story.append(Paragraph(f"Error: {summary['error']}", styles['Normal']))
        else:
            summary_data = [
                ["Total Workloads", str(summary.get('total_workloads_analyzed', 0))],
                ["Successful Analyses", str(summary.get('successful_analyses', 0))],
                ["Failed Analyses", str(summary.get('failed_analyses', 0))],
                ["Total Monthly Cost", f"${summary.get('total_monthly_cost', 0):,.2f}"],
                ["Total Annual Cost", f"${summary.get('total_annual_cost', 0):,.2f}"],
                ["Average Monthly Cost", f"${summary.get('average_monthly_cost', 0):,.2f}"],
                ["Average Complexity", f"{summary.get('average_complexity_score', 0):.1f}/100"],
                ["Most Common Instance", summary.get('most_common_instance_type', 'N/A')]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('FONTSIZE', (0, 1), (-1, -1), 10)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Workloads Table
        story.append(Paragraph("Workload Analysis", styles['Heading1']))
        
        headers = ["Workload", "Status", "Complexity", "Monthly Cost", "Instance Type"]
        workload_data = [headers]
        
        for workload in results.get('workloads', []):
            if workload['status'] == 'success':
                prod_analysis = workload['analysis']['PROD']
                claude_analysis = prod_analysis.get('claude_analysis', {})
                tco_analysis = prod_analysis.get('tco_analysis', {})
                cost_breakdown = prod_analysis.get('cost_breakdown', {})
                selected_instance = cost_breakdown.get('selected_instance', {})
                
                workload_data.append([
                    workload['workload_name'],
                    "Success",
                    f"{claude_analysis.get('complexity_score', 0):.0f}/100",
                    f"${tco_analysis.get('monthly_cost', 0):,.2f}",
                    selected_instance.get('type', 'N/A')
                ])
            else:
                workload_data.append([
                    workload['workload_name'],
                    "Failed",
                    "N/A",
                    "N/A",
                    "N/A"
                ])
        
        workload_table = Table(workload_data, colWidths=[2*inch, 1*inch, 1*inch, 1.2*inch, 1.5*inch])
        workload_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#93c5fd')),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(workload_table)
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"Report generated by Enhanced AWS Migration Platform v7.0 on {datetime.now().strftime('%B %d, %Y')}"
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#6b7280'))
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bulk_workload_analysis_{timestamp}.pdf"
        
        st.download_button(
            label="⬇️ Download PDF Report",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/pdf",
            key="bulk_pdf_report_download"
        )
        
        st.success("✅ Bulk PDF report generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

def main():
    """Enhanced main application."""
    
    # Initialize session state
    initialize_enhanced_session_state()
    
    # Check if calculator is properly initialized
    if st.session_state.enhanced_calculator is None:
        st.error("⚠️ Application initialization failed. Please refresh the page.")
        if st.button("🔄 Retry Initialization", key="retry_init_button"):
            st.rerun()
        st.stop()
    
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enhanced AWS Migration Platform v7.0</h1>
        <p>Comprehensive environment analysis with real Claude AI integration, detailed technical recommendations, and AI-powered migration insights</p>
        <p style="font-size: 0.9rem; opacity: 0.9;">🤖 Now featuring real Anthropic Claude API integration for intelligent migration analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("### 🔑 Claude AI Single Workload")
        
        # Claude API Key configuration
        api_key_placeholder = st.empty()
        
        # Check if API key is available
        analyzer = ClaudeAIMigrationAnalyzer()
        api_key = analyzer._get_claude_api_key()
        
        if api_key:
            api_status = "🟢 Connected"
            api_help = "Claude AI is connected and ready for analysis"
        else:
            api_status = "🔴 Not Connected"
            api_help = "Add ANTHROPIC_API_KEY to Streamlit secrets or environment variables"
        
        with api_key_placeholder.container():
            st.markdown(f"**Status:** {api_status}")
            st.markdown(f"*{api_help}*")
            
            if not api_key:
                with st.expander("🔧 How to configure Claude API", expanded=False):
                    st.markdown("""
                    **Option 1: Streamlit Secrets (Recommended)**
                    1. Create `.streamlit/secrets.toml` file
                    2. Add: `ANTHROPIC_API_KEY = "your-api-key-here"`
                    
                    **Option 2: Environment Variable**
                    1. Set environment variable: `ANTHROPIC_API_KEY=your-api-key-here`
                    
                    **Get API Key:**
                    1. Visit [Anthropic Console](https://console.anthropic.com/)
                    2. Create account and get API key
                    3. Add to your configuration
                    """)
        
        st.markdown("---")
        
        st.markdown("### 🤖 AI + AWS Integration Status")
        
        # Integration status indicators
        claude_status = "🟢 Active" if api_key else "🟡 Fallback Mode"
        
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 8px; background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #dc2626;">🤖 Claude AI</h4>
            <p style="margin: 0; font-size: 0.875rem;">Migration Complexity Analysis</p>
            <span style="background: {'#10b981' if api_key else '#f59e0b'}; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">{claude_status}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="padding: 1rem; border-radius: 8px; background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%); margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #ea580c;">☁️ AWS Integration</h4>
            <p style="margin: 0; font-size: 0.875rem;">Real-time Cost & Instance Analysis</p>
            <span style="background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">Connected</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Enhanced features list
        st.markdown("""
        ### 🚀 Enhanced Features
        
        **🤖 Claude AI Analysis:**
        - Migration complexity scoring
        - Risk assessment & mitigation
        - Intelligent migration strategies
        - Timeline estimation
        
        **☁️ AWS Integration:**
        - Real-time pricing data
        - Instance recommendations
        - Cost optimization insights
        - Rightsizing analysis
        
        **📊 Environment Analysis:**
        - Multi-environment heat maps
        - Impact assessment across dev lifecycle
        - Environment-specific recommendations
        
        **🔧 Technical Specifications:**
        - Compute, Network, Storage configs
        - Database recommendations
        - Security & monitoring setup
        - Auto-scaling strategies
        """)
        
        # Quick stats if results available
        if st.session_state.enhanced_results:
            st.markdown("---")
            st.markdown("### 📈 Quick Stats")
            
            prod_results = st.session_state.enhanced_results['recommendations'].get('PROD', {})
            claude_analysis = prod_results.get('claude_analysis', {})
            tco_analysis = prod_results.get('tco_analysis', {})
            
            complexity_score = claude_analysis.get('complexity_score', 0)
            monthly_cost = tco_analysis.get('monthly_cost', 0)
            
            st.metric("Complexity Score", f"{complexity_score:.0f}/100")
            st.metric("Monthly Cost", f"${monthly_cost:,.0f}")
    
    # Main tabs - CORRECTED SECTION
tabs = st.tabs(["Single Workload", "Bulk Upload"])
    
    with tabs[0]:
    sw_subtabs = st.tabs(["Single Workload", "Heat Map", "Technical Recommendation"])
        render_enhanced_configuration()
    
    with tabs[1]:
    bu_subtabs = st.tabs(["Single Workload", "Heat Map", "Technical Recommendation"])
        render_bulk_upload_tab()
    
    with tabs[2]:
        render_enhanced_results()
    
    with tabs[3]:
        render_enhanced_environment_heatmap_tab()
    
    with tabs[4]:
        render_technical_recommendations_tab()
    
    with tabs[5]:
        st.markdown("### 📋 Enhanced Reports")
        
        if st.session_state.enhanced_results:
            st.markdown("#### Available Reports")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Generate PDF Report", type="primary", key="reports_pdf_generate"):
                    generate_enhanced_pdf_report()
            
            with col2:
                if st.button("📊 Export to Excel", key="reports_tab_excel"):
                    generate_enhanced_excel_report()
            
            with col3:
                if st.button("📈 Generate Heat Map CSV", key="reports_heatmap_csv"):
                    if 'heat_map_data' in st.session_state.enhanced_results:
                        csv_data = st.session_state.enhanced_results['heat_map_data'].to_csv(index=False)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            "⬇️ Download Heat Map CSV",
                            csv_data,
                            f"environment_heatmap_{timestamp}.csv",
                            "text/csv",
                            key="heatmap_csv_download"
                        )
            
            # Report preview
            st.markdown("#### Report Preview")
            
            if st.session_state.enhanced_results:
                prod_results = st.session_state.enhanced_results['recommendations']['PROD']
                claude_analysis = prod_results.get('claude_analysis', {})
                
                st.markdown("**Executive Summary Preview:**")
                
                summary_preview = f"""
                **Workload:** {st.session_state.enhanced_results['inputs']['workload_name']}
                
                **Migration Complexity:** {claude_analysis.get('complexity_level', 'MEDIUM')} ({claude_analysis.get('complexity_score', 50):.0f}/100)
                
                **Recommended Strategy:** {claude_analysis.get('migration_strategy', {}).get('approach', 'Standard Migration')}
                
                **Estimated Timeline:** {claude_analysis.get('estimated_timeline', {}).get('max_weeks', 8)} weeks
                
                **Key Recommendations:**
                """
                
                st.markdown(summary_preview)
                
                recommendations = claude_analysis.get('recommendations', [])
                for i, rec in enumerate(recommendations[:3], 1):
                    st.markdown(f"{i}. {rec}")
                
                if len(recommendations) > 3:
                    st.markdown(f"... and {len(recommendations) - 3} more recommendations in the full report")
        else:
            st.info("💡 Run an enhanced analysis to generate comprehensive reports.")
    
    # Enhanced footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <strong>Enhanced AWS Migration Platform v7.0</strong><br>
        Now powered by <strong>Real Anthropic Claude AI API</strong> for intelligent migration analysis and comprehensive technical recommendations<br>
        <em>🤖 Real AI-Enhanced • ☁️ AWS-Native • 📊 Data-Driven • 🔧 Technical-Complete • 📋 Excel/PDF Reports</em>
    </div>
    """, unsafe_allow_html=True)
if __name__ == "__main__":
    main()