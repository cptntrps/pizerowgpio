"""
Layout Tests
============

Tests for layouts.py module covering:
- Header and footer layouts
- Split layout
- List layout with scrolling
- Grid layout
- Center layout
"""

import pytest
from display import layouts, canvas, fonts


class LayoutTestBase:
    """Base class for layout tests"""

    def setup_method(self):
        """Create canvas for each test"""
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


class TestHeaderLayout(LayoutTestBase):
    """Test HeaderLayout component"""

    def test_header_init_default(self):
        """Should initialize header with defaults"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("Test Title")

        assert header.title == "Test Title"
        assert not header.show_time
        assert header.height == 18

    def test_header_init_with_time(self):
        """Should initialize header with time enabled"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("Test", show_time=True)

        assert header.show_time

    def test_header_draw_default(self):
        """Should draw header"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("Test Title")
        next_y = header.draw(self.draw)

        assert next_y == header.height

    def test_header_draw_with_time(self):
        """Should draw header with time"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("Test Title", show_time=True)
        next_y = header.draw(self.draw)

        assert next_y == header.height

    def test_header_draw_without_divider(self):
        """Should draw header without divider line"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("Test Title")
        next_y = header.draw(self.draw, draw_divider=False)

        assert next_y == header.height

    def test_header_custom_height(self):
        """Should use custom header height"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("Test", height=25)

        assert header.height == 25


class TestFooterLayout(LayoutTestBase):
    """Test FooterLayout component"""

    def test_footer_init_default(self):
        """Should initialize footer with defaults"""
        self.skip_if_no_fonts()

        footer = layouts.FooterLayout("Test Instructions")

        assert footer.text == "Test Instructions"
        assert footer.height == 22

    def test_footer_draw_default(self):
        """Should draw footer"""
        self.skip_if_no_fonts()

        footer = layouts.FooterLayout("Tap: Next")
        footer_y = footer.draw(self.draw)

        # Footer should be at bottom
        assert footer_y == canvas.DISPLAY_HEIGHT - footer.height

    def test_footer_draw_without_divider(self):
        """Should draw footer without divider line"""
        self.skip_if_no_fonts()

        footer = layouts.FooterLayout("Test")
        footer_y = footer.draw(self.draw, draw_divider=False)

        assert footer_y == canvas.DISPLAY_HEIGHT - footer.height

    def test_footer_custom_height(self):
        """Should use custom footer height"""
        self.skip_if_no_fonts()

        footer = layouts.FooterLayout("Test", height=30)

        assert footer.height == 30


class TestSplitLayout(LayoutTestBase):
    """Test SplitLayout component"""

    def test_split_layout_init_default(self):
        """Should initialize split layout with default center split"""
        split = layouts.SplitLayout()

        assert split.split_x == canvas.DISPLAY_WIDTH // 2

    def test_split_layout_init_custom(self):
        """Should initialize split layout with custom position"""
        split = layouts.SplitLayout(split_x=100)

        assert split.split_x == 100

    def test_split_layout_draw_divider(self):
        """Should draw vertical divider"""
        split = layouts.SplitLayout()
        split.draw_divider(self.draw)

        # Just verify it doesn't error

    def test_split_layout_get_left_bounds(self):
        """Should return correct left panel bounds"""
        split = layouts.SplitLayout(split_x=125)

        x, y, width, height = split.get_left_bounds()

        assert x == 0
        assert y == 0
        assert width == 125
        assert height == canvas.DISPLAY_HEIGHT

    def test_split_layout_get_right_bounds(self):
        """Should return correct right panel bounds"""
        split = layouts.SplitLayout(split_x=125)

        x, y, width, height = split.get_right_bounds()

        assert x == 125
        assert y == 0
        assert width == canvas.DISPLAY_WIDTH - 125
        assert height == canvas.DISPLAY_HEIGHT

    def test_split_layout_bounds_match_split(self):
        """Right panel x should equal split_x"""
        split = layouts.SplitLayout(split_x=100)

        _, _, left_width, _ = split.get_left_bounds()
        right_x, _, _, _ = split.get_right_bounds()

        assert left_width == right_x


