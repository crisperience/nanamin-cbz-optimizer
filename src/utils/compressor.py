import os
import zipfile
from PIL import Image
import io
import shutil
from pathlib import Path
import time


class CBZCompressor:
    def __init__(self, quality=80):
        self.quality = quality

    def compress_file(self, input_path, output_path):
        """
        Compress a CBZ file while maintaining image quality
        Returns: tuple of (total_images, processed_images, current_file, speed)
        """
        # Create temporary directory for processing
        temp_dir = Path(output_path).parent / "temp_processing"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Extract CBZ to temp directory
            with zipfile.ZipFile(input_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Count total images first
            total_images = 0
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith((".png", ".jpg", ".jpeg")):
                        total_images += 1

            # Create new CBZ file
            processed_images = 0
            start_time = time.time()
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_out:
                # Process each image in the CBZ
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith((".png", ".jpg", ".jpeg")):
                            file_path = os.path.join(root, file)
                            # Change extension to .webp while keeping the same base name
                            rel_path = os.path.relpath(file_path, temp_dir)
                            rel_path = os.path.splitext(rel_path)[0] + ".webp"
                            current_file = file

                            # Open and compress image
                            with Image.open(file_path) as img:
                                # Convert to RGB if necessary
                                if img.mode in ("RGBA", "LA"):
                                    background = Image.new(
                                        "RGB", img.size, (255, 255, 255)
                                    )
                                    background.paste(img, mask=img.split()[-1])
                                    img = background
                                elif img.mode != "RGB":
                                    img = img.convert("RGB")

                                # Compress image using WebP
                                img_byte_arr = io.BytesIO()
                                img.save(
                                    img_byte_arr,
                                    format="WEBP",
                                    quality=self.quality,
                                    method=6,  # Highest compression method
                                )
                                img_byte_arr.seek(0)

                                # Add compressed image to new CBZ
                                zip_out.writestr(rel_path, img_byte_arr.read())

                            processed_images += 1
                            elapsed_time = time.time() - start_time
                            speed = (
                                processed_images / elapsed_time
                                if elapsed_time > 0
                                else 0
                            )
                            yield total_images, processed_images, current_file, speed

        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def get_file_size(self, file_path):
        """Get file size in MB"""
        return os.path.getsize(file_path) / (1024 * 1024)

    def calculate_savings(self, original_size, compressed_size):
        """Calculate space savings percentage"""
        if original_size == 0:
            return 0
        return ((original_size - compressed_size) / original_size) * 100
