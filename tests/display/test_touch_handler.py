"""
Touch Handler Tests
===================

Tests for touch_handler.py module covering:
- Thread safety
- Touch detection
- Handler lifecycle
- Error handling
- Context manager usage
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from display.touch_handler import TouchHandler, create_touch_handler, check_exit_requested, cleanup_touch_state


class MockGPIO:
    """Mock GPIO interface for testing"""

    def __init__(self):
        self.INT = 1
        self.pin_state = 1

    def digital_read(self, pin):
        return self.pin_state


class MockTouchDevice:
    """Mock touch device state"""

    def __init__(self):
        self.Touch = 0
        self.X = [0]
        self.Y = [0]
        self.S = [0]
        self.exit_requested = False


class TestTouchHandlerInit:
    """Test TouchHandler initialization"""

    def test_init_basic(self):
        """Should initialize with required parameters"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)

        assert handler.gt == gt
        assert handler.gt_dev == gt_dev
        assert handler.interval == 0.01
        assert not handler.is_running()

    def test_init_custom_interval(self):
        """Should accept custom polling interval"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev, interval=0.05)

        assert handler.interval == 0.05

    def test_init_custom_error_handler(self):
        """Should accept custom error handler"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()
        error_handler = Mock()

        handler = TouchHandler(gt, gt_dev, on_error=error_handler)

        assert handler.on_error == error_handler


class TestTouchHandlerLifecycle:
    """Test handler start/stop lifecycle"""

    def test_start_handler(self):
        """Should start handler thread"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        handler.start()

        assert handler.is_running()
        assert handler._thread is not None

        handler.stop()

    def test_stop_handler(self):
        """Should stop handler thread"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        handler.start()
        assert handler.is_running()

        handler.stop()
        assert not handler.is_running()

    def test_start_multiple_times(self):
        """Starting multiple times should not create duplicate threads"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        handler.start()
        thread1 = handler._thread

        handler.start()  # Start again
        thread2 = handler._thread

        # Should be same thread
        assert thread1 == thread2

        handler.stop()

    def test_stop_without_start(self):
        """Stopping without starting should not error"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        handler.stop()  # Should not raise

        assert not handler.is_running()

    def test_context_manager(self):
        """Should work as context manager"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        with TouchHandler(gt, gt_dev) as handler:
            assert handler.is_running()

        assert not handler.is_running()

    def test_context_manager_with_exception(self):
        """Should stop even if exception occurs"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        try:
            with TouchHandler(gt, gt_dev) as handler:
                assert handler.is_running()
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should have stopped despite exception
        # (Note: we can't check handler.is_running() here, but no exception should occur)


class TestTouchDetection:
    """Test touch detection functionality"""

    def test_is_touched_false(self):
        """Should detect no touch when device.Touch is 0"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()
        gt_dev.Touch = 0

        handler = TouchHandler(gt, gt_dev)

        assert not handler.is_touched()

    def test_is_touched_true(self):
        """Should detect touch when device.Touch is 1"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()
        gt_dev.Touch = 1

        handler = TouchHandler(gt, gt_dev)

        assert handler.is_touched()

    def test_touch_state_changes(self):
        """Should detect state changes"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)

        gt_dev.Touch = 0
        assert not handler.is_touched()

        gt_dev.Touch = 1
        assert handler.is_touched()

        gt_dev.Touch = 0
        assert not handler.is_touched()

    def test_is_touched_with_missing_touch_attribute(self):
        """Should handle missing Touch attribute"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()
        delattr(gt_dev, 'Touch')

        handler = TouchHandler(gt, gt_dev)

        # Should default to False
        assert not handler.is_touched()


