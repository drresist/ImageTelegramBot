# Telegram Image Bot

A Telegram bot for processing images with EXIF data extraction, cropping, and GPS location features.

## Table of Contents

1.  [Features](#features)
2.  [Quick Start](#quick-start)
3.  [Docker Deployment](#docker-deployment)
4.  [Usage](#usage)
5.  [Configuration](#configuration)
6.  [Development](#development)
7.  [Security Notes](#security-notes)


<a id="features"></a>

## Features

- **EXIF Data Extraction**: View camera settings and photo metadata (model, ISO, exposure, aperture, etc.)
- **Image Cropping**: Crop the center portion of images to 50% size
- **GPS Location**: Extract and display GPS coordinates from images on a map
- **Automatic Cache Cleanup**: Remove old cached files automatically (older than 24 hours)
- **Secure by Default**: Runs as non-root user in Docker container
- **Proper Error Handling**: Graceful handling of missing files and invalid data
- **Structured Logging**: Rotating log files with configurable levels


<a id="quick-start"></a>

## Quick Start

### Prerequisites

- Python 3.9+
- Telegram Bot API token (get from [@BotFather](https://t.me/BotFather))

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd image-bot
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set environment variable:
    ```bash
    export IMAGE_BOT_API="your-telegram-bot-token"
    ```

4.  Run the bot:
    ```bash
    python main.py
    ```


<a id="docker-deployment"></a>

## Docker Deployment

### Build and Run

```bash
docker build -t image-bot .
docker run -d \
  -e IMAGE_BOT_API="your-telegram-bot-token" \
  --name image-bot \
  image-bot
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - IMAGE_BOT_API=${IMAGE_BOT_API}
      - LOG_LEVEL=INFO
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
```

Run with:
```bash
docker-compose up -d
```


<a id="usage"></a>

## Usage

Send an image to the bot in a **private chat**, and it will offer you several options:

- **Show EXIF** - View camera and photo metadata
- **Crop photo x2** - Crop the center portion of the image
- **Score** - Image quality assessment (coming soon)
- **Show on map** - Display GPS location if available

### Commands

| Command | Description |
|---------|-------------|
| `/start` or `/help` | Show help message |
| `/clean` | Remove old cached files (older than 24 hours) |


<a id="configuration"></a>

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `IMAGE_BOT_API` | Telegram bot API token | - | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |

### Project Structure

```
image-bot/
├── main.py          # Bot entry point and handlers
├── utils.py         # Image processing utilities
├── config.py        # Configuration and constants
├── requirements.txt # Python dependencies
├── Dockerfile       # Docker build configuration
├── .dockerignore    # Docker ignore rules
├── cache/           # Temporary file storage (auto-created)
├── logs/            # Log files (auto-created)
└── tests/           # Unit tests
```


<a id="development"></a>

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

The project follows PEP 8 guidelines with type hints throughout the codebase.


<a id="security-notes"></a>

## Security Notes

- The bot runs as a **non-root user** in Docker
- API tokens should be passed via **environment variables only**
- Cache files are **automatically cleaned up** (files older than 24 hours)
- Only **private chats** are supported for image processing
- File paths are sanitized to prevent directory traversal


## Troubleshooting

### Bot doesn't respond to images

- Ensure `IMAGE_BOT_API` environment variable is set correctly
- Check that you're sending images as documents, not compressed photos
- Verify the bot is added to your contacts and privacy mode is disabled

### GPS coordinates not showing

- Not all images contain GPS data
- Check if the original image has EXIF GPS tags
- Some social media platforms strip GPS data

### Logs location

Logs are stored in `logs/bot.log` with daily rotation and 7-day retention.


## License

MIT License


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