class TestListLayout(LayoutTestBase):
    """Test ListLayout component"""

    def test_list_layout_init(self):
        """Should initialize list layout"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2", "Item 3"]
        list_layout = layouts.ListLayout(items)

        assert list_layout.items == items

    def test_list_layout_draw_empty(self):
        """Should handle empty list"""
        self.skip_if_no_fonts()

        list_layout = layouts.ListLayout([])
        next_y = list_layout.draw(self.draw)

        assert next_y == list_layout.start_y

    def test_list_layout_draw_items(self):
        """Should draw list items"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2", "Item 3"]
        list_layout = layouts.ListLayout(items)
        next_y = list_layout.draw(self.draw)

        # next_y should be below start_y (items were drawn)
        assert next_y > list_layout.start_y

    def test_list_layout_draw_with_bullets(self):
        """Should draw list with bullet points"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2"]
        list_layout = layouts.ListLayout(items)
        list_layout.draw(self.draw, show_bullets=True)

    def test_list_layout_draw_without_bullets(self):
        """Should draw list without bullet points"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2"]
        list_layout = layouts.ListLayout(items)
        list_layout.draw(self.draw, show_bullets=False)

    def test_list_layout_scroll_down(self):
        """Should scroll list down"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
        list_layout = layouts.ListLayout(items, item_height=15)

        assert list_layout.scroll_offset == 0
        list_layout.scroll_down()
        assert list_layout.scroll_offset == 1

    def test_list_layout_scroll_up(self):
        """Should scroll list up"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2", "Item 3"]
        list_layout = layouts.ListLayout(items)

        list_layout.scroll_offset = 2
        list_layout.scroll_up()
        assert list_layout.scroll_offset == 1

    def test_list_layout_scroll_bounds(self):
        """Should not scroll beyond bounds"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2", "Item 3"]
        list_layout = layouts.ListLayout(items)

        # Scroll up at top should stay at 0
        list_layout.scroll_up()
        assert list_layout.scroll_offset == 0

    def test_list_layout_reset_scroll(self):
        """Should reset scroll to top"""
        self.skip_if_no_fonts()

        items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
        list_layout = layouts.ListLayout(items)

        list_layout.scroll_offset = 5
        list_layout.reset_scroll()
        assert list_layout.scroll_offset == 0

    def test_list_layout_custom_item_height(self):
        """Should use custom item height"""
        self.skip_if_no_fonts()

        list_layout = layouts.ListLayout(["Item 1"], item_height=20)

        assert list_layout.item_height == 20


class TestGridLayout(LayoutTestBase):
    """Test GridLayout component"""

    def test_grid_layout_init(self):
        """Should initialize grid layout"""
        grid = layouts.GridLayout(rows=2, cols=2)

        assert grid.rows == 2
        assert grid.cols == 2

    def test_grid_layout_auto_cell_size(self):
        """Should auto-calculate cell sizes"""
        grid = layouts.GridLayout(rows=2, cols=2)

        assert grid.cell_width == canvas.DISPLAY_WIDTH // 2
        assert grid.cell_height == canvas.DISPLAY_HEIGHT // 2

    def test_grid_layout_custom_cell_size(self):
        """Should use custom cell sizes"""
        grid = layouts.GridLayout(rows=2, cols=2, cell_width=100, cell_height=50)

        assert grid.cell_width == 100
        assert grid.cell_height == 50

    def test_grid_layout_get_cell_position(self):
        """Should calculate cell positions correctly"""
        grid = layouts.GridLayout(rows=2, cols=2)

        # Cell 0 (0, 0)
        x, y = grid.get_cell_position(0)
        assert x == 0
        assert y == 0

        # Cell 1 (0, 1)
        x, y = grid.get_cell_position(1)
        assert x == grid.cell_width
        assert y == 0

        # Cell 2 (1, 0)
        x, y = grid.get_cell_position(2)
        assert x == 0
        assert y == grid.cell_height

    def test_grid_layout_get_cell_bounds(self):
        """Should return cell bounds"""
        grid = layouts.GridLayout(rows=2, cols=2)

        x, y, width, height = grid.get_cell_bounds(0)

        assert x == 0
        assert y == 0
        assert width > 0
        assert height > 0

    def test_grid_layout_draw_grid_lines(self):
        """Should draw grid lines"""
        grid = layouts.GridLayout(rows=2, cols=2)
        grid.draw_grid_lines(self.draw)

        # Just verify it doesn't error

    def test_grid_layout_single_cell(self):
        """Should handle single cell grid"""
        grid = layouts.GridLayout(rows=1, cols=1)

        x, y = grid.get_cell_position(0)
        assert x == 0
        assert y == 0

    def test_grid_layout_many_cells(self):
        """Should handle many cells"""
        grid = layouts.GridLayout(rows=10, cols=10)

        # Last cell
        x, y = grid.get_cell_position(99)
        assert x >= 0
        assert y >= 0


class TestCenterLayout(LayoutTestBase):
    """Test CenterLayout component"""

    def test_center_layout_init_default(self):
        """Should initialize center layout with default dimensions"""
        self.skip_if_no_fonts()

        center = layouts.CenterLayout()

        assert center.width == canvas.DISPLAY_WIDTH
        assert center.height == canvas.DISPLAY_HEIGHT

    def test_center_layout_init_custom(self):
        """Should initialize center layout with custom dimensions"""
        self.skip_if_no_fonts()

        center = layouts.CenterLayout(width=200, height=100)

        assert center.width == 200
        assert center.height == 100

    def test_center_layout_get_centered_text_position(self):
        """Should calculate centered text position"""
        self.skip_if_no_fonts()

        center = layouts.CenterLayout()
        x, y = center.get_centered_text_position(self.draw, "Test", self.font)

        # Position should be within bounds
        assert 0 <= x <= center.width
        assert 0 <= y <= center.height

    def test_center_layout_draw_centered_text(self):
        """Should draw centered text"""
        self.skip_if_no_fonts()

        center = layouts.CenterLayout()
        center.draw_centered_text(self.draw, "Test", self.font)

        # Just verify no error

    def test_center_layout_center_point(self):
        """Should calculate correct center point"""
        center = layouts.CenterLayout(width=200, height=100)

        assert center.center_x == 100
        assert center.center_y == 50


class TestLayoutEdgeCases(LayoutTestBase):
    """Test edge cases for layouts"""

    def test_header_very_long_title(self):
        """Should handle very long header title"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("A" * 100)
        header.draw(self.draw)

    def test_list_very_many_items(self):
        """Should handle list with many items"""
        self.skip_if_no_fonts()

        items = [f"Item {i}" for i in range(1000)]
        list_layout = layouts.ListLayout(items)
        list_layout.draw(self.draw)

    def test_list_very_long_item_text(self):
        """Should truncate very long item text"""
        self.skip_if_no_fonts()

        items = ["A" * 100]
        list_layout = layouts.ListLayout(items)
        list_layout.draw(self.draw)

    def test_grid_zero_dimensions(self):
        """Should handle edge cases in grid"""
        try:
            grid = layouts.GridLayout(rows=0, cols=0)
        except (ValueError, ZeroDivisionError):
            pass  # Either error or handle gracefully

    def test_layout_empty_strings(self):
        """Should handle empty strings"""
        self.skip_if_no_fonts()

        header = layouts.HeaderLayout("")
        header.draw(self.draw)

        footer = layouts.FooterLayout("")
        footer.draw(self.draw)
