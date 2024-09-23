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
        self.setup_ui()  # Initialize the user interface
        self.load_benchmark_data()  # Load benchmark data from CSV files

    def setup_ui(self):
        # Set up the UI components
        self.root.title("System Bottleneck Analyzer")

        self.system_info_label = ttk.Label(self.root, text="System Information: Not detected yet")
        self.system_info_label.pack(pady=10)

        self.bottleneck_label = ttk.Label(self.root, text="Bottleneck: Not analyzed yet")
        self.bottleneck_label.pack(pady=10)

        self.analyze_button = ttk.Button(self.root, text="Analyze System", command=self.analyze_system)
        self.analyze_button.pack(pady=20)

        self.upgrade_combo = ttk.Combobox(self.root, values=["CPU", "GPU", "RAM", "SSD"])
        self.upgrade_combo.set("Select component")  # Default text
        self.upgrade_combo.pack(pady=10)

        self.recommend_button = ttk.Button(self.root, text="Recommend Upgrade", command=self.recommend_upgrade)
        self.recommend_button.pack(pady=10)

        self.recommendation_label = ttk.Label(self.root, text="Upgrade recommendation will appear here", wraplength=400)
        self.recommendation_label.pack(pady=10)

    def load_benchmark_data(self):
        # Load benchmark data from various CSV files
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
        # Analyze the current system and update the UI with results
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
        # Update the UI with the current system information
        system_info_text = (
            f"CPU: {self.system_info['cpu']}\n"
            f"CPU Usage: {self.system_info['cpu_usage']:.1f}%\n"
            f"RAM: {self.system_info['ram']}\n"
            f"RAM Usage: {self.system_info['memory_usage']:.1f}%\n"
            f"GPU: {self.system_info['gpu']}\n"
            f"Disk Usage: {self.system_info['disk']:.1f}%"
        )
        self.system_info_label.config(text=f"System Information:\n{system_info_text}")

    def collect_system_info(self):
        # Gather detailed system information
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
            # We can't get GPU usage easily without additional libraries, so we'll omit it
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
        # Implement scoring logic here (currently a placeholder)
        return 0  # Placeholder return value

    def detect_bottleneck(self):
        # Detect which component is the bottleneck in the system
        cpu_score = self.get_benchmark_score(self.cpu_data, "Generic CPU")
        gpu_score = self.get_benchmark_score(self.gpu_data, self.system_info['gpu'])
        ram_score = self.get_benchmark_score(self.ram_data, "Generic RAM")
        ssd_score = self.get_benchmark_score(self.ssd_data, "Generic SSD")

        scores = {"CPU": cpu_score, "GPU": gpu_score, "RAM": ram_score, "SSD": ssd_score}
        
        # More sophisticated bottleneck detection logic
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
        # Get the benchmark score for a specific component
        if isinstance(component_name, (int, float)):
            return component_name  # Return the usage percentage as the score
        for item in benchmark_data:
            if component_name.lower() in item.model.lower():
                return item.benchmark
        return 0.0  # Return a score of 0 if not found

    def generate_upgrade_recommendations(self):
        # Generate upgrade recommendations based on the detected bottleneck
        bottleneck = self.detect_bottleneck()
        if bottleneck == "CPU":
            return "Consider upgrading your CPU for better performance."
        elif bottleneck == "GPU":
            return "Consider upgrading your GPU for better graphics performance."
        elif bottleneck == "RAM":
            return "Consider adding more RAM for better multitasking."
        elif bottleneck == "SSD":
            return "Consider upgrading to a faster SSD."
        else:
            return "Your system is well-balanced."

# Main entry point of the application
if __name__ == "__main__":
    root = tk.Tk()
    app = BottleneckAnalyzer(root)
    root.mainloop()
