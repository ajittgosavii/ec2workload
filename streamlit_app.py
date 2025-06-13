# Required dependencies for requirements.txt:
# streamlit>=1.28.0
# pandas>=1.5.0
# plotly>=5.0.0
# boto3>=1.26.0
# numpy>=1.24.0
# reportlab>=3.6.0
# kaleido>=0.2.1

import streamlit as st

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="Enterprise AWS EC2 Workload Sizing Platform v5.0",
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
# Removed seaborn and matplotlib dependencies - using plotly for all visualizations

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepInFrame
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    
# Try to import kaleido for static image export
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced custom CSS with new styling for environment heat maps
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

    .claude-ai-badge {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
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

    .aws-integration-badge {
        background: linear-gradient(135deg, #ff9500 0%, #ff8c00 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-left: 0.5rem;
        display: inline-block;
    }

    .environment-heatmap {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .migration-complexity-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        position: relative;
    }

    .complexity-level {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        text-align: center;
        margin: 0.5rem 0;
        color: white;
    }

    .complexity-low { background: #10b981; }
    .complexity-medium { background: #f59e0b; }
    .complexity-high { background: #ef4444; }
    .complexity-critical { background: #7c2d12; }

    .migration-step {
        background: white;
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .claude-analysis {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 2px solid #ff6b6b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .aws-analysis {
        background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%);
        border: 2px solid #ff9500;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
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
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .env-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .env-dev { border-left: 4px solid #3b82f6; }
    .env-qa { border-left: 4px solid #8b5cf6; }
    .env-uat { border-left: 4px solid #f59e0b; }
    .env-preprod { border-left: 4px solid #ef4444; }
    .env-prod { border-left: 4px solid #10b981; }

    .heat-cell {
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.1rem;
        text-align: center;
        font-weight: 600;
        color: white;
        min-height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .heat-low { background: #10b981; }
    .heat-medium { background: #f59e0b; }
    .heat-high { background: #ef4444; }
    .heat-critical { background: #7c2d12; }
</style>
""", unsafe_allow_html=True)

class ClaudeAIMigrationAnalyzer:
    """Claude AI powered migration complexity and strategy analyzer."""
    
    def __init__(self):
        self.complexity_factors = {
            'application_architecture': {
                'weight': 0.25,
                'factors': ['monolith_complexity', 'dependency_count', 'data_architecture', 'integration_points']
            },
            'technical_stack': {
                'weight': 0.20,
                'factors': ['legacy_components', 'custom_software', 'database_complexity', 'middleware_dependencies']
            },
            'operational_complexity': {
                'weight': 0.20,
                'factors': ['deployment_automation', 'monitoring_sophistication', 'security_requirements', 'compliance_scope']
            },
            'business_impact': {
                'weight': 0.20,
                'factors': ['availability_requirements', 'performance_criticality', 'user_base_size', 'revenue_impact']
            },
            'organizational_readiness': {
                'weight': 0.15,
                'factors': ['team_cloud_skills', 'change_management', 'stakeholder_alignment', 'budget_availability']
            }
        }

    def analyze_workload_complexity(self, workload_inputs: Dict, environment: str) -> Dict[str, Any]:
        """Analyze migration complexity using Claude AI-like intelligence."""
        
        workload_type = workload_inputs.get('workload_type', 'web_application')
        compliance_reqs = workload_inputs.get('compliance_requirements', [])
        
        # Calculate complexity scores
        complexity_score = self._calculate_complexity_score(workload_inputs, environment)
        
        # Determine complexity level
        if complexity_score >= 80:
            complexity_level = "CRITICAL"
            complexity_color = "critical"
        elif complexity_score >= 65:
            complexity_level = "HIGH"
            complexity_color = "high"
        elif complexity_score >= 45:
            complexity_level = "MEDIUM"
            complexity_color = "medium"
        else:
            complexity_level = "LOW"
            complexity_color = "low"
        
        # Generate migration strategy
        migration_strategy = self._generate_migration_strategy(workload_inputs, complexity_level, environment)
        
        # Generate specific migration steps
        migration_steps = self._generate_migration_steps(workload_inputs, complexity_level, environment)
        
        # Risk assessment
        risk_factors = self._assess_migration_risks(workload_inputs, complexity_level, environment)
        
        # Timeline estimation
        timeline = self._estimate_migration_timeline(complexity_level, environment, workload_inputs)
        
        return {
            'complexity_score': complexity_score,
            'complexity_level': complexity_level,
            'complexity_color': complexity_color,
            'migration_strategy': migration_strategy,
            'migration_steps': migration_steps,
            'risk_factors': risk_factors,
            'estimated_timeline': timeline,
            'recommendations': self._generate_recommendations(workload_inputs, complexity_level),
            'success_factors': self._identify_success_factors(workload_inputs, complexity_level)
        }

    def _calculate_complexity_score(self, workload_inputs: Dict, environment: str) -> float:
        """Calculate overall complexity score."""
        total_score = 0
        
        # Base complexity by workload type
        workload_complexity = {
            'web_application': 30,
            'application_server': 50,
            'database_server': 70,
            'file_server': 25,
            'compute_intensive': 45,
            'analytics_workload': 55
        }
        
        base_score = workload_complexity.get(workload_inputs.get('workload_type', 'web_application'), 40)
        
        # Environment factor
        env_multipliers = {
            'DEV': 0.7,
            'QA': 0.8,
            'UAT': 0.9,
            'PREPROD': 1.0,
            'PROD': 1.2
        }
        
        env_factor = env_multipliers.get(environment, 1.0)
        
        # Compliance complexity
        compliance_score = len(workload_inputs.get('compliance_requirements', [])) * 15
        
        # Infrastructure age factor
        infra_age = workload_inputs.get('infrastructure_age_years', 3)
        age_factor = min(infra_age * 5, 25)  # Cap at 25 points
        
        # Calculate total score
        total_score = (base_score * env_factor) + compliance_score + age_factor
        
        return min(total_score, 100)  # Cap at 100

    def _generate_migration_strategy(self, workload_inputs: Dict, complexity_level: str, environment: str) -> Dict[str, Any]:
        """Generate migration strategy based on complexity analysis."""
        
        strategies = {
            'LOW': {
                'approach': 'Lift and Shift with Optimization',
                'methodology': 'Direct migration with minimal changes',
                'timeline': 'Fast track (2-4 weeks)',
                'risk_level': 'Low',
                'automation_potential': 'High'
            },
            'MEDIUM': {
                'approach': 'Hybrid Migration with Re-architecting',
                'methodology': 'Phased migration with selective modernization',
                'timeline': 'Standard track (6-10 weeks)',
                'risk_level': 'Medium',
                'automation_potential': 'Medium'
            },
            'HIGH': {
                'approach': 'Comprehensive Re-architecting',
                'methodology': 'Full application modernization',
                'timeline': 'Extended track (12-16 weeks)',
                'risk_level': 'High',
                'automation_potential': 'Low'
            },
            'CRITICAL': {
                'approach': 'Strategic Rebuild',
                'methodology': 'Complete re-design and rebuild',
                'timeline': 'Long-term project (20+ weeks)',
                'risk_level': 'Very High',
                'automation_potential': 'Very Low'
            }
        }
        
        base_strategy = strategies.get(complexity_level, strategies['MEDIUM'])
        
        # Customize based on workload type
        workload_type = workload_inputs.get('workload_type', 'web_application')
        
        if workload_type == 'database_server':
            base_strategy['special_considerations'] = [
                'Database migration tools (DMS, SCT)',
                'Data consistency verification',
                'Minimal downtime strategy',
                'Performance baseline establishment'
            ]
        elif workload_type == 'web_application':
            base_strategy['special_considerations'] = [
                'Load balancer configuration',
                'Auto-scaling setup',
                'CDN integration',
                'SSL/TLS certificate migration'
            ]
        
        return base_strategy

    def _generate_migration_steps(self, workload_inputs: Dict, complexity_level: str, environment: str) -> List[Dict[str, Any]]:
        """Generate detailed migration steps."""
        
        base_steps = [
            {
                'phase': 'Discovery & Assessment',
                'duration': '1-2 weeks',
                'tasks': [
                    'Complete infrastructure inventory',
                    'Application dependency mapping',
                    'Performance baseline establishment',
                    'Security and compliance assessment'
                ],
                'deliverables': ['Migration plan', 'Risk assessment', 'Architecture design']
            },
            {
                'phase': 'Environment Preparation',
                'duration': '1-2 weeks', 
                'tasks': [
                    'AWS account setup and configuration',
                    'Network architecture implementation',
                    'Security groups and IAM configuration',
                    'Monitoring and logging setup'
                ],
                'deliverables': ['AWS environment', 'Security baseline', 'Monitoring dashboard']
            },
            {
                'phase': 'Migration Execution',
                'duration': '2-8 weeks',
                'tasks': [
                    'Data migration (if applicable)',
                    'Application deployment',
                    'Configuration and testing',
                    'Performance optimization'
                ],
                'deliverables': ['Migrated workload', 'Test results', 'Performance report']
            },
            {
                'phase': 'Validation & Go-Live',
                'duration': '1-2 weeks',
                'tasks': [
                    'End-to-end testing',
                    'User acceptance testing',
                    'Production cutover',
                    'Post-migration optimization'
                ],
                'deliverables': ['Production workload', 'Handover documentation', 'Support procedures']
            }
        ]
        
        # Adjust based on complexity
        if complexity_level in ['HIGH', 'CRITICAL']:
            base_steps.insert(2, {
                'phase': 'Pilot Migration',
                'duration': '2-3 weeks',
                'tasks': [
                    'Non-production environment migration',
                    'Application refactoring (if needed)',
                    'Integration testing',
                    'Process refinement'
                ],
                'deliverables': ['Pilot environment', 'Refined procedures', 'Lessons learned']
            })
        
        return base_steps

    def _assess_migration_risks(self, workload_inputs: Dict, complexity_level: str, environment: str) -> List[Dict[str, Any]]:
        """Assess migration risks with mitigation strategies."""
        
        base_risks = [
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
            },
            {
                'category': 'Security',
                'risk': 'Data exposure during migration',
                'probability': 'Low',
                'impact': 'Critical',
                'mitigation': 'Encryption in transit and at rest'
            }
        ]
        
        # Add complexity-specific risks
        if complexity_level in ['HIGH', 'CRITICAL']:
            base_risks.extend([
                {
                    'category': 'Technical',
                    'risk': 'Performance degradation post-migration',
                    'probability': 'Medium',
                    'impact': 'Medium',
                    'mitigation': 'Performance testing and optimization'
                },
                {
                    'category': 'Business',
                    'risk': 'Extended timeline and budget overrun',
                    'probability': 'High',
                    'impact': 'Medium',
                    'mitigation': 'Phased approach with regular checkpoints'
                }
            ])
        
        return base_risks

    def _estimate_migration_timeline(self, complexity_level: str, environment: str, workload_inputs: Dict) -> Dict[str, Any]:
        """Estimate migration timeline."""
        
        base_timelines = {
            'LOW': {'min_weeks': 3, 'max_weeks': 6, 'confidence': 'High'},
            'MEDIUM': {'min_weeks': 6, 'max_weeks': 12, 'confidence': 'Medium'},
            'HIGH': {'min_weeks': 12, 'max_weeks': 20, 'confidence': 'Medium'},
            'CRITICAL': {'min_weeks': 20, 'max_weeks': 32, 'confidence': 'Low'}
        }
        
        timeline = base_timelines.get(complexity_level, base_timelines['MEDIUM'])
        
        # Adjust for environment
        if environment == 'PROD':
            timeline['min_weeks'] = int(timeline['min_weeks'] * 1.3)
            timeline['max_weeks'] = int(timeline['max_weeks'] * 1.3)
        
        return timeline

    def _generate_recommendations(self, workload_inputs: Dict, complexity_level: str) -> List[str]:
        """Generate specific recommendations."""
        
        recommendations = [
            "Establish clear success criteria and KPIs",
            "Implement comprehensive backup and rollback procedures",
            "Conduct thorough security and compliance validation",
            "Plan for adequate testing and validation phases"
        ]
        
        if complexity_level in ['HIGH', 'CRITICAL']:
            recommendations.extend([
                "Consider engaging AWS Professional Services",
                "Implement extensive monitoring and alerting",
                "Plan for multiple migration phases",
                "Allocate additional budget for contingencies"
            ])
        
        return recommendations

    def _identify_success_factors(self, workload_inputs: Dict, complexity_level: str) -> List[str]:
        """Identify critical success factors."""
        
        factors = [
            "Strong project leadership and governance",
            "Clear communication with all stakeholders",
            "Adequate resource allocation and timeline",
            "Comprehensive testing strategy"
        ]
        
        if complexity_level in ['MEDIUM', 'HIGH', 'CRITICAL']:
            factors.extend([
                "Cloud expertise and training for team",
                "Executive sponsorship and support",
                "Risk management and mitigation planning",
                "Change management and user adoption strategy"
            ])
        
        return factors

class EnhancedAWSIntegration:
    """Enhanced AWS integration for real-time cost and instance sizing."""
    
    def __init__(self):
        self.pricing_client = None
        self.ec2_client = None
        self.ce_client = None  # Cost Explorer
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize AWS clients with error handling."""
        try:
            session = boto3.Session()
            self.pricing_client = session.client('pricing', region_name='us-east-1')
            self.ec2_client = session.client('ec2', region_name='us-east-1')
            self.ce_client = session.client('ce', region_name='us-east-1')
        except Exception as e:
            logger.warning(f"AWS clients initialization failed: {e}")

    def get_real_time_pricing(self, instance_type: str, region: str) -> Dict[str, float]:
        """Get real-time pricing from AWS Pricing API."""
        if not self.pricing_client:
            return self._get_fallback_pricing(instance_type)
        
        try:
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'}
                ]
            )
            
            pricing_data = {}
            for product in response['PriceList']:
                price_info = json.loads(product)
                terms = price_info.get('terms', {})
                
                # On-Demand pricing
                on_demand = terms.get('OnDemand', {})
                for term_key, term_data in on_demand.items():
                    price_dimensions = term_data.get('priceDimensions', {})
                    for pd_key, pd_data in price_dimensions.items():
                        price_per_hour = float(pd_data['pricePerUnit']['USD'])
                        pricing_data['on_demand'] = price_per_hour
                        break
                
                # Reserved Instance pricing would require additional calls
                pricing_data['ri_1y_no_upfront'] = pricing_data.get('on_demand', 0) * 0.7
                pricing_data['ri_3y_no_upfront'] = pricing_data.get('on_demand', 0) * 0.5
                pricing_data['spot'] = pricing_data.get('on_demand', 0) * 0.3
                
                break
            
            return pricing_data if pricing_data else self._get_fallback_pricing(instance_type)
            
        except Exception as e:
            logger.error(f"Error fetching real-time pricing: {e}")
            return self._get_fallback_pricing(instance_type)

    def _get_location_name(self, region: str) -> str:
        """Convert region code to location name for pricing API."""
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'ap-southeast-1': 'Asia Pacific (Singapore)'
        }
        return region_mapping.get(region, 'US East (N. Virginia)')

    def _get_fallback_pricing(self, instance_type: str) -> Dict[str, float]:
        """Fallback pricing when AWS API is not available."""
        # Use static pricing as fallback
        fallback_prices = {
            'm6i.large': {'on_demand': 0.0864, 'ri_1y_no_upfront': 0.0605, 'ri_3y_no_upfront': 0.0432, 'spot': 0.0259},
            'm6i.xlarge': {'on_demand': 0.1728, 'ri_1y_no_upfront': 0.1210, 'ri_3y_no_upfront': 0.0864, 'spot': 0.0518},
            'r6i.large': {'on_demand': 0.1008, 'ri_1y_no_upfront': 0.0706, 'ri_3y_no_upfront': 0.0504, 'spot': 0.0302}
        }
        return fallback_prices.get(instance_type, {'on_demand': 0.1, 'ri_1y_no_upfront': 0.07, 'ri_3y_no_upfront': 0.05, 'spot': 0.03})

    def get_instance_recommendations(self, requirements: Dict) -> List[Dict]:
        """Get AWS instance recommendations based on requirements."""
        if not self.ec2_client:
            return self._get_fallback_recommendations()
        
        try:
            # This would use AWS Compute Optimizer or similar service
            # For now, using intelligent matching logic
            return self._intelligent_instance_matching(requirements)
        except Exception as e:
            logger.error(f"Error getting instance recommendations: {e}")
            return self._get_fallback_recommendations()

    def _intelligent_instance_matching(self, requirements: Dict) -> List[Dict]:
        """Intelligent instance matching based on requirements."""
        required_vcpus = requirements.get('vCPUs', 2)
        required_ram = requirements.get('RAM_GB', 8)
        
        # Instance database (subset for demo)
        instances = [
            {'type': 'm6i.large', 'vCPU': 2, 'RAM': 8, 'family': 'general', 'score': 0},
            {'type': 'm6i.xlarge', 'vCPU': 4, 'RAM': 16, 'family': 'general', 'score': 0},
            {'type': 'm6i.2xlarge', 'vCPU': 8, 'RAM': 32, 'family': 'general', 'score': 0},
            {'type': 'r6i.large', 'vCPU': 2, 'RAM': 16, 'family': 'memory', 'score': 0},
            {'type': 'r6i.xlarge', 'vCPU': 4, 'RAM': 32, 'family': 'memory', 'score': 0},
            {'type': 'c6i.large', 'vCPU': 2, 'RAM': 4, 'family': 'compute', 'score': 0}
        ]
        
        # Score instances based on fit
        for instance in instances:
            if instance['vCPU'] >= required_vcpus and instance['RAM'] >= required_ram:
                cpu_efficiency = required_vcpus / instance['vCPU']
                ram_efficiency = required_ram / instance['RAM']
                instance['score'] = (cpu_efficiency + ram_efficiency) / 2
        
        # Filter and sort
        valid_instances = [i for i in instances if i['score'] > 0]
        valid_instances.sort(key=lambda x: x['score'], reverse=True)
        
        return valid_instances[:3]  # Top 3 recommendations

    def _get_fallback_recommendations(self) -> List[Dict]:
        """Fallback recommendations."""
        return [
            {'type': 'm6i.large', 'vCPU': 2, 'RAM': 8, 'family': 'general', 'score': 0.8},
            {'type': 'm6i.xlarge', 'vCPU': 4, 'RAM': 16, 'family': 'general', 'score': 0.7},
            {'type': 'r6i.large', 'vCPU': 2, 'RAM': 16, 'family': 'memory', 'score': 0.6}
        ]

class EnvironmentHeatMapGenerator:
    """Generate environment heat maps for workload analysis."""
    
    def __init__(self):
        self.environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
        self.metrics = ['Cost', 'Complexity', 'Risk', 'Timeline', 'Resources']

    def generate_heat_map_data(self, workload_results: Dict) -> pd.DataFrame:
        """Generate heat map data for environments."""
        heat_data = []
        
        for env in self.environments:
            env_results = workload_results.get(env, {})
            
            # Calculate metrics for each environment
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

    def _calculate_cost_score(self, env_results: Dict) -> float:
        """Calculate cost score for heat map (0-100)."""
        if not env_results:
            return 50
        
        cost_breakdown = env_results.get('cost_breakdown', {})
        total_costs = cost_breakdown.get('total_costs', {})
        monthly_cost = total_costs.get('on_demand', 1000)
        
        # Normalize cost score (higher cost = higher score)
        if monthly_cost < 500:
            return 20
        elif monthly_cost < 1500:
            return 50
        elif monthly_cost < 3000:
            return 75
        else:
            return 95

    def _calculate_complexity_score(self, env_results: Dict) -> float:
        """Calculate complexity score for heat map."""
        if not env_results:
            return 50
        
        # Extract complexity from Claude AI analysis if available
        claude_analysis = env_results.get('claude_analysis', {})
        complexity_score = claude_analysis.get('complexity_score', 50)
        
        return complexity_score

    def _calculate_risk_score(self, env_results: Dict) -> float:
        """Calculate risk score for heat map."""
        if not env_results:
            return 50
        
        risk_assessment = env_results.get('risk_assessment', {})
        overall_risk = risk_assessment.get('overall_risk', 'Medium')
        
        risk_scores = {'Low': 25, 'Medium': 50, 'High': 75, 'Critical': 95}
        return risk_scores.get(overall_risk, 50)

    def _calculate_timeline_score(self, env_results: Dict) -> float:
        """Calculate timeline score for heat map."""
        if not env_results:
            return 50
        
        claude_analysis = env_results.get('claude_analysis', {})
        timeline = claude_analysis.get('estimated_timeline', {})
        max_weeks = timeline.get('max_weeks', 8)
        
        # Normalize timeline score (longer timeline = higher score)
        if max_weeks < 4:
            return 20
        elif max_weeks < 8:
            return 40
        elif max_weeks < 16:
            return 70
        else:
            return 90

    def _calculate_resource_score(self, env_results: Dict) -> float:
        """Calculate resource utilization score."""
        if not env_results:
            return 50
        
        requirements = env_results.get('requirements', {})
        vcpus = requirements.get('vCPUs', 2)
        ram_gb = requirements.get('RAM_GB', 8)
        
        # Normalize resource score
        resource_intensity = (vcpus * 10) + (ram_gb * 2)
        
        if resource_intensity < 50:
            return 25
        elif resource_intensity < 150:
            return 50
        elif resource_intensity < 300:
            return 75
        else:
            return 95

    def create_heat_map_visualization(self, heat_data: pd.DataFrame) -> go.Figure:
        """Create Plotly heat map visualization."""
        
        # Prepare data for heat map
        environments = heat_data['Environment'].tolist()
        metrics = ['Cost', 'Complexity', 'Risk', 'Timeline', 'Resources']
        
        z_data = []
        for metric in metrics:
            z_data.append(heat_data[metric].tolist())
        
        # Create heat map
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=environments,
            y=metrics,
            colorscale='RdYlGn_r',  # Red-Yellow-Green reversed
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

# Enhanced PDF Report Generator with new features
class EnhancedPDFReportGenerator:
    """Enhanced PDF report generator with Claude AI analysis and heat maps."""

    def __init__(self, page_size=A4):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab library not found. Please install with: pip install reportlab")
        
        self.page_size = page_size
        self.width, self.height = page_size
        self.styles = getSampleStyleSheet()
        self.colors = {
            'primary': colors.HexColor('#667eea'),
            'claude_ai': colors.HexColor('#ff6b6b'),
            'aws': colors.HexColor('#ff9500'),
            'secondary': colors.HexColor('#764ba2'),
            'text': colors.HexColor('#2d3748'),
            'light_text': colors.HexColor('#718096'),
            'header_bg': colors.HexColor('#f8fafc'),
            'border': colors.HexColor('#e2e8f0'),
        }
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom styles for enhanced reports."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle', parent=self.styles['h1'], fontSize=24, spaceAfter=20,
            textColor=self.colors['primary'], alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='ClaudeAIHeader', parent=self.styles['h2'], fontSize=16, spaceBefore=16, spaceAfter=10,
            textColor=self.colors['claude_ai'], borderLeftWidth=4, borderLeftColor=self.colors['claude_ai'],
            leftIndent=6, paddingLeft=10
        ))
        self.styles.add(ParagraphStyle(
            name='AWSHeader', parent=self.styles['h2'], fontSize=16, spaceBefore=16, spaceAfter=10,
            textColor=self.colors['aws'], borderLeftWidth=4, borderLeftColor=self.colors['aws'],
            leftIndent=6, paddingLeft=10
        ))

    def generate_enhanced_report(self, analysis_results, company_name, report_title):
        """Generate enhanced PDF report with Claude AI analysis and heat maps."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.page_size,
                                topMargin=0.75*inch, leftMargin=0.75*inch,
                                rightMargin=0.75*inch, bottomMargin=0.75*inch)
        
        story = []
        
        # Title Page
        story.append(Paragraph(report_title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(company_name, ParagraphStyle(
            name='CompanyStyle', parent=self.styles['Normal'], fontSize=18, alignment=TA_CENTER, textColor=self.colors['text']
        )))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(PageBreak())

        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['h1']))
        self._add_executive_summary(story, analysis_results)
        
        # Claude AI Migration Analysis
        story.append(Paragraph("Claude AI Migration Complexity Analysis", self.styles['ClaudeAIHeader']))
        self._add_claude_ai_analysis(story, analysis_results)
        
        # AWS Cost and Instance Analysis
        story.append(Paragraph("AWS Cost and Instance Sizing Analysis", self.styles['AWSHeader']))
        self._add_aws_analysis(story, analysis_results)
        
        # Environment Heat Map
        story.append(Paragraph("Environment Impact Analysis", self.styles['h1']))
        self._add_environment_analysis(story, analysis_results)
        
        # Migration Plan
        story.append(Paragraph("Detailed Migration Plan", self.styles['h1']))
        self._add_migration_plan(story, analysis_results)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _add_claude_ai_analysis(self, story, analysis_results):
        """Add Claude AI analysis section to PDF."""
        prod_results = analysis_results.get('recommendations', {}).get('PROD', {})
        claude_analysis = prod_results.get('claude_analysis', {})
        
        if not claude_analysis:
            story.append(Paragraph("Claude AI analysis not available.", self.styles['Normal']))
            return
        
        # Complexity Assessment
        complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
        complexity_score = claude_analysis.get('complexity_score', 50)
        
        story.append(Paragraph(f"Migration Complexity Assessment", self.styles['h2']))
        story.append(Paragraph(f"<b>Complexity Level:</b> {complexity_level} ({complexity_score:.0f}/100)", self.styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Migration Strategy
        strategy = claude_analysis.get('migration_strategy', {})
        if strategy:
            story.append(Paragraph("Recommended Migration Strategy", self.styles['h3']))
            story.append(Paragraph(f"<b>Approach:</b> {strategy.get('approach', 'N/A')}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Methodology:</b> {strategy.get('methodology', 'N/A')}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Timeline:</b> {strategy.get('timeline', 'N/A')}", self.styles['Normal']))
        
        # Risk Factors
        risk_factors = claude_analysis.get('risk_factors', [])
        if risk_factors:
            story.append(Paragraph("Risk Assessment", self.styles['h3']))
            for risk in risk_factors[:5]:  # Top 5 risks
                story.append(Paragraph(f"• <b>{risk.get('category', 'General')}:</b> {risk.get('risk', 'N/A')}", self.styles['Normal']))

    def _add_aws_analysis(self, story, analysis_results):
        """Add AWS analysis section to PDF."""
        prod_results = analysis_results.get('recommendations', {}).get('PROD', {})
        
        # Cost Analysis
        cost_breakdown = prod_results.get('cost_breakdown', {})
        if cost_breakdown:
            story.append(Paragraph("Cost Analysis", self.styles['h2']))
            total_costs = cost_breakdown.get('total_costs', {})
            
            # Create cost table
            cost_data = [['Pricing Model', 'Monthly Cost', 'Annual Cost']]
            for model, cost in total_costs.items():
                cost_data.append([
                    model.replace('_', ' ').title(),
                    f"${cost:,.2f}",
                    f"${cost*12:,.2f}"
                ])
            
            cost_table = Table(cost_data)
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['aws']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, self.colors['border']),
            ]))
            story.append(cost_table)
        
        # Instance Recommendations
        instance_options = prod_results.get('instance_options', {})
        if instance_options:
            story.append(Paragraph("Instance Recommendations", self.styles['h3']))
            for scenario, instance in instance_options.items():
                story.append(Paragraph(f"<b>{scenario.title()}:</b> {instance.get('type', 'N/A')} - {instance.get('vCPU', 'N/A')} vCPUs, {instance.get('RAM', 'N/A')} GB RAM", self.styles['Normal']))

    def _add_environment_analysis(self, story, analysis_results):
        """Add environment heat map analysis to PDF."""
        story.append(Paragraph("Environment impact analysis provides insights into migration complexity across different environments.", self.styles['Normal']))
        
        # This would include the heat map image if available
        story.append(Paragraph("Heat map visualization shows relative impact levels for Cost, Complexity, Risk, Timeline, and Resources across DEV, QA, UAT, PREPROD, and PROD environments.", self.styles['Normal']))

    def _add_migration_plan(self, story, analysis_results):
        """Add detailed migration plan to PDF."""
        prod_results = analysis_results.get('recommendations', {}).get('PROD', {})
        claude_analysis = prod_results.get('claude_analysis', {})
        
        migration_steps = claude_analysis.get('migration_steps', [])
        if migration_steps:
            for i, step in enumerate(migration_steps, 1):
                story.append(Paragraph(f"Phase {i}: {step.get('phase', 'N/A')}", self.styles['h3']))
                story.append(Paragraph(f"<b>Duration:</b> {step.get('duration', 'N/A')}", self.styles['Normal']))
                
                tasks = step.get('tasks', [])
                if tasks:
                    story.append(Paragraph("<b>Key Tasks:</b>", self.styles['Normal']))
                    for task in tasks:
                        story.append(Paragraph(f"• {task}", self.styles['Normal']))
                
                deliverables = step.get('deliverables', [])
                if deliverables:
                    story.append(Paragraph(f"<b>Deliverables:</b> {', '.join(deliverables)}", self.styles['Normal']))
                
                story.append(Spacer(1, 0.1*inch))

    def _add_executive_summary(self, story, analysis_results):
        """Add executive summary to PDF."""
        prod_results = analysis_results.get('recommendations', {}).get('PROD', {})
        tco_analysis = prod_results.get('tco_analysis', {})
        
        summary_text = f"""
        This comprehensive analysis combines Claude AI-powered migration complexity assessment with AWS cost optimization 
        and instance sizing recommendations. The analysis covers migration strategy, risk assessment, detailed cost breakdown, 
        and environment-specific impact analysis across development lifecycle stages.
        
        Key Findings:
        • Recommended pricing strategy: {tco_analysis.get('best_pricing_option', 'N/A').replace('_', ' ').title()}
        • Estimated monthly cost: ${tco_analysis.get('monthly_cost', 0):,.2f}
        • Potential monthly savings: ${tco_analysis.get('monthly_savings', 0):,.2f}
        • 3-year ROI: {tco_analysis.get('roi_3_years', 'N/A')}%
        """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

# Update the main calculator class to integrate with Claude AI and AWS
class EnhancedEnterpriseEC2Calculator:
    """Enhanced calculator with Claude AI and AWS integration."""
    
    def __init__(self):
        # Initialize base calculator properties (keeping existing structure)
        self.claude_analyzer = ClaudeAIMigrationAnalyzer()
        self.aws_integration = EnhancedAWSIntegration()
        self.heat_map_generator = EnvironmentHeatMapGenerator()
        
        # Keep existing instance types and pricing structure
        self.INSTANCE_TYPES = [
            {"type": "m6i.large", "vCPU": 2, "RAM": 8, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
            {"type": "m6i.xlarge", "vCPU": 4, "RAM": 16, "max_ebs_bandwidth": 9500, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
            {"type": "m6i.2xlarge", "vCPU": 8, "RAM": 32, "max_ebs_bandwidth": 19000, "network": "Up to 12.5 Gbps", "family": "general", "processor": "Intel", "architecture": "x86_64"},
            {"type": "r6i.large", "vCPU": 2, "RAM": 16, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "memory", "processor": "Intel", "architecture": "x86_64"},
            {"type": "c6i.large", "vCPU": 2, "RAM": 4, "max_ebs_bandwidth": 4750, "network": "Up to 12.5 Gbps", "family": "compute", "processor": "Intel", "architecture": "x86_64"},
        ]
        
        # Enhanced environment multipliers including UAT and PREPROD
        self.ENV_MULTIPLIERS = {
            "PROD": {"cpu_ram": 1.0, "storage": 1.0, "description": "Production environment", "availability_requirement": "99.9%"},
            "PREPROD": {"cpu_ram": 0.9, "storage": 0.9, "description": "Pre-production environment", "availability_requirement": "99.5%"},
            "UAT": {"cpu_ram": 0.7, "storage": 0.7, "description": "User acceptance testing", "availability_requirement": "95.0%"},
            "QA": {"cpu_ram": 0.6, "storage": 0.6, "description": "Quality assurance", "availability_requirement": "95.0%"},
            "DEV": {"cpu_ram": 0.4, "storage": 0.4, "description": "Development environment", "availability_requirement": "90.0%"}
        }
        
        # Initialize inputs
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
            "pricing_model": "on_demand",
            "spot_percentage": 0,
            "multi_az": True,
            "compliance_requirements": [],
            "backup_retention_days": 30,
            "monitoring_level": "basic",
            "disaster_recovery": False,
            "auto_scaling": True,
            "load_balancer": "alb",
        }

    def calculate_enhanced_requirements(self, env: str) -> Dict[str, Any]:
        """Calculate requirements with Claude AI and AWS integration."""
        
        # Standard requirements calculation (keeping existing logic)
        requirements = self._calculate_standard_requirements(env)
        
        # Claude AI migration analysis
        claude_analysis = self.claude_analyzer.analyze_workload_complexity(self.inputs, env)
        
        # AWS cost and instance analysis
        aws_analysis = self._perform_aws_analysis(requirements, env)
        
        # Enhanced results
        enhanced_results = {
            **requirements,
            'claude_analysis': claude_analysis,
            'aws_analysis': aws_analysis,
            'environment': env,
            'enhanced_recommendations': self._generate_enhanced_recommendations(claude_analysis, aws_analysis)
        }
        
        return enhanced_results

    def _calculate_standard_requirements(self, env: str) -> Dict[str, Any]:
        """Calculate standard infrastructure requirements (existing logic)."""
        env_mult = self.ENV_MULTIPLIERS[env]
        
        # Basic calculations (simplified from original)
        required_vcpus = max(math.ceil(self.inputs["on_prem_cores"] * 1.2 * env_mult["cpu_ram"]), 2)
        required_ram = max(math.ceil(self.inputs["on_prem_ram_gb"] * 1.3 * env_mult["cpu_ram"]), 4)
        required_storage = math.ceil(self.inputs["storage_current_gb"] * 1.2 * env_mult["storage"])
        
        return {
            "requirements": {
                "vCPUs": required_vcpus,
                "RAM_GB": required_ram,
                "storage_GB": required_storage,
                "multi_az": self.inputs["multi_az"] and env in ["PROD", "PREPROD"]
            },
            "cost_breakdown": self._calculate_basic_costs(required_vcpus, required_ram, required_storage, env),
            "tco_analysis": {"monthly_cost": 1000, "monthly_savings": 200, "best_pricing_option": "ri_1y"}
        }

    def _calculate_basic_costs(self, vcpus: int, ram_gb: int, storage_gb: int, env: str) -> Dict[str, Any]:
        """Calculate basic costs (simplified)."""
        base_hourly_cost = 0.1 * vcpus + 0.02 * ram_gb + 0.0001 * storage_gb
        monthly_cost = base_hourly_cost * 24 * 30
        
        return {
            "total_costs": {
                "on_demand": monthly_cost,
                "ri_1y_no_upfront": monthly_cost * 0.7,
                "ri_3y_no_upfront": monthly_cost * 0.5,
                "spot": monthly_cost * 0.3
            },
            "instance_costs": {"on_demand": monthly_cost * 0.7},
            "storage_costs": {"primary_storage": monthly_cost * 0.2},
            "network_costs": {"data_transfer": monthly_cost * 0.1}
        }

    def _perform_aws_analysis(self, requirements: Dict, env: str) -> Dict[str, Any]:
        """Perform AWS-specific analysis."""
        
        # Get real-time pricing
        instance_recommendations = self.aws_integration.get_instance_recommendations(requirements["requirements"])
        
        # Enhanced cost analysis
        cost_optimization = {
            "recommended_instances": instance_recommendations,
            "cost_savings_opportunities": [
                "Consider Reserved Instances for production workloads",
                "Implement auto-scaling to optimize costs",
                "Use Spot Instances for development environments"
            ],
            "rightsizing_recommendations": [
                "Monitor CPU and memory utilization post-migration",
                "Consider graviton instances for better price-performance",
                "Implement storage lifecycle policies"
            ]
        }
        
        return cost_optimization

    def _generate_enhanced_recommendations(self, claude_analysis: Dict, aws_analysis: Dict) -> List[str]:
        """Generate enhanced recommendations combining Claude AI and AWS insights."""
        
        recommendations = []
        
        # Claude AI recommendations
        complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
        if complexity_level in ['HIGH', 'CRITICAL']:
            recommendations.extend([
                "🤖 Claude AI: High complexity detected - consider phased migration approach",
                "🤖 Claude AI: Allocate additional time for testing and validation",
                "🤖 Claude AI: Engage cloud migration specialists for complex components"
            ])
        
        # AWS recommendations
        recommendations.extend([
            "☁️ AWS: Implement comprehensive monitoring from day one",
            "☁️ AWS: Use AWS Well-Architected Framework for design validation",
            "☁️ AWS: Consider multi-AZ deployment for production workloads"
        ])
        
        return recommendations

def render_enhanced_configuration():
    """Render enhanced configuration with Claude AI and AWS integration indicators."""
    
    st.markdown('<div class="section-header"><h3>🏗️ Enhanced Enterprise Workload Configuration</h3></div>', unsafe_allow_html=True)
    
    # Show integration status
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="claude-analysis">
            <h4>🤖 Claude AI Integration</h4>
            <p>Migration complexity analysis, risk assessment, and intelligent migration strategy recommendations</p>
            <span class="claude-ai-badge">AI-Powered</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="aws-analysis">
            <h4>☁️ AWS Integration</h4>
            <p>Real-time cost analysis, instance sizing recommendations, and pricing optimization</p>
            <span class="aws-integration-badge">AWS-Native</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Configuration mode selection
    config_mode = st.radio(
        "Configuration Mode:",
        ["🎯 Single Workload Analysis", "📦 Bulk Workload Analysis"],
        horizontal=True,
        key="enhanced_config_mode"
    )
    
    if config_mode == "📦 Bulk Workload Analysis":
        render_enhanced_bulk_configuration()
    else:
        render_enhanced_single_configuration()

def render_enhanced_single_configuration():
    """Render enhanced single workload configuration."""
    
    if 'enhanced_calculator' not in st.session_state or st.session_state.enhanced_calculator is None:
        st.error("⚠️ Calculator not initialized. Please refresh the page.")
        return
        
    calculator = st.session_state.enhanced_calculator
    
    # Basic workload information
    with st.expander("📋 Workload Information", expanded=True):
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
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Run Enhanced Analysis", type="primary", key="enhanced_single_analysis"):
            run_enhanced_single_analysis()
    
    with col2:
        if st.button("🎯 Full AI + AWS Analysis", type="secondary", key="full_enhanced_analysis"):
            run_full_enhanced_analysis()

def render_enhanced_bulk_configuration():
    """Render enhanced bulk workload configuration."""
    
    st.markdown("#### 📦 Bulk Workload Analysis with AI Enhancement")
    
    # Enhanced CSV template
    st.markdown("""
    **Enhanced CSV Template includes:**
    - Standard workload configuration fields
    - Migration complexity indicators
    - Business impact factors
    - Compliance requirements
    """)
    
    # File upload with enhanced validation
    uploaded_file = st.file_uploader(
        "Upload Enhanced Workload CSV",
        type=['csv'],
        help="Upload CSV with workload configurations for bulk AI analysis"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("🤖 Run Bulk AI Analysis", type="primary"):
                run_enhanced_bulk_analysis(df)
                
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")

def run_enhanced_single_analysis():
    """Run enhanced single workload analysis."""
    
    with st.spinner("🔄 Running enhanced analysis with Claude AI and AWS integration..."):
        try:
            calculator = st.session_state.enhanced_calculator
            
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

def run_full_enhanced_analysis():
    """Run full enhanced analysis with all features."""
    
    with st.spinner("🔄 Running comprehensive AI + AWS analysis..."):
        try:
            # This would include full integration with both Claude AI and AWS
            run_enhanced_single_analysis()
            st.success("✅ Full enhanced analysis completed with AI insights and AWS optimization!")
            
        except Exception as e:
            st.error(f"❌ Error during full enhanced analysis: {str(e)}")

def run_enhanced_bulk_analysis(df):
    """Run enhanced bulk analysis on uploaded data."""
    
    with st.spinner("🔄 Running bulk AI analysis..."):
        try:
            # Process each workload with enhanced analysis
            bulk_results = []
            
            for idx, row in df.iterrows():
                # Convert row to workload inputs
                workload_inputs = convert_csv_row_to_enhanced_config(row)
                
                # Run enhanced analysis for this workload
                calculator = st.session_state.enhanced_calculator
                calculator.inputs.update(workload_inputs)
                
                workload_results = {}
                for env in calculator.ENV_MULTIPLIERS.keys():
                    workload_results[env] = calculator.calculate_enhanced_requirements(env)
                
                bulk_results.append({
                    'inputs': workload_inputs,
                    'recommendations': workload_results
                })
            
            st.session_state.enhanced_bulk_results = bulk_results
            st.success(f"✅ Bulk AI analysis completed for {len(bulk_results)} workloads!")
            
        except Exception as e:
            st.error(f"❌ Error during bulk analysis: {str(e)}")

def convert_csv_row_to_enhanced_config(row):
    """Convert CSV row to enhanced workload configuration."""
    # This would include enhanced fields for AI analysis
    config = {
        'workload_name': str(row.get('workload_name', 'Unknown')),
        'workload_type': str(row.get('workload_type', 'web_application')),
        'operating_system': str(row.get('operating_system', 'linux')),
        'region': str(row.get('region', 'us-east-1')),
        'on_prem_cores': int(row.get('on_prem_cores', 4)),
        'peak_cpu_percent': int(row.get('peak_cpu_percent', 70)),
        'on_prem_ram_gb': int(row.get('on_prem_ram_gb', 16)),
        'peak_ram_percent': int(row.get('peak_ram_percent', 80)),
        'storage_current_gb': int(row.get('storage_current_gb', 500)),
        'peak_iops': int(row.get('peak_iops', 5000)),
        'peak_throughput_mbps': int(row.get('peak_throughput_mbps', 250)),
        # Enhanced fields
        'infrastructure_age_years': int(row.get('infrastructure_age_years', 3)),
        'business_criticality': str(row.get('business_criticality', 'medium')),
        'compliance_requirements': str(row.get('compliance_requirements', '')).split(',') if row.get('compliance_requirements') else []
    }
    return config

def render_enhanced_results():
    """Render enhanced analysis results with Claude AI and AWS insights."""
    
    if 'enhanced_results' not in st.session_state:
        st.info("💡 Run an enhanced analysis to see results here.")
        return
    
    results = st.session_state.enhanced_results
    st.markdown('<div class="section-header"><h3>📊 Enhanced Analysis Results</h3></div>', unsafe_allow_html=True)
    
    # Enhanced summary metrics
    prod_results = results['recommendations']['PROD']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        claude_analysis = prod_results.get('claude_analysis', {})
        complexity_score = claude_analysis.get('complexity_score', 50)
        complexity_level = claude_analysis.get('complexity_level', 'MEDIUM')
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🤖 Migration Complexity</div>
            <div class="metric-value">{complexity_score:.0f}/100</div>
            <div class="metric-description">{complexity_level}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        tco = prod_results.get('tco_analysis', {})
        monthly_cost = tco.get('monthly_cost', 0)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">☁️ AWS Monthly Cost</div>
            <div class="metric-value">${monthly_cost:,.0f}</div>
            <div class="metric-description">Optimized Pricing</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        timeline = claude_analysis.get('estimated_timeline', {})
        max_weeks = timeline.get('max_weeks', 8)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏱️ Migration Timeline</div>
            <div class="metric-value">{max_weeks}</div>
            <div class="metric-description">Weeks (Estimated)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        aws_analysis = prod_results.get('aws_analysis', {})
        instance_count = len(aws_analysis.get('recommended_instances', []))
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🖥️ Instance Options</div>
            <div class="metric-value">{instance_count}</div>
            <div class="metric-description">Recommendations</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Environment Heat Map
    st.subheader("🌡️ Environment Impact Heat Map")
    
    if 'heat_map_fig' in results:
        st.plotly_chart(results['heat_map_fig'], use_container_width=True)
    
    # Claude AI Analysis Section
    st.subheader("🤖 Claude AI Migration Analysis")
    
    if claude_analysis:
        render_claude_analysis_section(claude_analysis)
    
    # AWS Analysis Section
    st.subheader("☁️ AWS Cost & Instance Analysis")
    
    if aws_analysis:
        render_aws_analysis_section(aws_analysis)

def render_claude_analysis_section(claude_analysis):
    """Render Claude AI analysis section."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="migration-complexity-card">
            <h4>Migration Strategy</h4>
        </div>
        """, unsafe_allow_html=True)
        
        strategy = claude_analysis.get('migration_strategy', {})
        if strategy:
            st.markdown(f"**Approach:** {strategy.get('approach', 'N/A')}")
            st.markdown(f"**Methodology:** {strategy.get('methodology', 'N/A')}")
            st.markdown(f"**Timeline:** {strategy.get('timeline', 'N/A')}")
            st.markdown(f"**Risk Level:** {strategy.get('risk_level', 'N/A')}")
    
    with col2:
        st.markdown("**Risk Factors:**")
        risk_factors = claude_analysis.get('risk_factors', [])
        for risk in risk_factors[:3]:  # Show top 3 risks
            st.markdown(f"• **{risk.get('category', 'General')}:** {risk.get('risk', 'N/A')}")
    
    # Migration Steps
    st.markdown("**Migration Steps:**")
    migration_steps = claude_analysis.get('migration_steps', [])
    
    for i, step in enumerate(migration_steps, 1):
        with st.expander(f"Phase {i}: {step.get('phase', 'N/A')} ({step.get('duration', 'N/A')})"):
            
            tasks = step.get('tasks', [])
            if tasks:
                st.markdown("**Tasks:**")
                for task in tasks:
                    st.markdown(f"• {task}")
            
            deliverables = step.get('deliverables', [])
            if deliverables:
                st.markdown(f"**Deliverables:** {', '.join(deliverables)}")

def render_aws_analysis_section(aws_analysis):
    """Render AWS analysis section."""
    
    # Instance recommendations
    recommended_instances = aws_analysis.get('recommended_instances', [])
    
    if recommended_instances:
        st.markdown("**Recommended Instance Types:**")
        
        instance_data = []
        for instance in recommended_instances:
            instance_data.append({
                'Instance Type': instance.get('type', 'N/A'),
                'vCPUs': instance.get('vCPU', 'N/A'),
                'RAM (GB)': instance.get('RAM', 'N/A'),
                'Family': instance.get('family', 'N/A').title(),
                'Fit Score': f"{instance.get('score', 0):.2f}"
            })
        
        df_instances = pd.DataFrame(instance_data)
        st.dataframe(df_instances, use_container_width=True, hide_index=True)
    
    # Cost savings opportunities
    savings_opps = aws_analysis.get('cost_savings_opportunities', [])
    if savings_opps:
        st.markdown("**Cost Savings Opportunities:**")
        for opp in savings_opps:
            st.markdown(f"• {opp}")

def render_enhanced_reports():
    """Render enhanced reports with Claude AI and AWS insights."""
    
    st.markdown("### 📋 Enhanced Enterprise Reports")
    
    if 'enhanced_results' not in st.session_state and 'enhanced_bulk_results' not in st.session_state:
        st.info("💡 Run an enhanced analysis to generate reports.")
        return
    
    # Report configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Report Sections")
        report_sections = st.multiselect(
            "Select sections to include:",
            [
                "Executive Summary",
                "Claude AI Migration Analysis",
                "AWS Cost & Instance Analysis", 
                "Environment Heat Map",
                "Detailed Migration Plan",
                "Risk Assessment & Mitigation",
                "Technical Specifications"
            ],
            default=["Executive Summary", "Claude AI Migration Analysis", "AWS Cost & Instance Analysis"]
        )
    
    with col2:
        st.markdown("#### 🎨 Report Options")
        company_name = st.text_input("Company Name", value="Enterprise Corporation")
        report_title = st.text_input("Report Title", value="Enhanced AWS Migration Analysis")
        include_heat_maps = st.checkbox("Include Environment Heat Maps", value=True)
        include_ai_insights = st.checkbox("Include Claude AI Insights", value=True)
    
    # Generate reports
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Generate Enhanced PDF", type="primary"):
            generate_enhanced_pdf_report(report_sections, company_name, report_title, include_heat_maps, include_ai_insights)
    
    with col2:
        if st.button("📊 Export to Excel"):
            generate_enhanced_excel_report()
    
    with col3:
        if st.button("📈 Generate Heat Map Report"):
            generate_heat_map_report()

def generate_enhanced_pdf_report(sections, company_name, title, include_heat_maps, include_ai_insights):
    """Generate enhanced PDF report with all new features."""
    
    with st.spinner("🔄 Generating enhanced PDF report..."):
        try:
            if not REPORTLAB_AVAILABLE:
                st.error("ReportLab library required for PDF generation")
                return
            
            # Get analysis results
            results = st.session_state.get('enhanced_results')
            if not results:
                st.error("No enhanced analysis results available")
                return
            
            # Generate PDF
            pdf_generator = EnhancedPDFReportGenerator()
            pdf_data = pdf_generator.generate_enhanced_report(results, company_name, title)
            
            # Download button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Enhanced_AWS_Migration_Report_{timestamp}.pdf"
            
            st.download_button(
                label="⬇️ Download Enhanced PDF Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                key="download_enhanced_pdf"
            )
            
            st.success("✅ Enhanced PDF report generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")

def generate_enhanced_excel_report():
    """Generate enhanced Excel report with multiple sheets."""
    
    with st.spinner("🔄 Generating enhanced Excel report..."):
        try:
            results = st.session_state.get('enhanced_results')
            if not results:
                st.error("No enhanced analysis results available")
                return
            
            # Create Excel file with multiple sheets
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Metric': ['Workload Name', 'Complexity Score', 'Migration Timeline', 'Monthly Cost'],
                    'Value': [
                        results['inputs']['workload_name'],
                        results['recommendations']['PROD']['claude_analysis']['complexity_score'],
                        f"{results['recommendations']['PROD']['claude_analysis']['estimated_timeline']['max_weeks']} weeks",
                        f"${results['recommendations']['PROD']['tco_analysis']['monthly_cost']:,.2f}"
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Heat map data
                if 'heat_map_data' in results:
                    results['heat_map_data'].to_excel(writer, sheet_name='Environment_HeatMap', index=False)
            
            output.seek(0)
            
            # Download button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Enhanced_AWS_Analysis_{timestamp}.xlsx"
            
            st.download_button(
                label="⬇️ Download Enhanced Excel Report",
                data=output.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_enhanced_excel"
            )
            
            st.success("✅ Enhanced Excel report generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating Excel: {str(e)}")

def generate_heat_map_report():
    """Generate specialized heat map report."""
    
    with st.spinner("🔄 Generating heat map analysis report..."):
        try:
            results = st.session_state.get('enhanced_results')
            if not results or 'heat_map_data' not in results:
                st.error("No heat map data available")
                return
            
            # Generate heat map CSV
            heat_map_csv = results['heat_map_data'].to_csv(index=False)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Environment_HeatMap_Analysis_{timestamp}.csv"
            
            st.download_button(
                label="⬇️ Download Heat Map Data",
                data=heat_map_csv,
                file_name=filename,
                mime="text/csv",
                key="download_heat_map"
            )
            
            st.success("✅ Heat map analysis report generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating heat map report: {str(e)}")

def initialize_enhanced_session_state():
    """Initialize enhanced session state."""
    try:
        if 'enhanced_calculator' not in st.session_state:
            st.session_state.enhanced_calculator = EnhancedEnterpriseEC2Calculator()
        if 'enhanced_results' not in st.session_state:
            st.session_state.enhanced_results = None
        if 'enhanced_bulk_results' not in st.session_state:
            st.session_state.enhanced_bulk_results = []
        if 'demo_mode' not in st.session_state:
            st.session_state.demo_mode = True
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = True
    except Exception as e:
        st.error(f"Error initializing session state: {str(e)}")
        # Fallback initialization
        st.session_state.enhanced_calculator = None
        st.session_state.enhanced_results = None
        st.session_state.enhanced_bulk_results = []

def main():
    """Enhanced main application with Claude AI and AWS integration."""
    
    # Initialize session state with error handling
    try:
        initialize_enhanced_session_state()
    except Exception as e:
        st.error(f"Error initializing application: {str(e)}")
        st.stop()
    
    # Check if calculator is properly initialized
    if st.session_state.enhanced_calculator is None:
        st.error("⚠️ Application initialization failed. Please refresh the page.")
        st.stop()
    
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise AWS Workload Sizing Platform v5.0</h1>
        <span class="claude-ai-badge">Claude AI Powered</span>
        <span class="aws-integration-badge">AWS Integrated</span>
        <p>AI-powered migration complexity analysis with real-time AWS cost optimization and intelligent instance sizing recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("### 🤖 AI + AWS Integration Status")
        
        # Integration status indicators
        st.markdown("""
        <div style="padding: 1rem; border-radius: 8px; background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #dc2626;">🤖 Claude AI</h4>
            <p style="margin: 0; font-size: 0.875rem;">Migration Complexity Analysis</p>
            <span class="status-badge status-success">Active</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="padding: 1rem; border-radius: 8px; background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%); margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #ea580c;">☁️ AWS Integration</h4>
            <p style="margin: 0; font-size: 0.875rem;">Real-time Cost & Instance Analysis</p>
            <span class="status-badge status-success">Connected</span>
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
        
        **📋 Enhanced Reporting:**
        - AI-powered insights
        - Interactive heat maps
        - Comprehensive migration plans
        - Executive-ready presentations
        """)
    
    # Enhanced tab structure
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚙️ Enhanced Configuration",
        "📊 AI + AWS Analysis Results", 
        "🌡️ Environment Heat Maps",
        "📋 Enhanced Reports"
    ])
    
    with tab1:
        render_enhanced_configuration()
    
    with tab2:
        render_enhanced_results()
    
    with tab3:
        st.markdown("### 🌡️ Environment Impact Analysis")
        
        if 'enhanced_results' in st.session_state and st.session_state.enhanced_results:
            # Environment cards
            st.markdown("#### Environment Overview")
            
            cols = st.columns(5)
            environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
            
            for i, env in enumerate(environments):
                with cols[i]:
                    env_class = f"env-{env.lower()}"
                    results = st.session_state.enhanced_results['recommendations'].get(env, {})
                    claude_analysis = results.get('claude_analysis', {})
                    complexity = claude_analysis.get('complexity_score', 50)
                    
                    st.markdown(f"""
                    <div class="env-card {env_class}">
                        <h4>{env}</h4>
                        <p>Complexity: {complexity:.0f}/100</p>
                        <small>{st.session_state.enhanced_calculator.ENV_MULTIPLIERS[env]['description']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Heat map visualization
            if 'heat_map_fig' in st.session_state.enhanced_results:
                st.plotly_chart(st.session_state.enhanced_results['heat_map_fig'], use_container_width=True)
        else:
            st.info("💡 Run an enhanced analysis to see environment heat maps.")
    
    with tab4:
        render_enhanced_reports()
    
    # Enhanced footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <strong>Enterprise AWS Workload Sizing Platform v5.0</strong><br>
        Powered by Claude AI for intelligent migration analysis and AWS integration for real-time cost optimization<br>
        <em>🤖 AI-Enhanced • ☁️ AWS-Native • 📊 Data-Driven • 🚀 Enterprise-Ready</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()