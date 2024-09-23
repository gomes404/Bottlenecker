# System Bottleneck Analyzer

## Description

The System Bottleneck Analyzer is a Python application that helps users identify performance bottlenecks in their computer systems and provides upgrade recommendations. It analyzes various components such as CPU, GPU, RAM, and storage devices, comparing them against benchmark data to determine potential performance improvements.

## Features

- Collects and displays detailed system information
- Analyzes system components to detect bottlenecks
- Provides upgrade recommendations based on benchmark data
- Checks compatibility of recommended upgrades
- Offers general upgrade suggestions for all major components

## Requirements

- Python 3.6+
- tkinter
- psutil
- wmi
- py-cpuinfo
- requests

## Installation

1. Clone this repository or download the source code.
2. Install the required dependencies:
```
pip install psutil wmi py-cpuinfo requests
```
3. Ensure you have the necessary benchmark CSV files in a `Benchmarks` folder:
   - CPU_UserBenchmarks.csv
   - GPU_UserBenchmarks.csv
   - RAM_UserBenchmarks.csv
   - SSD_UserBenchmarks.csv
   - HDD_UserBenchmarks.csv
   - USB_UserBenchmarks.csv

## Usage

1. Run the application:
```
python bottleneck_analyzer.py
```
2. Click the "Analyze System" button to collect and display system information.
3. Select a component from the dropdown menu and click "Recommend Upgrade" for specific upgrade suggestions.

## Contributing

Contributions to improve the Bottleneck Analyzer are welcome. Please feel free to submit pull requests or open issues to discuss proposed changes or report bugs.

## License

[MIT License](LICENSE)

## Disclaimer

This tool provides recommendations based on benchmark data and general performance metrics. Always consult with a professional or do thorough research before making any hardware upgrades to your system.
