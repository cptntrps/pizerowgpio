"""
API Load and Performance Tests
Phase 1.4 - API Testing Suite

Performance tests:
- Response time benchmarks
- Concurrent user simulation
- Database connection pool testing
- Endpoint performance under load
- Memory and resource usage
"""

import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pytest


class TestResponseTimes:
    """Test API response times"""

    def test_medicine_list_response_time(self, client_with_data, benchmark):
        """Benchmark medicine list endpoint"""

        def list_medicines():
            response = client_with_data.get('/api/v1/medicines')
            return response.status_code

        result = benchmark(list_medicines)
        assert result == 200

    def test_get_single_medicine_response_time(self, client_with_data, benchmark):
        """Benchmark getting single medicine"""

        def get_medicine():
            response = client_with_data.get('/api/v1/medicines/med_test_001')
            return response.status_code

        result = benchmark(get_medicine)
        assert result == 200

    def test_mark_medicine_taken_response_time(self, client_with_data, benchmark):
        """Benchmark marking medicine as taken"""

        def mark_taken():
            response = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                            data=json.dumps({}),
                                            content_type='application/json')
            return response.status_code

        result = benchmark(mark_taken)
        assert result == 201

    def test_tracking_history_response_time(self, client_with_data, benchmark):
        """Benchmark tracking history retrieval"""
        # Add some tracking data first
        for _ in range(5):
            client_with_data.post('/api/v1/medicines/med_test_001/take',
                                 data=json.dumps({}),
                                 content_type='application/json')

        def get_tracking():
            response = client_with_data.get('/api/v1/medicines/med_test_001/tracking')
            return response.status_code

        result = benchmark(get_tracking)
        assert result == 200


class TestConcurrentLoad:
    """Test API under concurrent load"""

    def test_concurrent_get_requests(self, client_with_data):
        """Test handling multiple concurrent GET requests"""
        num_requests = 50
        start_time = time.time()

        def get_medicines():
            response = client_with_data.get('/api/v1/medicines')
            return response.status_code == 200, time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_medicines) for _ in range(num_requests)]
            results = [f.result() for f in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # All requests should succeed
        success_count = sum(1 for success, _ in results if success)
        assert success_count == num_requests

        # Calculate average response time
        # Should handle 50 requests in reasonable time (< 10 seconds)
        assert total_time < 10.0

        print(f"\n  Concurrent GET: {num_requests} requests in {total_time:.2f}s")
        print(f"  Average: {total_time/num_requests:.3f}s per request")

    def test_concurrent_write_requests(self, client):
        """Test handling concurrent write operations"""
        num_requests = 20

        def create_medicine(index):
            medicine_data = {
                "name": f"Load Test Medicine {index}",
                "dosage": "10mg",
                "time_window": "morning",
                "window_start": "08:00",
                "window_end": "09:00",
                "days": ["mon"],
                "pills_remaining": 100,
                "pills_per_dose": 1,
                "low_stock_threshold": 10,
                "active": True
            }
            start = time.time()
            response = client.post('/api/v1/medicines',
                                 data=json.dumps(medicine_data),
                                 content_type='application/json')
            elapsed = time.time() - start
            return response.status_code == 201, elapsed, json.loads(response.data)

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_medicine, i) for i in range(num_requests)]
            results = [f.result() for f in as_completed(futures)]

        total_time = time.time() - start_time

        # Count successes
        successes = [r for r in results if r[0]]
        assert len(successes) == num_requests

        # Calculate response time statistics
        response_times = [elapsed for _, elapsed, _ in results]
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        print(f"\n  Concurrent CREATE: {num_requests} requests in {total_time:.2f}s")
        print(f"  Average: {avg_time:.3f}s, Max: {max_time:.3f}s")

        # Cleanup
        for success, _, data in successes:
            if success and 'data' in data:
                client.delete(f"/api/v1/medicines/{data['data']['id']}")

    def test_mixed_concurrent_operations(self, client_with_data):
        """Test mixed read/write operations concurrently"""
        num_operations = 100

        def random_operation(index):
            operation_type = index % 4
            start = time.time()

            if operation_type == 0:  # GET list
                response = client_with_data.get('/api/v1/medicines')
            elif operation_type == 1:  # GET single
                response = client_with_data.get('/api/v1/medicines/med_test_001')
            elif operation_type == 2:  # POST take
                response = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                                data=json.dumps({}),
                                                content_type='application/json')
            else:  # GET tracking
                response = client_with_data.get('/api/v1/tracking/today')

            elapsed = time.time() - start
            return response.status_code in [200, 201], elapsed

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(random_operation, i) for i in range(num_operations)]
            results = [f.result() for f in as_completed(futures)]

        total_time = time.time() - start_time

        # All operations should succeed
        success_count = sum(1 for success, _ in results if success)
        success_rate = (success_count / num_operations) * 100

        print(f"\n  Mixed operations: {num_operations} requests in {total_time:.2f}s")
        print(f"  Success rate: {success_rate:.1f}%")

        assert success_rate >= 95.0  # At least 95% success rate


