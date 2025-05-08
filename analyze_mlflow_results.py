#!/usr/bin/env python3
"""
Analyze MLflow Results

This script analyzes MLflow results from DSPy optimization runs, providing:
1. Summary statistics across all runs
2. Comparison of different optimizers
3. Performance over time analysis
4. Visualization of results

Usage:
    python analyze_mlflow_results.py [--experiment-name NAME] [--output-file PATH] [--limit NUM] [--visualize]
"""

import os
import sys
import json
import logging
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import mlflow
from mlflow.tracking import MlflowClient
import time

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import seaborn as sns
    from matplotlib.dates import DateFormatter
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("Visualization libraries not available. Install matplotlib and pandas for visualizations.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/analyze_mlflow.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze MLflow results from DSPy optimization runs")
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="bible_qa_optimization",
        help="MLflow experiment name to analyze"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="analysis_results/optimization_results.json",
        help="Output file for analysis results"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of runs to analyze"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualizations of results"
    )
    parser.add_argument(
        "--compare-optimizers",
        action="store_true",
        help="Compare performance of different optimizers"
    )
    parser.add_argument(
        "--time-analysis",
        action="store_true",
        help="Analyze performance over time"
    )
    return parser.parse_args()

def get_experiment_runs(experiment_name, limit=50):
    """Get runs from an MLflow experiment."""
    try:
        # Set up MLflow client
        client = MlflowClient()
        
        # Get experiment
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            logger.error(f"Experiment '{experiment_name}' not found")
            return []
        
        # Get runs
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            max_results=limit,
            order_by=["attributes.start_time DESC"]
        )
        
        logger.info(f"Found {len(runs)} runs for experiment '{experiment_name}'")
        return runs
    
    except Exception as e:
        logger.error(f"Error getting experiment runs: {e}")
        return []

