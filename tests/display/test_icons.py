"""
Icon Tests
==========

Tests for icons.py module covering:
- Icon rendering
- Icon variations (size, color)
- All icon types
- Edge cases
"""

import pytest
from display import icons, canvas


class IconTestBase:
    """Base class for icon tests"""

    def setup_method(self):
        """Create canvas for each test"""
        self.img, self.draw = canvas.create_canvas()


class TestMedicineIcons(IconTestBase):
    """Test medicine-related icons"""

    def test_draw_pill_icon_default(self):
        """Should draw pill icon with defaults"""
        icons.draw_pill_icon(self.draw, 10, 20)
        # Just verify no error

    def test_draw_pill_icon_custom_size(self):
        """Should draw pill with custom size"""
        icons.draw_pill_icon(self.draw, 10, 20, size=20)

    def test_draw_pill_icon_custom_color(self):
        """Should draw pill with custom color"""
        icons.draw_pill_icon(self.draw, 10, 20, color=255)

    def test_draw_pill_icon_at_edges(self):
        """Should draw pill near display edges"""
        icons.draw_pill_icon(self.draw, 0, 0, size=10)
        icons.draw_pill_icon(self.draw, canvas.DISPLAY_WIDTH - 15, canvas.DISPLAY_HEIGHT - 15)

    def test_draw_food_icon_default(self):
        """Should draw food icon with defaults"""
        icons.draw_food_icon(self.draw, 20, 30)

    def test_draw_food_icon_custom_size(self):
        """Should draw food icon with custom size"""
        icons.draw_food_icon(self.draw, 20, 30, size=15)

    def test_draw_checkmark_default(self):
        """Should draw checkmark with defaults"""
        icons.draw_checkmark(self.draw, 15, 25)

    def test_draw_checkmark_custom_size(self):
        """Should draw checkmark with custom size"""
        icons.draw_checkmark(self.draw, 15, 25, size=15)

    def test_draw_checkmark_custom_width(self):
        """Should draw checkmark with custom line width"""
        icons.draw_checkmark(self.draw, 15, 25, width=3)


class TestPomodoroIcons(IconTestBase):
    """Test Pomodoro timer icons"""

    def test_draw_tomato_icon_frame1(self):
        """Should draw tomato icon frame 1"""
        icons.draw_tomato_icon(self.draw, 125, 61, frame=1)

    def test_draw_tomato_icon_frame2(self):
        """Should draw tomato icon frame 2"""
        icons.draw_tomato_icon(self.draw, 125, 61, frame=2)

    def test_draw_tomato_icon_custom_size(self):
        """Should draw tomato with custom size"""
        icons.draw_tomato_icon(self.draw, 125, 61, size=50)

    def test_draw_tomato_icon_custom_color(self):
        """Should draw tomato with custom color"""
        icons.draw_tomato_icon(self.draw, 125, 61, color=255)

    def test_draw_tomato_icon_animation_frames(self):
        """Should handle both animation frames"""
        for frame in [1, 2]:
            icons.draw_tomato_icon(self.draw, 100, 50, frame=frame, size=30)


