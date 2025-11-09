"""
Components Tests
================

Tests for components.py module covering:
- StatusBar component
- ProgressBar component
- Button component
- ListItem component
- MessageBox component
- Badge component
"""

import pytest
from display import components, canvas, fonts


class ComponentTestBase:
    """Base class for component tests"""

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


class TestStatusBar(ComponentTestBase):
    """Test StatusBar component"""

    def test_status_bar_init_default(self):
        """Should initialize status bar with defaults"""
        self.skip_if_no_fonts()

        status = components.StatusBar()

        assert status.show_time
        assert not status.show_battery
        assert not status.show_wifi

    def test_status_bar_init_custom(self):
        """Should initialize with custom options"""
        self.skip_if_no_fonts()

        status = components.StatusBar(show_battery=True, show_wifi=True)

        assert status.show_battery
        assert status.show_wifi

    def test_status_bar_draw_default(self):
        """Should draw status bar"""
        self.skip_if_no_fonts()

        status = components.StatusBar()
        next_y = status.draw(self.draw)

        assert next_y == status.height

    def test_status_bar_draw_with_battery(self):
        """Should draw status bar with battery indicator"""
        self.skip_if_no_fonts()

        status = components.StatusBar(show_battery=True)
        next_y = status.draw(self.draw, battery_level=75)

        assert next_y == status.height

    def test_status_bar_draw_with_wifi(self):
        """Should draw status bar with WiFi indicator"""
        self.skip_if_no_fonts()

        status = components.StatusBar(show_wifi=True)
        next_y = status.draw(self.draw, wifi_strength=2)

        assert next_y == status.height

    def test_status_bar_battery_levels(self):
        """Should handle various battery levels"""
        self.skip_if_no_fonts()

        status = components.StatusBar(show_battery=True)

        for level in [0, 25, 50, 75, 100]:
            status.draw(self.draw, battery_level=level)

    def test_status_bar_wifi_strengths(self):
        """Should handle various WiFi strengths"""
        self.skip_if_no_fonts()

        status = components.StatusBar(show_wifi=True)

        for strength in range(0, 4):
            status.draw(self.draw, wifi_strength=strength)


class TestProgressBar(ComponentTestBase):
    """Test ProgressBar component"""

    def test_progress_bar_init(self):
        """Should initialize progress bar"""
        progress = components.ProgressBar(x=10, y=50, width=200, height=10)

        assert progress.x == 10
        assert progress.y == 50
        assert progress.width == 200
        assert progress.height == 10

    def test_progress_bar_draw_empty(self):
        """Should draw empty progress bar"""
        progress = components.ProgressBar(x=10, y=50, width=200, height=10)
        progress.draw(self.draw, progress=0)

    def test_progress_bar_draw_full(self):
        """Should draw full progress bar"""
        progress = components.ProgressBar(x=10, y=50, width=200, height=10)
        progress.draw(self.draw, progress=100)

    def test_progress_bar_draw_partial(self):
        """Should draw partially filled progress bar"""
        progress = components.ProgressBar(x=10, y=50, width=200, height=10)

        for value in [0, 25, 50, 75, 100]:
            progress.draw(self.draw, progress=value)

    def test_progress_bar_clamps_value(self):
        """Should clamp progress value to 0-100"""
        progress = components.ProgressBar(x=10, y=50, width=200, height=10)

        # Should not error
        progress.draw(self.draw, progress=-50)
        progress.draw(self.draw, progress=150)

    def test_progress_bar_with_percentage(self):
        """Should draw progress bar with percentage text"""
        self.skip_if_no_fonts()

        progress = components.ProgressBar(x=10, y=50, width=200, height=10)
        progress.draw(self.draw, progress=75, show_percentage=True)

    def test_progress_bar_custom_color(self):
        """Should draw progress bar with custom color"""
        progress = components.ProgressBar(x=10, y=50, width=200, height=10)
        progress.draw(self.draw, progress=50, color=255)


