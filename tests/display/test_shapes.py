"""
Shapes Tests
============

Tests for shapes.py module covering:
- Basic shape drawing
- Shape parameters and options
- Edge cases
- Coordinate validation
"""

import pytest
from PIL import Image, ImageDraw
from display import shapes, canvas


class ShapeTestBase:
    """Base class for shape tests"""

    def setup_method(self):
        """Create canvas for each test"""
        self.img, self.draw = canvas.create_canvas()


class TestBasicShapes(ShapeTestBase):
    """Test basic shape drawing"""

    def test_draw_line(self):
        """Should draw a line"""
        # Just verify no error
        shapes.draw_line(self.draw, 0, 0, 100, 100)

    def test_draw_line_with_width(self):
        """Should draw line with custom width"""
        shapes.draw_line(self.draw, 0, 0, 100, 100, width=3)

    def test_draw_rectangle(self):
        """Should draw rectangle"""
        shapes.draw_rectangle(self.draw, 10, 10, 50, 50)

    def test_draw_rectangle_with_fill(self):
        """Should draw filled rectangle"""
        shapes.draw_rectangle(self.draw, 10, 10, 50, 50, fill=0)

    def test_draw_circle(self):
        """Should draw circle"""
        shapes.draw_circle(self.draw, 125, 61, 20)

    def test_draw_circle_with_fill(self):
        """Should draw filled circle"""
        shapes.draw_circle(self.draw, 125, 61, 20, fill=0)

    def test_draw_ellipse(self):
        """Should draw ellipse"""
        shapes.draw_ellipse(self.draw, 125, 61, 50, 30)

    def test_draw_polygon(self):
        """Should draw polygon"""
        points = [(10, 10), (50, 10), (50, 50), (10, 50)]
        shapes.draw_polygon(self.draw, points)

    def test_draw_arc(self):
        """Should draw arc"""
        shapes.draw_arc(self.draw, 125, 61, 20, 0, 180)


class TestHorizontalVerticalLines(ShapeTestBase):
    """Test horizontal and vertical line shortcuts"""

    def test_draw_horizontal_line_full_width(self):
        """Should draw horizontal line across full width"""
        shapes.draw_horizontal_line(self.draw, 50)

    def test_draw_horizontal_line_custom_range(self):
        """Should draw horizontal line with custom x range"""
        shapes.draw_horizontal_line(self.draw, 50, x1=10, x2=100)

    def test_draw_vertical_line_full_height(self):
        """Should draw vertical line across full height"""
        shapes.draw_vertical_line(self.draw, 125)

    def test_draw_vertical_line_custom_range(self):
        """Should draw vertical line with custom y range"""
        shapes.draw_vertical_line(self.draw, 125, y1=10, y2=100)


class TestConvenientShapes(ShapeTestBase):
    """Test convenient shape functions"""

    def test_draw_rounded_rectangle(self):
        """Should draw rounded rectangle"""
        shapes.draw_rounded_rectangle(self.draw, 10, 10, 100, 50, radius=10)

    def test_draw_frame(self):
        """Should draw frame around display"""
        shapes.draw_frame(self.draw)

    def test_draw_frame_with_padding(self):
        """Should draw frame with custom padding"""
        shapes.draw_frame(self.draw, padding=5)

    def test_draw_divider(self):
        """Should draw horizontal divider"""
        shapes.draw_divider(self.draw, 60)

    def test_draw_divider_with_padding(self):
        """Should draw divider with padding"""
        shapes.draw_divider(self.draw, 60, padding=5)

    def test_draw_cross(self):
        """Should draw cross symbol"""
        shapes.draw_cross(self.draw, 125, 61, 10)


class TestShapeParameters(ShapeTestBase):
    """Test shape parameter handling"""

    def test_draw_with_default_color(self):
        """Should use default black color"""
        shapes.draw_line(self.draw, 0, 0, 50, 50)
        # Just verify no error

    def test_draw_with_custom_color(self):
        """Should accept custom color"""
        shapes.draw_line(self.draw, 0, 0, 50, 50, color=255)

    def test_draw_with_custom_width(self):
        """Should accept custom line width"""
        shapes.draw_line(self.draw, 0, 0, 50, 50, width=5)

    def test_rectangle_outline_and_fill(self):
        """Should accept both outline and fill"""
        shapes.draw_rectangle(self.draw, 10, 10, 50, 50, outline=0, fill=255)

    def test_circle_with_border_width(self):
        """Should accept custom border width"""
        shapes.draw_circle(self.draw, 125, 61, 20, border_width=3)