class TestWeatherIcons(IconTestBase):
    """Test weather condition icons"""

    def test_draw_weather_icon_sun(self):
        """Should draw sun icon"""
        icons.draw_weather_icon(self.draw, 125, 61, 'sun')

    def test_draw_weather_icon_clouds(self):
        """Should draw cloud icon"""
        icons.draw_weather_icon(self.draw, 125, 61, 'clouds')

    def test_draw_weather_icon_rain(self):
        """Should draw rain icon"""
        icons.draw_weather_icon(self.draw, 125, 61, 'rain')

    def test_draw_weather_icon_snow(self):
        """Should draw snow icon"""
        icons.draw_weather_icon(self.draw, 125, 61, 'snow')

    def test_draw_weather_icon_storm(self):
        """Should draw storm icon"""
        icons.draw_weather_icon(self.draw, 125, 61, 'storm')

    def test_draw_weather_icon_clear(self):
        """Should draw clear/sun icon"""
        icons.draw_weather_icon(self.draw, 125, 61, 'clear')

    def test_draw_weather_icon_cloudy(self):
        """Should draw cloudy variant"""
        icons.draw_weather_icon(self.draw, 125, 61, 'cloudy')

    def test_draw_weather_icon_rainy(self):
        """Should draw rainy variant"""
        icons.draw_weather_icon(self.draw, 125, 61, 'rainy')

    def test_draw_weather_icon_snowy(self):
        """Should draw snowy variant"""
        icons.draw_weather_icon(self.draw, 125, 61, 'snowy')

    def test_draw_weather_icon_thunderstorm(self):
        """Should draw thunderstorm variant"""
        icons.draw_weather_icon(self.draw, 125, 61, 'thunderstorm')

    def test_draw_weather_icon_unknown(self):
        """Should handle unknown weather condition"""
        # Unknown conditions default to cloud icon
        icons.draw_weather_icon(self.draw, 125, 61, 'unknown')

    def test_draw_weather_icon_case_insensitive(self):
        """Should handle case-insensitive weather conditions"""
        icons.draw_weather_icon(self.draw, 125, 61, 'SUN')
        icons.draw_weather_icon(self.draw, 125, 61, 'Rain')
        icons.draw_weather_icon(self.draw, 125, 61, 'SNOW')

    def test_draw_weather_icon_custom_size(self):
        """Should draw weather icons with custom size"""
        icons.draw_weather_icon(self.draw, 125, 61, 'sun', size=50)

    def test_draw_weather_icon_custom_color(self):
        """Should draw weather icons with custom color"""
        icons.draw_weather_icon(self.draw, 125, 61, 'rain', color=255)


