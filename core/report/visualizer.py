import matplotlib.pyplot as plt
from collections import Counter
from pathlib import Path
import logging

class ReportVisualizer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_charts(self, findings):
        if not findings or len(findings) == 0:
            logging.warning("No findings to visualize.")
            return []

        try:
            # Set light background for better readability on white paper
            plt.style.use('default')
            
            # 1. Chart: Protection Types
            types = [f.get("protection_type") for f in findings]
            counts = Counter(types)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('#f8f9fa')
            
            # Use professional colors for pie chart
            colors = ['#3b82f6', '#f59e0b', '#10b981', '#dc2626', '#8b5cf6', '#06b6d4', '#ec4899', '#f97316']
            ax.pie(counts.values(), labels=counts.keys(), autopct='%1.1f%%', 
                   startangle=140, colors=colors[:len(counts)], textprops={'color': '#1f2937', 'fontsize': 10})
            ax.set_title("Distribution of Detected Protections", fontsize=12, fontweight='bold', color='#1f2937')
            
            chart1_path = self.output_dir / "protection_dist.png"
            plt.savefig(chart1_path, facecolor='white', edgecolor='none', bbox_inches='tight', dpi=100)
            plt.close()

            # 2. Chart: Strategy
            strategies = [f.get("taxonomy", {}).get("strategy", "Unknown") for f in findings]
            strat_counts = Counter(strategies)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('#f8f9fa')
            
            bars = ax.bar(strat_counts.keys(), strat_counts.values(), color=['#3b82f6', '#f59e0b', '#10b981', '#dc2626'][:len(strat_counts)])
            ax.set_xlabel("Analysis Strategy", fontsize=11, fontweight='bold', color='#1f2937')
            ax.set_ylabel("Number of Hits", fontsize=11, fontweight='bold', color='#1f2937')
            ax.set_title("Protections by Strategy", fontsize=12, fontweight='bold', color='#1f2937')
            ax.tick_params(colors='#1f2937')
            ax.spines['bottom'].set_color('#d1d5db')
            ax.spines['left'].set_color('#d1d5db')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            chart2_path = self.output_dir / "strategy_dist.png"
            plt.savefig(chart2_path, facecolor='white', edgecolor='none', bbox_inches='tight', dpi=100)
            plt.close()

            return [chart1_path.name, chart2_path.name]
        except Exception as e:
            logging.error(f"Visualization failed: {e}")
            return []