# Enhanced AWS Migration Application with Detailed Environment Analysis

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io
from typing import Dict, List, Any

# Enhanced Environment Analysis Class
class EnhancedEnvironmentAnalyzer:
    """Enhanced environment analyzer with detailed complexity explanations and technical recommendations."""
    
    def __init__(self):
        self.environments = ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']
        
    def get_detailed_complexity_explanation(self, env: str, env_results: Dict) -> Dict[str, Any]:
        """Get detailed explanation of why an environment has specific complexity."""
        
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
        
        # Generate detailed explanations
        explanations = {
            'overall_score': complexity_score,
            'complexity_level': claude_analysis.get('complexity_level', 'MEDIUM'),
            'factors': factors,
            'detailed_reasons': self._generate_detailed_reasons(env, factors, complexity_score),
            'specific_challenges': self._identify_specific_challenges(env, factors),
            'mitigation_strategies': self._generate_mitigation_strategies(env, factors)
        }
        
        return explanations
    
    def _calculate_resource_intensity(self, requirements: Dict) -> Dict[str, Any]:
        """Calculate resource intensity factor."""
        vcpus = requirements.get('vCPUs', 2)
        ram_gb = requirements.get('RAM_GB', 8)
        storage_gb = requirements.get('storage_GB', 100)
        
        # Calculate intensity score
        cpu_intensity = min(vcpus / 2, 10) * 10  # Max 100 points
        memory_intensity = min(ram_gb / 8, 10) * 10  # Max 100 points
        storage_intensity = min(storage_gb / 100, 10) * 10  # Max 100 points
        
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
        base_risks = {
            'DEV': 20,    # Low risk - can be rebuilt easily
            'QA': 30,     # Low-medium risk - testing environment
            'UAT': 50,    # Medium risk - user acceptance critical
            'PREPROD': 70,  # High risk - production-like
            'PROD': 90    # Very high risk - business critical
        }
        
        base_score = base_risks.get(env, 50)
        
        # Adjust based on Claude analysis
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
                'factors': ['Automated testing integration', 'Test data management', 'Basic performance monitoring'],
                'description': 'Low-medium complexity - automated testing requirements'
            },
            'UAT': {
                'score': 55,
                'factors': ['User access management', 'Performance validation', 'Business process testing'],
                'description': 'Medium complexity - user acceptance validation'
            },
            'PREPROD': {
                'score': 75,
                'factors': ['Production-like configuration', 'Advanced monitoring', 'Disaster recovery testing'],
                'description': 'High complexity - production simulation requirements'
            },
            'PROD': {
                'score': 90,
                'factors': ['24/7 availability', 'Advanced monitoring & alerting', 'Disaster recovery', 'Compliance'],
                'description': 'Very high complexity - business-critical operations'
            }
        }
        
        return complexity_factors.get(env, {'score': 50, 'factors': [], 'description': 'Medium complexity'})
    
    def _calculate_compliance_complexity(self, env: str) -> Dict[str, Any]:
        """Calculate compliance complexity."""
        compliance_scores = {
            'DEV': 10,     # Minimal compliance
            'QA': 20,      # Basic compliance
            'UAT': 40,     # User data compliance
            'PREPROD': 70,  # Near-production compliance
            'PROD': 95     # Full compliance requirements
        }
        
        score = compliance_scores.get(env, 50)
        
        return {
            'score': score,
            'level': self._get_compliance_level(score),
            'requirements': self._get_compliance_requirements(env),
            'description': f'{env} environment compliance requirements'
        }
    
    def _calculate_integration_complexity(self, env: str) -> Dict[str, Any]:
        """Calculate integration complexity."""
        integration_scores = {
            'DEV': 30,     # Basic integrations
            'QA': 45,      # Test integrations
            'UAT': 60,     # User-facing integrations
            'PREPROD': 80,  # Full integration testing
            'PROD': 95     # All production integrations
        }
        
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
        
        # Resource-based reasons
        resource_factor = factors['Resource Intensity']
        if resource_factor['score'] > 70:
            reasons.append(f"High resource requirements: {resource_factor['description']}")
        elif resource_factor['score'] > 40:
            reasons.append(f"Moderate resource requirements: {resource_factor['description']}")
        else:
            reasons.append(f"Light resource requirements: {resource_factor['description']}")
        
        # Migration risk reasons
        migration_factor = factors['Migration Risk']
        if migration_factor['score'] > 70:
            reasons.append(f"High migration risk due to {env} environment criticality")
        
        # Operational complexity reasons
        ops_factor = factors['Operational Complexity']
        if ops_factor['score'] > 60:
            reasons.append(f"Complex operational requirements: {', '.join(ops_factor['factors'][:2])}")
        
        # Compliance reasons
        compliance_factor = factors['Compliance Requirements']
        if compliance_factor['score'] > 50:
            reasons.append(f"Significant compliance requirements for {env} environment")
        
        return reasons
    
    def _identify_specific_challenges(self, env: str, factors: Dict) -> List[str]:
        """Identify specific challenges for the environment."""
        challenges = []
        
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
        """Generate mitigation strategies for environment-specific challenges."""
        strategies = []
        
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
                'Create detailed disaster recovery and business continuity plans',
                'Implement advanced security and compliance controls'
            ]
        }
        
        return env_strategies.get(env, ['Follow standard migration best practices'])
    
    def get_technical_recommendations(self, env: str, env_results: Dict) -> Dict[str, Any]:
        """Get comprehensive technical recommendations for the environment."""
        
        requirements = env_results.get('requirements', {})
        cost_breakdown = env_results.get('cost_breakdown', {})
        selected_instance = cost_breakdown.get('selected_instance', {})
        
        recommendations = {
            'compute': self._get_compute_recommendations(env, selected_instance, requirements),
            'network': self._get_network_recommendations(env, requirements),
            'storage': self._get_storage_recommendations(env, requirements),
            'database': self._get_database_recommendations(env, requirements),
            'security': self._get_security_recommendations(env),
            'monitoring': self._get_monitoring_recommendations(env),
            'backup': self._get_backup_recommendations(env),
            'scaling': self._get_scaling_recommendations(env, requirements)
        }
        
        return recommendations
    
    def _get_compute_recommendations(self, env: str, selected_instance: Dict, requirements: Dict) -> Dict[str, Any]:
        """Get compute-specific recommendations."""
        
        instance_type = selected_instance.get('type', 'N/A')
        vcpus = selected_instance.get('vCPU', requirements.get('vCPUs', 2))
        ram_gb = selected_instance.get('RAM', requirements.get('RAM_GB', 8))
        
        recommendations = {
            'primary_instance': {
                'type': instance_type,
                'vcpus': vcpus,
                'memory_gb': ram_gb,
                'rationale': self._get_instance_rationale(env, instance_type)
            },
            'alternative_instances': self._get_alternative_instances(instance_type, vcpus, ram_gb),
            'placement_strategy': self._get_placement_strategy(env),
            'auto_scaling': self._get_auto_scaling_config(env),
            'pricing_optimization': self._get_pricing_optimization(env, instance_type)
        }
        
        return recommendations
    
    def _get_network_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get network-specific recommendations."""
        
        network_configs = {
            'DEV': {
                'vpc_design': 'Single AZ, basic VPC',
                'subnets': 'Public and private subnets',
                'security_groups': 'Development-focused security groups',
                'load_balancer': 'Application Load Balancer (if needed)',
                'bandwidth': 'Standard bandwidth allocation'
            },
            'QA': {
                'vpc_design': 'Single AZ with testing isolation',
                'subnets': 'Isolated testing subnets',
                'security_groups': 'Testing-specific security groups',
                'load_balancer': 'ALB for load testing',
                'bandwidth': 'Enhanced bandwidth for testing'
            },
            'UAT': {
                'vpc_design': 'Multi-AZ for availability testing',
                'subnets': 'Production-like subnet design',
                'security_groups': 'Production-like security',
                'load_balancer': 'ALB with SSL termination',
                'bandwidth': 'Production-like bandwidth'
            },
            'PREPROD': {
                'vpc_design': 'Full multi-AZ production design',
                'subnets': 'Production mirror subnet design',
                'security_groups': 'Production security groups',
                'load_balancer': 'ALB/NLB with full features',
                'bandwidth': 'Production bandwidth allocation'
            },
            'PROD': {
                'vpc_design': 'Multi-AZ with disaster recovery',
                'subnets': 'Highly available subnet design',
                'security_groups': 'Strict production security',
                'load_balancer': 'ALB/NLB with advanced features',
                'bandwidth': 'Premium bandwidth with burst capability'
            }
        }
        
        config = network_configs.get(env, network_configs['UAT'])
        
        config.update({
            'cdn': 'CloudFront' if env in ['PREPROD', 'PROD'] else 'Optional',
            'dns': 'Route 53 with health checks' if env == 'PROD' else 'Route 53 basic',
            'nat_gateway': 'Required' if env in ['PREPROD', 'PROD'] else 'Optional',
            'direct_connect': 'Recommended' if env == 'PROD' else 'Not required',
            'vpn': 'Site-to-site VPN for secure access'
        })
        
        return config
    
    def _get_storage_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get storage-specific recommendations."""
        
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
        
        # Add storage sizing recommendations
        config.update({
            'recommended_size': f"{storage_gb * self._get_storage_multiplier(env)} GB",
            'iops_recommendation': self._get_iops_recommendation(env, storage_gb),
            'throughput_recommendation': self._get_throughput_recommendation(env),
            'lifecycle_policy': self._get_lifecycle_policy(env)
        })
        
        return config
    
    def _get_database_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get database-specific recommendations."""
        
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
            'maintenance_window': self._get_maintenance_window(env),
            'parameter_groups': 'Environment-specific optimization'
        })
        
        return config
    
    def _get_security_recommendations(self, env: str) -> Dict[str, Any]:
        """Get security-specific recommendations."""
        
        security_configs = {
            'DEV': {
                'iam_roles': 'Developer access with resource restrictions',
                'encryption': 'Standard EBS and S3 encryption',
                'network_security': 'Basic security groups and NACLs',
                'compliance': 'Basic security standards',
                'monitoring': 'CloudTrail for audit logging'
            },
            'QA': {
                'iam_roles': 'QA team access with testing permissions',
                'encryption': 'Enhanced encryption for test data',
                'network_security': 'Restricted security groups',
                'compliance': 'Testing environment standards',
                'monitoring': 'CloudTrail + Config for compliance'
            },
            'UAT': {
                'iam_roles': 'Business user access with approval workflows',
                'encryption': 'Production-grade encryption',
                'network_security': 'Production-like security controls',
                'compliance': 'Pre-production compliance validation',
                'monitoring': 'Security Hub + GuardDuty'
            },
            'PREPROD': {
                'iam_roles': 'Production-like role-based access',
                'encryption': 'Customer-managed key encryption',
                'network_security': 'Strict production security',
                'compliance': 'Full compliance validation',
                'monitoring': 'Complete security monitoring stack'
            },
            'PROD': {
                'iam_roles': 'Least privilege production access',
                'encryption': 'Customer-managed keys with rotation',
                'network_security': 'Maximum security controls',
                'compliance': 'Full regulatory compliance',
                'monitoring': 'Complete security and compliance monitoring'
            }
        }
        
        config = security_configs.get(env, security_configs['UAT'])
        
        config.update({
            'secrets_management': 'AWS Secrets Manager',
            'certificate_management': 'ACM with auto-renewal',
            'vulnerability_scanning': 'Inspector' if env in ['PREPROD', 'PROD'] else 'Basic',
            'penetration_testing': 'Required' if env == 'PROD' else 'Recommended'
        })
        
        return config
    
    def _get_monitoring_recommendations(self, env: str) -> Dict[str, Any]:
        """Get monitoring-specific recommendations."""
        
        monitoring_configs = {
            'DEV': {
                'cloudwatch': 'Basic metrics and logs',
                'alerting': 'Development team notifications',
                'dashboards': 'Basic development dashboard',
                'log_retention': '30 days'
            },
            'QA': {
                'cloudwatch': 'Enhanced metrics for testing',
                'alerting': 'QA team and development notifications',
                'dashboards': 'Testing performance dashboard',
                'log_retention': '60 days'
            },
            'UAT': {
                'cloudwatch': 'Production-like monitoring',
                'alerting': 'Business stakeholder notifications',
                'dashboards': 'Business-focused dashboards',
                'log_retention': '90 days'
            },
            'PREPROD': {
                'cloudwatch': 'Full production monitoring',
                'alerting': 'Operations team 24/7 alerts',
                'dashboards': 'Comprehensive operations dashboard',
                'log_retention': '1 year'
            },
            'PROD': {
                'cloudwatch': 'Premium monitoring with custom metrics',
                'alerting': '24/7 operations with escalation',
                'dashboards': 'Executive and operations dashboards',
                'log_retention': 'Long-term retention (3+ years)'
            }
        }
        
        config = monitoring_configs.get(env, monitoring_configs['UAT'])
        
        config.update({
            'apm': 'X-Ray' if env in ['PREPROD', 'PROD'] else 'Optional',
            'synthetic_monitoring': 'Required' if env == 'PROD' else 'Recommended',
            'cost_monitoring': 'Cost Explorer + Budgets',
            'health_checks': 'Route 53 health checks' if env in ['PREPROD', 'PROD'] else 'Basic'
        })
        
        return config
    
    def _get_backup_recommendations(self, env: str) -> Dict[str, Any]:
        """Get backup-specific recommendations."""
        
        backup_configs = {
            'DEV': {
                'frequency': 'Daily',
                'retention': '7 days',
                'cross_region': False,
                'testing': 'Monthly'
            },
            'QA': {
                'frequency': 'Daily',
                'retention': '14 days', 
                'cross_region': False,
                'testing': 'Bi-weekly'
            },
            'UAT': {
                'frequency': 'Twice daily',
                'retention': '30 days',
                'cross_region': False,
                'testing': 'Weekly'
            },
            'PREPROD': {
                'frequency': 'Every 6 hours',
                'retention': '90 days',
                'cross_region': True,
                'testing': 'Weekly'
            },
            'PROD': {
                'frequency': 'Continuous (point-in-time recovery)',
                'retention': '7 years (compliance)',
                'cross_region': True,
                'testing': 'Daily'
            }
        }
        
        return backup_configs.get(env, backup_configs['UAT'])
    
    def _get_scaling_recommendations(self, env: str, requirements: Dict) -> Dict[str, Any]:
        """Get auto-scaling recommendations."""
        
        scaling_configs = {
            'DEV': {
                'auto_scaling': 'Basic scaling for cost optimization',
                'min_instances': 1,
                'max_instances': 2,
                'target_utilization': '70%'
            },
            'QA': {
                'auto_scaling': 'Load testing optimized scaling',
                'min_instances': 1,
                'max_instances': 4,
                'target_utilization': '60%'
            },
            'UAT': {
                'auto_scaling': 'User load optimized scaling',
                'min_instances': 2,
                'max_instances': 6,
                'target_utilization': '65%'
            },
            'PREPROD': {
                'auto_scaling': 'Production-like scaling',
                'min_instances': 2,
                'max_instances': 10,
                'target_utilization': '70%'
            },
            'PROD': {
                'auto_scaling': 'High availability scaling',
                'min_instances': 3,
                'max_instances': 20,
                'target_utilization': '75%'
            }
        }
        
        return scaling_configs.get(env, scaling_configs['UAT'])
    
    # Helper methods for various calculations and descriptions
    def _get_resource_description(self, score: float) -> str:
        if score > 70:
            return "High resource intensity requiring powerful instances"
        elif score > 40:
            return "Moderate resource requirements"
        else:
            return "Light resource requirements suitable for smaller instances"
    
    def _get_risk_level(self, score: float) -> str:
        if score > 80:
            return "Very High"
        elif score > 60:
            return "High"
        elif score > 40:
            return "Medium"
        elif score > 20:
            return "Low"
        else:
            return "Very Low"
    
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
        if score > 80:
            return "Full Compliance"
        elif score > 60:
            return "High Compliance"
        elif score > 40:
            return "Medium Compliance"
        else:
            return "Basic Compliance"
    
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
        if score > 80:
            return "Complex"
        elif score > 60:
            return "Moderate"
        else:
            return "Simple"
    
    def _get_integration_points(self, env: str) -> List[str]:
        integrations = {
            'DEV': ['CI/CD systems', 'Development tools', 'Version control'],
            'QA': ['Testing frameworks', 'Test data systems', 'Reporting tools'],
            'UAT': ['Business applications', 'User directories', 'Approval systems'],
            'PREPROD': ['Production integrations', 'Monitoring systems', 'External APIs'],
            'PROD': ['All business systems', 'External partners', 'Real-time integrations']
        }
        return integrations.get(env, ['Standard integrations'])
    
    def _get_instance_rationale(self, env: str, instance_type: str) -> str:
        return f"Selected {instance_type} for {env} environment based on performance requirements and cost optimization"
    
    def _get_alternative_instances(self, primary_type: str, vcpus: int, ram_gb: int) -> List[Dict]:
        # This would return alternative instance recommendations
        return [
            {'type': 'm6a.large', 'rationale': 'AMD-based cost optimization'},
            {'type': 'c6i.xlarge', 'rationale': 'Compute-optimized alternative'}
        ]
    
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
    
    def _get_pricing_optimization(self, env: str, instance_type: str) -> str:
        optimizations = {
            'DEV': 'Spot instances recommended for cost savings',
            'QA': 'Mix of on-demand and spot instances',
            'UAT': 'On-demand with some reserved instances',
            'PREPROD': 'Reserved instances for predictable costs',
            'PROD': 'Reserved instances with savings plans'
        }
        return optimizations.get(env, 'Standard pricing')
    
    def _get_storage_multiplier(self, env: str) -> float:
        multipliers = {
            'DEV': 1.0,
            'QA': 1.2,
            'UAT': 1.3,
            'PREPROD': 1.4,
            'PROD': 1.5
        }
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


# Enhanced PDF Report Generator
class EnhancedPDFReportGenerator:
    """Enhanced PDF report generator with proper formatting."""
    
    def generate_enhanced_pdf_report(self, results: Dict, sections: List[str], company_name: str, title: str, timestamp: str) -> io.BytesIO:
        """Generate enhanced PDF report with proper formatting."""
        
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            
            buffer = io.BytesIO()
            
            # Create document with proper margins
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                topMargin=1*inch,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch,
                bottomMargin=1*inch
            )
            
            # Get default styles
            styles = getSampleStyleSheet()
            
            # Create custom styles with proper spacing
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=20,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1f2937'),
                fontName='Helvetica-Bold'
            )
            
            heading1_style = ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontSize=16,
                spaceBefore=20,
                spaceAfter=12,
                textColor=colors.HexColor('#374151'),
                fontName='Helvetica-Bold'
            )
            
            heading2_style = ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=16,
                spaceAfter=10,
                textColor=colors.HexColor('#4b5563'),
                fontName='Helvetica-Bold'
            )
            
            heading3_style = ParagraphStyle(
                'CustomHeading3',
                parent=styles['Heading3'],
                fontSize=12,
                spaceBefore=12,
                spaceAfter=8,
                textColor=colors.HexColor('#6b7280'),
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceBefore=6,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                fontName='Helvetica'
            )
            
            bullet_style = ParagraphStyle(
                'CustomBullet',
                parent=styles['Normal'],
                fontSize=10,
                spaceBefore=3,
                spaceAfter=3,
                leftIndent=20,
                fontName='Helvetica'
            )
            
            # Story elements
            story = []
            
            # Title page
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.3*inch))
            
            story.append(Paragraph(f"<b>{company_name}</b>", normal_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
            story.append(Spacer(1, 0.5*inch))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", heading1_style))
            
            prod_results = results['recommendations']['PROD']
            claude_analysis = prod_results.get('claude_analysis', {})
            tco_analysis = prod_results.get('tco_analysis', {})
            
            summary_data = [
                ['Metric', 'Value'],
                ['Workload Name', results['inputs']['workload_name']],
                ['Migration Complexity', f"{claude_analysis.get('complexity_level', 'MEDIUM')} ({claude_analysis.get('complexity_score', 50):.0f}/100)"],
                ['Recommended Strategy', claude_analysis.get('migration_strategy', {}).get('approach', 'Standard Migration')],
                ['Estimated Timeline', f"{claude_analysis.get('estimated_timeline', {}).get('max_weeks', 8)} weeks"],
                ['Monthly Cost', f"${tco_analysis.get('monthly_cost', 0):,.2f}"],
                ['Best Pricing Option', tco_analysis.get('best_pricing_option', 'N/A').replace('_', ' ').title()],
                ['Projected 3-Year ROI', f"{tco_analysis.get('roi_3_years', 0):.1f}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
            ]))
            
            story.append(summary_table)
            story.append(PageBreak())
            
            # Environment Analysis
            if "Environment Heat Map" in sections:
                story.append(Paragraph("Environment Analysis Overview", heading1_style))
                
                # Environment comparison table
                env_data = [['Environment', 'Complexity Score', 'Instance Type', 'Monthly Cost', 'Key Characteristics']]
                
                for env in ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']:
                    env_results = results['recommendations'].get(env, {})
                    claude_env_analysis = env_results.get('claude_analysis', {})
                    cost_breakdown = env_results.get('cost_breakdown', {})
                    selected_instance = cost_breakdown.get('selected_instance', {})
                    total_costs = cost_breakdown.get('total_costs', {})
                    
                    # Get environment characteristics
                    characteristics = self._get_env_characteristics(env)
                    
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
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#93c5fd')),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eff6ff')])
                ]))
                
                story.append(env_table)
                story.append(Spacer(1, 0.3*inch))
                
                # Detailed environment explanations
                story.append(Paragraph("Detailed Environment Complexity Analysis", heading2_style))
                
                analyzer = EnhancedEnvironmentAnalyzer()
                
                for env in ['PROD', 'PREPROD', 'UAT']:  # Focus on key environments
                    env_results = results['recommendations'].get(env, {})
                    
                    if env_results:
                        complexity_explanation = analyzer.get_detailed_complexity_explanation(env, env_results)
                        
                        story.append(Paragraph(f"{env} Environment", heading3_style))
                        
                        # Complexity factors
                        factors_text = f"<b>Complexity Score:</b> {complexity_explanation['overall_score']:.0f}/100 ({complexity_explanation['complexity_level']})<br/><br/>"
                        factors_text += "<b>Key Complexity Factors:</b><br/>"
                        
                        for reason in complexity_explanation['detailed_reasons']:
                            factors_text += f"• {reason}<br/>"
                        
                        story.append(Paragraph(factors_text, normal_style))
                        
                        # Specific challenges
                        challenges_text = "<b>Specific Challenges:</b><br/>"
                        for challenge in complexity_explanation['specific_challenges'][:3]:  # Top 3
                            challenges_text += f"• {challenge}<br/>"
                        
                        story.append(Paragraph(challenges_text, normal_style))
                        story.append(Spacer(1, 0.2*inch))
                
                story.append(PageBreak())
            
            # Technical Recommendations Section
            if "Technical Specifications" in sections:
                story.append(Paragraph("Comprehensive Technical Recommendations", heading1_style))
                
                analyzer = EnhancedEnvironmentAnalyzer()
                
                for env in ['PROD', 'PREPROD']:  # Focus on critical environments
                    env_results = results['recommendations'].get(env, {})
                    
                    if env_results:
                        tech_recs = analyzer.get_technical_recommendations(env, env_results)
                        
                        story.append(Paragraph(f"{env} Environment Technical Specifications", heading2_style))
                        
                        # Compute recommendations
                        compute_recs = tech_recs['compute']
                        story.append(Paragraph("Compute Configuration", heading3_style))
                        
                        compute_data = [
                            ['Component', 'Specification', 'Rationale'],
                            ['Instance Type', compute_recs['primary_instance']['type'], compute_recs['primary_instance']['rationale']],
                            ['vCPUs', str(compute_recs['primary_instance']['vcpus']), 'Based on workload requirements'],
                            ['Memory', f"{compute_recs['primary_instance']['memory_gb']} GB", 'Optimized for application needs'],
                            ['Placement Strategy', compute_recs['placement_strategy'], 'Environment-specific placement'],
                            ['Auto Scaling', compute_recs['auto_scaling'], 'Availability and cost optimization'],
                            ['Pricing Strategy', compute_recs['pricing_optimization'], 'Cost optimization approach']
                        ]
                        
                        compute_table = Table(compute_data, colWidths=[1.5*inch, 2.5*inch, 3*inch])
                        compute_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#10b981')),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecfdf5')])
                        ]))
                        
                        story.append(compute_table)
                        story.append(Spacer(1, 0.2*inch))
                        
                        # Network recommendations
                        network_recs = tech_recs['network']
                        story.append(Paragraph("Network Configuration", heading3_style))
                        
                        network_data = [
                            ['Component', 'Configuration'],
                            ['VPC Design', network_recs['vpc_design']],
                            ['Subnet Strategy', network_recs['subnets']],
                            ['Load Balancer', network_recs['load_balancer']],
                            ['CDN', network_recs['cdn']],
                            ['DNS', network_recs['dns']],
                            ['VPN', network_recs['vpn']]
                        ]
                        
                        network_table = Table(network_data, colWidths=[2*inch, 5*inch])
                        network_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#f87171')),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef2f2')])
                        ]))
                        
                        story.append(network_table)
                        story.append(Spacer(1, 0.2*inch))
                        
                        # Storage recommendations
                        storage_recs = tech_recs['storage']
                        story.append(Paragraph("Storage Configuration", heading3_style))
                        
                        storage_data = [
                            ['Component', 'Configuration'],
                            ['Primary Storage', storage_recs['primary_storage']],
                            ['Recommended Size', storage_recs['recommended_size']],
                            ['IOPS', storage_recs['iops_recommendation']],
                            ['Throughput', storage_recs['throughput_recommendation']],
                            ['Backup Strategy', storage_recs['backup_strategy']],
                            ['Encryption', storage_recs['encryption']]
                        ]
                        
                        storage_table = Table(storage_data, colWidths=[2*inch, 5*inch])
                        storage_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c2d12')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#a78bfa')),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f3ff')])
                        ]))
                        
                        story.append(storage_table)
                        
                        if env == 'PROD':  # Add page break after PROD section
                            story.append(PageBreak())
                        else:
                            story.append(Spacer(1, 0.3*inch))
            
            # Migration Steps (from existing code)
            if "Claude AI Migration Analysis" in sections:
                story.append(Paragraph("Migration Implementation Plan", heading1_style))
                
                migration_steps = claude_analysis.get('migration_steps', [])
                if migration_steps:
                    for i, step in enumerate(migration_steps, 1):
                        if isinstance(step, dict):
                            story.append(Paragraph(f"Phase {i}: {step.get('phase', 'N/A')} ({step.get('duration', 'N/A')})", heading3_style))
                            
                            tasks = step.get('tasks', [])
                            if tasks:
                                tasks_text = "<b>Key Tasks:</b><br/>"
                                for task in tasks:
                                    tasks_text += f"• {task}<br/>"
                                story.append(Paragraph(tasks_text, normal_style))
                            
                            deliverables = step.get('deliverables', [])
                            if deliverables:
                                deliverables_text = f"<b>Deliverables:</b> {', '.join(deliverables)}"
                                story.append(Paragraph(deliverables_text, normal_style))
                            
                            story.append(Spacer(1, 0.15*inch))
                
                story.append(PageBreak())
            
            # Implementation Recommendations
            story.append(Paragraph("Implementation Recommendations", heading1_style))
            
            recommendations = claude_analysis.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("Key Recommendations", heading2_style))
                recs_text = ""
                for i, rec in enumerate(recommendations, 1):
                    recs_text += f"{i}. {rec}<br/>"
                story.append(Paragraph(recs_text, normal_style))
                story.append(Spacer(1, 0.2*inch))
            
            success_factors = claude_analysis.get('success_factors', [])
            if success_factors:
                story.append(Paragraph("Critical Success Factors", heading2_style))
                factors_text = ""
                for i, factor in enumerate(success_factors, 1):
                    factors_text += f"{i}. {factor}<br/>"
                story.append(Paragraph(factors_text, normal_style))
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer_text = f"Report generated by Enterprise AWS Workload Sizing Platform v5.0 on {datetime.now().strftime('%B %d, %Y')}"
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#6b7280')
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            st.error(f"Error generating enhanced PDF: {str(e)}")
            return None
    
    def _get_env_characteristics(self, env: str) -> str:
        """Get key characteristics for each environment."""
        characteristics = {
            'DEV': 'Development environment with flexible SLAs',
            'QA': 'Testing environment with automated validation',
            'UAT': 'User acceptance with business validation',
            'PREPROD': 'Production-like environment for final testing',
            'PROD': 'Business-critical production environment'
        }
        return characteristics.get(env, 'Standard environment')


# Enhanced Streamlit Application Functions
def render_enhanced_environment_heatmap_tab():
    """Render enhanced environment heat map tab with detailed explanations."""
    
    st.markdown("### 🌡️ Environment Impact Analysis with Detailed Explanations")
    
    if 'enhanced_results' not in st.session_state or not st.session_state.enhanced_results:
        st.info("💡 Run an enhanced analysis to see detailed environment heat maps and explanations.")
        return
    
    results = st.session_state.enhanced_results
    analyzer = EnhancedEnvironmentAnalyzer()
    
    # Environment overview cards with complexity explanations
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
            
            env_class = f"env-{env.lower()}"
            
            # Create expandable card with explanation
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
        st.plotly_chart(results['heat_map_fig'], use_container_width=True, key="detailed_environment_heat_map")
    
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
            'Compliance Requirements': f"{factors['Compliance Requirements']['score']:.0f}/100",
            'Integration Dependencies': f"{factors['Integration Dependencies']['score']:.0f}/100",
            'Primary Reason': complexity_explanation['detailed_reasons'][0] if complexity_explanation['detailed_reasons'] else 'N/A'
        })
    
    df_detailed = pd.DataFrame(detailed_data)
    st.dataframe(df_detailed, use_container_width=True, hide_index=True)
    
    # Complexity factor visualization
    st.markdown("#### Complexity Factors Comparison")
    
    # Create radar chart for complexity factors
    factor_names = ['Resource Intensity', 'Migration Risk', 'Operational Complexity', 'Compliance Requirements', 'Integration Dependencies']
    
    fig_radar = go.Figure()
    
    for env in ['DEV', 'QA', 'UAT', 'PREPROD', 'PROD']:
        env_results = results['recommendations'].get(env, {})
        complexity_explanation = analyzer.get_detailed_complexity_explanation(env, env_results)
        factors = complexity_explanation['factors']
        
        factor_scores = [factors[factor]['score'] for factor in factor_names]
        
        fig_radar.add_trace(go.Scatterpolar(
            r=factor_scores,
            theta=factor_names,
            fill='toself',
            name=env,
            line=dict(width=2)
        ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Environment Complexity Factors Comparison",
        height=600
    )
    
    st.plotly_chart(fig_radar, use_container_width=True, key="complexity_factors_radar")


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
        "🗄️ Database", "🔒 Security", "📊 Monitoring", 
        "💼 Backup", "⚡ Auto Scaling"
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Core Network Components**")
            
            core_network_data = [
                {'Component': 'VPC Design', 'Configuration': network_recs['vpc_design']},
                {'Component': 'Subnets', 'Configuration': network_recs['subnets']},
                {'Component': 'Security Groups', 'Configuration': network_recs['security_groups']},
                {'Component': 'Load Balancer', 'Configuration': network_recs['load_balancer']}
            ]
            
            df_core_network = pd.DataFrame(core_network_data)
            st.dataframe(df_core_network, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Advanced Network Services**")
            
            advanced_network_data = [
                {'Service': 'CDN', 'Configuration': network_recs['cdn']},
                {'Service': 'DNS', 'Configuration': network_recs['dns']},
                {'Service': 'NAT Gateway', 'Configuration': network_recs['nat_gateway']},
                {'Service': 'VPN', 'Configuration': network_recs['vpn']}
            ]
            
            df_advanced_network = pd.DataFrame(advanced_network_data)
            st.dataframe(df_advanced_network, use_container_width=True, hide_index=True)
        
        # Network performance recommendations
        st.markdown("**Network Performance Optimization**")
        
        perf_recommendations = [
            "🔧 Enable Enhanced Networking (SR-IOV) for better performance",
            "📊 Implement CloudWatch monitoring for network metrics",
            "🎯 Use Placement Groups for low-latency applications",
            "🌐 Configure multiple AZs for high availability",
            "⚡ Optimize security group rules for performance"
        ]
        
        for rec in perf_recommendations:
            st.markdown(rec)
    
    # Storage tab
    with tech_tabs[2]:
        st.markdown("#### Storage Configuration")
        
        storage_recs = tech_recs['storage']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Primary Storage Configuration**")
            
            storage_config_data = [
                {'Setting': 'Storage Type', 'Value': storage_recs['primary_storage']},
                {'Setting': 'Recommended Size', 'Value': storage_recs['recommended_size']},
                {'Setting': 'IOPS', 'Value': storage_recs['iops_recommendation']},
                {'Setting': 'Throughput', 'Value': storage_recs['throughput_recommendation']}
            ]
            
            df_storage_config = pd.DataFrame(storage_config_data)
            st.dataframe(df_storage_config, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Data Protection & Management**")
            
            protection_data = [
                {'Feature': 'Backup Strategy', 'Configuration': storage_recs['backup_strategy']},
                {'Feature': 'Encryption', 'Configuration': storage_recs['encryption']},
                {'Feature': 'Performance', 'Configuration': storage_recs['performance']},
                {'Feature': 'Lifecycle Policy', 'Configuration': storage_recs['lifecycle_policy']}
            ]
            
            df_protection = pd.DataFrame(protection_data)
            st.dataframe(df_protection, use_container_width=True, hide_index=True)
    
    # Database tab
    with tech_tabs[3]:
        st.markdown("#### Database Configuration")
        
        db_recs = tech_recs['database']
        
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
            st.markdown("**Advanced Database Features**")
            
            db_advanced_data = [
                {'Feature': 'Read Replicas', 'Configuration': db_recs['read_replicas']},
                {'Feature': 'Connection Pooling', 'Configuration': db_recs['connection_pooling']},
                {'Feature': 'Maintenance Window', 'Configuration': db_recs['maintenance_window']},
                {'Feature': 'Monitoring', 'Configuration': db_recs['monitoring']}
            ]
            
            df_db_advanced = pd.DataFrame(db_advanced_data)
            st.dataframe(df_db_advanced, use_container_width=True, hide_index=True)
    
    # Security tab
    with tech_tabs[4]:
        st.markdown("#### Security Configuration")
        
        security_recs = tech_recs['security']
        
        security_areas = [
            ('IAM & Access Control', security_recs['iam_roles']),
            ('Encryption', security_recs['encryption']),
            ('Network Security', security_recs['network_security']),
            ('Compliance', security_recs['compliance']),
            ('Monitoring & Logging', security_recs['monitoring']),
            ('Secrets Management', security_recs['secrets_management']),
            ('Certificate Management', security_recs['certificate_management'])
        ]
        
        security_data = []
        for area, config in security_areas:
            security_data.append({'Security Area': area, 'Configuration': config})
        
        df_security = pd.DataFrame(security_data)
        st.dataframe(df_security, use_container_width=True, hide_index=True)
        
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
    
    # Monitoring tab
    with tech_tabs[5]:
        st.markdown("#### Monitoring Configuration")
        
        monitoring_recs = tech_recs['monitoring']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Core Monitoring Setup**")
            
            monitoring_core_data = [
                {'Component': 'CloudWatch', 'Configuration': monitoring_recs['cloudwatch']},
                {'Component': 'Alerting', 'Configuration': monitoring_recs['alerting']},
                {'Component': 'Dashboards', 'Configuration': monitoring_recs['dashboards']},
                {'Component': 'Log Retention', 'Configuration': monitoring_recs['log_retention']}
            ]
            
            df_monitoring_core = pd.DataFrame(monitoring_core_data)
            st.dataframe(df_monitoring_core, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Advanced Monitoring Services**")
            
            monitoring_advanced_data = [
                {'Service': 'APM (X-Ray)', 'Configuration': monitoring_recs['apm']},
                {'Service': 'Synthetic Monitoring', 'Configuration': monitoring_recs['synthetic_monitoring']},
                {'Service': 'Cost Monitoring', 'Configuration': monitoring_recs['cost_monitoring']},
                {'Service': 'Health Checks', 'Configuration': monitoring_recs['health_checks']}
            ]
            
            df_monitoring_advanced = pd.DataFrame(monitoring_advanced_data)
            st.dataframe(df_monitoring_advanced, use_container_width=True, hide_index=True)
    
    # Backup tab
    with tech_tabs[6]:
        st.markdown("#### Backup & Disaster Recovery Configuration")
        
        backup_recs = tech_recs['backup']
        
        backup_data = [
            {'Backup Setting': 'Frequency', 'Configuration': backup_recs['frequency']},
            {'Backup Setting': 'Retention Period', 'Configuration': backup_recs['retention']},
            {'Backup Setting': 'Cross-Region Backup', 'Configuration': 'Yes' if backup_recs['cross_region'] else 'No'},
            {'Backup Setting': 'Backup Testing Frequency', 'Configuration': backup_recs['testing']}
        ]
        
        df_backup = pd.DataFrame(backup_data)
        st.dataframe(df_backup, use_container_width=True, hide_index=True)
        
        # Backup strategy visualization
        st.markdown("**Backup Strategy Timeline**")
        
        backup_timeline = f"""
        **{selected_env} Environment Backup Strategy:**
        
        • **Frequency:** {backup_recs['frequency']}
        • **Retention:** {backup_recs['retention']}
        • **Cross-Region:** {'Enabled' if backup_recs['cross_region'] else 'Disabled'}
        • **Testing Schedule:** {backup_recs['testing']}
        
        This backup strategy ensures {'business continuity' if selected_env == 'PROD' else 'data protection'} 
        appropriate for the {selected_env} environment requirements.
        """
        
        st.markdown(backup_timeline)
    
    # Auto Scaling tab
    with tech_tabs[7]:
        st.markdown("#### Auto Scaling Configuration")
        
        scaling_recs = tech_recs['scaling']
        
        scaling_data = [
            {'Scaling Parameter': 'Auto Scaling Type', 'Value': scaling_recs['auto_scaling']},
            {'Scaling Parameter': 'Minimum Instances', 'Value': str(scaling_recs['min_instances'])},
            {'Scaling Parameter': 'Maximum Instances', 'Value': str(scaling_recs['max_instances'])},
            {'Scaling Parameter': 'Target CPU Utilization', 'Value': scaling_recs['target_utilization']}
        ]
        
        df_scaling = pd.DataFrame(scaling_data)
        st.dataframe(df_scaling, use_container_width=True, hide_index=True)
        
        # Scaling strategy explanation
        st.markdown("**Auto Scaling Strategy**")
        
        scaling_explanation = f"""
        The {selected_env} environment is configured with:
        
        • **Minimum Capacity:** {scaling_recs['min_instances']} instances to ensure availability
        • **Maximum Capacity:** {scaling_recs['max_instances']} instances for peak load handling
        • **Target Utilization:** {scaling_recs['target_utilization']} CPU utilization for optimal performance
        • **Scaling Type:** {scaling_recs['auto_scaling']}
        
        This configuration balances cost optimization with performance requirements for the {selected_env} environment.
        """
        
        st.markdown(scaling_explanation)
    
    # Summary recommendations for the environment
    st.markdown("---")
    st.markdown(f"### 📋 {selected_env} Environment Implementation Summary")
    
    summary_recommendations = [
        f"🏗️ **Architecture:** Deploy using {tech_recs['compute']['placement_strategy'].lower()}",
        f"🔧 **Compute:** Use {tech_recs['compute']['primary_instance']['type']} instances with {tech_recs['scaling']['auto_scaling'].lower()}",
        f"🌐 **Network:** Implement {tech_recs['network']['vpc_design'].lower()} with {tech_recs['network']['load_balancer']}",
        f"💾 **Storage:** Configure {tech_recs['storage']['primary_storage']} with {tech_recs['storage']['backup_strategy'].lower()}",
        f"🗄️ **Database:** Deploy {tech_recs['database']['engine']} with {tech_recs['database']['backup_retention']} backup retention",
        f"🔒 **Security:** Implement {tech_recs['security']['compliance'].lower()} with {tech_recs['security']['encryption'].lower()}",
        f"📊 **Monitoring:** Set up {tech_recs['monitoring']['cloudwatch'].lower()} with {tech_recs['monitoring']['alerting'].lower()}",
        f"💼 **Backup:** Configure {backup_recs['frequency'].lower()} backups with {backup_recs['retention']} retention"
    ]
    
    for rec in summary_recommendations:
        st.markdown(rec)


# Enhanced main application integration
def main():
    """Enhanced main application."""
    
    st.set_page_config(
        page_title="Enhanced AWS Migration Platform",
        layout="wide",
        page_icon="🏢"
    )
    
    # Enhanced header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h1>🏢 Enhanced AWS Migration Platform v6.0</h1>
        <p>Comprehensive environment analysis with detailed technical recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'enhanced_results' not in st.session_state:
        st.session_state.enhanced_results = None
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚙️ Configuration", 
        "📊 Analysis Results",
        "🌡️ Environment Heat Maps", 
        "🔧 Technical Recommendations"
    ])
    
    with tab1:
        st.markdown("### Configuration")
        # Add your existing configuration code here
        st.info("Configure your workload parameters here")
    
    with tab2:
        st.markdown("### Analysis Results")
        # Add your existing results code here
        st.info("Analysis results will appear here")
    
    with tab3:
        render_enhanced_environment_heatmap_tab()
    
    with tab4:
        render_technical_recommendations_tab()

if __name__ == "__main__":
    main()