"""
Load Testing & Concurrent User Simulation
==========================================

Load testing suite to simulate multiple concurrent API requests and measure
system performance under stress. Tests scalability with 50+ concurrent users.

Target: Handle 50+ concurrent API requests
"""

import concurrent.futures
import time
import logging
import json
import os
import sys
import statistics
from datetime import datetime
from typing import Dict, List, Tuple
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api import create_app
from db.medicine_db import MedicineDatabase


class LoadTest:
    """Load testing and concurrent user simulation"""

    def __init__(self, num_concurrent_users: int = 50, requests_per_user: int = 10):
        """Initialize load test

        Args:
            num_concurrent_users: Number of concurrent users to simulate
            requests_per_user: Number of requests each user makes
        """
        self.num_concurrent_users = num_concurrent_users
        self.requests_per_user = requests_per_user
        self.app = None
        self.results = {
            'requests': [],
            'errors': [],
            'durations': []
        }
        self.lock = threading.Lock()

    def setup(self):
        """Setup test Flask app and database"""
        logger.info("Setting up load test environment...")

        # Create Flask test app
        self.app = create_app('testing')
        self.app.config['DB_PATH'] = ':memory:'

        # Create test database with sample data
        self._setup_test_data()

        logger.info("Load test environment ready")

    def _setup_test_data(self):
        """Setup test data in database"""
        db = MedicineDatabase(':memory:')

        # Create sample medicines
        medicines = [
            {
                'id': f'med_{i:04d}',
                'name': f'Medicine {i}',
                'dosage': f'{50 + i % 50}mg',
                'time_window': 'morning' if i % 2 == 0 else 'evening',
                'window_start': '08:00' if i % 2 == 0 else '20:00',
                'window_end': '10:00' if i % 2 == 0 else '22:00',
                'days': ['mon', 'wed', 'fri'] if i % 2 == 0 else ['tue', 'thu', 'sat'],
                'pills_per_dose': 1,
                'pills_remaining': 90,
                'low_stock_threshold': 15,
                'active': True
            }
            for i in range(30)
        ]

        for med in medicines:
            db.add_medicine(med)

        logger.info(f"Created {len(medicines)} test medicines for load test")

    def simulate_user(self, user_id: int) -> Dict:
        """Simulate a single user making API requests

        Args:
            user_id: Unique user ID

        Returns:
            Dictionary with user request results
        """
        client = self.app.test_client()
        user_results = {
            'user_id': user_id,
            'requests': 0,
            'successful': 0,
            'failed': 0,
            'timings': [],
            'errors': []
        }

        # Simulate different request patterns
        request_patterns = [
            ('GET', '/api/v1/medicines'),
            ('GET', '/api/v1/medicines/med_0000'),
            ('GET', '/api/v1/medicines/pending'),
            ('GET', '/api/v1/medicines/low-stock'),
            ('GET', '/api/v1/health'),
            ('POST', '/api/v1/medicines/batch-take', {
                'medicine_ids': ['med_0000', 'med_0001'],
                'timestamp': datetime.now().isoformat()
            }),
            ('POST', '/api/v1/medicines/med_0001/take', {
                'timestamp': datetime.now().isoformat()
            }),
        ]

        for request_num in range(self.requests_per_user):
            # Choose a request pattern
            pattern_idx = request_num % len(request_patterns)
            pattern = request_patterns[pattern_idx]

            method = pattern[0]
            endpoint = pattern[1]
            data = pattern[2] if len(pattern) > 2 else None

            try:
                start = time.perf_counter()

                if method == 'GET':
                    response = client.get(endpoint)
                elif method == 'POST':
                    response = client.post(
                        endpoint,
                        json=data,
                        content_type='application/json'
                    )
                else:
                    raise ValueError(f"Unknown method: {method}")

                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

                user_results['requests'] += 1
                user_results['timings'].append(elapsed)

                if response.status_code < 400:
                    user_results['successful'] += 1
                else:
                    user_results['failed'] += 1
                    user_results['errors'].append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'response': response.get_json()
                    })

            except Exception as e:
                logger.error(f"User {user_id} request failed: {e}")
                user_results['failed'] += 1
                user_results['requests'] += 1
                user_results['errors'].append({
                    'endpoint': endpoint,
                    'error': str(e)
                })

        return user_results

    def run_concurrent_load_test(self) -> Dict:
        """Run concurrent load test with multiple users

        Returns:
            Dictionary with load test results
        """
        logger.info("=" * 80)
        logger.info("LOAD TEST: CONCURRENT USERS SIMULATION")
        logger.info(f"Users: {self.num_concurrent_users}, Requests per User: {self.requests_per_user}")
        logger.info("=" * 80)

        self.setup()

        start_time = time.perf_counter()

        # Run concurrent users
        user_results_list = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_concurrent_users
        ) as executor:
            futures = [
                executor.submit(self.simulate_user, user_id)
                for user_id in range(self.num_concurrent_users)
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    user_results_list.append(result)
                except Exception as e:
                    logger.error(f"User simulation failed: {e}")

        total_duration = (time.perf_counter() - start_time)

        # Aggregate results
        results = {
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'concurrent_users': self.num_concurrent_users,
                'requests_per_user': self.requests_per_user,
                'total_requests': self.num_concurrent_users * self.requests_per_user
            },
            'execution': {
                'total_duration_seconds': total_duration,
                'requests_per_second': (self.num_concurrent_users * self.requests_per_user) / total_duration
            },
            'per_user_results': user_results_list
        }

        # Calculate aggregate statistics
        all_timings = []
        total_successful = 0
        total_failed = 0
        total_errors = []

        for user_result in user_results_list:
            all_timings.extend(user_result['timings'])
            total_successful += user_result['successful']
            total_failed += user_result['failed']
            total_errors.extend(user_result['errors'])

        if all_timings:
            results['aggregate_stats'] = {
                'total_requests': len(all_timings),
                'successful_requests': total_successful,
                'failed_requests': total_failed,
                'success_rate': (total_successful / len(all_timings) * 100) if all_timings else 0,
                'min_response_ms': min(all_timings),
                'max_response_ms': max(all_timings),
                'mean_response_ms': statistics.mean(all_timings),
                'median_response_ms': statistics.median(all_timings),
                'stdev_response_ms': statistics.stdev(all_timings) if len(all_timings) > 1 else 0,
                'p50_response_ms': sorted(all_timings)[int(len(all_timings) * 0.50)],
                'p95_response_ms': sorted(all_timings)[int(len(all_timings) * 0.95)],
                'p99_response_ms': sorted(all_timings)[int(len(all_timings) * 0.99)],
            }

            # Check if system can handle 50+ concurrent users
            results['load_test_target'] = {
                'target': '50+ concurrent users',
                'met': self.num_concurrent_users >= 50 and total_failed == 0,
                'concurrent_users_handled': self.num_concurrent_users,
                'errors_count': total_failed,
                'mean_response_under_100ms': results['aggregate_stats']['mean_response_ms'] < 100
            }

            if total_errors:
                results['errors_sample'] = total_errors[:10]  # First 10 errors

        return results

    def run_ramp_up_test(self) -> Dict:
        """Run ramp-up test - gradually increase load

        Simulates gradual increase in concurrent users to find breaking point.

        Returns:
            Dictionary with ramp-up test results
        """
        logger.info("=" * 80)
        logger.info("LOAD TEST: RAMP-UP (GRADUAL LOAD INCREASE)")
        logger.info("=" * 80)

        self.setup()

        results = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'ramp_up',
            'stages': []
        }

        # Ramp up: 10, 25, 50, 100 users
        user_counts = [10, 25, 50, 100]

        for user_count in user_counts:
            logger.info(f"Testing with {user_count} concurrent users...")

            start_time = time.perf_counter()

            user_results_list = []
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=user_count
            ) as executor:
                futures = [
                    executor.submit(self.simulate_user, user_id)
                    for user_id in range(user_count)
                ]

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        user_results_list.append(result)
                    except Exception as e:
                        logger.error(f"User simulation failed: {e}")

            stage_duration = (time.perf_counter() - start_time)

            # Aggregate for this stage
            all_timings = []
            total_successful = 0
            total_failed = 0

            for user_result in user_results_list:
                all_timings.extend(user_result['timings'])
                total_successful += user_result['successful']
                total_failed += user_result['failed']

            stage_result = {
                'concurrent_users': user_count,
                'total_requests': user_count * self.requests_per_user,
                'duration_seconds': stage_duration,
                'requests_per_second': (user_count * self.requests_per_user) / stage_duration,
                'success_rate': (total_successful / len(all_timings) * 100) if all_timings else 0,
                'mean_response_ms': statistics.mean(all_timings) if all_timings else 0,
                'p95_response_ms': sorted(all_timings)[int(len(all_timings) * 0.95)] if all_timings else 0,
                'failed_requests': total_failed
            }

            results['stages'].append(stage_result)

            logger.info(f"  Requests/sec: {stage_result['requests_per_second']:.2f}, "
                       f"Mean Response: {stage_result['mean_response_ms']:.2f}ms, "
                       f"Success Rate: {stage_result['success_rate']:.1f}%")

        return results

    def run_stress_test(self) -> Dict:
        """Run stress test - push system to limits

        Returns:
            Dictionary with stress test results
        """
        logger.info("=" * 80)
        logger.info("LOAD TEST: STRESS TEST (PUSH TO LIMITS)")
        logger.info("=" * 80)

        self.setup()

        results = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'stress',
            'stages': []
        }

        # Stress test: 200, 500 users (push to limits)
        user_counts = [200, 500]

        for user_count in user_counts:
            logger.info(f"Stress testing with {user_count} concurrent users...")

            start_time = time.perf_counter()

            user_results_list = []
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(user_count, 100)  # Limit thread pool size
            ) as executor:
                futures = []
                for user_id in range(user_count):
                    futures.append(executor.submit(self.simulate_user, user_id))

                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        user_results_list.append(result)
                        completed += 1
                        if completed % 50 == 0:
                            logger.info(f"  Completed {completed}/{user_count} users")
                    except Exception as e:
                        logger.error(f"User simulation failed: {e}")

            stage_duration = (time.perf_counter() - start_time)

            # Aggregate for this stage
            all_timings = []
            total_successful = 0
            total_failed = 0

            for user_result in user_results_list:
                all_timings.extend(user_result['timings'])
                total_successful += user_result['successful']
                total_failed += user_result['failed']

            stage_result = {
                'concurrent_users': user_count,
                'total_requests': user_count * self.requests_per_user,
                'duration_seconds': stage_duration,
                'requests_per_second': (user_count * self.requests_per_user) / stage_duration,
                'success_rate': (total_successful / len(all_timings) * 100) if all_timings else 0,
                'mean_response_ms': statistics.mean(all_timings) if all_timings else 0,
                'p95_response_ms': sorted(all_timings)[int(len(all_timings) * 0.95)] if all_timings else 0,
                'failed_requests': total_failed
            }

            results['stages'].append(stage_result)

            logger.info(f"  Requests/sec: {stage_result['requests_per_second']:.2f}, "
                       f"Mean Response: {stage_result['mean_response_ms']:.2f}ms, "
                       f"Success Rate: {stage_result['success_rate']:.1f}%")

        return results

    def print_concurrent_summary(self, results: Dict):
        """Print concurrent load test summary"""
        print("\n" + "=" * 80)
        print("CONCURRENT LOAD TEST SUMMARY")
        print("=" * 80)

        config = results.get('configuration', {})
        execution = results.get('execution', {})
        stats = results.get('aggregate_stats', {})
        target = results.get('load_test_target', {})

        print(f"Concurrent Users: {config.get('concurrent_users', 0)}")
        print(f"Requests per User: {config.get('requests_per_user', 0)}")
        print(f"Total Requests: {config.get('total_requests', 0)}")
        print(f"Total Duration: {execution.get('total_duration_seconds', 0):.2f}s")
        print(f"Requests/sec: {execution.get('requests_per_second', 0):.2f}")
        print(f"\nResponse Times:")
        print(f"  Min: {stats.get('min_response_ms', 0):.2f}ms")
        print(f"  Mean: {stats.get('mean_response_ms', 0):.2f}ms")
        print(f"  Median: {stats.get('median_response_ms', 0):.2f}ms")
        print(f"  P95: {stats.get('p95_response_ms', 0):.2f}ms")
        print(f"  P99: {stats.get('p99_response_ms', 0):.2f}ms")
        print(f"  Max: {stats.get('max_response_ms', 0):.2f}ms")
        print(f"\nReliability:")
        print(f"  Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"  Successful Requests: {stats.get('successful_requests', 0)}")
        print(f"  Failed Requests: {stats.get('failed_requests', 0)}")
        print(f"\nTarget Status:")
        print(f"  Target: {target.get('target', 'N/A')}")
        print(f"  Met: {'YES' if target.get('met', False) else 'NO'}")
        print("=" * 80 + "\n")

    def print_ramp_up_summary(self, results: Dict):
        """Print ramp-up test summary"""
        print("\n" + "=" * 80)
        print("RAMP-UP TEST SUMMARY")
        print("=" * 80)

        print(f"{'Users':<10} {'Requests/s':<15} {'Mean(ms)':<15} {'P95(ms)':<15} {'Success%':<15}")
        print("-" * 80)

        for stage in results.get('stages', []):
            print(f"{stage.get('concurrent_users', 0):<10} "
                  f"{stage.get('requests_per_second', 0):<15.2f} "
                  f"{stage.get('mean_response_ms', 0):<15.2f} "
                  f"{stage.get('p95_response_ms', 0):<15.2f} "
                  f"{stage.get('success_rate', 0):<15.1f}")

        print("-" * 80 + "\n")

    def print_stress_summary(self, results: Dict):
        """Print stress test summary"""
        print("\n" + "=" * 80)
        print("STRESS TEST SUMMARY")
        print("=" * 80)

        print(f"{'Users':<10} {'Requests/s':<15} {'Mean(ms)':<15} {'P95(ms)':<15} {'Success%':<15}")
        print("-" * 80)

        for stage in results.get('stages', []):
            print(f"{stage.get('concurrent_users', 0):<10} "
                  f"{stage.get('requests_per_second', 0):<15.2f} "
                  f"{stage.get('mean_response_ms', 0):<15.2f} "
                  f"{stage.get('p95_response_ms', 0):<15.2f} "
                  f"{stage.get('success_rate', 0):<15.1f}")

        print("-" * 80 + "\n")


def run_load_tests():
    """Run all load tests"""
    # Concurrent load test (50 users)
    load_test = LoadTest(num_concurrent_users=50, requests_per_user=10)
    concurrent_results = load_test.run_concurrent_load_test()
    load_test.print_concurrent_summary(concurrent_results)

    # Ramp-up test
    ramp_up = LoadTest(requests_per_user=5)
    ramp_up_results = ramp_up.run_ramp_up_test()
    ramp_up.print_ramp_up_summary(ramp_up_results)

    # Stress test
    stress = LoadTest(requests_per_user=3)
    stress_results = stress.run_stress_test()
    stress.print_stress_summary(stress_results)

    # Save results
    all_results = {
        'concurrent': concurrent_results,
        'ramp_up': ramp_up_results,
        'stress': stress_results
    }

    output_file = '/home/user/pizerowgpio/.benchmarks/load_test.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Results saved to {output_file}")

    return all_results


if __name__ == '__main__':
    run_load_tests()
