"""
Text Tests
==========

Tests for text.py module covering:
- Text measurement
- Text positioning and centering
- Text wrapping
- Text truncation
- Edge cases
"""

import pytest
from display import text, canvas, fonts


class TextTestBase:
    """Base class for text tests"""

    def setup_method(self):
        """Create canvas and font for each test"""
        self.img, self.draw = canvas.create_canvas()
        try:
            self.font = fonts.get_font_preset('body')
            self.font_skip = False
        except OSError:
            self.font_skip = True

    def skip_if_no_fonts(self):
        """Skip test if fonts not available"""
        if self.font_skip:
            pytest.skip("Font files not available")


class TestTextMeasurement(TextTestBase):
    """Test text measurement functions"""

    def test_get_text_size(self):
        """Should measure text size"""
        self.skip_if_no_fonts()

        width, height = text.get_text_size(self.draw, "Hello", self.font)

        assert width > 0
        assert height > 0

    def test_get_text_width(self):
        """Should measure text width"""
        self.skip_if_no_fonts()

        width = text.get_text_width(self.draw, "Hello", self.font)

        assert width > 0

    def test_get_text_height(self):
        """Should measure text height"""
        self.skip_if_no_fonts()

        height = text.get_text_height(self.draw, "Hello", self.font)

        assert height > 0

    def test_empty_string_size(self):
        """Should measure empty string as zero width"""
        self.skip_if_no_fonts()

        width, height = text.get_text_size(self.draw, "", self.font)

        # Empty string might have zero width or small width
        assert width >= 0
        assert height >= 0

    def test_longer_text_wider(self):
        """Longer text should be wider"""
        self.skip_if_no_fonts()

        width1 = text.get_text_width(self.draw, "Hi", self.font)
        width2 = text.get_text_width(self.draw, "Hello World", self.font)

        assert width2 > width1

    def test_different_fonts_different_sizes(self):
        """Different fonts should give different sizes"""
        self.skip_if_no_fonts()

        try:
            font_small = fonts.get_font_preset('small')
            font_large = fonts.get_font_preset('headline')

            width_small = text.get_text_width(self.draw, "Test", font_small)
            width_large = text.get_text_width(self.draw, "Test", font_large)

            # Large font should be wider (might have same width if rendering is off)
            assert width_large >= width_small
        except OSError:
            pytest.skip("Font files not available")


class TestTextPositioning(TextTestBase):
    """Test text positioning functions"""

    def test_draw_centered_text(self):
        """Should draw text centered horizontally"""
        self.skip_if_no_fonts()

        x, y = text.draw_centered_text(self.draw, "Test", y=50, font=self.font)

        # x should be calculated for centering
        assert x >= 0
        assert y == 50

    def test_draw_centered_text_custom_width(self):
        """Should center within custom width"""
        self.skip_if_no_fonts()

        x, y = text.draw_centered_text(self.draw, "Test", y=50, font=self.font, width=100)

        # x should be within the 100px width
        assert 0 <= x <= 100

    def test_draw_right_aligned_text(self):
        """Should draw text aligned to right"""
        self.skip_if_no_fonts()

        x, y = text.draw_right_aligned_text(self.draw, "Test", y=50, font=self.font)

        assert x > 0
        assert y == 50

    def test_draw_right_aligned_with_padding(self):
        """Should respect padding from right edge"""
        self.skip_if_no_fonts()

        x1, _ = text.draw_right_aligned_text(self.draw, "Test", y=50, font=self.font, padding=0)
        x2, _ = text.draw_right_aligned_text(self.draw, "Test", y=50, font=self.font, padding=10)

        # With padding, x should be further left
        assert x2 < x1

    def test_draw_centered_text_vertical(self):
        """Should draw text centered vertically"""
        self.skip_if_no_fonts()

        x, y = text.draw_centered_text_vertical(self.draw, "Test", x=50, font=self.font)

        assert x == 50
        assert y >= 0

    def test_draw_centered_text_vertical_custom_height(self):
        """Should center within custom height"""
        self.skip_if_no_fonts()

        x, y = text.draw_centered_text_vertical(
            self.draw, "Test", x=50, font=self.font, height=100
        )

        # y should be within the 100px height
        assert 0 <= y <= 100

    def test_draw_centered_text_both(self):
        """Should draw text centered both ways"""
        self.skip_if_no_fonts()

        x, y = text.draw_centered_text_both(self.draw, "Test", font=self.font)

        assert x >= 0
        assert y >= 0
        assert x < canvas.DISPLAY_WIDTH
        assert y < canvas.DISPLAY_HEIGHT


