"""Utility functions for image processing."""
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageFile
from PIL.ExifTags import TAGS, GPSTAGS

ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_exif(image_path: str) -> Dict[str, Any]:
    """Extract EXIF data from an image file.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Dictionary containing EXIF tags and their values.
        
    Raises:
        FileNotFoundError: If the image file doesn't exist.
        Exception: If the image cannot be opened or has no EXIF data.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    props = {}
    with Image.open(path) as img:
        info = img.getexif()
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            props[decoded] = value
    
    return props


def decimal_coordinates_to_degrees(coord: Tuple[Tuple[int, int], ...]) -> float:
    """Convert GPS coordinates from degrees/minutes/seconds to decimal degrees.
    
    Args:
        coord: Tuple of three (numerator, denominator) tuples representing
               degrees, minutes, and seconds.
               
    Returns:
        Coordinate in decimal degrees.
        
    Raises:
        ValueError: If coordinate format is invalid.
    """
    if len(coord) != 3:
        raise ValueError("Invalid coordinate format: expected 3 tuples")
    
    try:
        deg = float(coord[0][0]) / float(coord[0][1])
        minut = float(coord[1][0]) / float(coord[1][1])
        sec = float(coord[2][0]) / float(coord[2][1])
        return deg + (minut / 60.0) + (sec / 3600.0)
    except (ZeroDivisionError, IndexError, TypeError) as e:
        raise ValueError(f"Invalid coordinate values: {e}")


def extract_coordinates(image_path: str) -> Optional[Tuple[float, float]]:
    """Extract GPS coordinates from image EXIF data.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Tuple of (latitude, longitude) in decimal degrees, or None if no GPS data.
        
    Raises:
        FileNotFoundError: If the image file doesn't exist.
        KeyError: If GPS data is missing or incomplete.
    """
    try:
        exif_data = get_exif(image_path)
        
        if 'GPSInfo' not in exif_data:
            raise KeyError("No GPS information in EXIF data")
        
        gps_info = exif_data['GPSInfo']
        
        # Extract GPS components
        lat_ref = gps_info.get(1, 'N')
        lon_ref = gps_info.get(3, 'E')
        lat = gps_info.get(2)
        lon = gps_info.get(4)
        
        if lat is None or lon is None:
            raise KeyError("GPS latitude or longitude missing")
        
        # Convert to decimal degrees
        lat_decimal = decimal_coordinates_to_degrees(lat)
        lon_decimal = decimal_coordinates_to_degrees(lon)
        
        # Apply reference direction
        if lat_ref == 'S':
            lat_decimal = -lat_decimal
        if lon_ref == 'W':
            lon_decimal = -lon_decimal
        
        return (lat_decimal, lon_decimal)
        
    except FileNotFoundError:
        raise
    except Exception as e:
        raise KeyError(f"Failed to extract coordinates: {e}")


def show_exif(image_path: str) -> str:
    """Format EXIF data as a human-readable string.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Formatted string with camera and photo information.
        
    Raises:
        FileNotFoundError: If the image file doesn't exist.
        KeyError: If required EXIF fields are missing.
    """
    try:
        exif = get_exif(image_path)
        
        make = exif.get("Make", "Unknown")
        model = exif.get("Model", "Unknown")
        iso = exif.get("ISOSpeedRatings", "N/A")
        exposure = exif.get("ExposureTime", "N/A")
        aperture = exif.get("FNumber", "N/A")
        focal_length = exif.get("FocalLength", "N/A")
        software = exif.get("Software", "N/A")
        
        # Handle ExposureTime which might be a special object
        if hasattr(exposure, '_val'):
            exposure = exposure._val
        
        exif_text = (
            f"Модель: {make} {model}\n"
            f"Софт: {software}\n"
            f"ISO: {iso}\n"
            f"Выдержка: {exposure}\n"
            f"Диафрагма: f/{aperture}\n"
            f"Фокусное расстояние: {focal_length} mm"
        )
        
        return exif_text
        
    except FileNotFoundError:
        raise
    except KeyError as e:
        raise KeyError(f"Missing required EXIF data: {e}")
    except Exception as e:
        raise Exception(f"Error formatting EXIF data: {e}")


def crop_image(image_path: str, scale_factor: int = 2) -> str:
    """Crop the center portion of an image.
    
    Args:
        image_path: Path to the input image file.
        scale_factor: How many times to crop (default 2 = crop to 50% size).
        
    Returns:
        Path to the cropped image file.
        
    Raises:
        FileNotFoundError: If the image file doesn't exist.
        Exception: If the image cannot be processed.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        with Image.open(path) as img:
            width, height = img.size
            
            # Calculate crop box (center 50% of the image)
            left = width // 4
            upper = height // 4
            right = width - left
            lower = height - upper
            
            # Crop the image
            cropped = img.crop((left, upper, right, lower))
            
            # Generate output filename
            output_path = path.parent / f"{path.stem}_cropx{scale_factor}.jpeg"
            
            # Save as JPEG
            cropped.save(output_path, "JPEG", quality=95)
            
            return str(output_path)
            
    except Exception as e:
        raise Exception(f"Error cropping image: {e}")


def cleanup_cache(cache_dir: str, max_age_hours: int = 24) -> int:
    """Remove old files from cache directory.
    
    Args:
        cache_dir: Path to cache directory.
        max_age_hours: Maximum age of files to keep (in hours).
        
    Returns:
        Number of files removed.
    """
    import time
    from pathlib import Path
    
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    removed_count = 0
    
    for file_path in cache_path.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    removed_count += 1
                except OSError:
                    pass
    
    return removed_count
