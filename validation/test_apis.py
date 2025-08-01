#!/usr/bin/env python3
"""
Candidate API Validation Script

Tests candidate's API endpoints for functionality, data accuracy, and performance.
Provides automated scoring and detailed feedback for the coding test evaluation.
"""

import requests
import json
import time
import argparse
import sys
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
import statistics

@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    passed: bool
    score: float
    max_score: float
    message: str
    details: Dict[str, Any]
    execution_time: float

@dataclass
class ValidationReport:
    """Complete validation report"""
    candidate_url: str
    total_score: float
    max_total_score: float
    test_results: List[TestResult]
    summary: Dict[str, Any]
    timestamp: str

class CandidateAPIValidator:
    """Validates candidate API implementations"""
    
    def __init__(self, candidate_url: str, transaction_api_url: str = "http://localhost:8000"):
        self.candidate_url = candidate_url.rstrip('/')
        self.transaction_api_url = transaction_api_url.rstrip('/')
        self.test_results = []
        self.known_accounts = []
        self.expected_data = {}
        
        # Load test data and expected results
        self._load_test_data()
    
    def _load_test_data(self):
        """Load test accounts and expected data from transaction API"""
        try:
            # Get available accounts
            response = requests.get(f"{self.transaction_api_url}/accounts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.known_accounts = data['accounts'][:10]  # Use first 10 for testing
                print(f"Loaded {len(self.known_accounts)} test accounts")
            else:
                print(f"Warning: Could not load test accounts from {self.transaction_api_url}")
                
        except Exception as e:
            print(f"Error loading test data: {e}")
            
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Tuple[Optional[requests.Response], float]:
        """Make HTTP request with timing"""
        start_time = time.time()
        try:
            url = f"{self.candidate_url}{endpoint}"
            response = requests.request(method, url, timeout=30, **kwargs)
            execution_time = time.time() - start_time
            return response, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"Request failed: {e}")
            return None, execution_time
    
    def test_endpoint_availability(self) -> TestResult:
        """Test basic endpoint availability"""
        test_name = "Endpoint Availability"
        start_time = time.time()
        
        endpoints_to_test = [
            ("/health", "Health check"),
            (f"/users/{self.known_accounts[0]}/transactions", "User transactions"),
            (f"/users/{self.known_accounts[0]}/balance", "User balance")
        ]
        
        available_endpoints = 0
        details = {}
        
        for endpoint, description in endpoints_to_test:
            response, req_time = self._make_request(endpoint)
            if response and response.status_code < 500:
                available_endpoints += 1
                details[endpoint] = {"available": True, "status": response.status_code, "time": req_time}
            else:
                details[endpoint] = {"available": False, "status": response.status_code if response else 0, "time": req_time}
        
        execution_time = time.time() - start_time
        passed = available_endpoints == len(endpoints_to_test)
        score = (available_endpoints / len(endpoints_to_test)) * 20
        
        return TestResult(
            test_name=test_name,
            passed=passed,
            score=score,
            max_score=20.0,
            message=f"Available endpoints: {available_endpoints}/{len(endpoints_to_test)}",
            details=details,
            execution_time=execution_time
        )
    
    def test_transactions_endpoint(self) -> TestResult:
        """Test user transactions endpoint functionality"""
        test_name = "Transactions Endpoint"
        start_time = time.time()
        
        if not self.known_accounts:
            return TestResult(test_name, False, 0, 25.0, "No test accounts available", {}, 0)
        
        test_account = self.known_accounts[0]
        response, req_time = self._make_request(f"/users/{test_account}/transactions")
        
        details = {"account_tested": test_account, "response_time": req_time}
        
        if not response:
            return TestResult(test_name, False, 0, 25.0, "No response received", details, time.time() - start_time)
        
        details["status_code"] = response.status_code
        
        if response.status_code != 200:
            return TestResult(test_name, False, 0, 25.0, f"HTTP {response.status_code}", details, time.time() - start_time)
        
        try:
            data = response.json()
            details["response_size"] = len(str(data))
            
            # Check if response has expected structure
            checks = {
                "is_list_or_has_transactions": isinstance(data, list) or 'transactions' in data,
                "has_transaction_data": self._has_transaction_data(data),
                "response_not_empty": len(data) > 0 if isinstance(data, list) else len(data.get('transactions', [])) > 0
            }
            
            details["structure_checks"] = checks
            passed_checks = sum(checks.values())
            
            score = (passed_checks / len(checks)) * 25
            passed = passed_checks == len(checks)
            message = f"Structure checks passed: {passed_checks}/{len(checks)}"
            
        except json.JSONDecodeError:
            score = 0
            passed = False
            message = "Invalid JSON response"
            details["json_error"] = True
        
        execution_time = time.time() - start_time
        
        return TestResult(test_name, passed, score, 25.0, message, details, execution_time)
    
    def test_balance_endpoint(self) -> TestResult:
        """Test user balance endpoint functionality"""
        test_name = "Balance Endpoint"
        start_time = time.time()
        
        if not self.known_accounts:
            return TestResult(test_name, False, 0, 25.0, "No test accounts available", {}, 0)
        
        test_account = self.known_accounts[0]
        response, req_time = self._make_request(f"/users/{test_account}/balance")
        
        details = {"account_tested": test_account, "response_time": req_time}
        
        if not response:
            return TestResult(test_name, False, 0, 25.0, "No response received", details, time.time() - start_time)
        
        details["status_code"] = response.status_code
        
        if response.status_code != 200:
            return TestResult(test_name, False, 0, 25.0, f"HTTP {response.status_code}", details, time.time() - start_time)
        
        try:
            data = response.json()
            details["response_data"] = data
            
            # Check if response has balance information
            checks = {
                "has_balance_field": any(key in data for key in ['balance', 'amount', 'total', 'current_balance']),
                "balance_is_numeric": self._has_numeric_balance(data),
                "proper_json_structure": isinstance(data, dict)
            }
            
            details["structure_checks"] = checks
            passed_checks = sum(checks.values())
            
            score = (passed_checks / len(checks)) * 25
            passed = passed_checks == len(checks)
            message = f"Balance checks passed: {passed_checks}/{len(checks)}"
            
        except json.JSONDecodeError:
            score = 0
            passed = False
            message = "Invalid JSON response"
            details["json_error"] = True
        
        execution_time = time.time() - start_time
        
        return TestResult(test_name, passed, score, 25.0, message, details, execution_time)
    
    def test_data_consistency(self) -> TestResult:
        """Test data consistency across multiple accounts"""
        test_name = "Data Consistency"
        start_time = time.time()
        
        if len(self.known_accounts) < 3:
            return TestResult(test_name, False, 0, 15.0, "Need at least 3 accounts for consistency testing", {}, 0)
        
        details = {"accounts_tested": []}
        consistent_responses = 0
        
        for account in self.known_accounts[:3]:
            response, req_time = self._make_request(f"/users/{account}/transactions")
            
            account_detail = {"account": account, "response_time": req_time}
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    account_detail["has_valid_response"] = True
                    account_detail["transaction_count"] = self._count_transactions(data)
                    consistent_responses += 1
                except:
                    account_detail["has_valid_response"] = False
            else:
                account_detail["has_valid_response"] = False
            
            details["accounts_tested"].append(account_detail)
        
        score = (consistent_responses / 3) * 15
        passed = consistent_responses == 3
        message = f"Consistent responses: {consistent_responses}/3 accounts"
        
        execution_time = time.time() - start_time
        
        return TestResult(test_name, passed, score, 15.0, message, details, execution_time)
    
    def test_performance(self) -> TestResult:
        """Test API response time performance"""
        test_name = "Performance"
        start_time = time.time()
        
        if not self.known_accounts:
            return TestResult(test_name, False, 0, 15.0, "No test accounts available", {}, 0)
        
        test_account = self.known_accounts[0]
        response_times = []
        
        # Test multiple requests
        for i in range(5):
            _, req_time = self._make_request(f"/users/{test_account}/transactions")
            response_times.append(req_time)
            time.sleep(0.1)  # Small delay between requests
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        details = {
            "response_times": response_times,
            "average_time": avg_response_time,
            "max_time": max_response_time,
            "requests_tested": len(response_times)
        }
        
        # Scoring based on performance (under 2 seconds is good)
        if avg_response_time < 1.0:
            score = 15.0
            passed = True
            message = f"Excellent performance: {avg_response_time:.2f}s average"
        elif avg_response_time < 2.0:
            score = 12.0
            passed = True
            message = f"Good performance: {avg_response_time:.2f}s average"
        elif avg_response_time < 5.0:
            score = 8.0
            passed = True
            message = f"Acceptable performance: {avg_response_time:.2f}s average"
        else:
            score = 3.0
            passed = False
            message = f"Poor performance: {avg_response_time:.2f}s average"
        
        execution_time = time.time() - start_time
        
        return TestResult(test_name, passed, score, 15.0, message, details, execution_time)
    
    def _has_transaction_data(self, data: Any) -> bool:
        """Check if response contains transaction-like data"""
        if isinstance(data, list):
            return len(data) > 0 and isinstance(data[0], dict)
        elif isinstance(data, dict):
            if 'transactions' in data:
                transactions = data['transactions']
                return isinstance(transactions, list) and len(transactions) > 0
        return False
    
    def _has_numeric_balance(self, data: Dict[str, Any]) -> bool:
        """Check if response has a numeric balance value"""
        balance_fields = ['balance', 'amount', 'total', 'current_balance']
        for field in balance_fields:
            if field in data:
                value = data[field]
                try:
                    float(value)
                    return True
                except (ValueError, TypeError):
                    continue
        return False
    
    def _count_transactions(self, data: Any) -> int:
        """Count transactions in response"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict) and 'transactions' in data:
            return len(data['transactions'])
        return 0
    
    def run_all_tests(self) -> ValidationReport:
        """Run all validation tests"""
        print(f"Starting validation of candidate API: {self.candidate_url}")
        print(f"Using transaction API: {self.transaction_api_url}")
        print("-" * 60)
        
        # Run tests
        tests = [
            self.test_endpoint_availability,
            self.test_transactions_endpoint,
            self.test_balance_endpoint,
            self.test_data_consistency,
            self.test_performance
        ]
        
        for test_func in tests:
            result = test_func()
            self.test_results.append(result)
            
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {result.test_name}: {result.score:.1f}/{result.max_score:.1f} - {result.message}")
        
        # Calculate totals
        total_score = sum(r.score for r in self.test_results)
        max_total_score = sum(r.max_score for r in self.test_results)
        
        # Create summary
        summary = {
            "tests_run": len(self.test_results),
            "tests_passed": sum(1 for r in self.test_results if r.passed),
            "total_execution_time": sum(r.execution_time for r in self.test_results),
            "average_response_time": statistics.mean([
                detail.get("response_time", 0) for result in self.test_results 
                for detail in [result.details] if "response_time" in detail
            ]) if any("response_time" in r.details for r in self.test_results) else 0,
            "grade": self._calculate_grade(total_score, max_total_score)
        }
        
        print("-" * 60)
        print(f"Overall Score: {total_score:.1f}/{max_total_score:.1f} ({summary['grade']})")
        print(f"Tests Passed: {summary['tests_passed']}/{summary['tests_run']}")
        
        return ValidationReport(
            candidate_url=self.candidate_url,
            total_score=total_score,
            max_total_score=max_total_score,
            test_results=self.test_results,
            summary=summary,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _calculate_grade(self, score: float, max_score: float) -> str:
        """Calculate letter grade"""
        percentage = (score / max_score) * 100
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

def main():
    parser = argparse.ArgumentParser(description="Validate candidate API implementation")
    parser.add_argument("--candidate-url", required=True, help="Candidate's API base URL (e.g., http://localhost:3000)")
    parser.add_argument("--transaction-api", default="http://localhost:8000", help="Transaction API URL")
    parser.add_argument("--output", help="Output report to JSON file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Create validator
    validator = CandidateAPIValidator(args.candidate_url, args.transaction_api)
    
    # Run validation
    report = validator.run_all_tests()
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        print(f"\nReport saved to: {args.output}")
    
    # Exit with appropriate code
    if report.summary['grade'] in ['A', 'B', 'C']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 