def analyze_runs(runs):
    """Analyze runs and return results."""
    results = []
    
    for run in runs:
        try:
            # Get run data
            run_id = run.info.run_id
            run_name = run.info.run_name or "unnamed"
            status = run.info.status
            start_time = run.info.start_time
            end_time = run.info.end_time or 0
            
            # Get params
            optimizer = run.data.params.get("optimizer", "unknown")
            trainset_size = int(run.data.params.get("trainset_size", 0))
            valset_size = int(run.data.params.get("valset_size", 0))
            max_iterations = int(run.data.params.get("max_iterations", 0))
            target_accuracy = float(run.data.params.get("target_accuracy", 0.0))
            
            # Get metrics
            base_accuracy = float(run.data.metrics.get("base_accuracy", 0.0))
            optimized_accuracy = float(run.data.metrics.get("optimized_accuracy", 0.0))
            improvement = float(run.data.metrics.get("improvement", 0.0))
            
            # Calculate duration in seconds
            duration = (end_time - start_time) / 1000 if end_time > 0 else 0
            
            # Format start time
            start_time_str = datetime.datetime.fromtimestamp(
                start_time / 1000
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            # Create result entry
            result = {
                "run_id": run_id,
                "run_name": run_name,
                "status": status,
                "start_time": start_time_str,
                "duration_seconds": duration,
                "optimizer": optimizer,
                "trainset_size": trainset_size,
                "valset_size": valset_size,
                "max_iterations": max_iterations,
                "target_accuracy": target_accuracy,
                "base_accuracy": base_accuracy,
                "optimized_accuracy": optimized_accuracy,
                "improvement": improvement
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error analyzing run {run.info.run_id}: {e}")
    
    # Sort by start time (newest first)
    results.sort(key=lambda x: x["start_time"], reverse=True)
    return results

def summarize_results(results):
    """Generate a summary of the results."""
    if not results:
        return {
            "total_runs": 0,
            "message": "No results found"
        }
    
    # Calculate averages
    total_runs = len(results)
    avg_base_accuracy = sum(r["base_accuracy"] for r in results) / total_runs
    avg_optimized_accuracy = sum(r["optimized_accuracy"] for r in results) / total_runs
    avg_improvement = sum(r["improvement"] for r in results) / total_runs
    avg_duration = sum(r["duration_seconds"] for r in results) / total_runs
    
    # Find best run
    best_run = max(results, key=lambda r: r["optimized_accuracy"])
    
    # Find most improved run
    most_improved_run = max(results, key=lambda r: r["improvement"])
    
    # Count optimizers
    optimizers = {}
    for r in results:
        optimizer = r["optimizer"]
        if optimizer not in optimizers:
            optimizers[optimizer] = {
                "count": 0,
                "total_base_accuracy": 0.0,
                "total_optimized_accuracy": 0.0,
                "total_improvement": 0.0,
                "total_duration": 0.0
            }
        
        optimizers[optimizer]["count"] += 1
        optimizers[optimizer]["total_base_accuracy"] += r["base_accuracy"]
        optimizers[optimizer]["total_optimized_accuracy"] += r["optimized_accuracy"]
        optimizers[optimizer]["total_improvement"] += r["improvement"]
        optimizers[optimizer]["total_duration"] += r["duration_seconds"]
    
    # Calculate averages for each optimizer
    optimizer_stats = {}
    for opt, stats in optimizers.items():
        count = stats["count"]
        optimizer_stats[opt] = {
            "count": count,
            "avg_base_accuracy": stats["total_base_accuracy"] / count,
            "avg_optimized_accuracy": stats["total_optimized_accuracy"] / count,
            "avg_improvement": stats["total_improvement"] / count,
            "avg_duration_seconds": stats["total_duration"] / count
        }
    
    # Results by date
    dates = {}
    for r in results:
        date = r["start_time"].split()[0]  # Extract just the date
        if date not in dates:
            dates[date] = {
                "count": 0,
                "total_base_accuracy": 0.0,
                "total_optimized_accuracy": 0.0,
                "total_improvement": 0.0
            }
        
        dates[date]["count"] += 1
        dates[date]["total_base_accuracy"] += r["base_accuracy"]
        dates[date]["total_optimized_accuracy"] += r["optimized_accuracy"]
        dates[date]["total_improvement"] += r["improvement"]
    
    # Calculate averages for each date
    date_stats = {}
    for date, stats in dates.items():
        count = stats["count"]
        date_stats[date] = {
            "count": count,
            "avg_base_accuracy": stats["total_base_accuracy"] / count,
            "avg_optimized_accuracy": stats["total_optimized_accuracy"] / count,
            "avg_improvement": stats["total_improvement"] / count
        }
    
    return {
        "total_runs": total_runs,
        "avg_base_accuracy": avg_base_accuracy,
        "avg_optimized_accuracy": avg_optimized_accuracy,
        "avg_improvement": avg_improvement,
        "avg_duration_seconds": avg_duration,
        "best_run": best_run,
        "most_improved_run": most_improved_run,
        "optimizers": optimizer_stats,
        "dates": date_stats
    }

def save_results(results, summary, output_file):
    """Save results to a JSON file."""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create output data
        output_data = {
            "summary": summary,
            "results": results
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return False

def print_summary(summary):
    """Print summary to console."""
    print("\n===== MLflow Analysis Summary =====")
    print(f"Total runs: {summary['total_runs']}")
    
    if summary['total_runs'] > 0:
        print(f"Average base accuracy: {summary['avg_base_accuracy']:.4f}")
        print(f"Average optimized accuracy: {summary['avg_optimized_accuracy']:.4f}")
        print(f"Average improvement: {summary['avg_improvement']:.4f}")
        print(f"Average duration: {summary['avg_duration_seconds']:.2f} seconds")
        
        print("\nBest run:")
        best = summary['best_run']
        print(f"  Run name: {best['run_name']}")
        print(f"  Optimizer: {best['optimizer']}")
        print(f"  Base accuracy: {best['base_accuracy']:.4f}")
        print(f"  Optimized accuracy: {best['optimized_accuracy']:.4f}")
        print(f"  Improvement: {best['improvement']:.4f}")
        print(f"  Date: {best['start_time']}")
        
        print("\nMost improved run:")
        improved = summary['most_improved_run']
        print(f"  Run name: {improved['run_name']}")
        print(f"  Optimizer: {improved['optimizer']}")
        print(f"  Base accuracy: {improved['base_accuracy']:.4f}")
        print(f"  Optimized accuracy: {improved['optimized_accuracy']:.4f}")
        print(f"  Improvement: {improved['improvement']:.4f}")
        
        print("\nOptimizer comparison:")
        for optimizer, stats in summary['optimizers'].items():
            print(f"  {optimizer}:")
            print(f"    Runs: {stats['count']}")
            print(f"    Avg base accuracy: {stats['avg_base_accuracy']:.4f}")
            print(f"    Avg optimized accuracy: {stats['avg_optimized_accuracy']:.4f}")
            print(f"    Avg improvement: {stats['avg_improvement']:.4f}")
            print(f"    Avg duration: {stats['avg_duration_seconds']:.2f} seconds")
    
    print("====================================")

def generate_visualizations(results, summary, output_dir="analysis_results"):
    """Generate visualizations of results."""
    if not VISUALIZATION_AVAILABLE:
        logger.warning("Visualization libraries not available. Install matplotlib, pandas, and numpy.")
        return False
    
    if not results:
        logger.warning("No results to visualize")
        return False
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        
        # 1. Optimizer comparison
        if len(summary["optimizers"]) > 1:
            plt.figure(figsize=(12, 6))
            
            # Create data for plotting
            optimizers = []
            base_accs = []
            opt_accs = []
            improvements = []
            
            for opt, stats in summary["optimizers"].items():
                optimizers.append(opt)
                base_accs.append(stats["avg_base_accuracy"])
                opt_accs.append(stats["avg_optimized_accuracy"])
                improvements.append(stats["avg_improvement"])
            
            # Set width of bars
            barWidth = 0.25
            
            # Set position of bars on X axis
            r1 = np.arange(len(optimizers))
            r2 = [x + barWidth for x in r1]
            r3 = [x + barWidth for x in r2]
            
            # Create bars
            plt.bar(r1, base_accs, width=barWidth, label='Base Accuracy')
            plt.bar(r2, opt_accs, width=barWidth, label='Optimized Accuracy')
            plt.bar(r3, improvements, width=barWidth, label='Improvement')
            
            # Add labels and legend
            plt.xlabel('Optimizer', fontweight='bold')
            plt.xticks([r + barWidth for r in range(len(optimizers))], optimizers)
            plt.ylabel('Score')
            plt.title('Optimizer Performance Comparison')
            plt.legend()
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{output_dir}/optimizer_comparison.png")
            plt.close()
        
        # 2. Performance over time
        if df["start_time"].nunique() > 1:
            plt.figure(figsize=(12, 6))
            
            # Convert start_time to datetime
            df["start_datetime"] = pd.to_datetime(df["start_time"])
            df = df.sort_values("start_datetime")
            
            # Create plot
            plt.plot(df["start_datetime"], df["base_accuracy"], label="Base Accuracy", marker="o", linestyle="--")
            plt.plot(df["start_datetime"], df["optimized_accuracy"], label="Optimized Accuracy", marker="x")
            
            # Add labels and legend
            plt.xlabel("Time")
            plt.ylabel("Accuracy")
            plt.title("Performance Over Time")
            plt.xticks(rotation=45)
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{output_dir}/performance_over_time.png")
            plt.close()
        
        # 3. Improvement distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df["improvement"], bins=10, color="skyblue", edgecolor="black")
        plt.xlabel("Improvement")
        plt.ylabel("Frequency")
        plt.title("Distribution of Improvement")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/improvement_distribution.png")
        plt.close()
        
        # 4. Scatter plot of base vs optimized accuracy
        plt.figure(figsize=(8, 8))
        plt.scatter(df["base_accuracy"], df["optimized_accuracy"], alpha=0.7)
        plt.plot([0, 1], [0, 1], "r--", alpha=0.5)  # Diagonal line
        
        # Add labels
        for i, row in df.iterrows():
            plt.annotate(
                row["optimizer"],
                (row["base_accuracy"], row["optimized_accuracy"]),
                fontsize=8,
                alpha=0.7
            )
        
        plt.xlabel("Base Accuracy")
        plt.ylabel("Optimized Accuracy")
        plt.title("Base vs Optimized Accuracy")
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/base_vs_optimized.png")
        plt.close()
        
        logger.info(f"Visualizations saved to {output_dir}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        return False

def compare_optimizers(results):
    """Detailed comparison of different optimizers."""
    if not results:
        return "No results to compare"
    
    # Group by optimizer
    optimizer_results = {}
    for r in results:
        optimizer = r["optimizer"]
        if optimizer not in optimizer_results:
            optimizer_results[optimizer] = []
        optimizer_results[optimizer].append(r)
    
    if len(optimizer_results) <= 1:
        return "Not enough different optimizers to compare"
    
    # Compare optimizers
    comparison = []
    for optimizer, runs in optimizer_results.items():
        avg_base = sum(r["base_accuracy"] for r in runs) / len(runs)
        avg_optimized = sum(r["optimized_accuracy"] for r in runs) / len(runs)
        avg_improvement = sum(r["improvement"] for r in runs) / len(runs)
        avg_duration = sum(r["duration_seconds"] for r in runs) / len(runs)
        best_run = max(runs, key=lambda r: r["optimized_accuracy"])
        
        comparison.append({
            "optimizer": optimizer,
            "runs": len(runs),
            "avg_base_accuracy": avg_base,
            "avg_optimized_accuracy": avg_optimized,
            "avg_improvement": avg_improvement,
            "avg_duration_seconds": avg_duration,
            "best_run": best_run["run_name"],
            "best_accuracy": best_run["optimized_accuracy"]
        })
    
    # Sort by average optimized accuracy
    comparison.sort(key=lambda x: x["avg_optimized_accuracy"], reverse=True)
    
    # Generate report
    report = "\n===== Optimizer Comparison =====\n"
    
    for i, comp in enumerate(comparison):
        report += f"{i+1}. {comp['optimizer']} ({comp['runs']} runs)\n"
        report += f"   Avg optimized accuracy: {comp['avg_optimized_accuracy']:.4f}\n"
        report += f"   Avg improvement: {comp['avg_improvement']:.4f}\n"
        report += f"   Avg duration: {comp['avg_duration_seconds']:.2f} seconds\n"
        report += f"   Best run: {comp['best_run']} ({comp['best_accuracy']:.4f})\n\n"
    
    # Add ranking explanation
    report += "Ranking factors:\n"
    report += "1. Average optimized accuracy\n"
    report += "2. Average improvement\n"
    report += "3. Best run performance\n"
    
    return report

def analyze_performance_over_time(results):
    """Analyze performance trends over time."""
    if not results:
        return "No results to analyze"
    
    # Group by date
    date_results = {}
    for r in results:
        date = r["start_time"].split()[0]  # Extract just the date
        if date not in date_results:
            date_results[date] = []
        date_results[date].append(r)
    
    if len(date_results) <= 1:
        return "Not enough dates to analyze performance over time"
    
    # Sort dates
    sorted_dates = sorted(date_results.keys())
    
    # Analyze performance over time
    report = "\n===== Performance Over Time =====\n"
    
    for date in sorted_dates:
        runs = date_results[date]
        avg_base = sum(r["base_accuracy"] for r in runs) / len(runs)
        avg_optimized = sum(r["optimized_accuracy"] for r in runs) / len(runs)
        avg_improvement = sum(r["improvement"] for r in runs) / len(runs)
        
        report += f"{date} ({len(runs)} runs):\n"
        report += f"  Avg base accuracy: {avg_base:.4f}\n"
        report += f"  Avg optimized accuracy: {avg_optimized:.4f}\n"
        report += f"  Avg improvement: {avg_improvement:.4f}\n\n"
    
    # Add trend analysis
    first_date = sorted_dates[0]
    last_date = sorted_dates[-1]
    first_avg = sum(r["optimized_accuracy"] for r in date_results[first_date]) / len(date_results[first_date])
    last_avg = sum(r["optimized_accuracy"] for r in date_results[last_date]) / len(date_results[last_date])
    
    if last_avg > first_avg:
        report += f"TREND: Performance IMPROVED over time (+{(last_avg - first_avg):.4f})\n"
    elif last_avg < first_avg:
        report += f"TREND: Performance DECREASED over time ({(last_avg - first_avg):.4f})\n"
    else:
        report += "TREND: Performance remained STABLE over time\n"
    
    return report

def generate_optimizer_comparison_plot(runs, output_path=None):
    """Generate a comparison plot between different optimizers."""
    if output_path is None:
        output_path = os.path.join("analysis_results", f"optimizer_comparison_{int(time.time())}.png")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Prepare data for plotting
        data = []
        for run_id, run in runs.items():
            if 'params.optimizer' in run and 'metrics.base_accuracy' in run and 'metrics.optimized_accuracy' in run:
                optimizer = run['params.optimizer']
                base_acc = float(run['metrics.base_accuracy'])
                opt_acc = float(run['metrics.optimized_accuracy'])
                
                data.append({
                    'Optimizer': optimizer,
                    'Stage': 'Base Model',
                    'Accuracy': base_acc
                })
                data.append({
                    'Optimizer': optimizer,
                    'Stage': 'Optimized Model',
                    'Accuracy': opt_acc
                })
        
        if not data:
            logger.warning("No suitable data found for optimizer comparison plot")
            return None
        
        # Create DataFrame and plot
        df = pd.DataFrame(data)
        
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        
        ax = sns.barplot(x='Optimizer', y='Accuracy', hue='Stage', data=df)
        
        plt.title('Accuracy Comparison by Optimizer', fontsize=14)
        plt.xlabel('Optimizer', fontsize=12)
        plt.ylabel('Accuracy', fontsize=12)
        plt.ylim(0, 1.0)
        
        # Add value labels on bars
        for container in ax.containers:
            ax.bar_label(container, fmt='%.2f')
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Optimizer comparison plot saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Failed to generate optimizer comparison plot: {e}")
        return None

def generate_performance_trend_plot(runs, output_path=None):
    """Generate a line plot showing performance trends over time."""
    if output_path is None:
        output_path = os.path.join("analysis_results", f"performance_trend_{int(time.time())}.png")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Prepare data for plotting
        data = []
        for run_id, run in runs.items():
            if ('metrics.optimized_accuracy' in run and 
                'metrics.improvement' in run and 
                'params.optimizer' in run and
                'start_time' in run):
                
                opt_acc = float(run['metrics.optimized_accuracy'])
                improvement = float(run['metrics.improvement'])
                optimizer = run['params.optimizer']
                start_time = pd.to_datetime(run['start_time'])
                
                data.append({
                    'Date': start_time,
                    'Optimizer': optimizer,
                    'Optimized Accuracy': opt_acc,
                    'Improvement': improvement
                })
        
        if not data:
            logger.warning("No suitable data found for performance trend plot")
            return None
        
        # Create DataFrame and sort by date
        df = pd.DataFrame(data)
        df = df.sort_values('Date')
        
        # Create plots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Plot optimized accuracy
        for optimizer in df['Optimizer'].unique():
            subset = df[df['Optimizer'] == optimizer]
            ax1.plot(subset['Date'], subset['Optimized Accuracy'], 'o-', label=optimizer)
        
        ax1.set_title('Optimized Accuracy Over Time', fontsize=14)
        ax1.set_ylabel('Accuracy', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend()
        
        # Plot improvement
        for optimizer in df['Optimizer'].unique():
            subset = df[df['Optimizer'] == optimizer]
            ax2.plot(subset['Date'], subset['Improvement'], 'o-', label=optimizer)
        
        ax2.set_title('Improvement Over Base Model', fontsize=14)
        ax2.set_ylabel('Improvement', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Format date axis
        date_format = DateFormatter('%Y-%m-%d %H:%M')
        ax2.xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Performance trend plot saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Failed to generate performance trend plot: {e}")
        return None

def generate_parameter_impact_plot(runs, params_to_analyze=None, output_path=None):
    """Generate plots showing the impact of different parameters on model performance."""
    if output_path is None:
        output_path = os.path.join("analysis_results", f"parameter_impact_{int(time.time())}.png")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not params_to_analyze:
        params_to_analyze = ['max_train', 'max_val']
    
    try:
        # Prepare data for plotting
        data = []
        for run_id, run in runs.items():
            if 'metrics.optimized_accuracy' in run:
                row = {'Optimized Accuracy': float(run['metrics.optimized_accuracy'])}
                
                # Add parameters if available
                for param in params_to_analyze:
                    param_key = f'params.{param}'
                    if param_key in run:
                        try:
                            # Try to convert to numeric
                            row[param] = float(run[param_key])
                        except ValueError:
                            # Keep as string if not numeric
                            row[param] = run[param_key]
                
                # Add only if all requested parameters are available
                if all(param in row for param in params_to_analyze):
                    data.append(row)
        
        if not data:
            logger.warning("No suitable data found for parameter impact plot")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create subplots for each parameter
        n_params = len(params_to_analyze)
        fig, axes = plt.subplots(1, n_params, figsize=(6*n_params, 5))
        
        if n_params == 1:
            axes = [axes]  # Make it iterable for a single parameter
        
        for i, param in enumerate(params_to_analyze):
            ax = axes[i]
            
            # Check if parameter is numeric or categorical
            if pd.api.types.is_numeric_dtype(df[param]):
                # For numeric parameters, use scatter plot
                sns.regplot(x=param, y='Optimized Accuracy', data=df, ax=ax)
                ax.set_title(f'Impact of {param} on Accuracy', fontsize=14)
                ax.set_xlabel(param, fontsize=12)
                if i == 0:
                    ax.set_ylabel('Optimized Accuracy', fontsize=12)
                else:
                    ax.set_ylabel('')
            else:
                # For categorical parameters, use boxplot
                sns.boxplot(x=param, y='Optimized Accuracy', data=df, ax=ax)
                ax.set_title(f'Impact of {param} on Accuracy', fontsize=14)
                ax.set_xlabel(param, fontsize=12)
                if i == 0:
                    ax.set_ylabel('Optimized Accuracy', fontsize=12)
                else:
                    ax.set_ylabel('')
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Parameter impact plot saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Failed to generate parameter impact plot: {e}")
        return None

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze MLflow experiment results for Bible QA")
    parser.add_argument("--experiment", type=str, default="bible_qa_optimization", help="Experiment name to analyze")
    parser.add_argument("--limit", type=int, default=20, help="Limit number of runs to analyze")
    parser.add_argument("--filter", type=str, help="Filter runs by parameter (format: 'param=value')")
    parser.add_argument("--uri", type=str, default="http://localhost:5000", help="MLflow tracking URI")
    parser.add_argument("--output", type=str, default="analysis_results", help="Output directory for reports")
    parser.add_argument("--visualize", action="store_true", help="Generate visualization plots")
    parser.add_argument("--compare-optimizers", action="store_true", help="Generate optimizer comparison plot")
    parser.add_argument("--show-trends", action="store_true", help="Generate performance trends plot")
    parser.add_argument("--analyze-params", type=str, help="Parameters to analyze impact (comma-separated)")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # Connect to MLflow
        mlflow.set_tracking_uri(args.uri)
        client = MlflowClient()
        
        # Get experiment
        experiment = client.get_experiment_by_name(args.experiment)
        if not experiment:
            logger.error(f"Experiment '{args.experiment}' not found")
            return 1
        
        logger.info(f"Analyzing experiment: {experiment.name} (ID: {experiment.experiment_id})")
        
        # Get runs
        filter_string = ""
        if args.filter:
            parts = args.filter.split("=")
            if len(parts) == 2:
                param_name, param_value = parts
                filter_string = f"params.{param_name} = '{param_value}'"
        
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=filter_string,
            max_results=args.limit
        )
        
        logger.info(f"Found {len(runs)} runs")
        
        if not runs:
            logger.warning("No runs found matching criteria")
            return 1
        
        # Process runs
        run_data = {}
        for run in runs:
            run_id = run.info.run_id
            run_data[run_id] = {
                "run_id": run_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time
            }
            
            # Add metrics
            for metric_name, metric_value in run.data.metrics.items():
                run_data[run_id][f"metrics.{metric_name}"] = metric_value
            
            # Add parameters
            for param_name, param_value in run.data.params.items():
                run_data[run_id][f"params.{param_name}"] = param_value
        
        # Create report
        output_path = os.path.join(args.output, f"report_{args.experiment}_{int(time.time())}.json")
        report = create_report(run_data)
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_path}")
        
        # Print summary
        print_summary(report)
        
        # Generate visualizations if requested
        if args.visualize or args.compare_optimizers or args.show_trends or args.analyze_params:
            if not VISUALIZATION_AVAILABLE:
                logger.warning("Visualization libraries not available. Install matplotlib and pandas.")
            else:
                logger.info("Generating visualizations...")
                
                # Base path for visualizations
                viz_dir = os.path.join(args.output, "visualizations")
                os.makedirs(viz_dir, exist_ok=True)
                
                # Generate optimizer comparison
                if args.visualize or args.compare_optimizers:
                    opt_path = os.path.join(viz_dir, f"optimizer_comparison_{int(time.time())}.png")
                    generate_optimizer_comparison_plot(run_data, output_path=opt_path)
                
                # Generate performance trends
                if args.visualize or args.show_trends:
                    trend_path = os.path.join(viz_dir, f"performance_trend_{int(time.time())}.png")
                    generate_performance_trend_plot(run_data, output_path=trend_path)
                
                # Generate parameter impact plots
                if args.visualize or args.analyze_params:
                    params_to_analyze = None
                    if args.analyze_params:
                        params_to_analyze = args.analyze_params.split(",")
                    
                    param_path = os.path.join(viz_dir, f"parameter_impact_{int(time.time())}.png")
                    generate_parameter_impact_plot(run_data, params_to_analyze=params_to_analyze, output_path=param_path)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 