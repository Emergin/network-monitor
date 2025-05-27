import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
import os
import sys
from datetime import datetime, timedelta
import threading

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from monitor import NetworkMonitor

# Page configuration
st.set_page_config(
    page_title="Network Monitor Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .status-up {
        color: #00ff00;
        font-weight: bold;
    }
    
    .status-down {
        color: #ff4444;
        font-weight: bold;
    }
    
    .alert-box {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .stSelectbox > div > div {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_monitor_data():
    """Load network monitor data with caching"""
    try:
        if not hasattr(st.session_state, 'monitor'):
            st.session_state.monitor = NetworkMonitor()
        
        # Perform scan if no recent data
        if not st.session_state.monitor.results or \
           (datetime.now() - datetime.fromisoformat(st.session_state.monitor.results.get('timestamp', '2000-01-01T00:00:00'))).seconds > 60:
            with st.spinner('Scanning network...'):
                st.session_state.monitor.perform_full_scan()
        
        return st.session_state.monitor
    except Exception as e:
        st.error(f"Error loading monitor data: {e}")
        return None

def create_status_overview(monitor):
    """Create status overview section"""
    summary = monitor.get_status_summary()
    
    if summary.get("status") == "No data available":
        st.warning("No monitoring data available. Please wait for the next scan.")
        return
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌐 Network Monitor Dashboard</h1>
        <p>Real-time network monitoring and port scanning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🖥️ Hosts Up",
            value=f"{summary['hosts_up']}/{summary['total_hosts']}",
            delta=f"{(summary['hosts_up']/summary['total_hosts']*100):.1f}%" if summary['total_hosts'] > 0 else "0%"
        )
    
    with col2:
        st.metric(
            label="🔌 Services Up", 
            value=f"{summary['services_up']}/{summary['total_services']}",
            delta=f"{(summary['services_up']/summary['total_services']*100):.1f}%" if summary['total_services'] > 0 else "0%"
        )
    
    with col3:
        st.metric(
            label="🚨 Recent Alerts",
            value=summary['recent_alerts'],
            delta="Last Hour"
        )
    
    with col4:
        last_scan = datetime.fromisoformat(summary['last_scan']).strftime("%H:%M:%S")
        st.metric(
            label="⏰ Last Scan",
            value=last_scan,
            delta=datetime.fromisoformat(summary['last_scan']).strftime("%Y-%m-%d")
        )

def create_host_status_chart(monitor):
    """Create host status visualization"""
    if not monitor.results:
        return
    
    hosts_data = []
    for host, host_data in monitor.results["hosts"].items():
        ping_status = "Up" if host_data["ping"]["status"] else "Down"
        response_time = host_data["ping"]["response_time"]
        
        # Count services
        services_up = sum(1 for port_data in host_data["ports"].values() if port_data["status"])
        services_total = len(host_data["ports"])
        
        hosts_data.append({
            "Host": host,
            "Ping Status": ping_status,
            "Response Time (ms)": response_time,
            "Services Up": services_up,
            "Services Total": services_total,
            "Service Availability %": (services_up / services_total * 100) if services_total > 0 else 0
        })
    
    df = pd.DataFrame(hosts_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Host Ping Status")
        fig_pie = px.pie(
            df, 
            names="Ping Status", 
            title="Host Availability",
            color_discrete_map={"Up": "#00ff00", "Down": "#ff4444"}
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("⚡ Response Times")
        df_up = df[df["Ping Status"] == "Up"]
        if not df_up.empty:
            fig_bar = px.bar(
                df_up, 
                x="Host", 
                y="Response Time (ms)",
                title="Ping Response Times (Up Hosts Only)",
                color="Response Time (ms)",
                color_continuous_scale="RdYlGn_r"
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No hosts are responding to ping")

def create_service_status_table(monitor):
    """Create detailed service status table"""
    if not monitor.results:
        return
    
    st.subheader("🔍 Detailed Service Status")
    
    # Prepare data for table
    service_data = []
    for host, host_data in monitor.results["hosts"].items():
        for port, port_data in host_data["ports"].items():
            service_data.append({
                "Host": host,
                "Port": port,
                "Service": port_data["service"],
                "Status": "✅ Up" if port_data["status"] else "❌ Down",
                "Response Time (ms)": f"{port_data['response_time']:.1f}" if port_data["status"] else "N/A"
            })
    
    df = pd.DataFrame(service_data)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        host_filter = st.selectbox("Filter by Host", ["All"] + list(df["Host"].unique()))
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "✅ Up", "❌ Down"])
    with col3:
        service_filter = st.selectbox("Filter by Service Type", ["All"] + sorted(list(df["Service"].unique())))
    
    # Apply filters
    filtered_df = df.copy()
    if host_filter != "All":
        filtered_df = filtered_df[filtered_df["Host"] == host_filter]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]
    if service_filter != "All":
        filtered_df = filtered_df[filtered_df["Service"] == service_filter]
    
    # Display table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Port": st.column_config.NumberColumn("Port", width="small"),
            "Response Time (ms)": st.column_config.TextColumn("Response Time", width="medium")
        }
    )
    
    # Service statistics
    st.subheader("📈 Service Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Services by category
        service_counts = df.groupby("Service").size().reset_index(name="Count")
        service_counts = service_counts.sort_values("Count", ascending=False).head(10)
        
        fig_services = px.bar(
            service_counts,
            x="Count",
            y="Service",
            orientation="h",
            title="Top 10 Most Common Services",
            color="Count",
            color_continuous_scale="viridis"
        )
        fig_services.update_layout(height=400)
        st.plotly_chart(fig_services, use_container_width=True)
    
    with col2:
        # Service availability by host
        host_service_stats = df.groupby(["Host", "Status"]).size().unstack(fill_value=0)
        host_service_stats["Total"] = host_service_stats.sum(axis=1)
        host_service_stats["Availability %"] = (host_service_stats.get("✅ Up", 0) / host_service_stats["Total"] * 100).round(1)
        
        fig_availability = px.bar(
            x=host_service_stats.index,
            y=host_service_stats["Availability %"],
            title="Service Availability by Host",
            color=host_service_stats["Availability %"],
            color_continuous_scale="RdYlGn",
            range_color=[0, 100]
        )
        fig_availability.update_layout(
            xaxis_title="Host",
            yaxis_title="Availability %",
            xaxis_tickangle=-45,
            height=400
        )
        st.plotly_chart(fig_availability, use_container_width=True)

def create_alerts_section(monitor):
    """Create alerts section"""
    st.subheader("🚨 Recent Alerts")
    
    if not monitor.alert_history:
        st.success("✅ No recent alerts - All systems operational!")
        return
    
    # Filter alerts from last 24 hours
    recent_alerts = [
        alert for alert in monitor.alert_history
        if datetime.fromisoformat(alert["timestamp"]) > datetime.now() - timedelta(hours=24)
    ]
    
    if not recent_alerts:
        st.success("✅ No alerts in the last 24 hours!")
        return
    
    # Display alerts
    for alert in sorted(recent_alerts, key=lambda x: x["timestamp"], reverse=True):
        alert_time = datetime.fromisoformat(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        
        if alert["type"] == "ping_down":
            st.error(f"🔴 **HOST DOWN** - {alert['host']} | {alert_time}")
        elif alert["type"] == "port_down":
            st.warning(f"🟡 **SERVICE DOWN** - {alert['service']} on {alert['host']}:{alert['port']} | {alert_time}")
    
    # Alert statistics
    col1, col2 = st.columns(2)
    
    with col1:
        alert_types = {}
        for alert in recent_alerts:
            alert_types[alert["type"]] = alert_types.get(alert["type"], 0) + 1
        
        if alert_types:
            fig_alert_types = px.pie(
                values=list(alert_types.values()),
                names=list(alert_types.keys()),
                title="Alert Types (24h)",
                color_discrete_map={"ping_down": "#ff4444", "port_down": "#ff8800"}
            )
            st.plotly_chart(fig_alert_types, use_container_width=True)
    
    with col2:
        # Alert timeline
        alert_timeline = {}
        for alert in recent_alerts:
            hour = datetime.fromisoformat(alert["timestamp"]).strftime("%H:00")
            alert_timeline[hour] = alert_timeline.get(hour, 0) + 1
        
        if alert_timeline:
            timeline_df = pd.DataFrame(list(alert_timeline.items()), columns=["Hour", "Alerts"])
            timeline_df = timeline_df.sort_values("Hour")
            
            fig_timeline = px.line(
                timeline_df,
                x="Hour",
                y="Alerts",
                title="Alert Timeline (24h)",
                markers=True
            )
            fig_timeline.update_traces(line_color="#ff4444", marker_color="#ff4444")
            st.plotly_chart(fig_timeline, use_container_width=True)

def create_network_topology(monitor):
    """Create network topology visualization"""
    if not monitor.results:
        return
    
    st.subheader("🌐 Network Topology")
    
    # Create network graph data
    nodes = []
    edges = []
    
    # Add central node (monitoring system)
    nodes.append({"id": "monitor", "label": "Network Monitor", "color": "#4CAF50"})
    
    for host, host_data in monitor.results["hosts"].items():
        # Add host node
        host_color = "#4CAF50" if host_data["ping"]["status"] else "#F44336"
        nodes.append({"id": host, "label": host, "color": host_color})
        
        # Add edge from monitor to host
        edges.append({"from": "monitor", "to": host})
        
        # Add service nodes for active services
        active_services = [
            (port, port_data) for port, port_data in host_data["ports"].items() 
            if port_data["status"]
        ]
        
        for port, port_data in active_services[:5]:  # Limit to 5 services per host for clarity
            service_id = f"{host}:{port}"
            nodes.append({
                "id": service_id, 
                "label": f"{port_data['service']}\n({port})", 
                "color": "#2196F3"
            })
            edges.append({"from": host, "to": service_id})
    
    # Display network info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Hosts", len(monitor.results["hosts"]))
    with col2:
        active_services_count = sum(
            sum(1 for port_data in host_data["ports"].values() if port_data["status"])
            for host_data in monitor.results["hosts"].values()
        )
        st.metric("Active Services", active_services_count)
    with col3:
        st.metric("Total Connections", len(edges))

def main():
    """Main dashboard function"""
    # Sidebar
    st.sidebar.title("🌐 Network Monitor")
    st.sidebar.markdown("---")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
    
    # Configuration section
    st.sidebar.markdown("### ⚙️ Configuration")
    
    # Load monitor
    monitor = load_monitor_data()
    
    if monitor is None:
        st.error("Failed to initialize network monitor. Please check your configuration.")
        return
    
    # Display configuration info
    if hasattr(monitor, 'config'):
        st.sidebar.markdown(f"**Hosts:** {len(monitor.config.get('hosts', []))}")
        st.sidebar.markdown(f"**Ports:** {len(monitor.config.get('ports', []))}")
        st.sidebar.markdown(f"**Scan Interval:** {monitor.config.get('check_interval', 60)}s")
    
    # Main content
    create_status_overview(monitor)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Services", "🚨 Alerts", "🌐 Network"])
    
    with tab1:
        create_host_status_chart(monitor)
    
    with tab2:
        create_service_status_table(monitor)
    
    with tab3:
        create_alerts_section(monitor)
    
    with tab4:
        create_network_topology(monitor)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Network Monitor Dashboard** | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "🔄 Auto-refresh: " + ("ON" if auto_refresh else "OFF")
    )
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()