class TestCompassIcons(IconTestBase):
    """Test compass and navigation icons"""

    def test_draw_compass_icon_north(self):
        """Should draw compass pointing north"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=0)

    def test_draw_compass_icon_east(self):
        """Should draw compass pointing east"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=90)

    def test_draw_compass_icon_south(self):
        """Should draw compass pointing south"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=180)

    def test_draw_compass_icon_west(self):
        """Should draw compass pointing west"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=270)

    def test_draw_compass_icon_northeast(self):
        """Should draw compass pointing northeast"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=45)

    def test_draw_compass_icon_custom_size(self):
        """Should draw compass with custom size"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=0, size=40)

    def test_draw_compass_icon_with_user_heading(self):
        """Should draw compass with user heading rotation"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=45, user_heading=90)

    def test_draw_compass_icon_all_angles(self):
        """Should draw compass at various angles"""
        for angle in range(0, 360, 45):
            icons.draw_compass_icon(self.draw, 100, 50, direction=angle)

    def test_draw_airplane_icon_default(self):
        """Should draw airplane icon"""
        icons.draw_airplane_icon(self.draw, 100, 50)

    def test_draw_airplane_icon_rotated(self):
        """Should draw airplane at various angles"""
        for angle in [0, 45, 90, 135, 180]:
            icons.draw_airplane_icon(self.draw, 100, 50, angle=angle)

    def test_draw_airplane_icon_custom_size(self):
        """Should draw airplane with custom size"""
        icons.draw_airplane_icon(self.draw, 100, 50, size=30)


class TestUIIcons(IconTestBase):
    """Test UI status icons"""

    def test_draw_battery_icon_empty(self):
        """Should draw empty battery"""
        icons.draw_battery_icon(self.draw, 200, 5, level=0)

    def test_draw_battery_icon_half(self):
        """Should draw half-full battery"""
        icons.draw_battery_icon(self.draw, 200, 5, level=50)

    def test_draw_battery_icon_full(self):
        """Should draw full battery"""
        icons.draw_battery_icon(self.draw, 200, 5, level=100)

    def test_draw_battery_icon_custom_size(self):
        """Should draw battery with custom size"""
        icons.draw_battery_icon(self.draw, 200, 5, level=75, size=30)

    def test_draw_battery_icon_various_levels(self):
        """Should draw battery at various levels"""
        for level in [0, 25, 50, 75, 100]:
            icons.draw_battery_icon(self.draw, 100, 10, level=level)

    def test_draw_wifi_icon_no_signal(self):
        """Should draw no WiFi signal"""
        icons.draw_wifi_icon(self.draw, 220, 15, strength=0)

    def test_draw_wifi_icon_weak(self):
        """Should draw weak WiFi signal"""
        icons.draw_wifi_icon(self.draw, 220, 15, strength=1)

    def test_draw_wifi_icon_medium(self):
        """Should draw medium WiFi signal"""
        icons.draw_wifi_icon(self.draw, 220, 15, strength=2)

    def test_draw_wifi_icon_strong(self):
        """Should draw strong WiFi signal"""
        icons.draw_wifi_icon(self.draw, 220, 15, strength=3)

    def test_draw_wifi_icon_custom_size(self):
        """Should draw WiFi with custom size"""
        icons.draw_wifi_icon(self.draw, 220, 15, strength=2, size=20)

    def test_draw_wifi_icon_various_strengths(self):
        """Should draw WiFi at various signal strengths"""
        for strength in range(0, 4):
            icons.draw_wifi_icon(self.draw, 100, 20, strength=strength)


class TestIconEdgeCases(IconTestBase):
    """Test edge cases for icons"""

    def test_icon_at_origin(self):
        """Should draw icons at (0, 0)"""
        icons.draw_pill_icon(self.draw, 0, 0)
        icons.draw_weather_icon(self.draw, 0, 0, 'sun')
        icons.draw_battery_icon(self.draw, 0, 0, level=50)

    def test_icon_at_display_edge(self):
        """Should draw icons near display edges"""
        icons.draw_pill_icon(self.draw, canvas.DISPLAY_WIDTH - 20, canvas.DISPLAY_HEIGHT - 20)

    def test_icon_at_display_corner(self):
        """Should draw icons at display corners"""
        # Top-left
        icons.draw_battery_icon(self.draw, 0, 0, level=50)
        # Top-right
        icons.draw_wifi_icon(self.draw, canvas.DISPLAY_WIDTH - 20, 0, strength=2)

    def test_icon_with_zero_size(self):
        """Should handle zero size"""
        icons.draw_pill_icon(self.draw, 10, 10, size=0)
        icons.draw_tomato_icon(self.draw, 10, 10, size=0)

    def test_icon_with_large_size(self):
        """Should handle large size"""
        icons.draw_pill_icon(self.draw, 10, 10, size=200)
        icons.draw_weather_icon(self.draw, 125, 61, 'sun', size=100)

    def test_icon_with_negative_position(self):
        """Should handle negative coordinates"""
        icons.draw_pill_icon(self.draw, -10, -10)
        # Should not crash even if rendering outside canvas

    def test_battery_icon_level_bounds(self):
        """Should handle battery levels outside 0-100"""
        icons.draw_battery_icon(self.draw, 200, 5, level=-10)
        icons.draw_battery_icon(self.draw, 200, 5, level=150)

    def test_wifi_icon_strength_bounds(self):
        """Should handle WiFi strength outside 0-3"""
        icons.draw_wifi_icon(self.draw, 220, 15, strength=-1)
        icons.draw_wifi_icon(self.draw, 220, 15, strength=10)

    def test_compass_direction_full_rotation(self):
        """Should handle compass directions beyond 360°"""
        icons.draw_compass_icon(self.draw, 125, 61, direction=450)  # 90° equivalent
        icons.draw_compass_icon(self.draw, 125, 61, direction=720)  # 0° equivalent

    def test_tomato_invalid_frame(self):
        """Should handle invalid frame number"""
        # Might default to frame 2 or raise - just ensure no crash
        icons.draw_tomato_icon(self.draw, 125, 61, frame=5)

    def test_multiple_icons_same_position(self):
        """Should draw multiple icons at same position"""
        icons.draw_pill_icon(self.draw, 50, 50, size=10)
        icons.draw_checkmark(self.draw, 50, 50, size=10)
        # Both should render without issue

    def test_weather_icon_empty_string(self):
        """Should handle empty condition string"""
        # Should default to cloud or raise - just ensure no crash
        icons.draw_weather_icon(self.draw, 125, 61, '')


class TestIconColors(IconTestBase):
    """Test icon color variations"""

    def test_black_icons(self):
        """Should draw icons in black"""
        icons.draw_pill_icon(self.draw, 10, 10, color=0)
        icons.draw_weather_icon(self.draw, 50, 50, 'sun', color=0)

    def test_white_icons(self):
        """Should draw icons in white"""
        # Create black canvas for white icons
        img_black, draw_black = canvas.create_canvas_black()
        icons.draw_pill_icon(draw_black, 10, 10, color=255)
        icons.draw_weather_icon(draw_black, 50, 50, 'sun', color=255)
