#!/usr/bin/env python3
"""
Analyze MLflow Results for Bible QA Optimization

This script analyzes the MLflow results from Bible QA optimization runs
and generates visualizations and summary statistics.

Usage:
    python -m scripts.analyze_mlflow_results --experiment-name bible_qa_optimization
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import mlflow
from mlflow.tracking import MlflowClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/analyze_mlflow_results.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze MLflow results for Bible QA optimization")
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="bible_qa_optimization",
        help="Name of MLflow experiment to analyze"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="analysis_results",
        help="Directory to save analysis results"
    )
    parser.add_argument(
        "--metric-name",
        type=str,
        default="accuracy",
        help="Name of the metric to analyze"
    )
    parser.add_argument(
        "--min-iterations",
        type=int,
        default=3,
        help="Minimum number of iterations for a run to be included"
    )
    return parser.parse_args()

def get_experiment_runs(experiment_name: str) -> List[Dict[str, Any]]:
    """Get all runs from the specified experiment."""
    try:
        # Get experiment by name
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            logger.error(f"Experiment '{experiment_name}' not found")
            return []
        
        # Get all runs from the experiment
        client = MlflowClient()
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"]
        )
        
        logger.info(f"Found {len(runs)} runs for experiment '{experiment_name}'")
        return runs
    
    except Exception as e:
        logger.error(f"Error getting experiment runs: {e}")
        return []

def extract_metrics(runs: List[Dict[str, Any]], metric_name: str, min_iterations: int) -> Tuple[pd.DataFrame, Dict[str, List[float]]]:
    """Extract metrics from runs and organize by optimization method."""
    data = []
    methods_data = {}
    
    for run in runs:
        run_id = run.info.run_id
        run_name = run.info.run_name
        
        # Get metrics for the run
        metrics_history = {}
        client = MlflowClient()
        
        for metric in client.get_metric_history(run_id, metric_name):
            iteration = int(metric.step)
            metrics_history[iteration] = metric.value
        
        # Skip runs with too few iterations
        if len(metrics_history) < min_iterations:
            continue
        
        # Extract optimization method from tags or run name
        if "optimization_method" in run.data.tags:
            method = run.data.tags["optimization_method"]
        elif run_name:
            if "better_together" in run_name.lower():
                method = "better_together"
            elif "infer_rules" in run_name.lower():
                method = "infer_rules"
            else:
                method = "unknown"
        else:
            method = "unknown"
        
        # Add method data for plotting
        if method not in methods_data:
            methods_data[method] = []
        
        # Fill in missing iterations (in case of early stopping)
        max_iteration = max(metrics_history.keys())
        for i in range(max_iteration + 1):
            if i not in metrics_history:
                metrics_history[i] = metrics_history.get(i-1, 0.0)
        
        # Get final accuracy
        final_accuracy = max(metrics_history.values())
        best_iteration = [i for i, v in metrics_history.items() if v == final_accuracy][0]
        
        # Add run data
        data.append({
            "run_id": run_id,
            "run_name": run_name,
            "method": method,
            "iterations": len(metrics_history),
            "final_accuracy": final_accuracy,
            "best_iteration": best_iteration
        })
        
        # Add metrics history for plotting
        methods_data[method].append([metrics_history.get(i, 0.0) for i in range(max_iteration + 1)])
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Average metrics for each method
    for method in methods_data:
        if not methods_data[method]:
            continue
        
        # Find max length
        max_length = max(len(hist) for hist in methods_data[method])
        
        # Pad shorter histories
        for i in range(len(methods_data[method])):
            if len(methods_data[method][i]) < max_length:
                methods_data[method][i] += [methods_data[method][i][-1]] * (max_length - len(methods_data[method][i]))
        
        # Calculate average
        avg_metrics = []
        for i in range(max_length):
            values = [hist[i] for hist in methods_data[method] if i < len(hist)]
            avg_metrics.append(sum(values) / len(values))
        
        methods_data[method] = avg_metrics
    
    return df, methods_data

def plot_metrics(methods_data: Dict[str, List[float]], output_dir: str, metric_name: str):
    """Plot metrics for each optimization method."""
    if not methods_data:
        logger.warning("No methods data to plot")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot metrics
    plt.figure(figsize=(10, 6))
    
    for method, metrics in methods_data.items():
        plt.plot(range(len(metrics)), metrics, label=method)
    
    plt.xlabel("Iteration")
    plt.ylabel(metric_name.capitalize())
    plt.title(f"{metric_name.capitalize()} by Iteration")
    plt.legend()
    plt.grid(True)
    
    # Save plot
    plot_path = os.path.join(output_dir, f"{metric_name}_by_iteration.png")
    plt.savefig(plot_path)
    logger.info(f"Saved plot to {plot_path}")
    
    # Close plot to avoid memory leaks
    plt.close()
    
    # Create comparison bar chart for final values
    plt.figure(figsize=(8, 5))
    
    methods = []
    final_values = []
    
    for method, metrics in methods_data.items():
        methods.append(method)
        final_values.append(metrics[-1])
    
    plt.bar(methods, final_values)
    plt.xlabel("Optimization Method")
    plt.ylabel(f"Final {metric_name.capitalize()}")
    plt.title(f"Final {metric_name.capitalize()} by Method")
    plt.ylim(0, 1.0)  # Assuming metric is between 0 and 1
    
    # Add value labels
    for i, v in enumerate(final_values):
        plt.text(i, v + 0.02, f"{v:.3f}", ha='center')
    
    # Save plot
    plot_path = os.path.join(output_dir, f"final_{metric_name}_by_method.png")
    plt.savefig(plot_path)
    logger.info(f"Saved plot to {plot_path}")
    
    # Close plot to avoid memory leaks
    plt.close()

def save_summary(df: pd.DataFrame, output_dir: str):
    """Save summary statistics to file."""
    if df.empty:
        logger.warning("No data to summarize")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate summary statistics
    summary = {
        "total_runs": len(df),
        "methods": df["method"].value_counts().to_dict(),
        "accuracy_stats": {
            "mean": df["final_accuracy"].mean(),
            "median": df["final_accuracy"].median(),
            "max": df["final_accuracy"].max(),
            "min": df["final_accuracy"].min()
        },
        "best_run": df.loc[df["final_accuracy"].idxmax()].to_dict() if not df.empty else {}
    }
    
    # Calculate method statistics
    method_stats = {}
    for method in df["method"].unique():
        method_df = df[df["method"] == method]
        method_stats[method] = {
            "runs": len(method_df),
            "mean_accuracy": method_df["final_accuracy"].mean(),
            "max_accuracy": method_df["final_accuracy"].max(),
            "mean_iterations": method_df["iterations"].mean()
        }
    
    summary["method_stats"] = method_stats
    
    # Save summary to file
    summary_path = os.path.join(output_dir, "optimization_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved summary to {summary_path}")
    
    # Save raw data to CSV
    csv_path = os.path.join(output_dir, "optimization_runs.csv")
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved run data to {csv_path}")

def main():
    """Main function to analyze MLflow results."""
    args = parse_args()
    
    # Get experiment runs
    runs = get_experiment_runs(args.experiment_name)
    if not runs:
        return 1
    
    # Extract metrics
    df, methods_data = extract_metrics(runs, args.metric_name, args.min_iterations)
    
    if df.empty:
        logger.warning("No runs with iteration metrics found")
        return 1
    
    # Plot metrics
    if len(methods_data) < 2:
        logger.warning("Not enough methods to compare")
    else:
        plot_metrics(methods_data, args.output_dir, args.metric_name)
    
    # Save summary
    save_summary(df, args.output_dir)
    
    logger.info("Analysis complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 