class TestShapeCoordinates(ShapeTestBase):
    """Test coordinate handling"""

    def test_line_at_origin(self):
        """Should draw line at origin"""
        shapes.draw_line(self.draw, 0, 0, 10, 10)

    def test_line_out_of_bounds(self):
        """Should handle coordinates outside display"""
        # PIL handles this gracefully
        shapes.draw_line(self.draw, -10, -10, 500, 500)

    def test_rectangle_at_edge(self):
        """Should draw rectangle at display edge"""
        shapes.draw_rectangle(self.draw, 0, 0, canvas.DISPLAY_WIDTH, canvas.DISPLAY_HEIGHT)

    def test_circle_at_center(self):
        """Should draw circle at display center"""
        cx, cy = canvas.get_display_center()
        shapes.draw_circle(self.draw, cx, cy, 20)

    def test_zero_size_shapes(self):
        """Should handle zero-size shapes"""
        # These might render as points or nothing
        shapes.draw_rectangle(self.draw, 10, 10, 0, 0)
        shapes.draw_circle(self.draw, 125, 61, 0)

    def test_negative_coordinates(self):
        """Should handle negative coordinates"""
        shapes.draw_line(self.draw, -10, -10, 10, 10)


class TestEdgeCases(ShapeTestBase):
    """Test edge cases"""

    def test_polygon_single_point(self):
        """Should handle polygon with single point"""
        # PIL requires at least 2 points for polygon
        with pytest.raises(TypeError):
            shapes.draw_polygon(self.draw, [(10, 10)])

    def test_polygon_two_points(self):
        """Should handle polygon with two points"""
        shapes.draw_polygon(self.draw, [(10, 10), (50, 50)])

    def test_polygon_many_points(self):
        """Should handle polygon with many points"""
        points = [(i, i % 100) for i in range(100)]
        shapes.draw_polygon(self.draw, points)

    def test_arc_full_circle(self):
        """Should handle arc as full circle"""
        shapes.draw_arc(self.draw, 125, 61, 20, 0, 360)

    def test_arc_zero_size(self):
        """Should handle arc with zero radius"""
        shapes.draw_arc(self.draw, 125, 61, 0, 0, 180)

    def test_rounded_rectangle_large_radius(self):
        """Should handle radius larger than rectangle"""
        shapes.draw_rounded_rectangle(self.draw, 10, 10, 20, 20, radius=100)

    def test_very_large_coordinates(self):
        """Should handle very large coordinates"""
        shapes.draw_line(self.draw, 0, 0, 10000, 10000)


class TestLineVariations(ShapeTestBase):
    """Test line variations"""

    def test_horizontal_line_at_top(self):
        """Should draw horizontal line at top"""
        shapes.draw_horizontal_line(self.draw, 0)

    def test_horizontal_line_at_bottom(self):
        """Should draw horizontal line at bottom"""
        shapes.draw_horizontal_line(self.draw, canvas.DISPLAY_HEIGHT - 1)

    def test_vertical_line_at_left(self):
        """Should draw vertical line at left edge"""
        shapes.draw_vertical_line(self.draw, 0)

    def test_vertical_line_at_right(self):
        """Should draw vertical line at right edge"""
        shapes.draw_vertical_line(self.draw, canvas.DISPLAY_WIDTH - 1)

    def test_horizontal_line_range_none_defaults(self):
        """Should use full width when x2 is None"""
        shapes.draw_horizontal_line(self.draw, 50, x1=50, x2=None)

    def test_vertical_line_range_none_defaults(self):
        """Should use full height when y2 is None"""
        shapes.draw_vertical_line(self.draw, 125, y1=20, y2=None)


class TestCrossShape(ShapeTestBase):
    """Test cross/plus shape"""

    def test_cross_at_center(self):
        """Should draw cross at display center"""
        cx, cy = canvas.get_display_center()
        shapes.draw_cross(self.draw, cx, cy, 10)

    def test_cross_with_large_size(self):
        """Should draw large cross"""
        shapes.draw_cross(self.draw, 125, 61, 50)

    def test_cross_with_small_size(self):
        """Should draw small cross"""
        shapes.draw_cross(self.draw, 125, 61, 2)

    def test_cross_with_thick_lines(self):
        """Should draw cross with thick lines"""
        shapes.draw_cross(self.draw, 125, 61, 10, width=3)


class TestFrameShape(ShapeTestBase):
    """Test frame shape"""

    def test_frame_default(self):
        """Should draw frame with default padding"""
        shapes.draw_frame(self.draw)

    def test_frame_zero_padding(self):
        """Should draw frame with zero padding"""
        shapes.draw_frame(self.draw, padding=0)

    def test_frame_large_padding(self):
        """Should draw frame with large padding"""
        shapes.draw_frame(self.draw, padding=20)

    def test_frame_with_custom_width(self):
        """Should draw frame with custom width"""
        shapes.draw_frame(self.draw, width=3)


class TestShapeColors(ShapeTestBase):
    """Test shape color variations"""

    def test_black_shapes(self):
        """Should draw black shapes"""
        shapes.draw_rectangle(self.draw, 10, 10, 50, 50, outline=0)
        shapes.draw_circle(self.draw, 100, 50, 20, outline=0)

    def test_white_shapes(self):
        """Should draw white shapes"""
        # Create black canvas first
        img_black, draw_black = canvas.create_canvas_black()
        shapes.draw_rectangle(draw_black, 10, 10, 50, 50, outline=255)

    def test_mixed_color_shapes(self):
        """Should handle mix of colors"""
        shapes.draw_rectangle(self.draw, 10, 10, 50, 50, outline=0)
        shapes.draw_circle(self.draw, 100, 50, 20, outline=255)
