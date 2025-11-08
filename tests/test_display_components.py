#!/usr/bin/python3
"""
Unit Tests for Display Component Library
=========================================

Tests critical functionality of the display component library.

Run with: python -m pytest tests/test_display_components.py -v
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, project_root)

from PIL import Image, ImageDraw, ImageFont


# ============================================================================
# TEST: fonts.py
# ============================================================================

class TestFonts(unittest.TestCase):
    """Test font caching system"""

    def setUp(self):
        """Clear font cache before each test"""
        from display import fonts
        fonts.clear_font_cache()

    def test_get_font_caching(self):
        """Test that fonts are cached correctly"""
        from display import fonts

        # First call should load from disk
        font1 = fonts.get_font('Roboto-Regular', 12)
        self.assertIsNotNone(font1)
        self.assertEqual(fonts.get_cache_size(), 1)

        # Second call should return cached instance
        font2 = fonts.get_font('Roboto-Regular', 12)
        self.assertIs(font1, font2)  # Same object
        self.assertEqual(fonts.get_cache_size(), 1)

        # Different size should create new entry
        font3 = fonts.get_font('Roboto-Regular', 16)
        self.assertIsNot(font1, font3)
        self.assertEqual(fonts.get_cache_size(), 2)

    def test_font_presets(self):
        """Test font preset system"""
        from display import fonts

        # Get all presets
        preset_names = fonts.list_presets()
        self.assertIn('headline', preset_names)
        self.assertIn('body', preset_names)
        self.assertIn('small', preset_names)

        # Test preset loading
        headline = fonts.get_font_preset('headline')
        self.assertIsNotNone(headline)

        # Test invalid preset
        with self.assertRaises(KeyError):
            fonts.get_font_preset('nonexistent')

    def test_clear_cache(self):
        """Test cache clearing"""
        from display import fonts

        fonts.get_font('Roboto-Regular', 12)
        self.assertEqual(fonts.get_cache_size(), 1)

        fonts.clear_font_cache()
        self.assertEqual(fonts.get_cache_size(), 0)

    def test_preload_common_fonts(self):
        """Test preloading functionality"""
        from display import fonts

        fonts.preload_common_fonts()
        # Should have loaded at least a few fonts
        self.assertGreater(fonts.get_cache_size(), 0)


# ============================================================================
# TEST: canvas.py
# ============================================================================

class TestCanvas(unittest.TestCase):
    """Test canvas creation"""

    def test_create_canvas(self):
        """Test basic canvas creation"""
        from display import canvas

        img, draw = canvas.create_canvas()
        self.assertIsInstance(img, Image.Image)
        self.assertIsInstance(draw, ImageDraw.ImageDraw)
        self.assertEqual(img.size, (250, 122))
        self.assertEqual(img.mode, "1")

    def test_create_canvas_custom_size(self):
        """Test canvas with custom dimensions"""
        from display import canvas

        img, draw = canvas.create_canvas(width=100, height=50)
        self.assertEqual(img.size, (100, 50))

    def test_canvas_class(self):
        """Test Canvas class"""
        from display.canvas import Canvas

        canvas = Canvas()
        self.assertIsNotNone(canvas.image)
        self.assertIsNotNone(canvas.draw)
        self.assertEqual(canvas.width, 250)
        self.assertEqual(canvas.height, 122)

    def test_canvas_context_manager(self):
        """Test Canvas as context manager"""
        from display.canvas import Canvas

        with Canvas() as canvas:
            canvas.draw.text((10, 10), "Test", fill=0)
            img = canvas.get_image()
            self.assertIsInstance(img, Image.Image)

    def test_canvas_clear(self):
        """Test canvas clearing"""
        from display.canvas import Canvas

        canvas = Canvas()
        canvas.draw.text((10, 10), "Test", fill=0)
        canvas.clear()
        # After clear, should have fresh canvas
        self.assertIsNotNone(canvas.image)

    def test_display_dimensions(self):
        """Test display dimension helpers"""
        from display.canvas import get_display_dimensions, get_display_center

        width, height = get_display_dimensions()
        self.assertEqual(width, 250)
        self.assertEqual(height, 122)

        cx, cy = get_display_center()
        self.assertEqual(cx, 125)
        self.assertEqual(cy, 61)


# ============================================================================
# TEST: touch_handler.py
# ============================================================================

class TestTouchHandler(unittest.TestCase):
    """Test touch handler"""

    def setUp(self):
        """Create mock touch objects"""
        self.mock_gt = Mock()
        self.mock_gt.INT = 1
        self.mock_gt.digital_read = Mock(return_value=1)

        self.mock_gt_dev = Mock()
        self.mock_gt_dev.Touch = 0

    def test_touch_handler_creation(self):
        """Test TouchHandler instantiation"""
        from display import TouchHandler

        handler = TouchHandler(self.mock_gt, self.mock_gt_dev)
        self.assertFalse(handler.is_running())

    def test_touch_handler_start_stop(self):
        """Test starting and stopping handler"""
        from display import TouchHandler

        handler = TouchHandler(self.mock_gt, self.mock_gt_dev)
        handler.start()
        self.assertTrue(handler.is_running())

        handler.stop()
        self.assertFalse(handler.is_running())

    def test_touch_handler_context_manager(self):
        """Test TouchHandler as context manager"""
        from display import TouchHandler

        with TouchHandler(self.mock_gt, self.mock_gt_dev) as handler:
            self.assertTrue(handler.is_running())

        # Should be stopped after exiting context
        self.assertFalse(handler.is_running())


# ============================================================================
# TEST: text.py
# ============================================================================

class TestText(unittest.TestCase):
    """Test text utilities"""

    def setUp(self):
        """Create test canvas and font"""
        from display import canvas, fonts

        self.img, self.draw = canvas.create_canvas()
        self.font = fonts.get_font_preset('body')

    def test_get_text_size(self):
        """Test text measurement"""
        from display.text import get_text_size

        width, height = get_text_size(self.draw, "Hello", self.font)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

        # Longer text should be wider
        width2, _ = get_text_size(self.draw, "Hello World", self.font)
        self.assertGreater(width2, width)

    def test_truncate_text(self):
        """Test text truncation"""
        from display.text import truncate_text

        result = truncate_text("Very long text here", 10)
        self.assertEqual(len(result), 10)
        self.assertTrue(result.endswith("..."))

        # Short text should not be truncated
        result = truncate_text("Short", 10)
        self.assertEqual(result, "Short")

    def test_truncate_text_to_width(self):
        """Test pixel-width based truncation"""
        from display.text import truncate_text_to_width

        original = "Very long text that needs truncation"
        truncated = truncate_text_to_width(self.draw, original, 50, self.font)

        # Truncated should be shorter
        self.assertTrue(len(truncated) < len(original))
        self.assertTrue(truncated.endswith("..."))

    def test_wrap_text(self):
        """Test text wrapping"""
        from display.text import wrap_text

        text = "This is a long line that should be wrapped into multiple lines"
        lines = wrap_text(self.draw, text, max_width=100, font=self.font)

        # Should create multiple lines
        self.assertGreater(len(lines), 1)

        # Each line should fit within max width
        from display.text import get_text_size
        for line in lines:
            width, _ = get_text_size(self.draw, line, self.font)
            self.assertLessEqual(width, 100)

    def test_draw_centered_text(self):
        """Test centered text drawing"""
        from display.text import draw_centered_text

        x, y = draw_centered_text(self.draw, "Test", y=50, font=self.font)

        # X should be roughly centered
        self.assertGreater(x, 0)
        self.assertLess(x, 250)
        self.assertEqual(y, 50)


# ============================================================================
# TEST: shapes.py
# ============================================================================

class TestShapes(unittest.TestCase):
    """Test shape drawing functions"""

    def setUp(self):
        """Create test canvas"""
        from display import canvas
        self.img, self.draw = canvas.create_canvas()

    def test_draw_line(self):
        """Test line drawing"""
        from display.shapes import draw_line

        # Should not raise exception
        draw_line(self.draw, 0, 0, 100, 100)

    def test_draw_rectangle(self):
        """Test rectangle drawing"""
        from display.shapes import draw_rectangle

        draw_rectangle(self.draw, 10, 10, 50, 30)
        draw_rectangle(self.draw, 70, 10, 50, 30, fill=0)

    def test_draw_circle(self):
        """Test circle drawing"""
        from display.shapes import draw_circle

        draw_circle(self.draw, 125, 61, 20)

    def test_draw_horizontal_line(self):
        """Test horizontal line"""
        from display.shapes import draw_horizontal_line

        draw_horizontal_line(self.draw, 60)

    def test_draw_vertical_line(self):
        """Test vertical line"""
        from display.shapes import draw_vertical_line

        draw_vertical_line(self.draw, 125)

    def test_draw_divider(self):
        """Test divider line"""
        from display.shapes import draw_divider

        draw_divider(self.draw, 60, padding=10)


# ============================================================================
# TEST: layouts.py
# ============================================================================

class TestLayouts(unittest.TestCase):
    """Test layout components"""

    def setUp(self):
        """Create test canvas"""
        from display import canvas
        self.img, self.draw = canvas.create_canvas()

    def test_header_layout(self):
        """Test HeaderLayout"""
        from display.layouts import HeaderLayout

        header = HeaderLayout("Test Title", show_time=True)
        y = header.draw(self.draw)

        self.assertGreater(y, 0)
        self.assertEqual(y, header.height)

    def test_footer_layout(self):
        """Test FooterLayout"""
        from display.layouts import FooterLayout

        footer = FooterLayout("Instructions here")
        y = footer.draw(self.draw)

        self.assertGreater(y, 0)
        self.assertLess(y, 122)

    def test_split_layout(self):
        """Test SplitLayout"""
        from display.layouts import SplitLayout

        split = SplitLayout(split_x=125)
        split.draw_divider(self.draw)

        left_bounds = split.get_left_bounds()
        right_bounds = split.get_right_bounds()

        self.assertEqual(left_bounds[2], 125)  # Left width
        self.assertEqual(right_bounds[0], 125)  # Right start

    def test_list_layout(self):
        """Test ListLayout"""
        from display.layouts import ListLayout

        items = ["Item 1", "Item 2", "Item 3"]
        list_layout = ListLayout(items, item_height=15)
        y = list_layout.draw(self.draw)

        self.assertGreater(y, 20)  # Should have drawn items

    def test_grid_layout(self):
        """Test GridLayout"""
        from display.layouts import GridLayout

        grid = GridLayout(rows=2, cols=2)

        # Test cell positions
        x0, y0 = grid.get_cell_position(0)
        x1, y1 = grid.get_cell_position(1)
        x2, y2 = grid.get_cell_position(2)

        self.assertEqual((x0, y0), (0, 0))
        self.assertGreater(x1, x0)
        self.assertGreater(y2, y0)


# ============================================================================
# TEST: components.py
# ============================================================================

class TestComponents(unittest.TestCase):
    """Test UI components"""

    def setUp(self):
        """Create test canvas"""
        from display import canvas
        self.img, self.draw = canvas.create_canvas()

    def test_progress_bar(self):
        """Test ProgressBar"""
        from display.components import ProgressBar

        progress = ProgressBar(x=10, y=50, width=200, height=10)
        progress.draw(self.draw, progress=75)

    def test_button(self):
        """Test Button"""
        from display.components import Button

        button = Button("Click Me", x=50, y=50, width=100, height=30)
        button.draw(self.draw)

        # Test touch detection
        self.assertTrue(button.is_touched(100, 60))
        self.assertFalse(button.is_touched(10, 10))

    def test_list_item(self):
        """Test ListItem"""
        from display.components import ListItem

        item = ListItem("Task 1", y=20, checked=False)
        item.draw(self.draw)

        # Test toggle
        self.assertFalse(item.checked)
        item.toggle_checked()
        self.assertTrue(item.checked)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance(unittest.TestCase):
    """Performance benchmarks"""

    def test_font_cache_performance(self):
        """Test that font caching improves performance"""
        from display import fonts
        import time

        fonts.clear_font_cache()

        # First load (uncached)
        start = time.time()
        font1 = fonts.get_font('Roboto-Regular', 12)
        first_load = time.time() - start

        # Second load (cached)
        start = time.time()
        font2 = fonts.get_font('Roboto-Regular', 12)
        second_load = time.time() - start

        # Cached load should be much faster
        self.assertLess(second_load, first_load / 10)  # At least 10x faster

    def test_canvas_creation_speed(self):
        """Test canvas creation performance"""
        from display import canvas
        import time

        start = time.time()
        for _ in range(100):
            img, draw = canvas.create_canvas()
        elapsed = time.time() - start

        # Should create 100 canvases in less than 1 second
        self.assertLess(elapsed, 1.0)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""

    def test_complete_screen(self):
        """Test building a complete screen with multiple components"""
        from display import canvas, fonts
        from display.layouts import HeaderLayout, FooterLayout
        from display.icons import draw_pill_icon

        # Create canvas
        img, draw = canvas.create_canvas()

        # Add header
        header = HeaderLayout("Medicine Tracker", show_time=True)
        header_bottom = header.draw(draw)

        # Add icon
        draw_pill_icon(draw, 10, header_bottom + 10, size=15)

        # Add text
        font = fonts.get_font_preset('body')
        draw.text((30, header_bottom + 10), "Aspirin", font=font, fill=0)

        # Add footer
        footer = FooterLayout("Tap to continue")
        footer.draw(draw)

        # Should have valid image
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (250, 122))


# ============================================================================
# RUN TESTS
# ============================================================================

def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
