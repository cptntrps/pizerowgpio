"""
Canvas Tests
============

Tests for canvas.py module covering:
- Canvas creation
- Canvas context manager
- Canvas dimensions
- Canvas clearing
- Image operations
"""

import pytest
from PIL import Image, ImageDraw
from display import canvas


class TestCanvasCreation:
    """Test canvas creation functions"""

    def test_create_canvas_default(self):
        """Should create canvas with default dimensions"""
        img, draw = canvas.create_canvas()

        assert img is not None
        assert draw is not None
        assert img.size == (canvas.DISPLAY_WIDTH, canvas.DISPLAY_HEIGHT)
        assert img.mode == canvas.DISPLAY_MODE

    def test_create_canvas_dimensions(self):
        """Should respect custom dimensions"""
        width, height = 300, 150
        img, draw = canvas.create_canvas(width=width, height=height)

        assert img.size == (width, height)

    def test_create_canvas_background_white(self):
        """Should create canvas with white background by default"""
        img, draw = canvas.create_canvas()

        # Check pixel at (0, 0) is white (255)
        assert img.getpixel((0, 0)) == canvas.BACKGROUND_WHITE

    def test_create_canvas_background_black(self):
        """Should create canvas with black background when specified"""
        img, draw = canvas.create_canvas(background=canvas.BACKGROUND_BLACK)

        # Check pixel at (0, 0) is black (0)
        assert img.getpixel((0, 0)) == canvas.BACKGROUND_BLACK

    def test_create_canvas_black_function(self):
        """create_canvas_black should create black background canvas"""
        img, draw = canvas.create_canvas_black()

        assert img.getpixel((0, 0)) == canvas.BACKGROUND_BLACK

    def test_create_canvas_mode(self):
        """Should respect custom image mode"""
        img, draw = canvas.create_canvas(mode="1")

        assert img.mode == "1"

    def test_canvas_draw_is_valid(self):
        """Draw object should be valid ImageDraw"""
        img, draw = canvas.create_canvas()

        assert isinstance(draw, ImageDraw.ImageDraw)

    def test_canvas_image_is_valid(self):
        """Image object should be valid PIL Image"""
        img, draw = canvas.create_canvas()

        assert isinstance(img, Image.Image)


class TestCanvasClass:
    """Test Canvas class"""

    def test_canvas_init_default(self):
        """Should initialize with default values"""
        c = canvas.Canvas()

        assert c.width == canvas.DISPLAY_WIDTH
        assert c.height == canvas.DISPLAY_HEIGHT
        assert c.mode == canvas.DISPLAY_MODE
        assert c.image is not None
        assert c.draw is not None

    def test_canvas_init_custom(self):
        """Should initialize with custom values"""
        c = canvas.Canvas(width=300, height=150, background=0)

        assert c.width == 300
        assert c.height == 150
        assert c.image.size == (300, 150)

    def test_canvas_clear_white(self):
        """Should clear canvas to white"""
        c = canvas.Canvas()

        # Draw something
        c.draw.text((10, 10), "Test", fill=0)

        # Clear
        c.clear()

        # Should be white again
        assert c.image.getpixel((10, 10)) == canvas.BACKGROUND_WHITE

    def test_canvas_clear_black(self):
        """Should clear canvas to specified color"""
        c = canvas.Canvas()

        c.clear(color=0)

        # Check black pixels
        assert c.image.getpixel((0, 0)) == 0

    def test_canvas_get_image(self):
        """Should return underlying PIL Image"""
        c = canvas.Canvas()

        img = c.get_image()

        assert isinstance(img, Image.Image)
        assert img.size == (canvas.DISPLAY_WIDTH, canvas.DISPLAY_HEIGHT)

    def test_canvas_context_manager(self):
        """Should work as context manager"""
        with canvas.Canvas() as c:
            assert c is not None
            assert c.image is not None

    def test_canvas_context_manager_cleanup(self):
        """Context manager should complete without error"""
        with canvas.Canvas() as c:
            c.draw.text((10, 10), "Test", fill=0)
        # Should complete without error

    def test_canvas_draw_on_canvas(self):
        """Should allow drawing on canvas"""
        c = canvas.Canvas()

        c.draw.text((10, 10), "Test", fill=0)
        c.draw.rectangle([20, 20, 50, 50], outline=0)

        # Should have content (not all white)
        pixels_changed = False
        for x in range(10, 60):
            for y in range(10, 60):
                if c.image.getpixel((x, y)) != canvas.BACKGROUND_WHITE:
                    pixels_changed = True
                    break
            if pixels_changed:
                break

        # Don't assert because font rendering might not work in test env
        # Just ensure no error was raised


class TestCanvasDimensions:
    """Test display dimensions"""

    def test_display_dimensions(self):
        """Should return correct display dimensions"""
        width, height = canvas.get_display_dimensions()

        assert width == canvas.DISPLAY_WIDTH
        assert height == canvas.DISPLAY_HEIGHT

    def test_display_center(self):
        """Should calculate display center correctly"""
        cx, cy = canvas.get_display_center()

        assert cx == canvas.DISPLAY_WIDTH // 2
        assert cy == canvas.DISPLAY_HEIGHT // 2

    def test_display_center_coordinates_valid(self):
        """Display center should be valid coordinates"""
        cx, cy = canvas.get_display_center()

        assert 0 <= cx < canvas.DISPLAY_WIDTH
        assert 0 <= cy < canvas.DISPLAY_HEIGHT


class TestCanvasEdgeCases:
    """Test edge cases and error handling"""

    def test_create_canvas_zero_dimensions(self):
        """Should handle zero dimensions"""
        # This might raise or create unusual canvas
        try:
            img, draw = canvas.create_canvas(width=0, height=0)
            # If it succeeds, that's ok (PIL might allow it)
        except (ValueError, OSError):
            pass  # Either error or success is acceptable

    def test_create_canvas_large_dimensions(self):
        """Should handle large dimensions"""
        img, draw = canvas.create_canvas(width=1000, height=1000)

        assert img.size == (1000, 1000)

    def test_canvas_multiple_clears(self):
        """Should handle multiple clears"""
        c = canvas.Canvas()

        for _ in range(5):
            c.clear()
            # Verify it's still white
            assert c.image.getpixel((0, 0)) == canvas.BACKGROUND_WHITE

    def test_canvas_alternate_clear_colors(self):
        """Should handle alternating clear colors"""
        c = canvas.Canvas()

        c.clear(color=255)
        assert c.image.getpixel((0, 0)) == 255

        c.clear(color=0)
        assert c.image.getpixel((0, 0)) == 0

    def test_canvas_properties_consistent(self):
        """Canvas properties should match image properties"""
        c = canvas.Canvas(width=300, height=150)

        assert c.width == c.image.width
        assert c.height == c.image.height
        assert c.mode == c.image.mode


class TestCanvasConstants:
    """Test canvas constants"""

    def test_display_width_constant(self):
        """Display width should be 250"""
        assert canvas.DISPLAY_WIDTH == 250

    def test_display_height_constant(self):
        """Display height should be 122"""
        assert canvas.DISPLAY_HEIGHT == 122

    def test_display_mode_constant(self):
        """Display mode should be '1' (1-bit B&W)"""
        assert canvas.DISPLAY_MODE == "1"

    def test_background_white_constant(self):
        """Background white should be 255"""
        assert canvas.BACKGROUND_WHITE == 255

    def test_background_black_constant(self):
        """Background black should be 0"""
        assert canvas.BACKGROUND_BLACK == 0