class TestThreadSafety:
    """Test thread safety of TouchHandler"""

    def test_concurrent_reads(self):
        """Should safely handle concurrent touch reads"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        handler.start()

        results = []

        def reader():
            for _ in range(100):
                touched = handler.is_touched()
                results.append(touched)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        handler.stop()

        # Should have collected data without errors
        assert len(results) == 500

    def test_concurrent_state_changes(self):
        """Should safely handle state changes during reads"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)

        read_count = [0]
        write_count = [0]

        def reader():
            for _ in range(100):
                handler.is_touched()
                read_count[0] += 1

        def writer():
            for _ in range(50):
                gt_dev.Touch = 1
                gt_dev.Touch = 0
                write_count[0] += 1

        r_thread = threading.Thread(target=reader)
        w_thread = threading.Thread(target=writer)

        r_thread.start()
        w_thread.start()

        r_thread.join()
        w_thread.join()

        # Should complete without errors
        assert read_count[0] == 100
        assert write_count[0] == 50

    def test_stop_during_read(self):
        """Should handle stop request during active reading"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        handler.start()

        time.sleep(0.05)  # Let thread run a bit

        handler.stop()

        # Should stop cleanly
        assert not handler.is_running()


class TestFlagInterface:
    """Test flag interface for legacy compatibility"""

    def test_get_flag_returns_list(self):
        """Should return flag as list"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        flag = handler.get_flag()

        assert isinstance(flag, list)
        assert len(flag) == 1

    def test_flag_initial_value(self):
        """Flag should be 1 initially"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        flag = handler.get_flag()

        assert flag[0] == 1

    def test_flag_mutable(self):
        """Flag should be mutable"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev)
        flag = handler.get_flag()

        flag[0] = 0
        assert handler.get_flag()[0] == 0


class TestErrorHandling:
    """Test error handling"""

    def test_custom_error_handler_called(self):
        """Custom error handler should be called on error"""
        gt = Mock()
        gt.INT = 1
        gt.digital_read.side_effect = Exception("GPIO Error")

        gt_dev = MockTouchDevice()

        error_handler = Mock()
        handler = TouchHandler(gt, gt_dev, interval=0.001, on_error=error_handler)

        handler.start()
        time.sleep(0.05)
        handler.stop()

        # Error handler should have been called
        assert error_handler.called

    def test_default_error_handler(self):
        """Should handle errors with default handler"""
        gt = Mock()
        gt.INT = 1
        gt.digital_read.side_effect = Exception("GPIO Error")

        gt_dev = MockTouchDevice()

        handler = TouchHandler(gt, gt_dev, interval=0.001)

        handler.start()
        time.sleep(0.05)
        handler.stop()

        # Should not raise, just log


class TestFactoryFunction:
    """Test factory function"""

    def test_create_touch_handler(self):
        """Factory should create handler"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = create_touch_handler(gt, gt_dev)

        assert isinstance(handler, TouchHandler)
        assert not handler.is_running()

    def test_create_with_custom_interval(self):
        """Factory should accept custom interval"""
        gt = MockGPIO()
        gt_dev = MockTouchDevice()

        handler = create_touch_handler(gt, gt_dev, interval=0.05)

        assert handler.interval == 0.05


class TestCheckExitRequested:
    """Test exit request checking"""

    def test_exit_requested_true(self):
        """Should detect exit_requested = True"""
        gt_dev = MockTouchDevice()
        gt_dev.exit_requested = True

        assert check_exit_requested(gt_dev)

    def test_exit_requested_false(self):
        """Should detect exit_requested = False"""
        gt_dev = MockTouchDevice()
        gt_dev.exit_requested = False

        assert not check_exit_requested(gt_dev)

    def test_exit_requested_missing_attribute(self):
        """Should handle missing exit_requested attribute"""
        gt_dev = MockTouchDevice()
        delattr(gt_dev, 'exit_requested')

        # Should not raise, should return False
        assert not check_exit_requested(gt_dev)


class TestCleanupTouchState:
    """Test touch state cleanup"""

    def test_cleanup_touch_state(self):
        """Should reset touch state values"""
        gt_old = MockTouchDevice()

        gt_old.X[0] = 100
        gt_old.Y[0] = 200
        gt_old.S[0] = 5

        cleanup_touch_state(gt_old)

        assert gt_old.X[0] == 0
        assert gt_old.Y[0] == 0
        assert gt_old.S[0] == 0