class TestDatabaseConnectionPool:
    """Test database connection handling under load"""

    def test_many_sequential_queries(self, client_with_data):
        """Test many sequential database queries"""
        num_queries = 100
        start_time = time.time()

        for i in range(num_queries):
            response = client_with_data.get('/api/v1/medicines')
            assert response.status_code == 200

        total_time = time.time() - start_time
        avg_time = total_time / num_queries

        print(f"\n  Sequential queries: {num_queries} in {total_time:.2f}s")
        print(f"  Average: {avg_time:.3f}s per query")

        # Should handle 100 sequential queries reasonably fast
        assert total_time < 30.0

    def test_database_connection_reuse(self, client_with_data):
        """Test that database connections are reused efficiently"""
        num_requests = 50

        def make_request(index):
            start = time.time()
            response = client_with_data.get('/api/v1/medicines')
            elapsed = time.time() - start
            return response.status_code == 200, elapsed

        # Make requests in batches to test connection reuse
        batch_times = []

        for batch in range(5):
            batch_start = time.time()

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, i) for i in range(10)]
                results = [f.result() for f in as_completed(futures)]

            batch_time = time.time() - batch_start
            batch_times.append(batch_time)

            # All should succeed
            assert all(success for success, _ in results)

        # Later batches should not be significantly slower
        # (indicating connection pool is working)
        first_batch_avg = batch_times[0]
        last_batch_avg = batch_times[-1]

        print(f"\n  Connection pool test:")
        print(f"  First batch: {first_batch_avg:.3f}s")
        print(f"  Last batch: {last_batch_avg:.3f}s")

        # Last batch should not be more than 2x slower than first
        assert last_batch_avg < first_batch_avg * 2


class TestLargeDatasets:
    """Test performance with large datasets"""

    def test_list_many_medicines(self, client, create_test_medicines):
        """Test listing endpoint with many medicines"""
        # Create 50 test medicines
        medicines = create_test_medicines(count=50, prefix="perf_test")

        # Add them to database
        for medicine in medicines:
            client.post('/api/v1/medicines',
                       data=json.dumps(medicine),
                       content_type='application/json')

        # Time the list operation
        start_time = time.time()
        response = client.get('/api/v1/medicines')
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) >= 50

        print(f"\n  List {len(data['data'])} medicines: {elapsed:.3f}s")

        # Should be reasonably fast even with 50 medicines
        assert elapsed < 2.0

        # Cleanup
        for medicine in medicines:
            client.delete(f"/api/v1/medicines/{medicine['id']}")

    def test_pagination_performance(self, client, create_test_medicines):
        """Test pagination with large dataset"""
        # Create 100 test medicines
        medicines = create_test_medicines(count=100, prefix="page_test")

        for medicine in medicines:
            client.post('/api/v1/medicines',
                       data=json.dumps(medicine),
                       content_type='application/json')

        # Test different page sizes
        page_sizes = [10, 20, 50]
        results = {}

        for per_page in page_sizes:
            start_time = time.time()
            response = client.get(f'/api/v1/medicines?page=1&per_page={per_page}')
            elapsed = time.time() - start_time

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['data']) <= per_page

            results[per_page] = elapsed

        print(f"\n  Pagination performance:")
        for per_page, elapsed in results.items():
            print(f"  {per_page} items/page: {elapsed:.3f}s")

        # All should be fast
        for elapsed in results.values():
            assert elapsed < 1.0

        # Cleanup
        for medicine in medicines:
            client.delete(f"/api/v1/medicines/{medicine['id']}")

    def test_large_tracking_history(self, client):
        """Test performance with large tracking history"""
        # Create medicine
        medicine_data = {
            "name": "Large History Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            "pills_remaining": 1000,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        # Create 50 tracking records
        for i in range(50):
            client.post(f'/api/v1/medicines/{med_id}/take',
                       data=json.dumps({}),
                       content_type='application/json')

        # Time retrieval
        start_time = time.time()
        response = client.get(f'/api/v1/medicines/{med_id}/tracking')
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) >= 50

        print(f"\n  Retrieve {len(data['data'])} tracking records: {elapsed:.3f}s")

        # Should be reasonably fast
        assert elapsed < 2.0

        # Cleanup
        client.delete(f'/api/v1/medicines/{med_id}')


