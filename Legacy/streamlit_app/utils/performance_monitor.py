"""
Performance Monitoring for Spotify Music Recommendation System
Tracks performance metrics and identifies bottlenecks
"""

import streamlit as st
import time
import pandas as pd
from typing import Dict, List, Optional, Any
from functools import wraps
import logging
from datetime import datetime, timedelta
import gc

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring and profiling system"""
    
    def __init__(self):
        self.metrics = {
            'function_calls': {},
            'memory_usage': [],
            'user_interactions': []
        }
        
        # Initialize in session state
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = self.metrics
    
    def track_function_performance(self, func_name: str, execution_time: float):
        """Track function performance metrics"""
        if func_name not in st.session_state.performance_metrics['function_calls']:
            st.session_state.performance_metrics['function_calls'][func_name] = {
                'calls': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            }
        
        metrics = st.session_state.performance_metrics['function_calls'][func_name]
        metrics['calls'] += 1
        metrics['total_time'] += execution_time
        metrics['avg_time'] = metrics['total_time'] / metrics['calls']
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        metrics['min_time'] = min(metrics['min_time'], execution_time)
    
    def track_user_interaction(self, interaction_type: str, details: Dict[str, Any]):
        """Track user interactions for performance analysis"""
        interaction = {
            'timestamp': datetime.now(),
            'type': interaction_type,
            'details': details
        }
        
        st.session_state.performance_metrics['user_interactions'].append(interaction)
        
        # Keep only last 50 interactions
        if len(st.session_state.performance_metrics['user_interactions']) > 50:
            st.session_state.performance_metrics['user_interactions'] = \
                st.session_state.performance_metrics['user_interactions'][-50:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics"""
        metrics = st.session_state.performance_metrics
        
        # Function performance summary
        function_summary = {}
        for func_name, func_metrics in metrics['function_calls'].items():
            function_summary[func_name] = {
                'calls': func_metrics['calls'],
                'avg_time_ms': round(func_metrics['avg_time'] * 1000, 2),
                'max_time_ms': round(func_metrics['max_time'] * 1000, 2),
                'total_time_s': round(func_metrics['total_time'], 2)
            }
        
        # User interaction summary
        interaction_types = {}
        for interaction in metrics['user_interactions'][-20:]:
            itype = interaction['type']
            interaction_types[itype] = interaction_types.get(itype, 0) + 1
        
        return {
            'functions': function_summary,
            'interactions': interaction_types,
            'total_function_calls': sum(f['calls'] for f in function_summary.values()),
            'monitoring_duration_minutes': self._get_monitoring_duration()
        }
    
    def _get_monitoring_duration(self) -> float:
        """Get monitoring duration in minutes"""
        if not st.session_state.performance_metrics['user_interactions']:
            return 0
        
        first_timestamp = st.session_state.performance_metrics['user_interactions'][0]['timestamp']
        last_timestamp = st.session_state.performance_metrics['user_interactions'][-1]['timestamp']
        duration = (last_timestamp - first_timestamp).total_seconds() / 60
        return round(duration, 1)
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        metrics = st.session_state.performance_metrics
        
        # Check for slow functions
        for func_name, func_metrics in metrics['function_calls'].items():
            if func_metrics['avg_time'] > 1.0:  # Functions taking more than 1 second
                bottlenecks.append({
                    'type': 'slow_function',
                    'function': func_name,
                    'avg_time_s': round(func_metrics['avg_time'], 2),
                    'calls': func_metrics['calls'],
                    'severity': 'high' if func_metrics['avg_time'] > 3.0 else 'medium'
                })
        
        return bottlenecks
    
    def clear_metrics(self):
        """Clear all performance metrics"""
        st.session_state.performance_metrics = {
            'function_calls': {},
            'memory_usage': [],
            'user_interactions': []
        }
        logger.info("Performance metrics cleared")
    
    def export_metrics(self) -> pd.DataFrame:
        """Export metrics to DataFrame for analysis"""
        metrics = st.session_state.performance_metrics
        
        # Function performance data
        function_data = []
        for func_name, func_metrics in metrics['function_calls'].items():
            function_data.append({
                'function': func_name,
                'calls': func_metrics['calls'],
                'avg_time_ms': func_metrics['avg_time'] * 1000,
                'max_time_ms': func_metrics['max_time'] * 1000,
                'total_time_s': func_metrics['total_time']
            })
        
        return pd.DataFrame(function_data)

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance():
    """
    Decorator to monitor function performance
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Track performance
                performance_monitor.track_function_performance(
                    func.__name__, execution_time
                )
                
                # Log slow functions
                if execution_time > 2.0:
                    logger.warning(f"Slow function detected: {func.__name__} took {execution_time:.2f}s")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.track_function_performance(
                    f"{func.__name__}_error", execution_time
                )
                raise e
        
        return wrapper
    return decorator

def track_user_interaction(interaction_type: str, **details):
    """Track user interaction for performance analysis"""
    performance_monitor.track_user_interaction(interaction_type, details)

def get_performance_dashboard_data() -> Dict[str, Any]:
    """Get data for performance dashboard"""
    return {
        'summary': performance_monitor.get_performance_summary(),
        'bottlenecks': performance_monitor.identify_bottlenecks(),
        'metrics_df': performance_monitor.export_metrics()
    }

def optimize_memory():
    """Force garbage collection and memory optimization"""
    gc.collect()
    logger.info("Memory optimization performed")

def render_performance_dashboard():
    """Render performance monitoring dashboard"""
    st.markdown("### 🚀 Performance Monitor")
    
    dashboard_data = get_performance_dashboard_data()
    summary = dashboard_data['summary']
    bottlenecks = dashboard_data['bottlenecks']
    
    # Performance summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Function Calls", summary['total_function_calls'])
    
    with col2:
        st.metric("Monitoring Duration", f"{summary['monitoring_duration_minutes']} min")
    
    with col3:
        if st.button("🧹 Optimize Memory"):
            optimize_memory()
            st.success("Memory optimized!")
        
        if st.button("🗑️ Clear Metrics"):
            performance_monitor.clear_metrics()
            st.success("Metrics cleared!")
    
    # Bottlenecks
    if bottlenecks:
        st.markdown("#### ⚠️ Performance Bottlenecks")
        for bottleneck in bottlenecks:
            severity_color = "🔴" if bottleneck['severity'] == 'high' else "🟡"
            st.markdown(f"{severity_color} **{bottleneck['type'].replace('_', ' ').title()}**")
            
            if bottleneck['type'] == 'slow_function':
                st.markdown(f"   - Function: `{bottleneck['function']}`")
                st.markdown(f"   - Average time: {bottleneck['avg_time_s']}s")
                st.markdown(f"   - Calls: {bottleneck['calls']}")
    else:
        st.success("✅ No performance bottlenecks detected!")
    
    # Function performance table
    if summary['functions']:
        st.markdown("#### 📊 Function Performance")
        metrics_df = dashboard_data['metrics_df']
        if not metrics_df.empty:
            st.dataframe(
                metrics_df.sort_values('avg_time_ms', ascending=False),
                use_container_width=True
            )
