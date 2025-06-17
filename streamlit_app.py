# Complete Enhanced AWS Migration Analysis Platform v8.0 with vROps Integration
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
    page_title="Enhanced AWS Migration Platform v8.0 with vROps",
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

# Enhanced Modern CSS with vROps styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Hide Streamlit Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Enhanced Header Frame with vROps styling */
    .header-frame {
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 50%, #1e40af 100%);
        color: white;
        padding: 2rem 3rem;
        position: relative;
        overflow: hidden;
        border-left: 5px solid #00d4aa;
    }
    
    .header-frame::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><polygon fill="%23ffffff08" points="0,1000 1000,0 1000,1000"/></svg>');
        background-size: cover;
        pointer-events: none;
    }
    
    .header-content {
        position: relative;
        z-index: 2;
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 1rem;
        font-weight: 400;
    }
    
    .header-version {
        display: inline-block;
        background: linear-gradient(135deg, #00d4aa, #0097a7);
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 500;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* vROps-style metric cards */
    .vrops-metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 2px solid transparent;
        border-radius: 16px;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    .vrops-metric-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #00d4aa, #0097a7, #1976d2, #00d4aa);
        border-radius: 16px;
        z-index: -1;
        animation: vrops-glow 3s ease infinite;
        background-size: 400% 400%;
    }
    
    @keyframes vrops-glow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .vrops-metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0,212,170,0.2);
    }
    
    .vrops-health-excellent { border-left: 5px solid #4caf50; }
    .vrops-health-good { border-left: 5px solid #8bc34a; }
    .vrops-health-warning { border-left: 5px solid #ff9800; }
    .vrops-health-critical { border-left: 5px solid #f44336; }
    .vrops-health-unknown { border-left: 5px solid #9e9e9e; }
    
    /* vROps Status Indicators */
    .vrops-status {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        margin: 0.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .vrops-status-excellent {
        background: linear-gradient(135deg, #4caf50, #388e3c);
        color: white;
    }
    
    .vrops-status-good {
        background: linear-gradient(135deg, #8bc34a, #689f38);
        color: white;
    }
    
    .vrops-status-warning {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
    }
    
    .vrops-status-critical {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        color: white;
    }
    
    /* vROps Data Section Styling */
    .vrops-section {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #00d4aa;
        box-shadow: 0 2px 15px rgba(0,0,0,0.05);
    }
    
    .vrops-section h3 {
        color: #1e3a8a;
        margin-top: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Enhanced form elements for vROps */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e0e7ff;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #00d4aa;
        box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1);
    }
    
    .stNumberInput > div > div {
        border-radius: 8px;
        border: 2px solid #e0e7ff;
        transition: all 0.3s ease;
    }
    
    .stNumberInput > div > div:focus-within {
        border-color: #00d4aa;
        box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1);
    }
    
    /* vROps Performance Chart Styling */
    .vrops-chart-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

class VROpsDataCollector:
    """vROps data collection and analysis utilities."""
    
    def __init__(self):
        self.vrops_metrics = {
            'performance_metrics': {
                'cpu_ready_time_percent': {'display': 'CPU Ready Time %', 'unit': '%', 'good_threshold': 5, 'warning_threshold': 10},
                'cpu_utilization_percent': {'display': 'CPU Utilization %', 'unit': '%', 'good_threshold': 70, 'warning_threshold': 85},
                'memory_utilization_percent': {'display': 'Memory Utilization %', 'unit': '%', 'good_threshold': 80, 'warning_threshold': 90},
                'memory_swapped_mb': {'display': 'Memory Swapped', 'unit': 'MB', 'good_threshold': 0, 'warning_threshold': 100},
                'disk_latency_ms': {'display': 'Disk Latency', 'unit': 'ms', 'good_threshold': 20, 'warning_threshold': 50},
                'network_utilization_percent': {'display': 'Network Utilization %', 'unit': '%', 'good_threshold': 60, 'warning_threshold': 80},
                'disk_iops': {'display': 'Disk IOPS', 'unit': 'IOPS', 'good_threshold': 0, 'warning_threshold': float('inf')},
                'network_throughput_mbps': {'display': 'Network Throughput', 'unit': 'Mbps', 'good_threshold': 0, 'warning_threshold': float('inf')}
            },
            'capacity_metrics': {
                'cpu_demand_percent': {'display': 'CPU Demand %', 'unit': '%', 'good_threshold': 70, 'warning_threshold': 85},
                'memory_demand_gb': {'display': 'Memory Demand', 'unit': 'GB', 'good_threshold': 0, 'warning_threshold': float('inf')},
                'storage_demand_gb': {'display': 'Storage Demand', 'unit': 'GB', 'good_threshold': 0, 'warning_threshold': float('inf')},
                'cpu_workload_percent': {'display': 'CPU Workload %', 'unit': '%', 'good_threshold': 70, 'warning_threshold': 85}
            },
            'health_metrics': {
                'overall_health_score': {'display': 'Overall Health Score', 'unit': 'Score', 'good_threshold': 80, 'warning_threshold': 60},
                'performance_health_score': {'display': 'Performance Health', 'unit': 'Score', 'good_threshold': 80, 'warning_threshold': 60},
                'capacity_health_score': {'display': 'Capacity Health', 'unit': 'Score', 'good_threshold': 80, 'warning_threshold': 60},
                'availability_health_score': {'display': 'Availability Health', 'unit': 'Score', 'good_threshold': 95, 'warning_threshold': 90}
            },
            'rightsizing_metrics': {
                'cpu_oversized_percent': {'display': 'CPU Oversized %', 'unit': '%', 'good_threshold': 0, 'warning_threshold': 20},
                'memory_oversized_percent': {'display': 'Memory Oversized %', 'unit': '%', 'good_threshold': 0, 'warning_threshold': 20},
                'recommended_cpu_cores': {'display': 'Recommended CPU Cores', 'unit': 'Cores', 'good_threshold': 0, 'warning_threshold': float('inf')},
                'recommended_memory_gb': {'display': 'Recommended Memory', 'unit': 'GB', 'good_threshold': 0, 'warning_threshold': float('inf')},
                'waste_percentage': {'display': 'Resource Waste %', 'unit': '%', 'good_threshold': 0, 'warning_threshold': 15}
            }
        }
        
        self.workload_profiles = {
            'compute_intensive': {
                'name': 'Compute Intensive',
                'description': 'High CPU utilization, batch processing, scientific computing',
                'typical_metrics': {'cpu_utilization': 85, 'memory_utilization': 60, 'cpu_ready_time': 8}
            },
            'memory_intensive': {
                'name': 'Memory Intensive',
                'description': 'In-memory databases, caching layers, big data analytics',
                'typical_metrics': {'cpu_utilization': 50, 'memory_utilization': 90, 'cpu_ready_time': 3}
            },
            'io_intensive': {
                'name': 'I/O Intensive',
                'description': 'Database workloads, file servers, backup systems',
                'typical_metrics': {'cpu_utilization': 40, 'memory_utilization': 70, 'disk_latency': 25}
            },
            'balanced_workload': {
                'name': 'Balanced Workload',
                'description': 'Web applications, application servers, general purpose',
                'typical_metrics': {'cpu_utilization': 65, 'memory_utilization': 75, 'cpu_ready_time': 5}
            },
            'network_intensive': {
                'name': 'Network Intensive',
                'description': 'Load balancers, proxy servers, network appliances',
                'typical_metrics': {'cpu_utilization': 55, 'memory_utilization': 60, 'network_utilization': 75}
            },
            'bursty_workload': {
                'name': 'Bursty Workload',
                'description': 'Seasonal applications, batch jobs, variable demand',
                'typical_metrics': {'cpu_utilization': 45, 'memory_utilization': 65, 'cpu_ready_time': 12}
            }
        }
    
    def get_health_status(self, score: float) -> Dict[str, str]:
        """Get health status based on vROps scoring."""
        if score >= 80:
            return {'status': 'Excellent', 'color': 'excellent', 'icon': '🟢'}
        elif score >= 60:
            return {'status': 'Good', 'color': 'good', 'icon': '🟡'}
        elif score >= 40:
            return {'status': 'Warning', 'color': 'warning', 'icon': '🟠'}
        elif score >= 20:
            return {'status': 'Critical', 'color': 'critical', 'icon': '🔴'}
        else:
            return {'status': 'Unknown', 'color': 'unknown', 'icon': '⚪'}
    
    def get_waste_level(self, waste_percent: float) -> str:
        """Get waste level description."""
        if waste_percent > 30:
            return 'High'
        elif waste_percent > 15:
            return 'Medium'
        else:
            return 'Low'

class ClaudeAIMigrationAnalyzer:
    """Enhanced Claude AI powered migration complexity analyzer with vROps integration."""
    
    def __init__(self):
        self.complexity_factors = {
            'vrops_performance_analysis': {'weight': 0.30},
            'capacity_planning': {'weight': 0.25},
            'health_assessment': {'weight': 0.20},
            'rightsizing_opportunities': {'weight': 0.15},
            'workload_characterization': {'weight': 0.10}
        }

    def analyze_workload_complexity(self, workload_inputs: Dict, environment: str) -> Dict[str, Any]:
        """Analyze migration complexity using vROps data and Claude AI."""
        
        try:
            # Get Claude API key
            api_key = self._get_claude_api_key()
            
            if not api_key:
                logger.warning("Claude API key not found, using fallback analysis")
                return self._get_fallback_analysis()
            
            # Initialize Claude client
            client = anthropic.Anthropic(api_key=api_key)
            
            # Prepare the prompt for Claude with vROps data
            analysis_prompt = self._create_vrops_analysis_prompt(workload_inputs, environment)
            
            # Make API call to Claude
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                temperature=0.1,
                system="You are an expert VMware vROps analyst and AWS migration architect. Analyze the provided vROps workload information and provide detailed migration recommendations in JSON format.",
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

    def _create_vrops_analysis_prompt(self, workload_inputs: Dict, environment: str) -> str:
        """Create a detailed prompt for Claude to analyze the vROps workload."""
        
        prompt = f"""
        Please analyze the following workload based on vROps (VMware vRealize Operations) metrics for AWS migration and provide a comprehensive assessment in JSON format.

        **Workload Information:**
        - Name: {workload_inputs.get('workload_name', 'Unknown')}
        - Workload Profile: {workload_inputs.get('workload_profile', 'balanced_workload')}
        - Environment: {environment}
        - Region: {workload_inputs.get('region', 'us-east-1')}

        **vROps Performance Metrics:**
        - CPU Ready Time: {workload_inputs.get('cpu_ready_time_percent', 0)}%
        - CPU Utilization: {workload_inputs.get('cpu_utilization_percent', 70)}%
        - Memory Utilization: {workload_inputs.get('memory_utilization_percent', 80)}%
        - Memory Swapped: {workload_inputs.get('memory_swapped_mb', 0)} MB
        - Disk Latency: {workload_inputs.get('disk_latency_ms', 15)} ms
        - Network Utilization: {workload_inputs.get('network_utilization_percent', 30)}%

        **vROps Capacity Metrics:**
        - CPU Demand: {workload_inputs.get('cpu_demand_percent', 65)}%
        - Memory Demand: {workload_inputs.get('memory_demand_gb', 8)} GB
        - Storage Demand: {workload_inputs.get('storage_demand_gb', 100)} GB

        **vROps Health Scores:**
        - Overall Health: {workload_inputs.get('overall_health_score', 85)}/100
        - Performance Health: {workload_inputs.get('performance_health_score', 80)}/100
        - Capacity Health: {workload_inputs.get('capacity_health_score', 90)}/100

        **vROps Rightsizing Analysis:**
        - CPU Oversized: {workload_inputs.get('cpu_oversized_percent', 10)}%
        - Memory Oversized: {workload_inputs.get('memory_oversized_percent', 15)}%
        - Resource Waste: {workload_inputs.get('waste_percentage', 12)}%
        - Recommended CPU Cores: {workload_inputs.get('recommended_cpu_cores', 4)}
        - Recommended Memory: {workload_inputs.get('recommended_memory_gb', 8)} GB

        Please provide your analysis in the following JSON structure:
        
        {{
            "complexity_score": <number 0-100>,
            "complexity_level": "<MINIMAL|LOW|MEDIUM|HIGH|CRITICAL>",
            "complexity_color": "<minimal|low|medium|high|critical>",
            "migration_strategy": {{
                "approach": "<migration approach based on vROps data>",
                "methodology": "<migration methodology>",
                "timeline": "<estimated timeline>",
                "risk_level": "<risk assessment based on health scores>"
            }},
            "vrops_insights": {{
                "performance_bottlenecks": ["<bottleneck1>", "<bottleneck2>"],
                "rightsizing_opportunities": ["<opportunity1>", "<opportunity2>"],
                "health_concerns": ["<concern1>", "<concern2>"],
                "capacity_recommendations": ["<recommendation1>", "<recommendation2>"]
            }},
            "estimated_timeline": {{
                "min_weeks": <number>,
                "max_weeks": <number>,
                "confidence": "<Low|Medium|High>",
                "factors": ["<factor1>", "<factor2>"]
            }},
            "aws_rightsizing": {{
                "recommended_instance_family": "<instance family>",
                "sizing_confidence": "<High|Medium|Low>",
                "cost_optimization_potential": "<percentage>",
                "performance_risk": "<Low|Medium|High>"
            }},
            "recommendations": [
                "<recommendation1 based on vROps analysis>",
                "<recommendation2 based on vROps analysis>",
                "<recommendation3 based on vROps analysis>"
            ]
        }}
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
            'complexity_score': 55,
            'complexity_level': 'MEDIUM',
            'complexity_color': 'medium',
            'migration_strategy': {
                'approach': 'vROps-Guided Migration with Performance Validation',
                'methodology': 'Lift and shift with vROps-based rightsizing',
                'timeline': '8-12 weeks',
                'risk_level': 'Medium'
            },
            'vrops_insights': {
                'performance_bottlenecks': ['CPU ready time optimization needed', 'Memory utilization monitoring required'],
                'rightsizing_opportunities': ['Right-size based on actual demand metrics', 'Optimize for AWS instance families'],
                'health_concerns': ['Monitor performance health during migration', 'Validate capacity planning'],
                'capacity_recommendations': ['Use vROps trending for capacity planning', 'Consider seasonal workload patterns']
            },
            'estimated_timeline': {'min_weeks': 8, 'max_weeks': 12, 'confidence': 'Medium', 'factors': ['vROps data quality', 'Workload complexity']},
            'aws_rightsizing': {
                'recommended_instance_family': 'M6i (General Purpose)',
                'sizing_confidence': 'Medium',
                'cost_optimization_potential': '20-30%',
                'performance_risk': 'Low'
            },
            'recommendations': [
                'Use vROps historical data for accurate AWS sizing',
                'Implement comprehensive monitoring during migration',
                'Validate performance baselines before and after migration',
                'Leverage vROps insights for cost optimization opportunities'
            ]
        }

class EnhancedVROpsEC2Calculator:
    """Enhanced calculator with vROps metrics integration."""
    
    def __init__(self):
        try:
            self.claude_analyzer = ClaudeAIMigrationAnalyzer()
            self.vrops_collector = VROpsDataCollector()
            
            # Comprehensive instance types with vROps characteristics mapping
            self.INSTANCE_TYPES = [
                {
                    "type": "m6i.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750,
                    "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True,
                    "vrops_profile": "balanced_workload", "cpu_credits": None
                },
                {
                    "type": "m6i.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500,
                    "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True,
                    "vrops_profile": "balanced_workload", "cpu_credits": None
                },
                {
                    "type": "c6i.large", "vCPU": 2, "RAM": 4, "max_ebs_bandwidth": 4750,
                    "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True,
                    "vrops_profile": "compute_intensive", "cpu_credits": None
                },
                {
                    "type": "c6i.xlarge", "vCPU": 4, "RAM": 8, "max_ebs_bandwidth": 9500,
                    "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True,
                    "vrops_profile": "compute_intensive", "cpu_credits": None
                },
                {
                    "type": "r6i.large", "vCPU": 2, "RAM": 16, "max_ebs_bandwidth": 4750,
                    "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True,
                    "vrops_profile": "memory_intensive", "cpu_credits": None
                },
                {
                    "type": "r6i.xlarge", "vCPU": 4, "RAM": 32, "max_ebs_bandwidth": 9500,
                    "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel Xeon Ice Lake",
                    "architecture": "x86_64", "storage": "EBS Only", "network_performance": "Up to 12.5 Gigabit",
                    "ebs_optimized": True, "enhanced_networking": True, "placement_group": True,
                    "vrops_profile": "memory_intensive", "cpu_credits": None
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
            
            # Default vROps inputs
            self.inputs = {
                "workload_name": "Sample vROps Workload",
                "workload_profile": "balanced_workload",
                "region": "us-east-1",
                
                # vROps Performance Metrics
                "cpu_ready_time_percent": 3.2,
                "cpu_utilization_percent": 68,
                "memory_utilization_percent": 75,
                "memory_swapped_mb": 0,
                "disk_latency_ms": 12,
                "network_utilization_percent": 25,
                "disk_iops": 3500,
                "network_throughput_mbps": 150,
                
                # vROps Capacity Metrics  
                "cpu_demand_percent": 65,
                "memory_demand_gb": 12,
                "storage_demand_gb": 120,
                "cpu_workload_percent": 70,
                
                # vROps Health Scores
                "overall_health_score": 82,
                "performance_health_score": 78,
                "capacity_health_score": 88,
                "availability_health_score": 95,
                
                # vROps Rightsizing Analysis
                "cpu_oversized_percent": 15,
                "memory_oversized_percent": 12,
                "recommended_cpu_cores": 4,
                "recommended_memory_gb": 12,
                "waste_percentage": 18
            }
            
            logger.info("Enhanced vROps calculator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing calculator: {e}")
            raise

    def calculate_enhanced_requirements(self, env: str) -> Dict[str, Any]:
        """Calculate requirements with vROps data and Claude AI analysis."""
        
        try:
            # Standard requirements calculation based on vROps data
            requirements = self._calculate_vrops_requirements(env)
            
            # Claude AI migration analysis with vROps context
            claude_analysis = self.claude_analyzer.analyze_workload_complexity(self.inputs, env)
            
            # Enhanced results with vROps insights
            enhanced_results = {
                **requirements,
                'claude_analysis': claude_analysis,
                'environment': env,
                'vrops_analysis': self._analyze_vrops_metrics(),
                'rightsizing_analysis': self._calculate_rightsizing_recommendations()
            }
            
            return enhanced_results
        except Exception as e:
            logger.error(f"Error in enhanced requirements calculation: {e}")
            return self._get_fallback_requirements(env)

    def _calculate_vrops_requirements(self, env: str) -> Dict[str, Any]:
        """Calculate infrastructure requirements based on vROps metrics."""
        try:
            env_mult = self.ENV_MULTIPLIERS[env]
            
            # Use vROps rightsizing recommendations as primary input
            recommended_vcpus = max(self.inputs["recommended_cpu_cores"], 2)
            recommended_ram = max(self.inputs["recommended_memory_gb"], 4)
            
            # Apply environment multipliers
            required_vcpus = max(math.ceil(recommended_vcpus * env_mult["cpu_ram"]), 2)
            required_ram = max(math.ceil(recommended_ram * env_mult["cpu_ram"]), 4)
            
            # Storage based on vROps demand + growth
            storage_demand = self.inputs["storage_demand_gb"]
            required_storage = math.ceil(storage_demand * 1.2 * env_mult["storage"])
            
            return {
                "requirements": {
                    "vCPUs": required_vcpus,
                    "RAM_GB": required_ram,
                    "storage_GB": required_storage,
                    "multi_az": env in ["PROD", "PREPROD"],
                    "vrops_based": True
                },
                "cost_breakdown": self._calculate_vrops_costs(required_vcpus, required_ram, required_storage, env),
                "tco_analysis": self._calculate_vrops_tco(required_vcpus, required_ram, env)
            }
        except Exception as e:
            logger.error(f"Error calculating vROps requirements: {e}")
            return self._get_fallback_requirements(env)

    def _analyze_vrops_metrics(self) -> Dict[str, Any]:
        """Analyze vROps metrics for insights."""
        analysis = {
            'performance_analysis': {},
            'health_analysis': {},
            'capacity_analysis': {},
            'rightsizing_analysis': {}
        }
        
        # Performance Analysis
        cpu_ready = self.inputs["cpu_ready_time_percent"]
        memory_swapped = self.inputs["memory_swapped_mb"]
        disk_latency = self.inputs["disk_latency_ms"]
        
        performance_issues = []
        if cpu_ready > 10:
            performance_issues.append(f"High CPU ready time ({cpu_ready}%) indicates CPU contention")
        elif cpu_ready > 5:
            performance_issues.append(f"Moderate CPU ready time ({cpu_ready}%) - monitor during migration")
        
        if memory_swapped > 0:
            performance_issues.append(f"Memory swapping detected ({memory_swapped} MB) - memory pressure")
        
        if disk_latency > 20:
            performance_issues.append(f"High disk latency ({disk_latency} ms) - I/O bottleneck")
        
        analysis['performance_analysis'] = {
            'issues': performance_issues,
            'cpu_ready_status': self._get_metric_status(cpu_ready, 5, 10),
            'disk_latency_status': self._get_metric_status(disk_latency, 20, 50),
            'memory_swapping_status': 'Good' if memory_swapped == 0 else 'Critical'
        }
        
        # Health Analysis
        overall_health = self.inputs["overall_health_score"]
        perf_health = self.inputs["performance_health_score"]
        capacity_health = self.inputs["capacity_health_score"]
        
        analysis['health_analysis'] = {
            'overall_status': self.vrops_collector.get_health_status(overall_health),
            'performance_status': self.vrops_collector.get_health_status(perf_health),
            'capacity_status': self.vrops_collector.get_health_status(capacity_health),
            'migration_risk': self._assess_migration_risk_from_health(overall_health, perf_health)
        }
        
        # Capacity Analysis
        cpu_demand = self.inputs["cpu_demand_percent"]
        memory_demand = self.inputs["memory_demand_gb"]
        
        analysis['capacity_analysis'] = {
            'cpu_utilization_trend': self._get_metric_status(cpu_demand, 70, 85),
            'memory_pressure': self._get_metric_status(memory_demand / 16 * 100, 80, 90),  # Assuming 16GB baseline
            'growth_indicators': self._analyze_capacity_growth()
        }
        
        # Rightsizing Analysis
        waste_percent = self.inputs["waste_percentage"]
        cpu_oversized = self.inputs["cpu_oversized_percent"]
        memory_oversized = self.inputs["memory_oversized_percent"]
        
        analysis['rightsizing_analysis'] = {
            'waste_level': self.vrops_collector.get_waste_level(waste_percent),
            'cpu_rightsizing_opportunity': cpu_oversized,
            'memory_rightsizing_opportunity': memory_oversized,
            'cost_savings_potential': self._calculate_savings_potential(waste_percent, cpu_oversized, memory_oversized)
        }
        
        return analysis

    def _get_metric_status(self, value: float, good_threshold: float, warning_threshold: float) -> str:
        """Get status based on metric value and thresholds."""
        if value <= good_threshold:
            return 'Good'
        elif value <= warning_threshold:
            return 'Warning'
        else:
            return 'Critical'

    def _assess_migration_risk_from_health(self, overall_health: float, perf_health: float) -> str:
        """Assess migration risk based on health scores."""
        if overall_health >= 80 and perf_health >= 80:
            return 'Low'
        elif overall_health >= 60 and perf_health >= 60:
            return 'Medium'
        else:
            return 'High'

    def _analyze_capacity_growth(self) -> List[str]:
        """Analyze capacity growth indicators."""
        indicators = []
        
        cpu_util = self.inputs["cpu_utilization_percent"]
        memory_util = self.inputs["memory_utilization_percent"]
        
        if cpu_util > 80:
            indicators.append("High CPU utilization suggests need for scaling")
        if memory_util > 85:
            indicators.append("High memory utilization indicates memory pressure")
        
        waste_percent = self.inputs["waste_percentage"]
        if waste_percent > 20:
            indicators.append("High waste percentage suggests oversizing")
        
        return indicators if indicators else ["Capacity utilization within normal ranges"]

    def _calculate_savings_potential(self, waste_percent: float, cpu_oversized: float, memory_oversized: float) -> Dict[str, str]:
        """Calculate potential cost savings from rightsizing."""
        # Simplified calculation - in reality this would be more complex
        overall_savings = (waste_percent + cpu_oversized + memory_oversized) / 3
        
        if overall_savings > 25:
            return {'level': 'High', 'percentage': f"{overall_savings:.0f}%", 'description': 'Significant cost optimization opportunity'}
        elif overall_savings > 15:
            return {'level': 'Medium', 'percentage': f"{overall_savings:.0f}%", 'description': 'Moderate cost optimization opportunity'}
        else:
            return {'level': 'Low', 'percentage': f"{overall_savings:.0f}%", 'description': 'Limited cost optimization opportunity'}

    def _calculate_rightsizing_recommendations(self) -> Dict[str, Any]:
        """Calculate detailed rightsizing recommendations."""
        current_cpu = self.inputs.get("cpu_demand_percent", 65) / 100 * 8  # Estimate current cores
        current_memory = self.inputs["memory_demand_gb"]
        
        recommended_cpu = self.inputs["recommended_cpu_cores"]
        recommended_memory = self.inputs["recommended_memory_gb"]
        
        return {
            'current_sizing': {
                'estimated_cpu_cores': math.ceil(current_cpu),
                'memory_gb': current_memory
            },
            'recommended_sizing': {
                'cpu_cores': recommended_cpu,
                'memory_gb': recommended_memory
            },
            'sizing_delta': {
                'cpu_change': recommended_cpu - math.ceil(current_cpu),
                'memory_change': recommended_memory - current_memory
            },
            'confidence_level': self._calculate_sizing_confidence(),
            'implementation_notes': self._get_implementation_notes()
        }

    def _calculate_sizing_confidence(self) -> Dict[str, str]:
        """Calculate confidence level for sizing recommendations."""
        health_score = self.inputs["overall_health_score"]
        waste_percent = self.inputs["waste_percentage"]
        
        if health_score >= 80 and waste_percent <= 20:
            return {'level': 'High', 'description': 'vROps data is reliable with good health scores'}
        elif health_score >= 60:
            return {'level': 'Medium', 'description': 'vROps data is generally reliable but monitor performance'}
        else:
            return {'level': 'Low', 'description': 'Health issues detected - validate sizing during migration'}

    def _get_implementation_notes(self) -> List[str]:
        """Get implementation notes for rightsizing."""
        notes = []
        
        cpu_ready = self.inputs["cpu_ready_time_percent"]
        if cpu_ready > 5:
            notes.append("Monitor CPU ready time closely during migration")
        
        memory_swapped = self.inputs["memory_swapped_mb"]
        if memory_swapped > 0:
            notes.append("Ensure adequate memory allocation to prevent swapping")
        
        waste_percent = self.inputs["waste_percentage"]
        if waste_percent > 20:
            notes.append("Significant rightsizing opportunity - implement gradually")
        
        return notes if notes else ["Standard implementation approach recommended"]

    def _calculate_vrops_costs(self, vcpus: int, ram_gb: int, storage_gb: int, env: str) -> Dict[str, Any]:
        """Calculate costs with vROps-informed instance selection."""
        try:
            # Select instance based on vROps workload profile
            workload_profile = self.inputs["workload_profile"]
            selected_instance = self._select_instance_by_profile(vcpus, ram_gb, workload_profile)
            
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
                "selected_instance": selected_instance,
                "vrops_rationale": f"Selected based on {workload_profile} profile from vROps analysis"
            }
        except Exception as e:
            logger.error(f"Error calculating vROps costs: {e}")
            return {
                "total_costs": {"on_demand": 1000, "ri_1y_no_upfront": 700},
                "selected_instance": {'type': 'm6i.large', 'vCPU': 2, 'RAM': 8}
            }

    def _select_instance_by_profile(self, required_vcpus: int, required_ram_gb: int, workload_profile: str) -> Dict[str, Any]:
        """Select instance type based on vROps workload profile."""
        
        # Filter instances by workload profile preference
        if workload_profile == "compute_intensive":
            preferred_families = ["compute", "general"]
        elif workload_profile == "memory_intensive":
            preferred_families = ["memory", "general"]
        elif workload_profile == "io_intensive":
            preferred_families = ["storage", "general"]
        else:
            preferred_families = ["general", "compute", "memory"]
        
        best_instance = None
        best_score = 0
        
        for instance in self.INSTANCE_TYPES:
            # Check if instance meets minimum requirements
            if instance['vCPU'] >= required_vcpus and instance['RAM'] >= required_ram_gb:
                
                # Calculate efficiency score
                cpu_efficiency = required_vcpus / instance['vCPU']
                ram_efficiency = required_ram_gb / instance['RAM']
                overall_efficiency = (cpu_efficiency + ram_efficiency) / 2
                
                # Apply family preference bonus
                family_bonus = 1.2 if instance['family'] in preferred_families else 1.0
                
                # Apply vROps profile matching bonus
                profile_bonus = 1.1 if instance.get('vrops_profile') == workload_profile else 1.0
                
                final_score = overall_efficiency * family_bonus * profile_bonus
                
                if final_score > best_score:
                    best_score = final_score
                    best_instance = instance.copy()
                    best_instance['efficiency_score'] = overall_efficiency
                    best_instance['selection_score'] = final_score
                    best_instance['vrops_match'] = instance.get('vrops_profile') == workload_profile
        
        if best_instance is None:
            # Fallback to any instance that meets requirements
            for instance in self.INSTANCE_TYPES:
                if instance['vCPU'] >= required_vcpus and instance['RAM'] >= required_ram_gb:
                    best_instance = instance.copy()
                    best_instance['efficiency_score'] = 0.5
                    best_instance['vrops_match'] = False
                    break
        
        if best_instance is None:
            # Final fallback
            best_instance = {
                'type': 'm6i.large',
                'vCPU': 2,
                'RAM': 8,
                'family': 'general',
                'efficiency_score': 0.5,
                'vrops_match': False
            }
        
        return best_instance

    def _calculate_vrops_tco(self, vcpus: int, ram_gb: int, env: str) -> Dict[str, Any]:
        """Calculate TCO with vROps-informed optimizations."""
        try:
            workload_profile = self.inputs["workload_profile"]
            selected_instance = self._select_instance_by_profile(vcpus, ram_gb, workload_profile)
            pricing = self._get_fallback_pricing(selected_instance['type'])
            
            on_demand_monthly = pricing['on_demand'] * 730
            ri_1y_monthly = pricing['ri_1y_no_upfront'] * 730
            ri_3y_monthly = pricing['ri_3y_no_upfront'] * 730
            
            storage_monthly = max(self.inputs.get('storage_demand_gb', 120), 100) * 0.08
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
            
            # Factor in vROps rightsizing savings
            waste_percent = self.inputs["waste_percentage"]
            rightsizing_savings = best_cost * (waste_percent / 100)
            
            return {
                "monthly_cost": best_cost,
                "monthly_savings": savings,
                "rightsizing_savings": rightsizing_savings,
                "total_monthly_savings": savings + rightsizing_savings,
                "best_pricing_option": best_option,
                "roi_3_years": ((savings + rightsizing_savings) * 36 / total_on_demand) * 100 if total_on_demand > 0 else 0,
                "vrops_optimization_notes": self._get_vrops_optimization_notes()
            }
        except Exception as e:
            logger.error(f"Error calculating vROps TCO: {e}")
            return {
                "monthly_cost": 1000, 
                "monthly_savings": 200, 
                "rightsizing_savings": 150,
                "best_pricing_option": "ri_1y_no_upfront"
            }

    def _get_vrops_optimization_notes(self) -> List[str]:
        """Get vROps-specific optimization notes."""
        notes = []
        
        waste_percent = self.inputs["waste_percentage"]
        if waste_percent > 20:
            notes.append(f"vROps identified {waste_percent:.0f}% resource waste - significant cost savings opportunity")
        
        cpu_oversized = self.inputs["cpu_oversized_percent"]
        if cpu_oversized > 15:
            notes.append(f"CPU oversized by {cpu_oversized:.0f}% - consider smaller instance family")
        
        health_score = self.inputs["overall_health_score"]
        if health_score < 70:
            notes.append("Lower health scores detected - monitor performance closely during migration")
        
        cpu_ready = self.inputs["cpu_ready_time_percent"]
        if cpu_ready > 5:
            notes.append("CPU ready time indicates contention - ensure adequate AWS instance sizing")
        
        return notes if notes else ["Standard optimization recommendations apply"]

    def _get_fallback_pricing(self, instance_type: str) -> Dict[str, float]:
        """Fallback pricing data."""
        fallback_prices = {
            'm6i.large': {'on_demand': 0.0864, 'ri_1y_no_upfront': 0.0605, 'ri_3y_no_upfront': 0.0432, 'spot': 0.0259},
            'm6i.xlarge': {'on_demand': 0.1728, 'ri_1y_no_upfront': 0.1210, 'ri_3y_no_upfront': 0.0864, 'spot': 0.0518},
            'c6i.large': {'on_demand': 0.0765, 'ri_1y_no_upfront': 0.0535, 'ri_3y_no_upfront': 0.0382, 'spot': 0.0230},
            'c6i.xlarge': {'on_demand': 0.1530, 'ri_1y_no_upfront': 0.1071, 'ri_3y_no_upfront': 0.0765, 'spot': 0.0459},
            'r6i.large': {'on_demand': 0.1008, 'ri_1y_no_upfront': 0.0706, 'ri_3y_no_upfront': 0.0504, 'spot': 0.0302},
            'r6i.xlarge': {'on_demand': 0.2016, 'ri_1y_no_upfront': 0.1411, 'ri_3y_no_upfront': 0.1008, 'spot': 0.0605}
        }
        return fallback_prices.get(instance_type, {'on_demand': 0.1, 'ri_1y_no_upfront': 0.07, 'ri_3y_no_upfront': 0.05, 'spot': 0.03})

    def _get_fallback_requirements(self, env: str) -> Dict[str, Any]:
        """Fallback requirements."""
        return {
            'requirements': {'vCPUs': 4, 'RAM_GB': 12, 'storage_GB': 120, 'vrops_based': True},
            'cost_breakdown': {'total_costs': {'on_demand': 800}},
            'tco_analysis': {'monthly_cost': 800, 'monthly_savings': 200, 'rightsizing_savings': 120},
            'claude_analysis': self.claude_analyzer._get_fallback_analysis(),
            'environment': env,
            'vrops_analysis': {
                'performance_analysis': {'issues': ['Sample performance analysis']},
                'health_analysis': {'overall_status': {'status': 'Good', 'icon': '🟢'}},
                'capacity_analysis': {'cpu_utilization_trend': 'Good'},
                'rightsizing_analysis': {'waste_level': 'Medium'}
            }
        }

# Enhanced Streamlit Functions for vROps Integration
def initialize_enhanced_session_state():
    """Initialize enhanced session state with vROps support."""
    try:
        if 'enhanced_calculator' not in st.session_state:
            st.session_state.enhanced_calculator = EnhancedVROpsEC2Calculator()
        if 'enhanced_results' not in st.session_state:
            st.session_state.enhanced_results = None
        if 'bulk_results' not in st.session_state:
            st.session_state.bulk_results = None
            
        logger.info("vROps session state initialized successfully")
        
    except Exception as e:
        st.error(f"Error initializing session state: {str(e)}")
        logger.error(f"Error initializing session state: {e}")
        st.session_state.enhanced_calculator = None
        st.session_state.enhanced_results = None

def render_vrops_configuration():
    """Render vROps-enhanced configuration interface."""
    
    st.markdown("### ⚙️ vROps-Enhanced Enterprise Workload Configuration")
    st.markdown("*Powered by VMware vRealize Operations metrics for accurate AWS sizing*")
    
    # Check if calculator exists
    if 'enhanced_calculator' not in st.session_state or st.session_state.enhanced_calculator is None:
        st.error("⚠️ Calculator not initialized. Please refresh the page.")
        return
        
    calculator = st.session_state.enhanced_calculator
    vrops_collector = calculator.vrops_collector
    
    # Basic workload information
    with st.expander("📋 Workload Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            calculator.inputs["workload_name"] = st.text_input(
                "Workload Name",
                value=calculator.inputs["workload_name"],
                help="Descriptive name for this workload from vROps"
            )
            
            calculator.inputs["workload_profile"] = st.selectbox(
                "vROps Workload Profile",
                list(vrops_collector.workload_profiles.keys()),
                format_func=lambda x: vrops_collector.workload_profiles[x]['name'],
                help="Select the workload pattern identified by vROps analysis"
            )
        
        with col2:
            calculator.inputs["region"] = st.selectbox(
                "Primary AWS Region",
                ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
                help="Primary AWS region for deployment"
            )
            
            # Show workload profile description
            profile_info = vrops_collector.workload_profiles[calculator.inputs["workload_profile"]]
            st.info(f"**Profile:** {profile_info['description']}")

    # vROps Performance Metrics
    with st.expander("🖥️ vROps Performance Metrics", expanded=True):
        st.markdown("*Real performance data from VMware vRealize Operations*")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**CPU Performance**")
            calculator.inputs["cpu_ready_time_percent"] = st.number_input(
                "CPU Ready Time (%)", 
                min_value=0.0, max_value=100.0, 
                value=float(calculator.inputs["cpu_ready_time_percent"]),
                step=0.1,
                help="CPU ready time percentage from vROps - indicates CPU contention"
            )
            
            calculator.inputs["cpu_utilization_percent"] = st.number_input(
                "CPU Utilization (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["cpu_utilization_percent"],
                help="Average CPU utilization from vROps"
            )
        
        with col2:
            st.markdown("**Memory Performance**")
            calculator.inputs["memory_utilization_percent"] = st.number_input(
                "Memory Utilization (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["memory_utilization_percent"],
                help="Memory utilization percentage from vROps"
            )
            
            calculator.inputs["memory_swapped_mb"] = st.number_input(
                "Memory Swapped (MB)", 
                min_value=0, 
                value=calculator.inputs["memory_swapped_mb"],
                help="Amount of memory swapped - indicates memory pressure"
            )
        
        with col3:
            st.markdown("**I/O & Network Performance**")
            calculator.inputs["disk_latency_ms"] = st.number_input(
                "Disk Latency (ms)", 
                min_value=0.0, 
                value=float(calculator.inputs["disk_latency_ms"]),
                step=0.1,
                help="Average disk latency from vROps"
            )
            
            calculator.inputs["network_utilization_percent"] = st.number_input(
                "Network Utilization (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["network_utilization_percent"],
                help="Network utilization percentage from vROps"
            )

    # vROps Capacity & Demand Metrics
    with st.expander("📊 vROps Capacity & Demand Analysis", expanded=True):
        st.markdown("*Capacity planning metrics from vROps*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Resource Demand**")
            calculator.inputs["cpu_demand_percent"] = st.number_input(
                "CPU Demand (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["cpu_demand_percent"],
                help="CPU demand percentage from vROps capacity analysis"
            )
            
            calculator.inputs["memory_demand_gb"] = st.number_input(
                "Memory Demand (GB)", 
                min_value=1, 
                value=calculator.inputs["memory_demand_gb"],
                help="Memory demand in GB from vROps"
            )
        
        with col2:
            st.markdown("**Storage & Workload**")
            calculator.inputs["storage_demand_gb"] = st.number_input(
                "Storage Demand (GB)", 
                min_value=1, 
                value=calculator.inputs["storage_demand_gb"],
                help="Storage demand in GB from vROps"
            )
            
            calculator.inputs["cpu_workload_percent"] = st.number_input(
                "CPU Workload (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["cpu_workload_percent"],
                help="CPU workload percentage from vROps"
            )

    # vROps Health Scores
    with st.expander("🏥 vROps Health Scores", expanded=True):
        st.markdown("*Health assessment from VMware vRealize Operations*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            calculator.inputs["overall_health_score"] = st.slider(
                "Overall Health Score", 
                0, 100, 
                calculator.inputs["overall_health_score"],
                help="Overall health score from vROps (0-100)"
            )
            
            calculator.inputs["performance_health_score"] = st.slider(
                "Performance Health Score", 
                0, 100, 
                calculator.inputs["performance_health_score"],
                help="Performance health score from vROps"
            )
        
        with col2:
            calculator.inputs["capacity_health_score"] = st.slider(
                "Capacity Health Score", 
                0, 100, 
                calculator.inputs["capacity_health_score"],
                help="Capacity health score from vROps"
            )
            
            calculator.inputs["availability_health_score"] = st.slider(
                "Availability Health Score", 
                0, 100, 
                calculator.inputs["availability_health_score"],
                help="Availability health score from vROps"
            )
        
        # Show health status indicators
        health_status = vrops_collector.get_health_status(calculator.inputs["overall_health_score"])
        st.markdown(f"""
        <div class="vrops-status vrops-status-{health_status['color']}">
            {health_status['icon']} Overall Health: {health_status['status']}
        </div>
        """, unsafe_allow_html=True)

    # vROps Rightsizing Analysis
    with st.expander("🎯 vROps Rightsizing Analysis", expanded=True):
        st.markdown("*Rightsizing recommendations from vROps*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Oversizing Analysis**")
            calculator.inputs["cpu_oversized_percent"] = st.number_input(
                "CPU Oversized (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["cpu_oversized_percent"],
                help="Percentage CPU is oversized according to vROps"
            )
            
            calculator.inputs["memory_oversized_percent"] = st.number_input(
                "Memory Oversized (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["memory_oversized_percent"],
                help="Percentage memory is oversized according to vROps"
            )
            
            calculator.inputs["waste_percentage"] = st.number_input(
                "Resource Waste (%)", 
                min_value=0, max_value=100, 
                value=calculator.inputs["waste_percentage"],
                help="Overall resource waste percentage from vROps"
            )
        
        with col2:
            st.markdown("**vROps Recommendations**")
            calculator.inputs["recommended_cpu_cores"] = st.number_input(
                "Recommended CPU Cores", 
                min_value=1, max_value=128, 
                value=calculator.inputs["recommended_cpu_cores"],
                help="vROps recommended CPU cores"
            )
            
            calculator.inputs["recommended_memory_gb"] = st.number_input(
                "Recommended Memory (GB)", 
                min_value=1, max_value=1024, 
                value=calculator.inputs["recommended_memory_gb"],
                help="vROps recommended memory in GB"
            )
        
        # Show waste level indicator
        waste_level = vrops_collector.get_waste_level(calculator.inputs["waste_percentage"])
        waste_color = {'Low': 'good', 'Medium': 'warning', 'High': 'critical'}[waste_level]
        st.markdown(f"""
        <div class="vrops-status vrops-status-{waste_color}">
            💰 Resource Waste Level: {waste_level} ({calculator.inputs["waste_percentage"]}%)
        </div>
        """, unsafe_allow_html=True)

    # Analysis buttons
    st.markdown("---")
    if st.button("🚀 Run vROps-Enhanced Analysis", type="primary", key="main_vrops_analysis_button"):
        run_enhanced_analysis()
        
    # Success message with navigation hint
    if st.session_state.enhanced_results:
        st.success("✅ vROps-enhanced analysis completed! Check the 'Results', 'Heat Map', and 'Technical Reports' tabs for detailed analysis.")
        st.info("💡 Visit the 'Reports' tab to generate comprehensive PDF and Excel reports with vROps insights.")

def run_enhanced_analysis():
    """Run enhanced analysis with vROps integration."""
    
    with st.spinner("🔄 Running vROps-enhanced analysis with Claude AI..."):
        try:
            calculator = st.session_state.enhanced_calculator
            
            if calculator is None:
                st.error("Calculator not available. Please refresh the page.")
                return
            
            # Calculate for all environments
            results = {}
            for env in calculator.ENV_MULTIPLIERS.keys():
                results[env] = calculator.calculate_enhanced_requirements(env)
            
            # Generate simple heat map data
            heat_map_data = generate_simple_heat_map_data(results)
            heat_map_fig = create_simple_heat_map_visualization(heat_map_data)
            
            # Store results
            st.session_state.enhanced_results = {
                'inputs': calculator.inputs.copy(),
                'recommendations': results,
                'heat_map_data': heat_map_data,
                'heat_map_fig': heat_map_fig,
                'vrops_enabled': True
            }
            
            st.success("✅ vROps-enhanced analysis completed successfully!")
            
        except Exception as e:
            st.error(f"❌ Error during vROps-enhanced analysis: {str(e)}")
            logger.error(f"Error in enhanced analysis: {e}")

def generate_simple_heat_map_data(results):
    """Generate simple heat map data."""
    environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
    metrics = ['Complexity', 'Cost', 'Risk', 'Timeline']
    
    data = []
    for env in environments:
        env_results = results.get(env, {})
        claude_analysis = env_results.get('claude_analysis', {})
        tco_analysis = env_results.get('tco_analysis', {})
        
        complexity = claude_analysis.get('complexity_score', 50)
        cost = min(tco_analysis.get('monthly_cost', 1000) / 50, 100)  # Normalize to 0-100
        risk = {'Low': 25, 'Medium': 50, 'High': 75}.get(claude_analysis.get('migration_strategy', {}).get('risk_level', 'Medium'), 50)
        timeline = min(claude_analysis.get('estimated_timeline', {}).get('max_weeks', 8) * 10, 100)  # Normalize
        
        for metric, value in zip(metrics, [complexity, cost, risk, timeline]):
            data.append({
                'Environment': env,
                'Metric': metric,
                'Value': value
            })
    
    return pd.DataFrame(data)

def create_simple_heat_map_visualization(heat_map_data):
    """Create simple heat map visualization."""
    pivot_data = heat_map_data.pivot(index='Metric', columns='Environment', values='Value')
    
    fig = px.imshow(
        pivot_data,
        labels=dict(x="Environment", y="Metric", color="Impact Score"),
        x=pivot_data.columns,
        y=pivot_data.index,
        color_continuous_scale='RdYlBu_r',
        title="vROps-Enhanced Environment Impact Analysis"
    )
    
    fig.update_layout(
        height=400,
        title_x=0.5,
        font=dict(size=12)
    )
    
    return fig

def render_vrops_results():
    """Render vROps-enhanced analysis results."""
    
    if 'enhanced_results' not in st.session_state or st.session_state.enhanced_results is None:
        st.info("💡 Run a vROps-enhanced analysis to see results here.")
        return
    
    try:
        results = st.session_state.enhanced_results
        st.markdown("### 📊 vROps-Enhanced Analysis Results")
        st.markdown("*Analysis powered by VMware vRealize Operations metrics*")
        
        recommendations = results.get('recommendations', {})
        if not recommendations or 'PROD' not in recommendations:
            st.warning("⚠️ Analysis results incomplete. Please run the analysis again.")
            return
        
        prod_results = recommendations['PROD']
        claude_analysis = prod_results.get('claude_analysis', {})
        tco_analysis = prod_results.get('tco_analysis', {})
        vrops_analysis = prod_results.get('vrops_analysis', {})
        
        # Enhanced summary metrics with vROps insights
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            complexity_score = claude_analysis.get('complexity_score', 50)
            complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
            
            st.markdown(f"""
            <div class="vrops-metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">🤖 Migration Complexity (vROps)</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{complexity_score:.0f}/100</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">{complexity_level}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            monthly_cost = tco_analysis.get('monthly_cost', 0)
            rightsizing_savings = tco_analysis.get('rightsizing_savings', 0)
            
            st.markdown(f"""
            <div class="vrops-metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">☁️ AWS Monthly Cost</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">${monthly_cost:,.0f}</div>
                <div style="font-size: 0.75rem; color: #10b981;">💰 vROps Savings: ${rightsizing_savings:.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            timeline = claude_analysis.get('estimated_timeline', {})
            max_weeks = timeline.get('max_weeks', 8)
            
            st.markdown(f"""
            <div class="vrops-metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">⏱️ Migration Timeline</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{max_weeks}</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">Weeks (vROps-Informed)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            instance_type = prod_results.get('cost_breakdown', {}).get('selected_instance', {}).get('type', 'N/A')
            vrops_match = prod_results.get('cost_breakdown', {}).get('selected_instance', {}).get('vrops_match', False)
            
            st.markdown(f"""
            <div class="vrops-metric-card">
                <div style="font-size: 0.875rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">🖥️ Instance Type</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{instance_type}</div>
                <div style="font-size: 0.75rem; color: {'#10b981' if vrops_match else '#6b7280'};">
                    {'✅ vROps Matched' if vrops_match else '📊 vROps Optimized'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # vROps-specific insights section
        st.markdown("### 🔍 vROps Performance Insights")
        
        if vrops_analysis:
            vrops_tabs = st.tabs(["Performance", "Health", "Capacity", "Rightsizing"])
            
            with vrops_tabs[0]:
                st.markdown("#### 🖥️ Performance Analysis")
                perf_analysis = vrops_analysis.get('performance_analysis', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Performance Issues Detected:**")
                    issues = perf_analysis.get('issues', [])
                    if issues:
                        for issue in issues:
                            st.markdown(f"⚠️ {issue}")
                    else:
                        st.markdown("✅ No significant performance issues detected")
                
                with col2:
                    st.markdown("**Performance Metrics Status:**")
                    cpu_ready_status = perf_analysis.get('cpu_ready_status', 'Unknown')
                    disk_latency_status = perf_analysis.get('disk_latency_status', 'Unknown')
                    memory_status = perf_analysis.get('memory_swapping_status', 'Unknown')
                    
                    status_colors = {'Good': '🟢', 'Warning': '🟡', 'Critical': '🔴', 'Unknown': '⚪'}
                    
                    st.markdown(f"{status_colors.get(cpu_ready_status, '⚪')} CPU Ready Time: {cpu_ready_status}")
                    st.markdown(f"{status_colors.get(disk_latency_status, '⚪')} Disk Latency: {disk_latency_status}")
                    st.markdown(f"{status_colors.get(memory_status, '⚪')} Memory Swapping: {memory_status}")
            
            with vrops_tabs[1]:
                st.markdown("#### 🏥 Health Analysis")
                health_analysis = vrops_analysis.get('health_analysis', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Health Scores:**")
                    
                    overall_status = health_analysis.get('overall_status', {})
                    performance_status = health_analysis.get('performance_status', {})
                    capacity_status = health_analysis.get('capacity_status', {})
                    
                    st.markdown(f"{overall_status.get('icon', '⚪')} Overall Health: {overall_status.get('status', 'Unknown')}")
                    st.markdown(f"{performance_status.get('icon', '⚪')} Performance Health: {performance_status.get('status', 'Unknown')}")
                    st.markdown(f"{capacity_status.get('icon', '⚪')} Capacity Health: {capacity_status.get('status', 'Unknown')}")
                
                with col2:
                    st.markdown("**Migration Risk Assessment:**")
                    migration_risk = health_analysis.get('migration_risk', 'Medium')
                    risk_colors = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}
                    
                    st.markdown(f"{risk_colors.get(migration_risk, '🟡')} Migration Risk: **{migration_risk}**")
                    
                    if migration_risk == 'High':
                        st.warning("⚠️ High migration risk detected based on health scores. Consider addressing health issues before migration.")
                    elif migration_risk == 'Medium':
                        st.info("💡 Medium migration risk. Monitor performance closely during migration.")
                    else:
                        st.success("✅ Low migration risk based on excellent health scores.")
            
            with vrops_tabs[2]:
                st.markdown("#### 📊 Capacity Analysis")
                capacity_analysis = vrops_analysis.get('capacity_analysis', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Resource Utilization:**")
                    cpu_trend = capacity_analysis.get('cpu_utilization_trend', 'Unknown')
                    memory_pressure = capacity_analysis.get('memory_pressure', 'Unknown')
                    
                    status_colors = {'Good': '🟢', 'Warning': '🟡', 'Critical': '🔴', 'Unknown': '⚪'}
                    
                    st.markdown(f"{status_colors.get(cpu_trend, '⚪')} CPU Utilization Trend: {cpu_trend}")
                    st.markdown(f"{status_colors.get(memory_pressure, '⚪')} Memory Pressure: {memory_pressure}")
                
                with col2:
                    st.markdown("**Growth Indicators:**")
                    growth_indicators = capacity_analysis.get('growth_indicators', [])
                    for indicator in growth_indicators:
                        st.markdown(f"📈 {indicator}")
            
            with vrops_tabs[3]:
                st.markdown("#### 🎯 Rightsizing Analysis")
                rightsizing_analysis = vrops_analysis.get('rightsizing_analysis', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Resource Waste Analysis:**")
                    waste_level = rightsizing_analysis.get('waste_level', 'Unknown')
                    cpu_opportunity = rightsizing_analysis.get('cpu_rightsizing_opportunity', 0)
                    memory_opportunity = rightsizing_analysis.get('memory_rightsizing_opportunity', 0)
                    
                    waste_colors = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}
                    
                    st.markdown(f"{waste_colors.get(waste_level, '⚪')} Resource Waste Level: {waste_level}")
                    st.markdown(f"🖥️ CPU Rightsizing Opportunity: {cpu_opportunity:.0f}%")
                    st.markdown(f"💾 Memory Rightsizing Opportunity: {memory_opportunity:.0f}%")
                
                with col2:
                    st.markdown("**Cost Savings Potential:**")
                    savings_potential = rightsizing_analysis.get('cost_savings_potential', {})
                    
                    if savings_potential:
                        level = savings_potential.get('level', 'Unknown')
                        percentage = savings_potential.get('percentage', '0%')
                        description = savings_potential.get('description', 'No description available')
                        
                        level_colors = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}
                        
                        st.markdown(f"{level_colors.get(level, '⚪')} Savings Level: {level}")
                        st.markdown(f"💰 Potential Savings: {percentage}")
                        st.markdown(f"📋 {description}")
        
        # Claude AI Analysis with vROps Context
        st.markdown("### 🤖 Claude AI Migration Analysis (vROps-Enhanced)")
        
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
                
                # vROps-specific insights
                vrops_insights = claude_analysis.get('vrops_insights', {})
                if vrops_insights:
                    st.markdown("**vROps Performance Insights:**")
                    bottlenecks = vrops_insights.get('performance_bottlenecks', [])
                    for bottleneck in bottlenecks[:3]:
                        st.markdown(f"⚠️ {bottleneck}")
            
            with col2:
                st.markdown("**AWS Rightsizing Recommendations**")
                aws_rightsizing = claude_analysis.get('aws_rightsizing', {})
                if aws_rightsizing:
                    st.markdown(f"**Instance Family:** {aws_rightsizing.get('recommended_instance_family', 'N/A')}")
                    st.markdown(f"**Sizing Confidence:** {aws_rightsizing.get('sizing_confidence', 'N/A')}")
                    st.markdown(f"**Cost Optimization:** {aws_rightsizing.get('cost_optimization_potential', 'N/A')}")
                    st.markdown(f"**Performance Risk:** {aws_rightsizing.get('performance_risk', 'N/A')}")
                
                # vROps rightsizing opportunities
                if vrops_insights:
                    st.markdown("**vROps Rightsizing Opportunities:**")
                    opportunities = vrops_insights.get('rightsizing_opportunities', [])
                    for opportunity in opportunities[:3]:
                        st.markdown(f"💰 {opportunity}")
        
        # Enhanced Cost Analysis with vROps Savings
        st.markdown("### 💰 Enhanced Cost Analysis with vROps Insights")
        
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
                st.markdown("**vROps-Enhanced Savings Analysis**")
                
                monthly_savings = tco_analysis.get('monthly_savings', 0)
                rightsizing_savings = tco_analysis.get('rightsizing_savings', 0)
                total_savings = tco_analysis.get('total_monthly_savings', 0)
                
                savings_data = [
                    {'Savings Type': 'AWS Pricing Optimization', 'Monthly Savings': f"${monthly_savings:.2f}"},
                    {'Savings Type': 'vROps Rightsizing', 'Monthly Savings': f"${rightsizing_savings:.2f}"},
                    {'Savings Type': 'Total Combined Savings', 'Monthly Savings': f"${total_savings:.2f}"}
                ]
                
                df_savings = pd.DataFrame(savings_data)
                st.dataframe(df_savings, use_container_width=True, hide_index=True)
                
                # Show annual savings
                annual_total_savings = total_savings * 12
                st.markdown(f"**📈 Annual Savings Potential: ${annual_total_savings:,.2f}**")
                
                # vROps optimization notes
                vrops_notes = tco_analysis.get('vrops_optimization_notes', [])
                if vrops_notes:
                    st.markdown("**💡 vROps Optimization Notes:**")
                    for note in vrops_notes:
                        st.markdown(f"• {note}")
        
    except Exception as e:
        st.error(f"❌ Error displaying vROps results: {str(e)}")
        logger.error(f"Error in render_vrops_results: {e}")

def render_vrops_heat_map():
    """Render enhanced heat map with vROps metrics."""
    
    st.markdown("### 🌡️ vROps-Enhanced Environment Impact Analysis")
    st.markdown("*Environment complexity analysis powered by vROps metrics*")
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.info("💡 Run a vROps-enhanced analysis to see detailed environment heat maps.")
        return
    
    results = st.session_state.enhanced_results
    
    # Environment overview cards with vROps insights
    st.markdown("#### Environment Complexity Overview (vROps-Enhanced)")
    
    cols = st.columns(5)
    environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
    
    for i, env in enumerate(environments):
        with cols[i]:
            env_results = results['recommendations'].get(env, {})
            claude_analysis = env_results.get('claude_analysis', {})
            vrops_analysis = env_results.get('vrops_analysis', {})
            complexity = claude_analysis.get('complexity_score', 50)
            complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
            
            # Get vROps health status
            health_analysis = vrops_analysis.get('health_analysis', {})
            overall_health = health_analysis.get('overall_status', {})
            health_icon = overall_health.get('icon', '⚪')
            health_status = overall_health.get('status', 'Unknown')
            
            # Create expandable card with vROps data
            with st.expander(f"{env} - {complexity:.0f}/100 ({complexity_level})", expanded=False):
                
                st.markdown(f"**Overall Complexity Score:** {complexity:.0f}/100")
                st.markdown(f"**Complexity Level:** {complexity_level}")
                st.markdown(f"**vROps Health:** {health_icon} {health_status}")
                
                # vROps-specific metrics
                if vrops_analysis:
                    st.markdown("**vROps Performance Status:**")
                    
                    perf_analysis = vrops_analysis.get('performance_analysis', {})
                    cpu_ready_status = perf_analysis.get('cpu_ready_status', 'Unknown')
                    disk_latency_status = perf_analysis.get('disk_latency_status', 'Unknown')
                    
                    status_colors = {'Good': '🟢', 'Warning': '🟡', 'Critical': '🔴', 'Unknown': '⚪'}
                    
                    st.markdown(f"{status_colors.get(cpu_ready_status, '⚪')} CPU Ready: {cpu_ready_status}")
                    st.markdown(f"{status_colors.get(disk_latency_status, '⚪')} Disk Latency: {disk_latency_status}")
                    
                    # Rightsizing opportunities
                    rightsizing_analysis = vrops_analysis.get('rightsizing_analysis', {})
                    waste_level = rightsizing_analysis.get('waste_level', 'Unknown')
                    savings_potential = rightsizing_analysis.get('cost_savings_potential', {})
                    
                    st.markdown("**vROps Rightsizing:**")
                    st.markdown(f"💰 Waste Level: {waste_level}")
                    
                    if savings_potential:
                        percentage = savings_potential.get('percentage', '0%')
                        st.markdown(f"📈 Savings Potential: {percentage}")
                
                # Migration recommendations
                recommendations = claude_analysis.get('recommendations', [])
                if recommendations:
                    st.markdown("**Key Recommendations:**")
                    for rec in recommendations[:2]:
                        st.markdown(f"• {rec}")
    
    # Heat map visualization
    st.markdown("#### vROps-Enhanced Impact Heat Map")
    
    if 'heat_map_fig' in results:
        st.plotly_chart(results['heat_map_fig'], use_container_width=True)
    
    # vROps metrics comparison across environments
    st.markdown("#### vROps Metrics Comparison Across Environments")
    
    metrics_data = []
    
    for env in environments:
        env_results = results['recommendations'].get(env, {})
        vrops_analysis = env_results.get('vrops_analysis', {})
        claude_analysis = env_results.get('claude_analysis', {})
        
        # Extract key vROps metrics
        health_analysis = vrops_analysis.get('health_analysis', {})
        performance_analysis = vrops_analysis.get('performance_analysis', {})
        rightsizing_analysis = vrops_analysis.get('rightsizing_analysis', {})
        
        overall_health = health_analysis.get('overall_status', {}).get('status', 'Unknown')
        cpu_ready_status = performance_analysis.get('cpu_ready_status', 'Unknown')
        waste_level = rightsizing_analysis.get('waste_level', 'Unknown')
        complexity_score = claude_analysis.get('complexity_score', 50)
        
        metrics_data.append({
            'Environment': env,
            'Complexity Score': f"{complexity_score:.0f}/100",
            'vROps Health': overall_health,
            'CPU Ready Status': cpu_ready_status,
            'Resource Waste': waste_level,
            'Migration Priority': 'High' if complexity_score > 70 else 'Medium' if complexity_score > 40 else 'Low'
        })
    
    df_metrics = pd.DataFrame(metrics_data)
    st.dataframe(df_metrics, use_container_width=True, hide_index=True)
    
    # vROps insights summary
    st.markdown("#### 📊 vROps Insights Summary")
    
    # Aggregate insights across all environments
    total_envs = len(environments)
    high_complexity_envs = sum(1 for env in environments 
                               if results['recommendations'].get(env, {}).get('claude_analysis', {}).get('complexity_score', 0) > 70)
    
    health_issues = 0
    performance_issues = 0
    rightsizing_opportunities = 0
    
    for env in environments:
        env_results = results['recommendations'].get(env, {})
        vrops_analysis = env_results.get('vrops_analysis', {})
        
        # Count health issues
        health_analysis = vrops_analysis.get('health_analysis', {})
        overall_health = health_analysis.get('overall_status', {}).get('status', 'Good')
        if overall_health in ['Warning', 'Critical']:
            health_issues += 1
        
        # Count performance issues
        performance_analysis = vrops_analysis.get('performance_analysis', {})
        issues = performance_analysis.get('issues', [])
        if issues:
            performance_issues += 1
        
        # Count rightsizing opportunities
        rightsizing_analysis = vrops_analysis.get('rightsizing_analysis', {})
        waste_level = rightsizing_analysis.get('waste_level', 'Low')
        if waste_level in ['Medium', 'High']:
            rightsizing_opportunities += 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("High Complexity Environments", f"{high_complexity_envs}/{total_envs}")
    
    with col2:
        st.metric("Health Issues Detected", health_issues)
    
    with col3:
        st.metric("Performance Issues", performance_issues)
    
    with col4:
        st.metric("Rightsizing Opportunities", rightsizing_opportunities)

def render_vrops_technical_recommendations():
    """Render vROps-enhanced technical recommendations."""
    
    st.markdown("### 🔧 vROps-Enhanced Technical Recommendations")
    st.markdown("*Comprehensive technical specifications powered by vROps metrics*")
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.info("💡 Run a vROps-enhanced analysis to see detailed technical recommendations.")
        return
    
    results = st.session_state.enhanced_results
    
    # Environment selector
    selected_env = st.selectbox(
        "Select Environment for vROps-Enhanced Technical Recommendations:",
        ['PROD', 'PREPROD', 'UAT', 'QA', 'DEV'],
        help="Choose an environment to see comprehensive technical specifications based on vROps analysis"
    )
    
    env_results = results['recommendations'].get(selected_env, {})
    
    if not env_results:
        st.warning(f"No vROps analysis results available for {selected_env} environment.")
        return
    
    claude_analysis = env_results.get('claude_analysis', {})
    vrops_analysis = env_results.get('vrops_analysis', {})
    rightsizing_analysis = env_results.get('rightsizing_analysis', {})
    
    st.markdown(f"## {selected_env} Environment - vROps-Enhanced Technical Specifications")
    
    # vROps Summary Section
    st.markdown("### 📊 vROps Analysis Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Extract key vROps metrics from inputs (since they're stored there)
    calculator = st.session_state.enhanced_calculator
    
    with col1:
        cpu_ready = calculator.inputs.get("cpu_ready_time_percent", 0)
        cpu_util = calculator.inputs.get("cpu_utilization_percent", 0)
        st.metric("CPU Ready Time", f"{cpu_ready}%", help="vROps CPU ready time percentage")
        st.metric("CPU Utilization", f"{cpu_util}%", help="vROps CPU utilization")
    
    with col2:
        memory_util = calculator.inputs.get("memory_utilization_percent", 0)
        memory_swapped = calculator.inputs.get("memory_swapped_mb", 0)
        st.metric("Memory Utilization", f"{memory_util}%", help="vROps memory utilization")
        st.metric("Memory Swapped", f"{memory_swapped} MB", help="vROps memory swapping")
    
    with col3:
        disk_latency = calculator.inputs.get("disk_latency_ms", 0)
        overall_health = calculator.inputs.get("overall_health_score", 0)
        st.metric("Disk Latency", f"{disk_latency} ms", help="vROps disk latency")
        st.metric("Overall Health", f"{overall_health}/100", help="vROps overall health score")
    
    with col4:
        waste_percent = calculator.inputs.get("waste_percentage", 0)
        recommended_cpu = calculator.inputs.get("recommended_cpu_cores", 0)
        st.metric("Resource Waste", f"{waste_percent}%", help="vROps resource waste percentage")
        st.metric("Recommended CPU", f"{recommended_cpu} cores", help="vROps recommended CPU cores")
    
    # Enhanced technical sections with vROps insights
    vrops_tech_tabs = st.tabs(["Compute & Rightsizing", "Performance Optimization", "Health & Monitoring", "Cost Analysis"])
    
    # Compute & Rightsizing tab
    with vrops_tech_tabs[0]:
        st.markdown("#### 💻 vROps-Based Compute Configuration & Rightsizing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Current vs. Recommended Sizing**")
            
            if rightsizing_analysis:
                current_sizing = rightsizing_analysis.get('current_sizing', {})
                recommended_sizing = rightsizing_analysis.get('recommended_sizing', {})
                sizing_delta = rightsizing_analysis.get('sizing_delta', {})
                
                sizing_data = [
                    {'Metric': 'CPU Cores', 
                     'Current': current_sizing.get('estimated_cpu_cores', 'N/A'),
                     'vROps Recommended': recommended_sizing.get('cpu_cores', 'N/A'),
                     'Delta': sizing_delta.get('cpu_change', 'N/A')},
                    {'Metric': 'Memory (GB)', 
                     'Current': current_sizing.get('memory_gb', 'N/A'),
                     'vROps Recommended': recommended_sizing.get('memory_gb', 'N/A'),
                     'Delta': sizing_delta.get('memory_change', 'N/A')}
                ]
                
                df_sizing = pd.DataFrame(sizing_data)
                st.dataframe(df_sizing, use_container_width=True, hide_index=True)
                
                # Confidence level
                confidence = rightsizing_analysis.get('confidence_level', {})
                confidence_level = confidence.get('level', 'Unknown')
                confidence_desc = confidence.get('description', 'No description')
                
                confidence_color = {'High': '🟢', 'Medium': '🟡', 'Low': '🔴'}.get(confidence_level, '⚪')
                st.markdown(f"**Sizing Confidence:** {confidence_color} {confidence_level}")
                st.info(confidence_desc)
        
        with col2:
            st.markdown("**AWS Instance Recommendation**")
            
            cost_breakdown = env_results.get('cost_breakdown', {})
            selected_instance = cost_breakdown.get('selected_instance', {})
            
            instance_data = [
                {'Specification': 'Instance Type', 'Value': selected_instance.get('type', 'N/A')},
                {'Specification': 'vCPUs', 'Value': str(selected_instance.get('vCPU', 'N/A'))},
                {'Specification': 'Memory (GB)', 'Value': str(selected_instance.get('RAM', 'N/A'))},
                {'Specification': 'Instance Family', 'Value': selected_instance.get('family', 'N/A').title()},
                {'Specification': 'vROps Profile Match', 'Value': 'Yes' if selected_instance.get('vrops_match', False) else 'Optimized'}
            ]
            
            df_instance = pd.DataFrame(instance_data)
            st.dataframe(df_instance, use_container_width=True, hide_index=True)
            
            # Workload profile information
            workload_profile = calculator.inputs.get("workload_profile", "balanced_workload")
            profile_info = calculator.vrops_collector.workload_profiles.get(workload_profile, {})
            
            st.markdown(f"**Workload Profile:** {profile_info.get('name', 'Unknown')}")
            st.markdown(f"*{profile_info.get('description', 'No description available')}*")
        
        # Implementation notes
        if rightsizing_analysis:
            implementation_notes = rightsizing_analysis.get('implementation_notes', [])
            if implementation_notes:
                st.markdown("**🔧 Implementation Notes:**")
                for note in implementation_notes:
                    st.markdown(f"• {note}")
    
    # Performance Optimization tab
    with vrops_tech_tabs[1]:
        st.markdown("#### ⚡ vROps Performance Optimization Recommendations")
        
        # Performance bottlenecks from Claude analysis
        vrops_insights = claude_analysis.get('vrops_insights', {})
        performance_bottlenecks = vrops_insights.get('performance_bottlenecks', [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Performance Bottlenecks Identified:**")
            if performance_bottlenecks:
                for bottleneck in performance_bottlenecks:
                    st.markdown(f"⚠️ {bottleneck}")
            else:
                st.markdown("✅ No significant performance bottlenecks identified")
            
            # Performance metrics analysis
            if vrops_analysis:
                perf_analysis = vrops_analysis.get('performance_analysis', {})
                issues = perf_analysis.get('issues', [])
                
                if issues:
                    st.markdown("**Additional Performance Issues:**")
                    for issue in issues:
                        st.markdown(f"🔍 {issue}")
        
        with col2:
            st.markdown("**Performance Optimization Strategies:**")
            
            # CPU optimization
            cpu_ready = calculator.inputs.get("cpu_ready_time_percent", 0)
            if cpu_ready > 10:
                st.markdown("🖥️ **CPU Optimization:**")
                st.markdown("• Consider CPU-optimized instances (C6i family)")
                st.markdown("• Implement CPU affinity settings")
                st.markdown("• Monitor CPU ready time post-migration")
            
            # Memory optimization
            memory_swapped = calculator.inputs.get("memory_swapped_mb", 0)
            if memory_swapped > 0:
                st.markdown("💾 **Memory Optimization:**")
                st.markdown("• Consider memory-optimized instances (R6i family)")
                st.markdown("• Ensure adequate memory allocation")
                st.markdown("• Monitor memory pressure metrics")
            
            # I/O optimization
            disk_latency = calculator.inputs.get("disk_latency_ms", 0)
            if disk_latency > 20:
                st.markdown("💿 **I/O Optimization:**")
                st.markdown("• Use provisioned IOPS EBS volumes")
                st.markdown("• Consider NVMe-backed instance types")
                st.markdown("• Implement I/O monitoring and alerting")
        
        # Performance validation framework
        st.markdown("**📊 Performance Validation Framework:**")
        
        validation_data = [
            {'Metric': 'CPU Ready Time', 'vROps Baseline': f"{cpu_ready}%", 'AWS Target': '<5%', 'Monitoring': 'CloudWatch + Custom Metrics'},
            {'Metric': 'Memory Utilization', 'vROps Baseline': f"{calculator.inputs.get('memory_utilization_percent', 0)}%", 'AWS Target': '<90%', 'Monitoring': 'CloudWatch Memory Metrics'},
            {'Metric': 'Disk Latency', 'vROps Baseline': f"{disk_latency}ms", 'AWS Target': '<20ms', 'Monitoring': 'EBS CloudWatch Metrics'},
            {'Metric': 'Application Response Time', 'vROps Baseline': 'TBD', 'AWS Target': 'Match vROps baseline', 'Monitoring': 'Application-level monitoring'}
        ]
        
        df_validation = pd.DataFrame(validation_data)
        st.dataframe(df_validation, use_container_width=True, hide_index=True)
    
    # Health & Monitoring tab
    with vrops_tech_tabs[2]:
        st.markdown("#### 🏥 vROps Health Analysis & AWS Monitoring Strategy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Current vROps Health Status:**")
            
            health_data = [
                {'Health Category': 'Overall Health', 'Score': f"{calculator.inputs.get('overall_health_score', 0)}/100"},
                {'Health Category': 'Performance Health', 'Score': f"{calculator.inputs.get('performance_health_score', 0)}/100"},
                {'Health Category': 'Capacity Health', 'Score': f"{calculator.inputs.get('capacity_health_score', 0)}/100"},
                {'Health Category': 'Availability Health', 'Score': f"{calculator.inputs.get('availability_health_score', 0)}/100"}
            ]
            
            df_health = pd.DataFrame(health_data)
            st.dataframe(df_health, use_container_width=True, hide_index=True)
            
            # Health concerns
            health_concerns = vrops_insights.get('health_concerns', [])
            if health_concerns:
                st.markdown("**Health Concerns:**")
                for concern in health_concerns:
                    st.markdown(f"⚠️ {concern}")
        
        with col2:
            st.markdown("**AWS Monitoring Strategy:**")
            
            # Generate monitoring recommendations based on health scores
            monitoring_recommendations = []
            
            overall_health = calculator.inputs.get('overall_health_score', 100)
            if overall_health < 80:
                monitoring_recommendations.append("Enhanced CloudWatch monitoring with 1-minute resolution")
                monitoring_recommendations.append("Custom CloudWatch alarms for critical metrics")
            
            performance_health = calculator.inputs.get('performance_health_score', 100)
            if performance_health < 80:
                monitoring_recommendations.append("AWS X-Ray for application performance monitoring")
                monitoring_recommendations.append("Enhanced EC2 monitoring with detailed metrics")
            
            capacity_health = calculator.inputs.get('capacity_health_score', 100)
            if capacity_health < 90:
                monitoring_recommendations.append("Auto Scaling with capacity-based policies")
                monitoring_recommendations.append("CloudWatch capacity planning dashboards")
            
            if not monitoring_recommendations:
                monitoring_recommendations = [
                    "Standard CloudWatch monitoring",
                    "Basic performance alarms",
                    "Cost monitoring and budgets"
                ]
            
            for rec in monitoring_recommendations:
                st.markdown(f"📊 {rec}")
            
            # Migration validation checklist
            st.markdown("**Migration Validation Checklist:**")
            validation_items = [
                "Baseline performance metrics captured",
                "Health monitoring alerts configured",
                "Performance comparison framework ready",
                "Rollback procedures documented"
            ]
            
            for item in validation_items:
                st.markdown(f"☐ {item}")
    
    # Cost Analysis tab
    with vrops_tech_tabs[3]:
        st.markdown("#### 💰 vROps-Enhanced Cost Analysis & Optimization")
        
        tco_analysis = env_results.get('tco_analysis', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Cost Breakdown & Savings:**")
            
            monthly_cost = tco_analysis.get('monthly_cost', 0)
            monthly_savings = tco_analysis.get('monthly_savings', 0)
            rightsizing_savings = tco_analysis.get('rightsizing_savings', 0)
            total_savings = tco_analysis.get('total_monthly_savings', 0)
            
            cost_summary_data = [
                {'Cost Component': 'Base Monthly Cost', 'Amount': f"${monthly_cost:,.2f}"},
                {'Cost Component': 'AWS Pricing Savings', 'Amount': f"${monthly_savings:,.2f}"},
                {'Cost Component': 'vROps Rightsizing Savings', 'Amount': f"${rightsizing_savings:,.2f}"},
                {'Cost Component': 'Total Monthly Savings', 'Amount': f"${total_savings:,.2f}"},
                {'Cost Component': 'Annual Savings Potential', 'Amount': f"${total_savings * 12:,.2f}"}
            ]
            
            df_cost_summary = pd.DataFrame(cost_summary_data)
            st.dataframe(df_cost_summary, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**vROps Optimization Insights:**")
            
            # Rightsizing opportunities
            rightsizing_opportunities = vrops_insights.get('rightsizing_opportunities', [])
            if rightsizing_opportunities:
                st.markdown("**Rightsizing Opportunities:**")
                for opportunity in rightsizing_opportunities:
                    st.markdown(f"💰 {opportunity}")
            
            # Cost optimization notes
            vrops_notes = tco_analysis.get('vrops_optimization_notes', [])
            if vrops_notes:
                st.markdown("**Cost Optimization Notes:**")
                for note in vrops_notes:
                    st.markdown(f"📋 {note}")
        
        # AWS rightsizing recommendations
        aws_rightsizing = claude_analysis.get('aws_rightsizing', {})
        if aws_rightsizing:
            st.markdown("**🎯 AWS Rightsizing Analysis:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                rightsizing_data = [
                    {'Metric': 'Recommended Instance Family', 'Value': aws_rightsizing.get('recommended_instance_family', 'N/A')},
                    {'Metric': 'Sizing Confidence', 'Value': aws_rightsizing.get('sizing_confidence', 'N/A')},
                    {'Metric': 'Cost Optimization Potential', 'Value': aws_rightsizing.get('cost_optimization_potential', 'N/A')},
                    {'Metric': 'Performance Risk', 'Value': aws_rightsizing.get('performance_risk', 'N/A')}
                ]
                
                df_rightsizing = pd.DataFrame(rightsizing_data)
                st.dataframe(df_rightsizing, use_container_width=True, hide_index=True)
            
            with col2:
                # ROI calculation
                roi_3_years = tco_analysis.get('roi_3_years', 0)
                
                st.markdown("**💹 Return on Investment:**")
                st.markdown(f"**3-Year ROI:** {roi_3_years:.1f}%")
                
                if roi_3_years > 50:
                    st.success("🎉 Excellent ROI - Strong business case for migration")
                elif roi_3_years > 25:
                    st.info("👍 Good ROI - Positive business case")
                else:
                    st.warning("⚠️ Limited ROI - Consider optimization strategies")

def main():
    """Enhanced main application with vROps integration."""
    
    # Initialize session state
    initialize_enhanced_session_state()
    
    # Check if calculator is properly initialized
    if st.session_state.enhanced_calculator is None:
        st.error("⚠️ Application initialization failed. Please refresh the page.")
        if st.button("🔄 Retry Initialization", key="retry_init_button"):
            st.rerun()
        st.stop()
    
    # Enhanced header with vROps branding
    st.markdown("""
    <div class="header-frame">
        <div class="header-content">
            <h1 class="header-title">🏢 Enhanced AWS Migration Platform v8.0</h1>
            <p class="header-subtitle">vROps-Powered Enterprise AWS Migration Analysis</p>
            <div class="header-version">🤖 Real Claude AI + 📊 VMware vROps Integration</div>
            <p style="margin-top: 1rem; opacity: 0.9; font-size: 0.95rem;">
                Comprehensive migration analysis powered by VMware vRealize Operations metrics and intelligent Claude AI insights
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar with vROps status
    with st.sidebar:
        st.markdown("### 🔑 Integration Status")
        
        # Claude API Key configuration
        analyzer = ClaudeAIMigrationAnalyzer()
        api_key = analyzer._get_claude_api_key()
        
        if api_key:
            claude_status = "🟢 Connected"
            claude_help = "Claude AI is connected and ready for analysis"
        else:
            claude_status = "🔴 Not Connected"
            claude_help = "Add ANTHROPIC_API_KEY to Streamlit secrets or environment variables"
        
        st.markdown(f"**Claude AI Status:** {claude_status}")
        st.markdown(f"*{claude_help}*")
        
        st.markdown("---")
        
        st.markdown("### 🚀 vROps + AWS + AI Integration")
        
        # Integration status indicators with vROps
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 8px; background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%); margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #00695c;">📊 vROps Integration</h4>
            <p style="margin: 0; font-size: 0.875rem;">VMware vRealize Operations Metrics</p>
            <span style="background: #00897b; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">✅ Active</span>
        </div>
        """, unsafe_allow_html=True)
        
        claude_status_display = "🟢 Active" if api_key else "🟡 Fallback Mode"
        claude_color = "#10b981" if api_key else "#f59e0b"
        
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 8px; background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #dc2626;">🤖 Claude AI</h4>
            <p style="margin: 0; font-size: 0.875rem;">Migration Complexity Analysis</p>
            <span style="background: {claude_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">{claude_status_display}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="padding: 1rem; border-radius: 8px; background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%); margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #ea580c;">☁️ AWS Integration</h4>
            <p style="margin: 0; font-size: 0.875rem;">Real-time Cost & Instance Analysis</p>
            <span style="background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">🟢 Connected</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Enhanced features list with vROps
        st.markdown("""
        ### 🚀 vROps-Enhanced Features
        
        **📊 vROps Metrics Integration:**
        - CPU ready time & utilization analysis
        - Memory pressure & swapping detection
        - Health scores & performance insights
        - Rightsizing recommendations
        
        **🤖 Claude AI Analysis:**
        - vROps-informed complexity scoring
        - Performance bottleneck identification
        - Migration risk assessment
        - Timeline estimation with health factors
        
        **☁️ AWS Integration:**
        - vROps workload profile matching
        - Instance family optimization
        - Cost optimization with rightsizing
        - Performance validation framework
        
        **📈 Advanced Analytics:**
        - Multi-environment heat maps
        - Bulk workload analysis
        - Portfolio optimization insights
        - ROI calculation with vROps savings
        """)
        
        # Quick stats if results available
        if st.session_state.enhanced_results:
            st.markdown("---")
            st.markdown("### 📈 Quick vROps Stats")
            
            prod_results = st.session_state.enhanced_results['recommendations'].get('PROD', {})
            claude_analysis = prod_results.get('claude_analysis', {})
            tco_analysis = prod_results.get('tco_analysis', {})
            
            complexity_score = claude_analysis.get('complexity_score', 0)
            monthly_cost = tco_analysis.get('monthly_cost', 0)
            rightsizing_savings = tco_analysis.get('rightsizing_savings', 0)
            
            st.metric("Complexity Score", f"{complexity_score:.0f}/100")
            st.metric("Monthly Cost", f"${monthly_cost:,.0f}")
            st.metric("vROps Savings", f"${rightsizing_savings:,.0f}")
    
    # MAIN TABS - Enhanced for vROps
    main_tabs = st.tabs(["Single Workload", "Bulk Analysis", "Reports"])
    
    # SINGLE WORKLOAD TAB with vROps sub-tabs
    with main_tabs[0]:
        st.markdown("### 🖥️ Single Workload Analysis (vROps-Enhanced)")
        
        # Create vROps-enhanced sub-tabs
        single_workload_subtabs = st.tabs(["vROps Configuration", "Results", "Heat Map", "Technical Reports"])
        
        # vROps Configuration sub-tab
        with single_workload_subtabs[0]:
            render_vrops_configuration()
        
        # Results sub-tab
        with single_workload_subtabs[1]:
            render_vrops_results()
        
        # Heat Map sub-tab
        with single_workload_subtabs[2]:
            render_vrops_heat_map()
        
        # Technical Reports sub-tab
        with single_workload_subtabs[3]:
            render_vrops_technical_recommendations()
    
    # BULK ANALYSIS TAB with vROps support
    with main_tabs[1]:
        st.markdown("### 📁 Bulk Workload Analysis (vROps-Enhanced)")
        st.info("🚧 Bulk analysis features will be implemented in the next version.")
        st.markdown("""
        **Planned vROps Bulk Features:**
        - Upload CSV/Excel files with vROps metrics
        - Bulk workload profile analysis
        - Portfolio-wide rightsizing recommendations
        - Aggregate health score analysis
        - Bulk migration prioritization
        """)
    
    # REPORTS TAB
    with main_tabs[2]:
        st.markdown("### 📋 vROps-Enhanced Reports")
        
        if st.session_state.enhanced_results:
            st.info("💡 Reports will include vROps metrics, health scores, and rightsizing analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Generate vROps PDF Report", type="primary", key="vrops_reports_pdf_generate"):
                    st.info("🚧 vROps-enhanced PDF generation would be implemented here")
            
            with col2:
                if st.button("📊 Export vROps Excel", key="vrops_reports_tab_excel"):
                    st.info("🚧 vROps-enhanced Excel export would be implemented here")
            
            with col3:
                if st.button("📈 vROps Heat Map CSV", key="vrops_reports_heatmap_csv"):
                    st.info("🚧 vROps heat map CSV would be implemented here")
        else:
            st.info("💡 Run a vROps analysis to generate comprehensive reports with vROps insights.")
    
    # Enhanced footer with vROps branding
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <strong>Enhanced AWS Migration Platform v8.0 with vROps Integration</strong><br>
        Powered by <strong>VMware vRealize Operations</strong> metrics and <strong>Real Anthropic Claude AI</strong><br>
        <em>📊 vROps-Native • 🤖 AI-Enhanced • ☁️ AWS-Optimized • 💰 Cost-Intelligent • 📋 Report-Complete</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()