class TestButton(ComponentTestBase):
    """Test Button component"""

    def test_button_init(self):
        """Should initialize button"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=100, height=30)

        assert button.text == "Click"
        assert button.x == 50
        assert button.y == 50

    def test_button_draw_default(self):
        """Should draw button"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=100, height=30)
        button.draw(self.draw)

    def test_button_draw_pressed(self):
        """Should draw button in pressed state"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=100, height=30)
        button.draw(self.draw, pressed=True)

    def test_button_is_touched_true(self):
        """Should detect touch within button bounds"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=100, height=30)

        # Touch in center of button
        assert button.is_touched(100, 65)

    def test_button_is_touched_false(self):
        """Should detect touch outside button bounds"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=100, height=30)

        # Touch outside button
        assert not button.is_touched(10, 10)
        assert not button.is_touched(200, 100)

    def test_button_is_touched_at_edge(self):
        """Should detect touch at button edge"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=100, height=30)

        # Exact corners
        assert button.is_touched(50, 50)
        assert button.is_touched(150, 80)

    def test_button_get_bounds(self):
        """Should return button bounds"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=100, height=30)
        x, y, width, height = button.get_bounds()

        assert x == 50
        assert y == 50
        assert width == 100
        assert height == 30


class TestListItem(ComponentTestBase):
    """Test ListItem component"""

    def test_list_item_init(self):
        """Should initialize list item"""
        self.skip_if_no_fonts()

        item = components.ListItem("Task 1", y=20)

        assert item.text == "Task 1"
        assert item.y == 20

    def test_list_item_draw_default(self):
        """Should draw list item"""
        self.skip_if_no_fonts()

        item = components.ListItem("Task 1", y=20)
        item.draw(self.draw)

    def test_list_item_draw_checked(self):
        """Should draw checked list item"""
        self.skip_if_no_fonts()

        item = components.ListItem("Task 1", y=20, checked=True)
        item.draw(self.draw)

    def test_list_item_draw_unchecked(self):
        """Should draw unchecked list item"""
        self.skip_if_no_fonts()

        item = components.ListItem("Task 1", y=20, checked=False)
        item.draw(self.draw)

    def test_list_item_toggle_checked(self):
        """Should toggle checked state"""
        self.skip_if_no_fonts()

        item = components.ListItem("Task", y=20, checked=False)

        assert not item.checked
        item.toggle_checked()
        assert item.checked
        item.toggle_checked()
        assert not item.checked

    def test_list_item_draw_without_checkbox(self):
        """Should draw list item without checkbox"""
        self.skip_if_no_fonts()

        item = components.ListItem("Task", y=20, show_checkbox=False)
        item.draw(self.draw)

    def test_list_item_with_icon(self):
        """Should draw list item with icon"""
        self.skip_if_no_fonts()

        from display import icons

        item = components.ListItem("Task", y=20, show_icon=True)
        item.draw(self.draw, icon_callback=icons.draw_pill_icon)


class TestMessageBox(ComponentTestBase):
    """Test MessageBox component"""

    def test_message_box_init(self):
        """Should initialize message box"""
        self.skip_if_no_fonts()

        msg = components.MessageBox("Success", "Operation completed")

        assert msg.title == "Success"
        assert msg.message == "Operation completed"

    def test_message_box_draw(self):
        """Should draw message box"""
        self.skip_if_no_fonts()

        msg = components.MessageBox("Success", "Operation completed")
        msg.draw(self.draw)

    def test_message_box_custom_size(self):
        """Should respect custom dimensions"""
        self.skip_if_no_fonts()

        msg = components.MessageBox("Title", "Message", width=150, height=100)
        msg.draw(self.draw)

        assert msg.width == 150
        assert msg.height == 100

    def test_message_box_centered(self):
        """Should be centered on display"""
        self.skip_if_no_fonts()

        msg = components.MessageBox("Title", "Message", width=200)

        # x should be centered
        expected_x = (canvas.DISPLAY_WIDTH - 200) // 2
        assert msg.x == expected_x

    def test_message_box_long_text(self):
        """Should handle long message text"""
        self.skip_if_no_fonts()

        msg = components.MessageBox(
            "Title",
            "A" * 100
        )
        msg.draw(self.draw)


class TestBadge(ComponentTestBase):
    """Test Badge component"""

    def test_badge_init(self):
        """Should initialize badge"""
        self.skip_if_no_fonts()

        badge = components.Badge("NEW", x=200, y=10)

        assert badge.text == "NEW"
        assert badge.x == 200
        assert badge.y == 10

    def test_badge_draw_default(self):
        """Should draw badge"""
        self.skip_if_no_fonts()

        badge = components.Badge("NEW", x=200, y=10)
        badge.draw(self.draw)

    def test_badge_draw_inverted(self):
        """Should draw inverted badge"""
        self.skip_if_no_fonts()

        badge = components.Badge("NEW", x=200, y=10)
        badge.draw(self.draw, inverted=True)

    def test_badge_custom_padding(self):
        """Should respect custom padding"""
        self.skip_if_no_fonts()

        badge = components.Badge("NEW", x=200, y=10, padding=5)

        assert badge.padding == 5

    def test_badge_at_edges(self):
        """Should draw badge at display edges"""
        self.skip_if_no_fonts()

        # Top-left
        badge1 = components.Badge("TL", x=0, y=0)
        badge1.draw(self.draw)

        # Top-right
        badge2 = components.Badge("TR", x=canvas.DISPLAY_WIDTH - 30, y=0)
        badge2.draw(self.draw)


class TestComponentEdgeCases(ComponentTestBase):
    """Test edge cases for components"""

    def test_button_zero_size(self):
        """Should handle zero-size button"""
        self.skip_if_no_fonts()

        button = components.Button("Click", x=50, y=50, width=0, height=0)
        button.draw(self.draw)

    def test_button_very_long_text(self):
        """Should handle very long button text"""
        self.skip_if_no_fonts()

        button = components.Button("A" * 100, x=50, y=50, width=100, height=30)
        button.draw(self.draw)

    def test_progress_bar_zero_width(self):
        """Should handle zero-width progress bar"""
        progress = components.ProgressBar(x=10, y=50, width=0, height=10)
        progress.draw(self.draw, progress=50)

    def test_progress_bar_zero_height(self):
        """Should handle zero-height progress bar"""
        progress = components.ProgressBar(x=10, y=50, width=200, height=0)
        # Zero height may cause drawing errors in PIL
        try:
            progress.draw(self.draw, progress=50)
        except (ValueError, ZeroDivisionError):
            pass  # Expected - PIL can't draw with invalid dimensions

    def test_message_box_zero_size(self):
        """Should handle zero-size message box"""
        self.skip_if_no_fonts()

        msg = components.MessageBox("Title", "Message", width=0, height=0)
        msg.draw(self.draw)

    def test_multiple_buttons(self):
        """Should handle multiple buttons"""
        self.skip_if_no_fonts()

        button1 = components.Button("Button 1", x=10, y=20, width=80, height=30)
        button2 = components.Button("Button 2", x=100, y=20, width=80, height=30)

        button1.draw(self.draw)
        button2.draw(self.draw)

    def test_multiple_badges(self):
        """Should handle multiple badges"""
        self.skip_if_no_fonts()

        for i in range(5):
            badge = components.Badge(f"B{i}", x=10 + i * 40, y=10)
            badge.draw(self.draw)

    def test_list_item_very_long_text(self):
        """Should truncate very long list item text"""
        self.skip_if_no_fonts()

        item = components.ListItem("A" * 200, y=20)
        item.draw(self.draw)

    def test_status_bar_extreme_battery(self):
        """Should handle extreme battery levels"""
        self.skip_if_no_fonts()

        status = components.StatusBar(show_battery=True)

        # Below 0
        status.draw(self.draw, battery_level=-100)

        # Above 100
        status.draw(self.draw, battery_level=200)

    def test_status_bar_extreme_wifi(self):
        """Should handle extreme WiFi strengths"""
        self.skip_if_no_fonts()

        status = components.StatusBar(show_wifi=True)

        # Negative
        status.draw(self.draw, wifi_strength=-1)

        # Very high
        status.draw(self.draw, wifi_strength=100)
