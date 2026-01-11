# 🖼️ Reddit Image Scraper

**Download images from Reddit without needing any API keys!**

This scraper uses Reddit’s public JSON feeds, which means no authentication is required.

## ✨ Features

- ✅ **No API required** – Uses public JSON endpoints
- ✅ **Parallel downloads** – Fast and efficient
- ✅ **Advanced filters** – By score, dimensions, NSFW
- ✅ **Multi-source support** – Reddit, Imgur, previews
- ✅ **Duplicate avoidance** – Does not re-download existing files
- ✅ **CLI and GUI interface** – Choose your preferred mode
- ✅ **Error handling** – Rate limiting, timeouts, etc.

## 📦 Installation

```bash
# No external dependencies required!
# The script uses only the Python standard library.

# Optional: For the graphical interface
pip install tk  # If not included with your Python
```

## 🚀 Usage

### Command Line Mode (CLI)

```bash
# Basic usage – downloads 25 "hot" images
python reddit_image_scraper.py wallpapers

# Download 100 images from top all-time
python reddit_image_scraper.py earthporn --sort top --time all --limit 100

# Recent images with minimum score
python reddit_image_scraper.py pics --sort new --min-score 500 --limit 50

# HD images only (1920px minimum)
python reddit_image_scraper.py wallpapers --min-width 1920 --limit 30

# Include NSFW
python reddit_image_scraper.py art --nsfw --limit 25
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `subreddit` | Subreddit name (required) | - |
| `-o, --output` | Output directory | `downloads` |
| `-l, --limit` | Number of images | `25` |
| `-s, --sort` | Sort: hot, new, top, rising | `hot` |
| `-t, --time` | Time range: hour, day, week, month, year, all | `week` |
| `--min-score` | Minimum score | `0` |
| `--min-width` | Minimum width | `0` |
| `--min-height` | Minimum height | `0` |
| `--nsfw` | Include NSFW content | `false` |
| `--no-skip` | Re-download existing files | `false` |
| `-w, --workers` | Parallel downloads | `5` |
| `-q, --quiet` | Quiet mode | `false` |

## 📁 File Structure

```
reddit_scraper/
├── reddit_image_scraper.py  # Main script (CLI)
├── reddit_scraper_gui.py    # Graphical interface
├── README.md
└── downloads/               # Default output directory
    └── wallpapers/          # One subfolder per subreddit
        ├── abc123_title.jpg
        └── def456_other.png
```

## 🔧 How It Works

The script uses Reddit’s public JSON endpoints:

```
https://www.reddit.com/r/{subreddit}/{sort}.json
```

These endpoints do not require authentication and return post data in JSON format.

### Supported Image Sources

- `i.redd.it` – Native Reddit images
- `i.imgur.com` – Direct Imgur links
- `preview.redd.it` – Reddit previews
- Images with direct extensions (.jpg, .png, .gif, .webp)
- Reddit galleries (first image only)

## ⚠️ Limitations

- **Rate limiting**: Reddit may limit requests if you make too many. The script automatically waits when rate-limited.
- **100 posts per page**: Reddit limits results to 100 per request, but the script automatically handles pagination.
- **No videos**: Only images are downloaded, not videos.
- **Partial galleries**: For Reddit galleries, only the first image is downloaded.

## 📝 Usage Examples

### Download HD wallpapers

```bash
python reddit_image_scraper.py wallpapers \
    --sort top \
    --time month \
    --min-width 1920 \
    --min-height 1080 \
    --limit 50
```

### Build an art collection

```bash
python reddit_image_scraper.py art \
    --sort top \
    --time year \
    --min-score 5000 \
    --limit 200
```

### Get today’s images

```bash
python reddit_image_scraper.py pics \
    --sort top \
    --time day \
    --limit 25
```

## 🐛 Troubleshooting

### "Rate limited"
The script automatically waits 60 seconds. You can also reduce `--workers`.

### Images not downloaded
Some images may be unavailable (deleted, private). The script continues with the next ones.

### SSL errors
The script disables SSL verification to avoid certificate issues.

## 📜 License

Feel free to use this script.

## ⚡ Tips

1. **Start small**: Test with `--limit 10` before running large downloads
2. **Use filters**: `--min-score` helps you get higher-quality content
3. **Be patient**: Respect Reddit’s limits to avoid getting blocked
4. **Check usage rights**: Images remain the property of their original authors

# Use a VPN preferably to avoid getting your account banned.