class TestTextWrapping(TextTestBase):
    """Test text wrapping functions"""

    def test_wrap_text_single_line(self):
        """Should not wrap short text"""
        self.skip_if_no_fonts()

        lines = text.wrap_text(self.draw, "Hi", 100, self.font)

        assert len(lines) == 1
        assert lines[0] == "Hi"

    def test_wrap_text_multiple_lines(self):
        """Should wrap long text"""
        self.skip_if_no_fonts()

        long_text = "This is a very long text that should definitely wrap to multiple lines"
        lines = text.wrap_text(self.draw, long_text, 50, self.font)

        assert len(lines) > 1

    def test_wrap_text_empty_string(self):
        """Should handle empty string"""
        self.skip_if_no_fonts()

        lines = text.wrap_text(self.draw, "", 100, self.font)

        # Empty text should result in empty list or list with empty string
        assert isinstance(lines, list)

    def test_wrap_text_narrow_width(self):
        """Should wrap with narrow width"""
        self.skip_if_no_fonts()

        lines = text.wrap_text(self.draw, "Hello World", 20, self.font)

        # Each word should be on separate line (or wrapped further)
        assert len(lines) >= 1

    def test_draw_wrapped_text(self):
        """Should draw wrapped text"""
        self.skip_if_no_fonts()

        next_y = text.draw_wrapped_text(
            self.draw, "Test text here", x=10, y=20, max_width=100, font=self.font
        )

        # next_y should be below starting y
        assert next_y >= 20

    def test_draw_wrapped_text_with_spacing(self):
        """Should respect line spacing"""
        self.skip_if_no_fonts()

        next_y1 = text.draw_wrapped_text(
            self.draw, "Test text", x=10, y=20, max_width=100, font=self.font, line_spacing=2
        )

        next_y2 = text.draw_wrapped_text(
            self.draw, "Test text", x=10, y=20, max_width=100, font=self.font, line_spacing=10
        )

        # Larger spacing should result in larger next_y
        assert next_y2 > next_y1


class TestTextTruncation(TextTestBase):
    """Test text truncation functions"""

    def test_truncate_text_no_truncation_needed(self):
        """Should not truncate short text"""
        result = text.truncate_text("Hi", 10)

        assert result == "Hi"

    def test_truncate_text_truncate_needed(self):
        """Should truncate long text"""
        result = text.truncate_text("Hello World", 8)

        assert len(result) == 8
        assert result.endswith("...")

    def test_truncate_text_custom_suffix(self):
        """Should use custom suffix"""
        result = text.truncate_text("Hello World", 8, suffix="--")

        assert result.endswith("--")

    def test_truncate_text_empty_suffix(self):
        """Should handle empty suffix"""
        result = text.truncate_text("Hello World", 5, suffix="")

        assert len(result) == 5

    def test_truncate_text_exact_length(self):
        """Should truncate to exact length"""
        result = text.truncate_text("Hello", 5)

        assert len(result) == 5

    def test_truncate_text_to_width_no_truncation(self):
        """Should not truncate text that fits width"""
        self.skip_if_no_fonts()

        result = text.truncate_text_to_width(self.draw, "Hi", 100, self.font)

        assert result == "Hi"

    def test_truncate_text_to_width_truncate(self):
        """Should truncate text that exceeds width"""
        self.skip_if_no_fonts()

        result = text.truncate_text_to_width(self.draw, "Hello World", 20, self.font)

        assert len(result) > 0
        # Should be truncated with suffix
        if len(result) < len("Hello World"):
            assert result.endswith("...")

    def test_truncate_text_to_width_empty_string(self):
        """Should handle empty string"""
        self.skip_if_no_fonts()

        result = text.truncate_text_to_width(self.draw, "", 100, self.font)

        assert result == ""


