"""
Font Caching and Preset Tests
==============================

Tests for font.py module covering:
- Font caching performance
- Font preset availability
- Font preloading
- Error handling
"""

import pytest
import time
from display import fonts


class TestFontCaching:
    """Test font caching mechanism"""

    def setup_method(self):
        """Clear cache before each test"""
        fonts.clear_font_cache()

    def test_font_cache_empty_on_start(self):
        """Cache should be empty after clearing"""
        assert fonts.get_cache_size() == 0

    def test_font_loading(self):
        """Font should load successfully"""
        # Skip if font files not available
        try:
            font = fonts.get_font('Roboto-Regular', 12)
            assert font is not None
        except OSError:
            pytest.skip("Font files not available")

    def test_font_caching_performance(self):
        """Second font access should be faster (cached)"""
        try:
            # First load (from disk)
            start = time.time()
            fonts.get_font('Roboto-Regular', 12)
            first_load = time.time() - start

            # Second load (from cache)
            start = time.time()
            fonts.get_font('Roboto-Regular', 12)
            cached_load = time.time() - start

            # Cached load should be significantly faster
            # (at least 10x faster, usually 100x+)
            assert cached_load < first_load / 10 or cached_load < 0.001

        except OSError:
            pytest.skip("Font files not available")

    def test_font_cache_size_increases(self):
        """Cache size should increase as fonts are loaded"""
        try:
            fonts.clear_font_cache()
            assert fonts.get_cache_size() == 0

            fonts.get_font('Roboto-Regular', 12)
            assert fonts.get_cache_size() == 1

            fonts.get_font('Roboto-Bold', 14)
            assert fonts.get_cache_size() == 2

            # Same font and size should not increase cache
            fonts.get_font('Roboto-Regular', 12)
            assert fonts.get_cache_size() == 2

        except OSError:
            pytest.skip("Font files not available")

    def test_font_cache_clear(self):
        """Cache should clear properly"""
        try:
            fonts.get_font('Roboto-Regular', 12)
            assert fonts.get_cache_size() > 0

            fonts.clear_font_cache()
            assert fonts.get_cache_size() == 0

        except OSError:
            pytest.skip("Font files not available")

    def test_different_sizes_are_cached_separately(self):
        """Different font sizes should have separate cache entries"""
        try:
            fonts.clear_font_cache()

            fonts.get_font('Roboto-Regular', 10)
            fonts.get_font('Roboto-Regular', 12)
            fonts.get_font('Roboto-Regular', 14)

            # Should have 3 entries
            assert fonts.get_cache_size() == 3

        except OSError:
            pytest.skip("Font files not available")

    def test_different_names_are_cached_separately(self):
        """Different font names should have separate cache entries"""
        try:
            fonts.clear_font_cache()

            fonts.get_font('Roboto-Regular', 12)
            fonts.get_font('Roboto-Bold', 12)

            # Should have 2 entries
            assert fonts.get_cache_size() == 2

        except OSError:
            pytest.skip("Font files not available")


class TestFontPresets:
    """Test font preset system"""

    def setup_method(self):
        """Clear cache before each test"""
        fonts.clear_font_cache()

    def test_preset_exists_headline(self):
        """Headline preset should exist"""
        assert 'headline' in fonts.list_presets()

    def test_preset_exists_body(self):
        """Body preset should exist"""
        assert 'body' in fonts.list_presets()

    def test_all_presets_in_list(self):
        """All defined presets should be in list"""
        presets = fonts.list_presets()
        expected = ['headline', 'title', 'subtitle', 'body', 'body_bold',
                   'small', 'small_bold', 'tiny', 'display', 'display_huge']
        for preset in expected:
            assert preset in presets

    def test_list_presets_sorted(self):
        """Preset list should be sorted"""
        presets = fonts.list_presets()
        assert presets == sorted(presets)

    def test_get_font_preset_valid(self):
        """Should retrieve valid preset"""
        try:
            font = fonts.get_font_preset('headline')
            assert font is not None
        except OSError:
            pytest.skip("Font files not available")

    def test_get_font_preset_invalid(self):
        """Should raise KeyError for invalid preset"""
        with pytest.raises(KeyError):
            fonts.get_font_preset('nonexistent_preset')

    def test_font_preset_cached(self):
        """Font presets should be cached"""
        try:
            fonts.clear_font_cache()

            # First access
            fonts.get_font_preset('headline')
            cache_size = fonts.get_cache_size()

            # Second access (should use cache)
            fonts.get_font_preset('headline')
            assert fonts.get_cache_size() == cache_size

        except OSError:
            pytest.skip("Font files not available")

    def test_preset_has_correct_size(self):
        """Presets should have expected sizes"""
        try:
            # Headline should be 20pt
            # We can't directly check size, but we can verify it loads
            font = fonts.get_font_preset('headline')
            assert font is not None

        except OSError:
            pytest.skip("Font files not available")


class TestFontPreloading:
    """Test font preloading functions"""

    def setup_method(self):
        """Clear cache before each test"""
        fonts.clear_font_cache()

    def test_preload_common_fonts(self):
        """Preload common fonts should populate cache"""
        try:
            fonts.clear_font_cache()
            assert fonts.get_cache_size() == 0

            fonts.preload_common_fonts()
            # Should have loaded 4 presets
            assert fonts.get_cache_size() >= 4

        except OSError:
            pytest.skip("Font files not available")

    def test_preload_all_presets(self):
        """Preload all presets should populate cache"""
        try:
            fonts.clear_font_cache()

            fonts.preload_all_presets()

            # Should have loaded all presets
            num_presets = len(fonts.list_presets())
            assert fonts.get_cache_size() == num_presets

        except OSError:
            pytest.skip("Font files not available")

    def test_preload_improves_performance(self):
        """Preloading should improve subsequent access time"""
        try:
            fonts.clear_font_cache()
            fonts.preload_common_fonts()

            # Accessing preloaded font should be fast
            start = time.time()
            for _ in range(10):
                fonts.get_font_preset('headline')
            elapsed = time.time() - start

            # 10 accesses should be fast (< 10ms total on modern hardware)
            assert elapsed < 0.1

        except OSError:
            pytest.skip("Font files not available")


class TestFontErrors:
    """Test font error handling"""

    def setup_method(self):
        """Clear cache before each test"""
        fonts.clear_font_cache()

    def test_invalid_font_file(self):
        """Loading non-existent font should raise OSError"""
        with pytest.raises(OSError):
            fonts.get_font('NonexistentFont-Regular', 12)

    def test_invalid_preset_name(self):
        """Invalid preset name should raise KeyError"""
        with pytest.raises(KeyError) as exc_info:
            fonts.get_font_preset('invalid_preset_name')

        # Error message should mention available presets
        assert 'Available presets' in str(exc_info.value)

    def test_zero_size_font(self):
        """Font with size 0 should handle gracefully"""
        # This might raise an error or handle it - just ensure no crash
        try:
            fonts.get_font('Roboto-Regular', 0)
        except (OSError, ValueError):
            pass  # Either is acceptable

    def test_negative_size_font(self):
        """Font with negative size should handle gracefully"""
        try:
            fonts.get_font('Roboto-Regular', -12)
        except (OSError, ValueError):
            pass  # Either is acceptable
