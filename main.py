"""Telegram bot for image processing."""
import os
import logging
from pathlib import Path
from typing import Optional

from loguru import logger
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery
)

from config import (
    API_TOKEN,
    BOT_OPTIONS,
    OPTION_LABELS,
    CACHE_DIR,
    LOG_LEVEL,
    LOG_FORMAT
)
from utils import show_exif, crop_image, extract_coordinates, cleanup_cache

# Configure logging
logger.remove()
logger.add(
    "logs/bot.log",
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    rotation="1 day",
    retention="7 days"
)
logger.add(
    lambda msg: print(msg, end=""),
    level=LOG_LEVEL,
    format=LOG_FORMAT
)

# Initialize bot
bot = telebot.TeleBot(API_TOKEN)


def is_valid_image(mime_type: str) -> bool:
    """Check if the MIME type is a supported image format."""
    return mime_type in {"image/jpeg", "image/png", "image/webp"}


def download_file(file_info: telebot.types.File, file_name: str) -> Optional[Path]:
    """Download a file from Telegram to the cache directory.
    
    Args:
        file_info: Telegram file object.
        file_name: Name to save the file as.
        
    Returns:
        Path to the downloaded file, or None if download failed.
    """
    try:
        file_path = CACHE_DIR / file_name
        bot.download_file(file_info.file_path, str(file_path))
        return file_path
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return None


@bot.message_handler(content_types=["document"])
def image_handler(message: Message):
    """Handle incoming document messages (images)."""
    logger.info(f"Received message from {message.from_user.username or message.from_user.id}")
    
    # Validate chat type
    if message.chat.type != "private":
        return
    
    # Validate file exists
    if not hasattr(message, 'document') or not message.document:
        return
    
    # Check MIME type
    mime_type = message.document.mime_type
    if not is_valid_image(mime_type):
        logger.warning(f"Unsupported MIME type: {mime_type}")
        return
    
    # Get file info
    try:
        file_info = bot.get_file(message.document.file_id)
    except Exception as e:
        logger.error(f"Failed to get file info: {e}")
        return
    
    # Generate safe filename
    original_name = Path(message.document.file_name).stem
    safe_name = f"{original_name}_{message.document.file_id}.jpg"
    
    # Download file
    file_path = download_file(file_info, safe_name)
    if not file_path:
        bot.reply_to(message, "Failed to download image. Please try again.")
        return
    
    # Send typing action
    bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Create keyboard with options
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for option_key, label in OPTION_LABELS.items():
        callback_data = f"{file_path} {option_key}"
        button = InlineKeyboardButton(text=label, callback_data=callback_data)
        buttons.append(button)
    
    keyboard.add(*buttons)
    
    bot.reply_to(
        message,
        text="Выберите действие:",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: any(call.data.endswith(opt) for opt in BOT_OPTIONS))
def handle_callback(call: CallbackQuery):
    """Handle callback queries from inline buttons."""
    parts = call.data.rsplit(' ', 1)
    if len(parts) != 2:
        bot.answer_callback_query(call.id, text="Invalid request", show_alert=True)
        return
    
    file_path_str, func = parts
    file_path = Path(file_path_str)
    
    # Validate file exists
    if not file_path.exists():
        bot.answer_callback_query(
            call.id,
            text="File not found. Please send the image again.",
            show_alert=True
        )
        return
    
    try:
        if func == 'exif':
            exif_text = show_exif(str(file_path))
            logger.debug(f"EXIF data extracted: {exif_text[:100]}...")
            bot.answer_callback_query(
                callback_query_id=call.id,
                text=exif_text,
                show_alert=True
            )
        
        elif func == 'cropx2':
            logger.info(f"Cropping image: {file_path}")
            cropped_path = crop_image(str(file_path), scale_factor=2)
            
            with open(cropped_path, 'rb') as f:
                bot.send_document(
                    chat_id=call.message.chat.id,
                    data=f,
                    caption="Cropped image"
                )
            
            # Clean up cropped file after sending
            try:
                Path(cropped_path).unlink()
            except OSError:
                pass
            
            bot.answer_callback_query(call.id, text="Image cropped successfully")
        
        elif func == 'score':
            # TODO: Implement image scoring
            bot.answer_callback_query(
                call.id,
                text="Image scoring feature coming soon!",
                show_alert=False
            )
            logger.info("Score calculation requested (not implemented)")
        
        elif func == 'geo':
            try:
                lat, lon = extract_coordinates(str(file_path))
                logger.debug(f"Coordinates extracted: {lat}, {lon}")
                
                # Send location
                bot.send_location(
                    chat_id=call.message.chat.id,
                    latitude=lat,
                    longitude=lon
                )
                
                bot.answer_callback_query(
                    call.id,
                    text=f"Location: {lat:.6f}, {lon:.6f}",
                    show_alert=False
                )
            except KeyError as e:
                logger.warning(f"No GPS data in image: {e}")
                bot.answer_callback_query(
                    call.id,
                    text="No GPS coordinates found in this image",
                    show_alert=False
                )
            except Exception as e:
                logger.error(f"Error extracting GPS: {e}")
                bot.answer_callback_query(
                    call.id,
                    text="Failed to extract location data",
                    show_alert=False
                )
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        bot.answer_callback_query(
            call.id,
            text="File not found. Please send the image again.",
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        bot.answer_callback_query(
            call.id,
            text="An error occurred. Please try again.",
            show_alert=True
        )


@bot.message_handler(commands=["clean"])
def cleanup_command(message: Message):
    """Clean up old cached files."""
    logger.info(f"Cleanup requested by user {message.from_user.username or message.from_user.id}")
    
    try:
        removed_count = cleanup_cache(str(CACHE_DIR), max_age_hours=24)
        response = f"Cleaned up {removed_count} old file(s)."
        logger.info(f"Cleanup complete: {removed_count} files removed")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        response = "Cleanup failed. Please check logs."
    
    bot.reply_to(message, text=response)


@bot.message_handler(commands=["start", "help"])
def help_command(message: Message):
    """Send help message to user."""
    help_text = (
        "📸 Image Processing Bot\n\n"
        "Send me an image and I'll offer you several options:\n"
        "• Show EXIF - View camera and photo metadata\n"
        "• Crop photo x2 - Crop the center portion of the image\n"
        "• Score - Image quality assessment (coming soon)\n"
        "• Show on map - Display GPS location if available\n\n"
        "Commands:\n"
        "/clean - Remove old cached files\n"
        "/help - Show this help message"
    )
    bot.reply_to(message, text=help_text)


def main():
    """Main entry point for the bot."""
    logger.info("Starting Telegram image bot...")
    logger.info(f"Cache directory: {CACHE_DIR}")
    
    # Ensure cache directory exists
    CACHE_DIR.mkdir(exist_ok=True)
    
    # Start polling
    try:
        bot.polling(none_stop=True, interval=1, timeout=60)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()
