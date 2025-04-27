import os
import zipfile
from PIL import Image
import io
import shutil
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing


class CBZCompressor:
    def __init__(self, quality=80):
        self.quality = quality
        # Use number of CPU cores for parallel processing
        self.max_workers = max(1, multiprocessing.cpu_count() - 1)

    def compress_image(self, file_path, rel_path):
        """Compress a single image and return the compressed data"""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Compress image using WebP with optimized settings
                img_byte_arr = io.BytesIO()
                img.save(
                    img_byte_arr,
                    format="WEBP",
                    quality=self.quality,
                    method=6,  # Highest compression method for maximum quality
                    lossless=False,
                    exact=False,  # Faster encoding
                )
                img_byte_arr.seek(0)
                return rel_path, img_byte_arr.read()
        except Exception as e:
            print(f"Error compressing {file_path}: {e}")
            return None

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

            # Get list of image files
            image_files = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith((".png", ".jpg", ".jpeg")):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, temp_dir)
                        rel_path = os.path.splitext(rel_path)[0] + ".webp"
                        image_files.append((file_path, rel_path))

            total_images = len(image_files)
            processed_images = 0
            start_time = time.time()

            # Create new CBZ file
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_out:
                # Process images in parallel
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all compression tasks
                    future_to_file = {
                        executor.submit(
                            self.compress_image, file_path, rel_path
                        ): file_path
                        for file_path, rel_path in image_files
                    }

                    # Process completed tasks
                    for future in as_completed(future_to_file):
                        file_path = future_to_file[future]
                        try:
                            result = future.result()
                            if result:
                                rel_path, compressed_data = result
                                zip_out.writestr(rel_path, compressed_data)
                                processed_images += 1
                                elapsed_time = time.time() - start_time
                                speed = (
                                    processed_images / elapsed_time
                                    if elapsed_time > 0
                                    else 0
                                )
                                yield total_images, processed_images, os.path.basename(
                                    file_path
                                ), speed
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")

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
