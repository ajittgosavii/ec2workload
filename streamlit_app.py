# Complete Enhanced AWS Migration Analysis Platform
# Requirements: streamlit>=1.28.0, pandas>=1.5.0, plotly>=5.0.0, reportlab>=3.6.0

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

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="Enhanced AWS Migration Platform v6.0",
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
    """Claude AI powered migration complexity analyzer."""
    
    def __init__(self):
        self.complexity_factors = {
            'application_architecture': {'weight': 0.25},
            'technical_stack': {'weight': 0.20},
            'operational_complexity': {'weight': 0.20},
            'business_impact': {'weight': 0.20},
            'organizational_readiness': {'weight': 0.15}
        }

    def analyze_workload_complexity(self, workload_inputs: Dict, environment: str) -> Dict[str, Any]:
        """Analyze migration complexity using Claude AI-like intelligence."""
        
        try:
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
            migration_strategy = self._generate_migration_strategy(complexity_level, environment)
            
            # Generate migration steps
            migration_steps = self._generate_migration_steps(complexity_level, environment)
            
            # Risk assessment
            risk_factors = self._assess_migration_risks(complexity_level, environment)
            
            # Timeline estimation
            timeline = self._estimate_migration_timeline(complexity_level, environment)
            
            return {
                'complexity_score': complexity_score,
                'complexity_level': complexity_level,
                'complexity_color': complexity_color,
                'migration_strategy': migration_strategy,
                'migration_steps': migration_steps,
                'risk_factors': risk_factors,
                'estimated_timeline': timeline,
                'recommendations': self._generate_recommendations(complexity_level),
                'success_factors': self._identify_success_factors(complexity_level)
            }
        except Exception as e:
            logger.error(f"Error in Claude AI analysis: {e}")
            return self._get_fallback_analysis()

    def _calculate_complexity_score(self, workload_inputs: Dict, environment: str) -> float:
        """Calculate overall complexity score."""
        try:
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
            env_multipliers = {'DEV': 0.7, 'QA': 0.8, 'UAT': 0.9, 'PREPROD': 1.0, 'PROD': 1.2}
            env_factor = env_multipliers.get(environment, 1.0)
            
            # Infrastructure age factor
            infra_age = workload_inputs.get('infrastructure_age_years', 3)
            age_factor = min(infra_age * 5, 25)
            
            total_score = (base_score * env_factor) + age_factor
            return min(total_score, 100)
        except Exception:
            return 50

    def _generate_migration_strategy(self, complexity_level: str, environment: str) -> Dict[str, Any]:
        """Generate migration strategy based on complexity."""
        strategies = {
            'LOW': {
                'approach': 'Lift and Shift with Optimization',
                'methodology': 'Direct migration with minimal changes',
                'timeline': 'Fast track (2-4 weeks)',
                'risk_level': 'Low'
            },
            'MEDIUM': {
                'approach': 'Hybrid Migration with Re-architecting',
                'methodology': 'Phased migration with selective modernization',
                'timeline': 'Standard track (6-10 weeks)',
                'risk_level': 'Medium'
            },
            'HIGH': {
                'approach': 'Comprehensive Re-architecting',
                'methodology': 'Full application modernization',
                'timeline': 'Extended track (12-16 weeks)',
                'risk_level': 'High'
            },
            'CRITICAL': {
                'approach': 'Strategic Rebuild',
                'methodology': 'Complete re-design and rebuild',
                'timeline': 'Long-term project (20+ weeks)',
                'risk_level': 'Very High'
            }
        }
        return strategies.get(complexity_level, strategies['MEDIUM'])

    def _generate_migration_steps(self, complexity_level: str, environment: str) -> List[Dict[str, Any]]:
        """Generate detailed migration steps."""
        return [
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

    def _assess_migration_risks(self, complexity_level: str, environment: str) -> List[Dict[str, Any]]:
        """Assess migration risks."""
        return [
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

    def _estimate_migration_timeline(self, complexity_level: str, environment: str) -> Dict[str, Any]:
        """Estimate migration timeline."""
        timelines = {
            'LOW': {'min_weeks': 3, 'max_weeks': 6, 'confidence': 'High'},
            'MEDIUM': {'min_weeks': 6, 'max_weeks': 12, 'confidence': 'Medium'},
            'HIGH': {'min_weeks': 12, 'max_weeks': 20, 'confidence': 'Medium'},
            'CRITICAL': {'min_weeks': 20, 'max_weeks': 32, 'confidence': 'Low'}
        }
        return timelines.get(complexity_level, timelines['MEDIUM'])

    def _generate_recommendations(self, complexity_level: str) -> List[str]:
        """Generate recommendations."""
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
                "Plan for multiple migration phases"
            ])
        
        return recommendations

    def _identify_success_factors(self, complexity_level: str) -> List[str]:
        """Identify success factors."""
        return [
            "Strong project leadership and governance",
            "Clear communication with all stakeholders",
            "Adequate resource allocation and timeline",
            "Comprehensive testing strategy"
        ]

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis."""
        return {
            'complexity_score': 50,
            'complexity_level': 'MEDIUM',
            'complexity_color': 'medium',
            'migration_strategy': {
                'approach': 'Standard Migration',
                'methodology': 'Lift and shift with optimization',
                'timeline': '6-10 weeks',
                'risk_level': 'Medium'
            },
            'migration_steps': [],
            'risk_factors': [],
            'estimated_timeline': {'min_weeks': 6, 'max_weeks': 10, 'confidence': 'Medium'},
            'recommendations': ['Follow standard best practices'],
            'success_factors': ['Strong project leadership']
        }

class EnhancedEnvironmentAnalyzer:
    """Enhanced environment analyzer with detailed complexity explanations."""
    
    def __init__(self):
        self.environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
        
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

# Enhanced Streamlit Functions
def initialize_enhanced_session_state():
    """Initialize enhanced session state."""
    try:
        if 'enhanced_calculator' not in st.session_state:
            st.session_state.enhanced_calculator = EnhancedEnterpriseEC2Calculator()
        if 'enhanced_results' not in st.session_state:
            st.session_state.enhanced_results = None
        
        logger.info("Session state initialized successfully")
        
    except Exception as e:
        st.error(f"Error initializing session state: {str(e)}")
        logger.error(f"Error initializing session state: {e}")
        st.session_state.enhanced_calculator = None
        st.session_state.enhanced_results = None

def render_enhanced_configuration():
    """Render enhanced configuration."""
    
    st.markdown("### ⚙️ Enhanced Enterprise Workload Configuration")
    
    # Check if calculator exists
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
    if st.button("🚀 Run Enhanced Analysis", type="primary", key="enhanced_analysis_button"):
        run_enhanced_analysis()

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
                
                for i, step in enumerate(migration_steps[:3], 1):  # Show first 3 steps
                    if isinstance(step, dict):
                        with st.expander(f"Phase {i}: {step.get('phase', 'N/A')}", expanded=False):
                            st.markdown(f"**Duration:** {step.get('duration', 'N/A')}")
                            
                            tasks = step.get('tasks', [])
                            if tasks:
                                st.markdown("**Key Tasks:**")
                                for task in tasks[:3]:  # Show first 3 tasks
                                    st.markdown(f"• {task}")
        
        # Cost Analysis
        st.markdown("### 💰 Cost Analysis")
        
        cost_breakdown = prod_results.get('cost_breakdown', {})
        total_costs = cost_breakdown.get('total_costs', {})
        
        if total_costs:
            cost_data = []
            for pricing_model, cost in total_costs.items():
                cost_data.append({
                    'Pricing Model': pricing_model.replace('_', ' ').title(),
                    'Monthly Cost': f"${cost:,.2f}",
                    'Annual Cost': f"${cost*12:,.2f}"
                })
            
            df_costs = pd.DataFrame(cost_data)
            st.dataframe(df_costs, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Error displaying results: {str(e)}")
        logger.error(f"Error in render_enhanced_results: {e}")

def render_enhanced_environment_heatmap_tab():
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
    """Render comprehensive technical recommendations tab."""
    
    st.markdown("### 🔧 Comprehensive Technical Recommendations by Environment")
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.info("💡 Run an enhanced analysis to see detailed technical recommendations.")
        return
    
    results = st.session_state.enhanced_results
    analyzer = EnhancedEnvironmentAnalyzer()
    
    # Environment selector
    selected_env = st.selectbox(
        "Select Environment for Detailed Technical Recommendations:",
        ['PROD', 'PREPROD', 'UAT', 'QA', 'DEV'],
        help="Choose an environment to see comprehensive technical specifications"
    )
    
    env_results = results['recommendations'].get(selected_env, {})
    
    if not env_results:
        st.warning(f"No analysis results available for {selected_env} environment.")
        return
    
    # Get technical recommendations
    tech_recs = analyzer.get_technical_recommendations(selected_env, env_results)
    
    st.markdown(f"## {selected_env} Environment - Technical Specifications")
    
    # Create tabs for different technical areas
    tech_tabs = st.tabs([
        "💻 Compute", "🌐 Network", "💾 Storage", 
        "🗄️ Database", "🔒 Security", "📊 Monitoring"
    ])
    
    # Compute tab
    with tech_tabs[0]:
        st.markdown("#### Compute Configuration")
        
        compute_recs = tech_recs['compute']
        
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
            st.markdown("**Alternative Instance Options**")
            
            alternatives = compute_recs['alternative_instances']
            if alternatives:
                alt_data = []
                for alt in alternatives:
                    alt_data.append({
                        'Instance Type': alt['type'],
                        'Rationale': alt['rationale']
                    })
                
                df_alternatives = pd.DataFrame(alt_data)
                st.dataframe(df_alternatives, use_container_width=True, hide_index=True)
        
        st.markdown("**Deployment Configuration**")
        
        deployment_data = [
            {'Configuration': 'Placement Strategy', 'Recommendation': compute_recs['placement_strategy']},
            {'Configuration': 'Auto Scaling', 'Recommendation': compute_recs['auto_scaling']},
            {'Configuration': 'Pricing Optimization', 'Recommendation': compute_recs['pricing_optimization']}
        ]
        
        df_deployment = pd.DataFrame(deployment_data)
        st.dataframe(df_deployment, use_container_width=True, hide_index=True)
    
    # Network tab
    with tech_tabs[1]:
        st.markdown("#### Network Configuration")
        
        network_recs = tech_recs['network']
        
        network_data = []
        for key, value in network_recs.items():
            network_data.append({'Component': key.replace('_', ' ').title(), 'Configuration': value})
        
        df_network = pd.DataFrame(network_data)
        st.dataframe(df_network, use_container_width=True, hide_index=True)
    
    # Storage tab
    with tech_tabs[2]:
        st.markdown("#### Storage Configuration")
        
        storage_recs = tech_recs['storage']
        
        storage_data = []
        for key, value in storage_recs.items():
            storage_data.append({'Setting': key.replace('_', ' ').title(), 'Configuration': value})
        
        df_storage = pd.DataFrame(storage_data)
        st.dataframe(df_storage, use_container_width=True, hide_index=True)
    
    # Database tab
    with tech_tabs[3]:
        st.markdown("#### Database Configuration")
        
        db_recs = tech_recs['database']
        
        db_data = []
        for key, value in db_recs.items():
            db_data.append({'Setting': key.replace('_', ' ').title(), 'Configuration': value})
        
        df_db = pd.DataFrame(db_data)
        st.dataframe(df_db, use_container_width=True, hide_index=True)
    
    # Security tab
    with tech_tabs[4]:
        st.markdown("#### Security Configuration")
        
        security_recs = tech_recs['security']
        
        security_data = []
        for key, value in security_recs.items():
            security_data.append({'Security Area': key.replace('_', ' ').title(), 'Configuration': value})
        
        df_security = pd.DataFrame(security_data)
        st.dataframe(df_security, use_container_width=True, hide_index=True)
    
    # Monitoring tab
    with tech_tabs[5]:
        st.markdown("#### Monitoring Configuration")
        
        monitoring_recs = tech_recs['monitoring']
        
        monitoring_data = []
        for key, value in monitoring_recs.items():
            monitoring_data.append({'Component': key.replace('_', ' ').title(), 'Configuration': value})
        
        df_monitoring = pd.DataFrame(monitoring_data)
        st.dataframe(df_monitoring, use_container_width=True, hide_index=True)

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
        story.append(Paragraph("Technical Recommendations Summary", styles['Heading1']))
        
        # Production environment technical specs
        prod_env_results = results['recommendations'].get('PROD', {})
        if prod_env_results:
            tech_recs = analyzer.get_technical_recommendations('PROD', prod_env_results)
            
            # Compute recommendations
            story.append(Paragraph("Production Compute Configuration", styles['Heading2']))
            compute_recs = tech_recs['compute']
            
            compute_data = [
                ['Component', 'Specification'],
                ['Instance Type', compute_recs['primary_instance']['type']],
                ['vCPUs', str(compute_recs['primary_instance']['vcpus'])],
                ['Memory (GB)', str(compute_recs['primary_instance']['memory_gb'])],
                ['Placement Strategy', compute_recs['placement_strategy']],
                ['Auto Scaling', compute_recs['auto_scaling']],
                ['Pricing Strategy', compute_recs['pricing_optimization']]
            ]
            
            compute_table = Table(compute_data, colWidths=[2.5*inch, 4*inch])
            compute_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#10b981')),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            story.append(compute_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Recommendations
        recommendations = claude_analysis.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Key Recommendations", styles['Heading2']))
            recs_text = "<br/>".join([f"{i}. {rec}" for i, rec in enumerate(recommendations, 1)])
            story.append(Paragraph(recs_text, styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"Report generated by Enhanced AWS Migration Platform v6.0 on {datetime.now().strftime('%B %d, %Y')}"
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
            mime="application/pdf"
        )
        
        st.success("✅ Enhanced PDF report generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

def get_env_characteristics(env: str) -> str:
    """Get key characteristics for each environment."""
    characteristics = {
        'DEV': 'Development environment with flexible SLAs',
        'QA': 'Testing environment with automated validation',
        'UAT': 'User acceptance with business validation',
        'PREPROD': 'Production-like environment for final testing',
        'PROD': 'Business-critical production environment'
    }
    return characteristics.get(env, 'Standard environment')

# Additional utility functions
def format_currency(amount: float) -> str:
    """Format currency with proper formatting."""
    return f"${amount:,.2f}"

def calculate_savings_percentage(original: float, new: float) -> float:
    """Calculate savings percentage."""
    if original <= 0:
        return 0
    return ((original - new) / original) * 100

def get_complexity_color(score: float) -> str:
    """Get color for complexity score."""
    if score >= 80:
        return "#dc2626"  # Red
    elif score >= 65:
        return "#ea580c"  # Orange
    elif score >= 45:
        return "#ca8a04"  # Yellow
    else:
        return "#16a34a"  # Green

def validate_inputs(inputs: Dict) -> List[str]:
    """Validate user inputs and return list of errors."""
    errors = []
    
    if inputs.get('on_prem_cores', 0) <= 0:
        errors.append("CPU cores must be greater than 0")
    
    if inputs.get('on_prem_ram_gb', 0) <= 0:
        errors.append("RAM must be greater than 0")
    
    if inputs.get('storage_current_gb', 0) <= 0:
        errors.append("Storage must be greater than 0")
    
    return errors

def main():
    """Enhanced main application."""
    
    # Initialize session state
    initialize_enhanced_session_state()
    
    # Check if calculator is properly initialized
    if st.session_state.enhanced_calculator is None:
        st.error("⚠️ Application initialization failed. Please refresh the page.")
        if st.button("🔄 Retry Initialization"):
            st.rerun()
        st.stop()
    
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enhanced AWS Migration Platform v6.0</h1>
        <p>Comprehensive environment analysis with detailed technical recommendations and AI-powered migration insights</p>
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
            <span style="background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">Active</span>
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
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚙️ Configuration",
        "📊 Analysis Results", 
        "🌡️ Environment Heat Maps",
        "🔧 Technical Recommendations",
        "📋 Reports"
    ])
    
    with tab1:
        render_enhanced_configuration()
    
    with tab2:
        render_enhanced_results()
    
    with tab3:
        render_enhanced_environment_heatmap_tab()
    
    with tab4:
        render_technical_recommendations_tab()
    
    with tab5:
        st.markdown("### 📋 Enhanced Reports")
        
        if st.session_state.enhanced_results:
            st.markdown("#### Available Reports")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Generate PDF Report", type="primary"):
                    generate_enhanced_pdf_report()
            
            with col2:
                if st.button("📊 Export to Excel"):
                    st.info("Excel export functionality - install openpyxl for full Excel support")
            
            with col3:
                if st.button("📈 Generate Heat Map CSV"):
                    if 'heat_map_data' in st.session_state.enhanced_results:
                        csv_data = st.session_state.enhanced_results['heat_map_data'].to_csv(index=False)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            "⬇️ Download Heat Map CSV",
                            csv_data,
                            f"environment_heatmap_{timestamp}.csv",
                            "text/csv"
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
        <strong>Enhanced AWS Migration Platform v6.0</strong><br>
        Powered by Claude AI for intelligent migration analysis and comprehensive technical recommendations<br>
        <em>🤖 AI-Enhanced • ☁️ AWS-Native • 📊 Data-Driven • 🔧 Technical-Complete</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()