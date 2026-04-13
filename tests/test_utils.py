"""Unit tests for image processing utilities."""
import pytest
from pathlib import Path
from PIL import Image
import tempfile
import os

from utils import (
    get_exif,
    show_exif,
    extract_coordinates,
    crop_image,
    cleanup_cache,
    decimal_coordinates_to_degrees
)


class TestDecimalCoordinatesToDegrees:
    """Tests for coordinate conversion function."""
    
    def test_valid_coordinates(self):
        """Test conversion of valid DMS coordinates."""
        coord = ((52, 1), (30, 1), (0, 1))  # 52°30'0"
        result = decimal_coordinates_to_degrees(coord)
        assert result == 52.5
    
    def test_zero_coordinates(self):
        """Test conversion of zero coordinates."""
        coord = ((0, 1), (0, 1), (0, 1))
        result = decimal_coordinates_to_degrees(coord)
        assert result == 0.0
    
    def test_invalid_format(self):
        """Test that invalid format raises ValueError."""
        coord = ((52, 1), (30, 1))  # Missing seconds
        with pytest.raises(ValueError):
            decimal_coordinates_to_degrees(coord)


class TestGetExif:
    """Tests for EXIF extraction."""
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            get_exif("nonexistent_file.jpg")
    
    def test_basic_image(self):
        """Test EXIF extraction from a basic image."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            exif_data = get_exif(tmp_path)
            assert isinstance(exif_data, dict)
        finally:
            os.unlink(tmp_path)


class TestCropImage:
    """Tests for image cropping."""
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            crop_image("nonexistent_file.jpg")
    
    def test_crop_basic_image(self):
        """Test cropping a basic image."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            output_path = crop_image(tmp_path, scale_factor=2)
            assert Path(output_path).exists()
            assert "_cropx2" in output_path
            
            # Verify cropped image is smaller
            with Image.open(output_path) as cropped:
                assert cropped.size == (50, 50)
            
            # Cleanup
            Path(output_path).unlink()
        finally:
            if Path(tmp_path).exists():
                os.unlink(tmp_path)


class TestCleanupCache:
    """Tests for cache cleanup."""
    
    def test_empty_directory(self):
        """Test cleanup of empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            count = cleanup_cache(tmpdir)
            assert count == 0
    
    def test_cleanup_old_files(self):
        """Test that old files are cleaned up."""
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")
            
            # Modify the file's mtime to be older than 24 hours
            old_time = time.time() - (25 * 3600)  # 25 hours ago
            os.utime(test_file, (old_time, old_time))
            
            # Cleanup should remove the old file
            count = cleanup_cache(tmpdir, max_age_hours=24)
            assert count == 1
            assert not test_file.exists()
    
    def test_keep_recent_files(self):
        """Test that recent files are kept."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")
            
            # Cleanup should not remove recent file
            count = cleanup_cache(tmpdir, max_age_hours=24)
            assert count == 0
            assert test_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