class TestEndpointPerformanceComparison:
    """Compare performance across different endpoints"""

    def test_endpoint_performance_comparison(self, client_with_data):
        """Measure and compare performance of all major endpoints"""
        endpoints = {
            'GET /medicines': lambda: client_with_data.get('/api/v1/medicines'),
            'GET /medicines/<id>': lambda: client_with_data.get('/api/v1/medicines/med_test_001'),
            'GET /tracking': lambda: client_with_data.get('/api/v1/tracking'),
            'GET /tracking/today': lambda: client_with_data.get('/api/v1/tracking/today'),
            'GET /medicines/pending': lambda: client_with_data.get('/api/v1/medicines/pending'),
            'GET /medicines/low-stock': lambda: client_with_data.get('/api/v1/medicines/low-stock'),
            'POST /medicines/<id>/take': lambda: client_with_data.post(
                '/api/v1/medicines/med_test_001/take',
                data=json.dumps({}),
                content_type='application/json'
            ),
        }

        results = {}
        num_iterations = 10

        print("\n  Endpoint Performance Comparison:")
        print("  " + "=" * 60)

        for name, endpoint_func in endpoints.items():
            times = []

            for _ in range(num_iterations):
                start = time.time()
                response = endpoint_func()
                elapsed = time.time() - start
                times.append(elapsed)

                # Verify success
                assert response.status_code in [200, 201]

            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)

            results[name] = {
                'avg': avg_time,
                'min': min_time,
                'max': max_time
            }

            print(f"  {name:30} Avg: {avg_time:.3f}s  Min: {min_time:.3f}s  Max: {max_time:.3f}s")

        # All endpoints should respond in under 1 second on average
        for name, metrics in results.items():
            assert metrics['avg'] < 1.0, f"{name} too slow: {metrics['avg']:.3f}s"


class TestStressTest:
    """Stress tests to find performance limits"""

    @pytest.mark.slow
    def test_sustained_load(self, client_with_data):
        """Test sustained load over time"""
        duration_seconds = 10
        requests_made = 0
        errors = 0

        start_time = time.time()
        end_time = start_time + duration_seconds

        print(f"\n  Sustained load test for {duration_seconds} seconds...")

        while time.time() < end_time:
            try:
                response = client_with_data.get('/api/v1/medicines')
                if response.status_code != 200:
                    errors += 1
                requests_made += 1
            except Exception as e:
                errors += 1
                print(f"    Error: {e}")

        total_time = time.time() - start_time
        requests_per_second = requests_made / total_time
        error_rate = (errors / requests_made * 100) if requests_made > 0 else 0

        print(f"  Total requests: {requests_made}")
        print(f"  Requests/second: {requests_per_second:.2f}")
        print(f"  Error rate: {error_rate:.2f}%")

        # Should handle sustained load with low error rate
        assert error_rate < 5.0

    @pytest.mark.slow
    def test_burst_traffic(self, client_with_data):
        """Test handling sudden burst of traffic"""
        burst_size = 100

        print(f"\n  Burst traffic test: {burst_size} concurrent requests...")

        def make_request(index):
            try:
                start = time.time()
                response = client_with_data.get('/api/v1/medicines')
                elapsed = time.time() - start
                return response.status_code == 200, elapsed
            except Exception as e:
                return False, 0

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(burst_size)]
            results = [f.result() for f in as_completed(futures)]

        total_time = time.time() - start_time

        success_count = sum(1 for success, _ in results if success)
        success_rate = (success_count / burst_size) * 100

        response_times = [elapsed for success, elapsed in results if success]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        print(f"  Total time: {total_time:.2f}s")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Avg response time: {avg_response_time:.3f}s")
        print(f"  Max response time: {max_response_time:.3f}s")

        # Should handle burst with high success rate
        assert success_rate >= 90.0
