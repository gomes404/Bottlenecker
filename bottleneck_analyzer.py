import csv
import tkinter as tk
from tkinter import ttk
import sys
import platform
import psutil
import subprocess
import os
import requests
import wmi
import cpuinfo
import re

# Class to represent benchmark data for different components
class BenchmarkData:
    def __init__(self, type, part_number, brand, model, rank, benchmark, samples, url):
        self.type = type
        self.part_number = part_number
        self.brand = brand
        self.model = model
        self.rank = int(rank) if rank else 0
        self.benchmark = float(benchmark) if benchmark else 0.0
        self.samples = int(samples) if samples else 0
        self.url = url

    def __repr__(self):
        return f"{self.type}: {self.brand} {self.model} (Rank: {self.rank}, Benchmark: {self.benchmark})"

# Main class for the Bottleneck Analyzer application
class BottleneckAnalyzer:
    def __init__(self, root):
        self.root = root
        self.system_info = {}
        self.setup_ui() # Set up the user interface
        self.load_benchmark_data() # Load benchmark data from CSV files

    def setup_ui(self):
        # Set up the main window
        self.root.title("System Bottleneck Analyzer")

        self.system_info_label = ttk.Label(self.root, text="System Information: Not detected yet")
        self.system_info_label.pack(pady=10)

        self.bottleneck_label = ttk.Label(self.root, text="Bottleneck: Not analyzed yet")
        self.bottleneck_label.pack(pady=10)

        self.analyze_button = ttk.Button(self.root, text="Analyze System", command=self.analyze_system)
        self.analyze_button.pack(pady=20)

        self.upgrade_combo = ttk.Combobox(self.root, values=["CPU", "GPU", "RAM", "SSD"])
        self.upgrade_combo.set("Select component")  # Set a default text
        self.upgrade_combo.pack(pady=10)

        self.recommend_button = ttk.Button(self.root, text="Recommend Upgrade", command=self.recommend_upgrade)
        self.recommend_button.pack(pady=10)

        self.recommendation_label = ttk.Label(self.root, text="Upgrade recommendation will appear here", wraplength=400)
        self.recommendation_label.pack(pady=10)

    def load_benchmark_data(self):
        # Load benchmark data from CSV files
        self.cpu_data = self.load_csv('Benchmarks/CPU_UserBenchmarks.csv')
        self.gpu_data = self.load_csv('Benchmarks/GPU_UserBenchmarks.csv')
        self.ram_data = self.load_csv('Benchmarks/RAM_UserBenchmarks.csv')
        self.ssd_data = self.load_csv('Benchmarks/SSD_UserBenchmarks.csv')
        self.hdd_data = self.load_csv('Benchmarks/HDD_UserBenchmarks.csv')
        self.usb_data = self.load_csv('Benchmarks/USB_UserBenchmarks.csv')

    def load_csv(self, filename):
        # Load data from a given CSV file and return as a list of BenchmarkData objects
        data = []
        try:
            with open(filename, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    benchmark_entry = BenchmarkData(
                        type=row.get('Type'),
                        part_number=row.get('Part Number'),
                        brand=row.get('Brand'),
                        model=row.get('Model'),
                        rank=row.get('Rank'),
                        benchmark=row.get('Benchmark'),
                        samples=row.get('Samples'),
                        url=row.get('URL')
                    )
                    data.append(benchmark_entry)
        except FileNotFoundError:
            print(f"Error: The file {filename} was not found.")
        except Exception as e:
            print(f"Error while reading the file {filename}: {e}")
        
        return data

    def analyze_system(self):
        # Analyze the current system
        self.collect_system_info()
        
        results = []
        for component, value in self.system_info.items():
            if component in ['cpu_usage', 'memory_usage', 'disk']:
                score = self.calculate_score(component, value)
                results.append((component, value, score))
        
        self.update_ui(results)
        
        bottleneck = self.detect_bottleneck()
        upgrade_recommendations = self.generate_upgrade_recommendations()
        
        self.bottleneck_label.config(text=f"Bottleneck: {bottleneck}")
        self.recommendation_label.config(text=f"Upgrade Recommendations:\n{upgrade_recommendations}")

    def update_ui(self, results):
        # Update the UI with system information and bottleneck analysis results
        system_info_text = (
            f"CPU: {self.system_info['cpu']}\n"
            f"CPU Usage: {self.system_info['cpu_usage']:.1f}%\n"
            f"RAM: {self.system_info['ram']}\n"
            f"RAM Usage: {self.system_info['memory_usage']:.1f}%\n"
            f"GPU: {self.system_info['gpu']}\n"
            f"Disk Usage: {self.system_info['disk']:.1f}%"
        )
        self.system_info_label.config(text=f"System Information:\n{system_info_text}")

        bottleneck = self.detect_bottleneck()
        self.bottleneck_label.config(text=f"Bottleneck: {bottleneck}")

    def collect_system_info(self):
        # Collect detailed system information
        self.system_info = {}
        
        # Get detailed CPU info
        cpu_info = cpuinfo.get_cpu_info()
        cpu_brand = cpu_info['brand_raw']
        cpu_freq = psutil.cpu_freq().max / 1000  # Convert to GHz
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        self.system_info['cpu'] = cpu_brand  # Store just the brand and model
        self.system_info['cpu_usage'] = psutil.cpu_percent()

        # Get RAM info
        c = wmi.WMI()
        ram_modules = c.Win32_PhysicalMemory()
        total_ram = sum(int(module.Capacity) for module in ram_modules) / (1024**3)  # Convert to GB
        if ram_modules:
            ram_speed = ram_modules[0].Speed
            ram_type = ram_modules[0].MemoryType
            ram_manufacturer = ram_modules[0].Manufacturer
            ram_type_name = "DDR4" if ram_type == 26 else "DDR5" if ram_type == 30 else f"Type {ram_type}"
            ram_model = f"{ram_manufacturer} {ram_type_name} {ram_speed}MHz"
            self.system_info['ram'] = ram_model  # Store just the RAM model
        else:
            self.system_info['ram'] = "Unknown RAM"
        self.system_info['memory_usage'] = psutil.virtual_memory().percent

        # Get GPU information
        try:
            gpu_info = c.Win32_VideoController()[0]
            self.system_info['gpu'] = gpu_info.Name
            self.system_info['gpu_usage'] = "N/A"
        except Exception as e:
            print(f"Error getting GPU info: {e}")
            self.system_info['gpu'] = "Unknown GPU"
            self.system_info['gpu_usage'] = "N/A"

        # Get disk information
        try:
            self.system_info['disk'] = psutil.disk_usage('/').percent
        except:
            self.system_info['disk'] = "N/A"

        # Ensure all percentage values are floats
        for key in ['cpu_usage', 'memory_usage', 'disk']:
            try:
                self.system_info[key] = float(self.system_info[key])
            except ValueError:
                self.system_info[key] = 0.0

    def calculate_score(self, component, value):
        component = component.lower()
        
        if component == 'cpu':
            # Assuming value is clock speed in GHz
            return value * 1000  # Simple score based on clock speed
        
        elif component == 'gpu':
            # Assuming value is VRAM in GB
            return value * 500  # Simple score based on VRAM
        
        elif component == 'ram':
            # Assuming value is RAM size in GB
            return value * 100  # Simple score based on RAM size
        
        elif component == 'ssd' or component == 'hdd':
            # Assuming value is storage size in GB
            return value * 0.5  # Simple score based on storage size
        
        else:
            # For unknown components, return a default score
            return 0

    def detect_bottleneck(self):
        cpu_score = self.get_benchmark_score(self.cpu_data, "Generic CPU")
        gpu_score = self.get_benchmark_score(self.gpu_data, self.system_info['gpu'])
        ram_score = self.get_benchmark_score(self.ram_data, "Generic RAM")
        ssd_score = self.get_benchmark_score(self.ssd_data, "Generic SSD")

        scores = {"CPU": cpu_score, "GPU": gpu_score, "RAM": ram_score, "SSD": ssd_score}
        
        # More sophisticated bottleneck detection
        cpu_gpu_ratio = cpu_score / gpu_score if gpu_score else float('inf')
        if cpu_gpu_ratio < 0.5:
            return "CPU (significantly weaker than GPU)"
        elif cpu_gpu_ratio > 2:
            return "GPU (significantly weaker than CPU)"
        elif ram_score < min(cpu_score, gpu_score) * 0.5:
            return "RAM (significantly slower than CPU/GPU)"
        elif ssd_score < min(cpu_score, gpu_score, ram_score) * 0.3:
            return "SSD (significantly slower than other components)"
        else:
            return "Balanced system (no significant bottleneck)"

    def get_benchmark_score(self, benchmark_data, component_name):
        # Get the benchmark score for a given component
        if isinstance(component_name, (int, float)):
            return component_name  # Return the usage percentage as the score
        for item in benchmark_data:
            if component_name.lower() in item.model.lower():
                return item.benchmark
        return 0.0  # Return a low score if no match is found to ensure upgrades are recommended

    def recommend_upgrade(self):
        # Generate upgrade recommendations
        component = self.upgrade_combo.get()
        if not component:
            self.recommendation_label.config(text="Please select a component to upgrade")
            return

        recommendation = self.get_recommendation(component)
        compatibility = self.check_compatibility(recommendation)
        potential_bottleneck = self.analyze_potential_bottleneck(recommendation)

        # Generate general upgrade recommendations
        general_recommendations = self.generate_general_recommendations()

        result = f"Recommended {component} upgrade: {recommendation}\n"
        result += f"Compatibility: {compatibility}\n"
        result += f"Potential bottleneck: {potential_bottleneck}\n\n"
        result += "General Upgrade Recommendations:\n" + general_recommendations

        self.recommendation_label.config(text=result)

    def get_recommendation(self, component):
        # Get a specific upgrade recommendation for a given component
        component_lower = component.lower()
        benchmark_data = {
            "cpu": self.cpu_data,
            "gpu": self.gpu_data,
            "ram": self.ram_data,
            "ssd": self.ssd_data
        }.get(component_lower)

        if not benchmark_data:
            return f"No benchmark data available for {component}"

        current_model = self.system_info.get(component_lower, "Unknown")
        current_score = self.get_benchmark_score(benchmark_data, current_model)
        current_rank = self.get_component_rank(benchmark_data, current_model)

        # Find better performing components
        better_components = [item for item in benchmark_data if item.benchmark > current_score and item.rank < current_rank]
        
        if better_components:
            # Sort by highest benchmark and lowest rank
            better_components.sort(key=lambda x: (-x.benchmark, x.rank))
            
            # Recommend the component with the highest benchmark and lowest rank
            recommendation = better_components[0]
            return f"{recommendation.brand} {recommendation.model} (Rank: {recommendation.rank}, Score: {recommendation.benchmark:.1f})"
        else:
            return f"Your current {component} is already top-tier. No upgrade necessary."

    def generate_general_recommendations(self):
        recommendations = []

        components = [
            ('CPU', self.cpu_data, self.system_info.get('cpu', 'Unknown')),
            ('RAM', self.ram_data, self.system_info.get('ram', 'Unknown')),
            ('GPU', self.gpu_data, self.system_info.get('gpu', 'Unknown')),
            ('SSD', self.ssd_data, self.system_info.get('disk', 'Unknown'))
        ]

        for component_name, benchmark_data, current_model in components:
            current_score = self.get_benchmark_score(benchmark_data, current_model)
            current_rank = self.get_component_rank(benchmark_data, current_model)

            better_components = [item for item in benchmark_data if item.benchmark > current_score and item.rank < current_rank]
            
            if better_components:
                # Sort by highest benchmark and lowest rank
                better_components.sort(key=lambda x: (-x.benchmark, x.rank))
                
                # Recommend the component with the highest benchmark and lowest rank
                recommendation = better_components[0]
                improvement_percentage = ((recommendation.benchmark - current_score) / current_score) * 100
                
                recommendations.append(f"Consider upgrading your {component_name} to {recommendation.brand} {recommendation.model} "
                                       f"(Rank: {recommendation.rank}, Score: {recommendation.benchmark:.1f}). "
                                       f"This would provide a {improvement_percentage:.1f}% performance improvement.")
            else:
                recommendations.append(f"Your {component_name} ({current_model}) is already high-performing. No immediate upgrade necessary.")

        # Storage recommendation
        disk_usage = self.system_info['disk']
        if isinstance(disk_usage, float):
            if disk_usage > 80:
                recommendations.append(f"Disk usage is high ({disk_usage:.1f}%). Consider upgrading to a larger or faster storage device.")
            elif disk_usage > 60:
                recommendations.append(f"Disk usage is moderate ({disk_usage:.1f}%). An SSD upgrade might improve system responsiveness.")
        else:
            recommendations.append("Unable to determine disk usage. Consider checking your storage device's health.")

        return "\n".join(recommendations)

    def get_component_rank(self, benchmark_data, component_name):
        for item in benchmark_data:
            if component_name.lower() in item.model.lower():
                return item.rank
        return float('inf')  # Return a high rank if no match is found

    def get_price(self, model):
        # This is a placeholder. In a real application, you'd want to use an API or web scraping to get current prices.
        # For demonstration, we'll return a random price between $100 and $1000
        import random
        return random.uniform(100, 1000)

    def check_compatibility(self, recommendation):
        component = self.upgrade_combo.get().lower()
        
        if component == "cpu":
            current_socket = self.get_cpu_socket(self.system_info.get('cpu', 'Unknown'))
            new_socket = self.get_cpu_socket(recommendation)
            if current_socket != new_socket:
                return f"Incompatible: Current socket {current_socket}, recommended CPU uses {new_socket}"
        elif component == "ram":
            current_type = self.get_ram_type(self.system_info.get('memory', 'Unknown'))
            new_type = self.get_ram_type(recommendation)
            if current_type != new_type:
                return f"Incompatible: Current RAM type {current_type}, recommended RAM is {new_type}"
        
        return "Compatible with current system"

    def get_cpu_socket(self, cpu_model):
        # This is a placeholder. In a real application, you'd want to use a database or API to get this information.
        return "LGA1200"  # Example socket

    def get_ram_type(self, ram_model):
        # This is a placeholder. In a real application, you'd want to use a database or API to get this information.
        return "DDR4"  # Example RAM type

    def analyze_potential_bottleneck(self, recommendation):
        current_scores = {
            "CPU": self.get_benchmark_score(self.cpu_data, "Generic CPU"),
            "GPU": self.get_benchmark_score(self.gpu_data, self.system_info['gpu']),
            "RAM": self.get_benchmark_score(self.ram_data, "Generic RAM"),
            "SSD": self.get_benchmark_score(self.ssd_data, "Generic SSD")
        }
        
        component = self.upgrade_combo.get()
        if component and component.lower() in ["cpu", "gpu", "ram", "ssd"]:
            data_attr = f"{component.lower()}_data"
            if hasattr(self, data_attr):
                new_score = self.get_benchmark_score(getattr(self, data_attr), recommendation)
                current_scores[component] = new_score
            else:
                return f"Error: No benchmark data available for {component}"
        else:
            return "Error: Invalid component selected"
        
        bottleneck = min(current_scores, key=current_scores.get)
        if bottleneck == component:
            return f"No new bottleneck introduced. {component} will still be the limiting factor."
        else:
            return f"Potential new bottleneck: {bottleneck}"

    def generate_upgrade_recommendations(self):
        recommendations = []

        # CPU recommendation
        cpu_usage = self.system_info['cpu_usage']
        if cpu_usage > 80:
            recommendations.append(f"CPU usage is high ({cpu_usage:.1f}%). Consider upgrading your CPU.")
        elif cpu_usage > 60:
            recommendations.append(f"CPU usage is moderate ({cpu_usage:.1f}%). An upgrade might improve performance.")

        # RAM recommendation
        ram_usage = self.system_info['memory_usage']
        if ram_usage > 80:
            recommendations.append(f"RAM usage is high ({ram_usage:.1f}%). Consider adding more RAM.")
        elif ram_usage > 60:
            recommendations.append(f"RAM usage is moderate ({ram_usage:.1f}%). Adding more RAM might improve performance.")

        # GPU recommendation
        # Since we don't have GPU usage, we'll make a generic recommendation
        recommendations.append("Consider upgrading your GPU if you experience lag in graphics-intensive applications.")

        # Storage recommendation
        disk_usage = self.system_info['disk']
        if disk_usage > 80:
            recommendations.append(f"Disk usage is high ({disk_usage:.1f}%). Consider upgrading to a larger or faster storage device.")
        elif disk_usage > 60:
            recommendations.append(f"Disk usage is moderate ({disk_usage:.1f}%). An SSD upgrade might improve system responsiveness.")

        # If no specific recommendations, provide a general suggestion
        if not recommendations:
            recommendations.append("Your system is performing well. No immediate upgrades necessary.")

        return "\n".join(recommendations)

    def get_component_rank(self, benchmark_data, component_name):
        if not isinstance(component_name, str):
            return float('inf')  # Return a high rank if component_name is not a string
        
        component_name_lower = component_name.lower()
        for item in benchmark_data:
            if isinstance(item.model, str) and component_name_lower in item.model.lower():
                return item.rank
        return float('inf')  # Return a high rank if no match is found

    def generate_general_recommendations(self):
        recommendations = []

        components = [
            ('CPU', self.cpu_data, str(self.system_info.get('cpu', 'Unknown'))),
            ('RAM', self.ram_data, str(self.system_info.get('ram', 'Unknown'))),
            ('GPU', self.gpu_data, str(self.system_info.get('gpu', 'Unknown'))),
            ('SSD', self.ssd_data, str(self.system_info.get('disk', 'Unknown')))
        ]

        for component_name, benchmark_data, current_model in components:
            current_score = self.get_benchmark_score(benchmark_data, current_model)
            current_rank = self.get_component_rank(benchmark_data, current_model)

            better_components = [item for item in benchmark_data if item.benchmark > current_score and item.rank < current_rank]
            
            if better_components:
                better_components.sort(key=lambda x: (-x.benchmark, x.rank))
                recommendation = better_components[0]
                
                if current_score > 0:
                    improvement_percentage = ((recommendation.benchmark - current_score) / current_score) * 100
                    recommendations.append(f"Consider upgrading your {component_name} to {recommendation.brand} {recommendation.model} "
                                           f"(Rank: {recommendation.rank}, Score: {recommendation.benchmark:.1f}). "
                                           f"This would provide a {improvement_percentage:.1f}% performance improvement.")
                else:
                    recommendations.append(f"Consider upgrading your {component_name} to {recommendation.brand} {recommendation.model} "
                                           f"(Rank: {recommendation.rank}, Score: {recommendation.benchmark:.1f}) "
                                           f"for better performance.")
            else:
                if current_score > 0:
                    recommendations.append(f"Your {component_name} ({current_model}, Score: {current_score:.1f}) is already high-performing. No immediate upgrade necessary.")
                else:
                    recommendations.append(f"Unable to determine the performance of your current {component_name} ({current_model}). Consider checking for updates or potential issues.")

        # Storage recommendation
        disk_usage = self.system_info.get('disk_usage')
        if isinstance(disk_usage, (int, float)):
            if disk_usage > 80:
                recommendations.append(f"Disk usage is high ({disk_usage:.1f}%). Consider upgrading to a larger or faster storage device.")
            elif disk_usage > 60:
                recommendations.append(f"Disk usage is moderate ({disk_usage:.1f}%). An SSD upgrade might improve system responsiveness.")
        else:
            recommendations.append("Unable to determine disk usage. Consider checking your storage device's health.")

        return "\n".join(recommendations)

def main():
    root = tk.Tk()
    app = BottleneckAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()