Bottleneck Analyzer
Overview
Bottleneck Analyzer is a Python application designed to analyze your system's performance and identify potential bottlenecks. The application evaluates various hardware components (CPU, GPU, RAM, SSD) and provides recommendations for upgrades based on benchmark data.

Features
System Analysis: Automatically detects and displays system information, including CPU, GPU, RAM, and disk usage.
Bottleneck Detection: Analyzes component performance to identify any potential bottlenecks in the system.
Upgrade Recommendations: Offers suggestions for hardware upgrades based on current performance and benchmark comparisons.
User-Friendly Interface: Built with Tkinter for a simple and intuitive user experience.
Requirements
Python 3.x
Tkinter (usually included with Python)
psutil
wmi
cpuinfo
requests
CSV files with benchmark data
Installation
Clone this repository:

bash
Copy code
git clone https://github.com/yourusername/bottleneck-analyzer.git
cd bottleneck-analyzer
Install required packages:

bash
Copy code
pip install psutil wmi py-cpuinfo requests
Download benchmark CSV files and place them in the Benchmarks folder:

CPU_UserBenchmarks.csv
GPU_UserBenchmarks.csv
RAM_UserBenchmarks.csv
SSD_UserBenchmarks.csv
HDD_UserBenchmarks.csv
USB_UserBenchmarks.csv
Usage
Run the application:

bash
Copy code
python bottleneck_analyzer.py
Click the Analyze System button to gather system information and detect bottlenecks.

Select a component from the dropdown and click Recommend Upgrade to receive upgrade suggestions.

Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

License
This project is licensed under the MIT License.

Acknowledgements
psutil for system information retrieval.
WMI for Windows management.
py-cpuinfo for CPU details.
