import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from io import BytesIO

# Configure Streamlit page
st.set_page_config(
    page_title="AWS EC2 Workload Sizing Calculator",
    layout="wide",
    page_icon="☁️",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #FF9500 0%, #FF6B35 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #FF6B35;
    }
    .metric-label {
        color: #6b7280;
        font-size: 0.875rem;
    }
    .recommendation {
        background: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class InstanceType:
    """AWS EC2 Instance Type data structure"""
    name: str
    vcpu: int
    memory: int
    family: str
    pricing: Dict[str, float]
    network_performance: str

@dataclass
class WorkloadProfile:
    """Workload profile configuration"""
    name: str
    cpu_factor: float
    memory_factor: float
    storage_factor: float
    description: str

class AWSPricingData:
    """Centralized AWS pricing data management"""
    
    def __init__(self):
        self.instance_types = self._load_instance_types()
        self.workload_profiles = self._load_workload_profiles()
        self.regions = self._load_regions()
    
    def _load_instance_types(self) -> List[InstanceType]:
        """Load AWS EC2 instance types with pricing"""
        return [
            InstanceType("t3.medium", 2, 4, "general", {"on_demand": 0.0416, "reserved": 0.025, "spot": 0.012}, "Up to 5 Gbps"),
            InstanceType("t3.large", 2, 8, "general", {"on_demand": 0.0832, "reserved": 0.050, "spot": 0.025}, "Up to 5 Gbps"),
            InstanceType("t3.xlarge", 4, 16, "general", {"on_demand": 0.1664, "reserved": 0.100, "spot": 0.050}, "Up to 5 Gbps"),
            InstanceType("m6i.large", 2, 8, "general", {"on_demand": 0.0864, "reserved": 0.052, "spot": 0.026}, "Up to 12.5 Gbps"),
            InstanceType("m6i.xlarge", 4, 16, "general", {"on_demand": 0.1728, "reserved": 0.104, "spot": 0.052}, "Up to 12.5 Gbps"),
            InstanceType("m6i.2xlarge", 8, 32, "general", {"on_demand": 0.3456, "reserved": 0.208, "spot": 0.104}, "Up to 12.5 Gbps"),
            InstanceType("m6i.4xlarge", 16, 64, "general", {"on_demand": 0.6912, "reserved": 0.415, "spot": 0.207}, "12.5 Gbps"),
            InstanceType("r6i.large", 2, 16, "memory", {"on_demand": 0.1008, "reserved": 0.061, "spot": 0.030}, "Up to 12.5 Gbps"),
            InstanceType("r6i.xlarge", 4, 32, "memory", {"on_demand": 0.2016, "reserved": 0.121, "spot": 0.061}, "Up to 12.5 Gbps"),
            InstanceType("r6i.2xlarge", 8, 64, "memory", {"on_demand": 0.4032, "reserved": 0.242, "spot": 0.121}, "Up to 12.5 Gbps"),
            InstanceType("c6i.large", 2, 4, "compute", {"on_demand": 0.0765, "reserved": 0.046, "spot": 0.023}, "Up to 12.5 Gbps"),
            InstanceType("c6i.xlarge", 4, 8, "compute", {"on_demand": 0.1530, "reserved": 0.092, "spot": 0.046}, "Up to 12.5 Gbps"),
            InstanceType("c6i.2xlarge", 8, 16, "compute", {"on_demand": 0.3060, "reserved": 0.184, "spot": 0.092}, "Up to 12.5 Gbps"),
        ]
    
    def _load_workload_profiles(self) -> Dict[str, WorkloadProfile]:
        """Load predefined workload profiles"""
        return {
            "web_server": WorkloadProfile("Web Server", 1.0, 1.0, 0.8, "Frontend web servers and load balancers"),
            "app_server": WorkloadProfile("Application Server", 1.2, 1.3, 1.0, "Business logic and API servers"),
            "database": WorkloadProfile("Database Server", 1.1, 1.8, 1.5, "Database and data processing workloads"),
            "analytics": WorkloadProfile("Analytics", 1.4, 1.6, 2.0, "Data analytics and processing"),
            "compute": WorkloadProfile("Compute Intensive", 1.8, 1.2, 0.8, "CPU-intensive batch processing"),
        }
    
    def _load_regions(self) -> Dict[str, str]:
        """Load AWS regions"""
        return {
            "us-east-1": "US East (N. Virginia)",
            "us-west-2": "US West (Oregon)",
            "eu-west-1": "Europe (Ireland)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
        }

class WorkloadCalculator:
    """Core workload sizing calculator"""
    
    def __init__(self, pricing_data: AWSPricingData):
        self.pricing_data = pricing_data
    
    def calculate_requirements(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate infrastructure requirements based on inputs"""
        
        # Get workload profile
        profile = self.pricing_data.workload_profiles[inputs['workload_type']]
        
        # Calculate CPU requirements with buffers and efficiency
        cpu_efficiency = 0.7  # 70% efficiency assumption
        cpu_buffer = 1.3  # 30% buffer for peaks
        
        required_vcpus = max(2, math.ceil(
            inputs['current_cores'] * 
            (inputs['peak_cpu_util'] / 100) * 
            profile.cpu_factor * 
            cpu_buffer / 
            cpu_efficiency
        ))
        
        # Calculate memory requirements
        memory_efficiency = 0.85  # 85% efficiency
        os_overhead = 1.15  # 15% OS overhead
        
        required_memory = max(4, math.ceil(
            inputs['current_memory'] * 
            (inputs['peak_memory_util'] / 100) * 
            profile.memory_factor * 
            os_overhead / 
            memory_efficiency
        ))
        
        # Calculate storage with growth
        growth_years = inputs.get('planning_years', 3)
        growth_rate = inputs.get('annual_growth_rate', 0.15)
        growth_factor = (1 + growth_rate) ** growth_years
        
        required_storage = math.ceil(
            inputs['current_storage'] * 
            profile.storage_factor * 
            growth_factor * 
            1.2  # 20% buffer
        )
        
        return {
            'vcpus': required_vcpus,
            'memory': required_memory,
            'storage': required_storage,
            'profile': profile
        }
    
    def find_best_instances(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find the best matching instance types"""
        
        suitable_instances = []
        
        for instance in self.pricing_data.instance_types:
            if (instance.vcpu >= requirements['vcpus'] and 
                instance.memory >= requirements['memory']):
                
                # Calculate efficiency scores
                cpu_efficiency = requirements['vcpus'] / instance.vcpu
                memory_efficiency = requirements['memory'] / instance.memory
                overall_efficiency = (cpu_efficiency + memory_efficiency) / 2
                
                suitable_instances.append({
                    'instance': instance,
                    'efficiency': overall_efficiency,
                    'cpu_efficiency': cpu_efficiency,
                    'memory_efficiency': memory_efficiency,
                    'monthly_cost_on_demand': instance.pricing['on_demand'] * 24 * 30,
                    'monthly_cost_reserved': instance.pricing['reserved'] * 24 * 30,
                    'monthly_cost_spot': instance.pricing['spot'] * 24 * 30,
                })
        
        # Sort by efficiency (descending)
        suitable_instances.sort(key=lambda x: x['efficiency'], reverse=True)
        
        return suitable_instances[:5]  # Return top 5 options

class ReportGenerator:
    """Generate reports and exports"""
    
    @staticmethod
    def generate_summary_data(results: Dict[str, Any]) -> pd.DataFrame:
        """Generate summary data for export"""
        instances = results['recommended_instances']
        
        data = []
        for inst in instances:
            data.append({
                'Instance Type': inst['instance'].name,
                'vCPUs': inst['instance'].vcpu,
                'Memory (GB)': inst['instance'].memory,
                'Family': inst['instance'].family,
                'Efficiency Score': f"{inst['efficiency']:.2%}",
                'Monthly Cost (On-Demand)': f"${inst['monthly_cost_on_demand']:.2f}",
                'Monthly Cost (Reserved)': f"${inst['monthly_cost_reserved']:.2f}",
                'Monthly Cost (Spot)': f"${inst['monthly_cost_spot']:.2f}",
                'Annual Savings (Reserved)': f"${(inst['monthly_cost_on_demand'] - inst['monthly_cost_reserved']) * 12:.2f}"
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_csv_export(df: pd.DataFrame) -> str:
        """Generate CSV export"""
        return df.to_csv(index=False)
    
    @staticmethod
    def generate_excel_export(df: pd.DataFrame) -> bytes:
        """Generate Excel export"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='AWS Sizing Recommendations', index=False)
        return output.getvalue()

def render_input_form() -> Dict[str, Any]:
    """Render the main input form"""
    
    st.markdown("""
    <div class="main-header">
        <h1>☁️ AWS EC2 Workload Sizing Calculator</h1>
        <p>Optimize your cloud migration with intelligent instance recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    pricing_data = get_pricing_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Current Infrastructure")
        
        workload_name = st.text_input("Workload Name", value="Production Workload")
        
        workload_type = st.selectbox(
            "Workload Type",
            options=list(pricing_data.workload_profiles.keys()),
            format_func=lambda x: pricing_data.workload_profiles[x].name,
            help="Select the workload type that best matches your application"
        )
        
        current_cores = st.number_input("Current CPU Cores", min_value=1, value=8, step=1)
        peak_cpu_util = st.slider("Peak CPU Utilization (%)", 0, 100, 75)
        
        current_memory = st.number_input("Current Memory (GB)", min_value=1, value=32, step=1)
        peak_memory_util = st.slider("Peak Memory Utilization (%)", 0, 100, 80)
        
        current_storage = st.number_input("Current Storage (GB)", min_value=1, value=500, step=50)
    
    with col2:
        st.subheader("🎯 Planning Parameters")
        
        region = st.selectbox(
            "AWS Region",
            options=list(pricing_data.regions.keys()),
            format_func=lambda x: pricing_data.regions[x]
        )
        
        environment = st.selectbox(
            "Environment",
            ["Production", "Staging", "Development", "Testing"],
            help="Different environments may have different sizing requirements"
        )
        
        planning_years = st.slider("Planning Horizon (Years)", 1, 5, 3)
        annual_growth_rate = st.slider("Annual Growth Rate", 0.0, 0.5, 0.15, format="%.0%")
        
        multi_az = st.checkbox("Multi-AZ Deployment", value=True, 
                              help="Deploy across multiple Availability Zones for high availability")
        
        include_spot = st.checkbox("Consider Spot Instances", value=False,
                                  help="Include Spot instances for cost optimization (suitable for fault-tolerant workloads)")
    
    # Show selected workload profile info
    profile = pricing_data.workload_profiles[workload_type]
    st.info(f"**{profile.name}**: {profile.description}")
    
    return {
        'workload_name': workload_name,
        'workload_type': workload_type,
        'current_cores': current_cores,
        'peak_cpu_util': peak_cpu_util,
        'current_memory': current_memory,
        'peak_memory_util': peak_memory_util,
        'current_storage': current_storage,
        'region': region,
        'environment': environment,
        'planning_years': planning_years,
        'annual_growth_rate': annual_growth_rate,
        'multi_az': multi_az,
        'include_spot': include_spot
    }

def render_results(results: Dict[str, Any]):
    """Render calculation results"""
    
    requirements = results['requirements']
    instances = results['recommended_instances']
    
    st.subheader("📋 Calculated Requirements")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{requirements['vcpus']}</div>
            <div class="metric-label">vCPUs Required</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{requirements['memory']}</div>
            <div class="metric-label">Memory (GB)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{requirements['storage']}</div>
            <div class="metric-label">Storage (GB)</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.subheader("🏆 Recommended Instances")
    
    if not instances:
        st.error("No suitable instances found for your requirements. Please adjust your inputs.")
        return
    
    # Display top 3 recommendations
    for i, inst in enumerate(instances[:3]):
        instance = inst['instance']
        
        with st.expander(f"Option {i+1}: {instance.name} (Efficiency: {inst['efficiency']:.1%})", 
                        expanded=(i == 0)):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Specifications:**
                - vCPUs: {instance.vcpu}
                - Memory: {instance.memory} GB
                - Family: {instance.family.title()}
                - Network: {instance.network_performance}
                
                **Efficiency:**
                - CPU Efficiency: {inst['cpu_efficiency']:.1%}
                - Memory Efficiency: {inst['memory_efficiency']:.1%}
                """)
            
            with col2:
                st.markdown(f"""
                **Monthly Costs:**
                - On-Demand: ${inst['monthly_cost_on_demand']:.2f}
                - Reserved (1-year): ${inst['monthly_cost_reserved']:.2f}
                - Spot: ${inst['monthly_cost_spot']:.2f}
                
                **Annual Savings:**
                - Reserved vs On-Demand: ${(inst['monthly_cost_on_demand'] - inst['monthly_cost_reserved']) * 12:.2f}
                - Spot vs On-Demand: ${(inst['monthly_cost_on_demand'] - inst['monthly_cost_spot']) * 12:.2f}
                """)
    
    # Cost comparison chart
    st.subheader("💰 Cost Comparison")
    
    chart_data = []
    for inst in instances[:3]:
        instance_name = inst['instance'].name
        chart_data.extend([
            {'Instance': instance_name, 'Pricing Model': 'On-Demand', 'Monthly Cost': inst['monthly_cost_on_demand']},
            {'Instance': instance_name, 'Pricing Model': 'Reserved', 'Monthly Cost': inst['monthly_cost_reserved']},
            {'Instance': instance_name, 'Pricing Model': 'Spot', 'Monthly Cost': inst['monthly_cost_spot']},
        ])
    
    df_chart = pd.DataFrame(chart_data)
    
    fig = px.bar(df_chart, x='Instance', y='Monthly Cost', color='Pricing Model',
                 title='Monthly Cost Comparison by Pricing Model',
                 barmode='group')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.subheader("💡 Recommendations")
    
    best_instance = instances[0]
    savings_reserved = (best_instance['monthly_cost_on_demand'] - best_instance['monthly_cost_reserved']) * 12
    savings_spot = (best_instance['monthly_cost_on_demand'] - best_instance['monthly_cost_spot']) * 12
    
    recommendations = [
        f"**Best Overall**: {best_instance['instance'].name} offers the best efficiency ({best_instance['efficiency']:.1%}) for your requirements",
        f"**Cost Optimization**: Consider Reserved Instances to save ${savings_reserved:.2f} annually",
    ]
    
    if savings_spot > savings_reserved * 2:
        recommendations.append(f"**Spot Instances**: Could save ${savings_spot:.2f} annually if your workload can tolerate interruptions")
    
    if requirements['profile'].memory_factor > 1.5:
        recommendations.append("**Memory-Optimized**: Consider R-series instances for memory-intensive workloads")
    
    for rec in recommendations:
        st.markdown(f'<div class="recommendation">{rec}</div>', unsafe_allow_html=True)

def render_export_options(results: Dict[str, Any]):
    """Render export options"""
    
    st.subheader("📤 Export Results")
    
    report_gen = ReportGenerator()
    df = report_gen.generate_summary_data(results)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download CSV", type="secondary"):
            csv_data = report_gen.generate_csv_export(df)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label="⬇️ Download CSV File",
                data=csv_data,
                file_name=f"aws_sizing_recommendations_{timestamp}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 Download Excel", type="secondary"):
            excel_data = report_gen.generate_excel_export(df)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label="⬇️ Download Excel File",
                data=excel_data,
                file_name=f"aws_sizing_recommendations_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col3:
        if st.button("👁️ Preview Data", type="secondary"):
            st.dataframe(df, use_container_width=True)

@st.cache_data
def get_pricing_data() -> AWSPricingData:
    """Cached pricing data loader"""
    return AWSPricingData()

def main():
    """Main application function"""
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    
    # Sidebar with instructions
    with st.sidebar:
        st.markdown("### 📖 How to Use")
        st.markdown("""
        1. **Enter Current Infrastructure**: Provide details about your existing on-premises setup
        2. **Set Planning Parameters**: Define your cloud migration timeline and growth expectations
        3. **Review Recommendations**: Analyze the suggested EC2 instance types
        4. **Export Results**: Download detailed reports for further analysis
        """)
        
        st.markdown("### 🔧 Features")
        st.markdown("""
        - **Intelligent Sizing**: Accounts for cloud efficiency, buffers, and growth
        - **Multiple Pricing Models**: On-Demand, Reserved, and Spot pricing
        - **Workload Profiles**: Optimized recommendations per workload type
        - **Cost Optimization**: Identifies best value options
        - **Export Options**: CSV and Excel reports
        """)
        
        st.markdown("### ℹ️ About")
        st.markdown("""
        This calculator helps you right-size AWS EC2 instances for your cloud migration.
        
        **Efficiency Assumptions:**
        - CPU: 70% efficiency
        - Memory: 85% efficiency  
        - Includes 30% buffer for peaks
        - OS overhead: 15%
        """)
    
    # Main application flow
    inputs = render_input_form()
    
    if st.button("🚀 Calculate Recommendations", type="primary", use_container_width=True):
        with st.spinner("Calculating optimal instance recommendations..."):
            try:
                # Initialize calculator
                pricing_data = get_pricing_data()
                calculator = WorkloadCalculator(pricing_data)
                
                # Calculate requirements
                requirements = calculator.calculate_requirements(inputs)
                
                # Find best instances
                recommended_instances = calculator.find_best_instances(requirements)
                
                # Store results
                results = {
                    'inputs': inputs,
                    'requirements': requirements,
                    'recommended_instances': recommended_instances
                }
                
                st.session_state.results = results
                
                st.success("✅ Recommendations calculated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error calculating recommendations: {str(e)}")
                st.stop()
    
    # Display results if available
    if st.session_state.results:
        st.markdown("---")
        render_results(st.session_state.results)
        
        st.markdown("---")
        render_export_options(st.session_state.results)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 1rem;">
        <strong>AWS EC2 Workload Sizing Calculator</strong><br>
        Intelligent cloud migration planning made simple
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()