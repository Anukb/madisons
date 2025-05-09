import pytest
import os
import sys
from datetime import datetime

def run_tests():
    # Create results directory if it doesn't exist
    if not os.path.exists("results"):
        os.makedirs("results")
    
    # Generate timestamp for report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"results/test_report_{timestamp}.html"
    
    # Run pytest with HTML reporting
    pytest_args = [
        "-v",
        "--html", report_file,
        "--self-contained-html",
        "tests/"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    print(f"\nTest report generated: {report_file}")
    return exit_code

if __name__ == "__main__":
    sys.exit(run_tests())