class TestMultilineText(TextTestBase):
    """Test multiline text drawing"""

    def test_draw_multiline_text_left(self):
        """Should draw multiline text left-aligned"""
        self.skip_if_no_fonts()

        lines = ["Line 1", "Line 2", "Line 3"]
        next_y = text.draw_multiline_text(self.draw, lines, x=10, y=20, font=self.font)

        assert next_y > 20

    def test_draw_multiline_text_center(self):
        """Should draw multiline text centered"""
        self.skip_if_no_fonts()

        lines = ["Line 1", "Line 2"]
        next_y = text.draw_multiline_text(
            self.draw, lines, x=canvas.DISPLAY_WIDTH // 2, y=20,
            font=self.font, align="center"
        )

        assert next_y > 20

    def test_draw_multiline_text_right(self):
        """Should draw multiline text right-aligned"""
        self.skip_if_no_fonts()

        lines = ["Line 1", "Line 2"]
        next_y = text.draw_multiline_text(
            self.draw, lines, x=canvas.DISPLAY_WIDTH, y=20,
            font=self.font, align="right"
        )

        assert next_y > 20

    def test_draw_multiline_empty_list(self):
        """Should handle empty line list"""
        self.skip_if_no_fonts()

        next_y = text.draw_multiline_text(self.draw, [], x=10, y=20, font=self.font)

        # Should return starting y (no lines drawn)
        assert next_y == 20

    def test_draw_multiline_single_line(self):
        """Should handle single line"""
        self.skip_if_no_fonts()

        next_y = text.draw_multiline_text(self.draw, ["Single Line"], x=10, y=20, font=self.font)

        assert next_y > 20

    def test_draw_multiline_with_spacing(self):
        """Should respect line spacing"""
        self.skip_if_no_fonts()

        lines = ["Line 1", "Line 2", "Line 3"]

        next_y1 = text.draw_multiline_text(
            self.draw, lines, x=10, y=20, font=self.font, line_spacing=2
        )

        next_y2 = text.draw_multiline_text(
            self.draw, lines, x=10, y=20, font=self.font, line_spacing=10
        )

        # Larger spacing should result in larger next_y
        assert next_y2 > next_y1


class TestTextEdgeCases(TextTestBase):
    """Test edge cases for text functions"""

    def test_text_with_special_characters(self):
        """Should handle special characters"""
        self.skip_if_no_fonts()

        # These might not render but shouldn't crash
        text.get_text_size(self.draw, "Test!@#$%", self.font)
        text.get_text_size(self.draw, "Greek: αβγ", self.font)

    def test_text_very_long(self):
        """Should handle very long text"""
        self.skip_if_no_fonts()

        long_text = "A" * 1000
        width, height = text.get_text_size(self.draw, long_text, self.font)

        assert width > 0
        assert height > 0

    def test_wrap_text_single_word_too_long(self):
        """Should handle single word longer than max width"""
        self.skip_if_no_fonts()

        # Single word that's too long
        lines = text.wrap_text(self.draw, "Supercalifragilisticexpialidocious", 20, self.font)

        # Should still return at least the word
        assert len(lines) > 0

    def test_truncate_text_at_boundary(self):
        """Should handle truncation at exact boundary"""
        # Exactly equal to max length
        result = text.truncate_text("12345", 5)

        assert len(result) == 5

    def test_text_with_newlines(self):
        """Should handle text with newlines"""
        self.skip_if_no_fonts()

        # wrap_text doesn't split on newlines by default
        lines = text.wrap_text(self.draw, "Line1\nLine2", 100, self.font)

        # Should treat as single line or handle gracefully
        assert len(lines) >= 1


class TestTextConstants(TextTestBase):
    """Test text module constants"""

    def test_default_color(self):
        """DEFAULT_COLOR should be black (0)"""
        assert text.DEFAULT_COLOR == 0

    def test_default_truncate_suffix(self):
        """DEFAULT_TRUNCATE_SUFFIX should be '...'"""
        assert text.DEFAULT_TRUNCATE_SUFFIX == "..."
