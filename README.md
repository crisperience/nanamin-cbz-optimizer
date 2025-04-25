# Nanamin - CBZ Optimizer

A modern and efficient CBZ compression tool to reduce the size of your manga and comics, saving valuable storage space.

## Features

- Compress CBZ files with adjustable quality settings
- Batch processing of multiple files
- Real-time progress tracking
- Preserves original file structure

## Requirements

- macOS 10.13 or later
- Python 3.11 or later

## Installation

1. Download the latest release from the [Releases](https://github.com/crisperience/nanamin-cbz-compressor/releases) page
2. Open the DMG file
3. Drag Nanamin to your Applications folder

## Usage

1. Launch Nanamin from your Applications folder
2. Click "Select CBZ Files" to choose files to compress
3. Select an output directory
4. Adjust the quality slider if needed (default: 85)
5. Click "Compress" to start the process

## Development

To build from source:

```bash
# Clone the repository
git clone https://github.com/crisperience/nanamin-cbz-compressor.git

# Install dependencies
pip install -r requirements.txt

# Build the application
pyinstaller manga_compressor.spec
```

## License

MIT License 