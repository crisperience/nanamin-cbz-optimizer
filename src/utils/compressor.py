import io
import multiprocessing
import os
import shutil
import time
import zipfile
from collections.abc import Callable, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import cast

from PIL import Image
from PIL.Image import Image as PILImage

# Constants
SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg")
WEBP_METHOD = 6  # Highest compression


class CBZCompressor:
    def __init__(self, quality: int) -> None:
        """Initialize CBZ compressor.

        Args:
            quality: Compression quality (1-100)
        """
        self.quality = quality
        self.max_workers = max(1, multiprocessing.cpu_count() - 1)

    def _convert_to_rgb(self, img: Image.Image) -> Image.Image:
        """Convert image to RGB format.

        Args:
            img: Input image

        Returns:
            RGB version of the image
        """
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            return background
        elif img.mode != "RGB":
            return img.convert("RGB")
        return img

    def validate_cbz(self, file_path: str) -> tuple[bool, str]:
        """Validate if a file is a valid CBZ file.

        Args:
            file_path: Path to the CBZ file to validate.

        Returns:
            A tuple containing:
            - bool: True if valid, False otherwise
            - str: Error message if invalid, empty string if valid
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        if not file_path.lower().endswith(".cbz"):
            return False, "File is not a CBZ file"
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                if not zf.namelist():
                    return False, "CBZ file is empty"
                return True, ""
        except zipfile.BadZipFile:
            return False, "Invalid CBZ file format"
        except Exception as e:
            return False, f"Error validating CBZ file: {e!s}"

    def compress_image(self, file_path: str, rel_path: str) -> tuple[bytes, str]:
        """Compress a single image file.

        Args:
            file_path: Path to the image file.
            rel_path: Relative path within the CBZ file.

        Returns:
            A tuple containing:
            - bytes: Compressed image data
            - str: New filename with .webp extension
        """
        with Image.open(file_path) as img:
            rgb_img = self._convert_to_rgb(img)
            output = io.BytesIO()
            rgb_img.save(
                output,
                format="WEBP",
                quality=self.quality,
                method=WEBP_METHOD,
                lossless=False,
            )
            output.seek(0)
            return output.getvalue(), f"{os.path.splitext(rel_path)[0]}.webp"

    def compress_file(
        self, input_file: str, output_file: str
    ) -> Generator[tuple[int, int, str, float], None, None]:
        """Compress a CBZ file.

        Args:
            input_file: Path to input CBZ file.
            output_file: Path to output CBZ file.

        Yields:
            A tuple containing:
            - int: Total number of images
            - int: Number of processed images
            - str: Current file being processed
            - float: Processing speed (images/second)
        """
        start_time = time.time()
        processed_images = 0
        total_images = 0

        # First pass: count images
        with zipfile.ZipFile(input_file, "r") as zip_ref:
            for file in zip_ref.namelist():
                if file.lower().endswith(SUPPORTED_FORMATS):
                    total_images += 1

        # Create temporary directory
        temp_dir = Path(output_file).parent / "temp_processing"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Extract files
            with zipfile.ZipFile(input_file, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Process images in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith(SUPPORTED_FORMATS):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, temp_dir)
                            futures.append(
                                executor.submit(
                                    self.compress_image, file_path, rel_path
                                )
                            )

                # Create new CBZ file
                with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zip_out:
                    for future in as_completed(futures):
                        if future.exception():
                            raise future.exception()
                        data, new_filename = future.result()
                        zip_out.writestr(new_filename, data)
                        processed_images += 1
                        speed = processed_images / (time.time() - start_time)
                        yield total_images, processed_images, new_filename, speed

        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def get_file_size(self, file_path: str) -> float:
        """Get file size in megabytes.

        Args:
            file_path: Path to the file.

        Returns:
            File size in megabytes.
        """
        return os.path.getsize(file_path) / (1024 * 1024)

    def calculate_savings(self, original_size: float, compressed_size: float) -> float:
        """Calculate space savings percentage.

        Args:
            original_size: Original size in megabytes.
            compressed_size: Compressed size in megabytes.

        Returns:
            Space savings percentage.
        """
        if original_size == 0:
            return 0
        return ((original_size - compressed_size) / original_size) * 100

    def process_image(self, image_data: bytes, quality: int) -> bytes:
        """Process a single image with the given quality.

        Args:
            image_data: Raw image data as bytes
            quality: JPEG quality (0-100)

        Returns:
            Processed image data as bytes
        """
        try:
            img = cast(PILImage, Image.open(io.BytesIO(image_data)))
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = cast(PILImage, background)
            elif img.mode != "RGB":
                img = cast(PILImage, img.convert("RGB"))
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            return output.getvalue()
        except Exception as e:
            raise RuntimeError(f"Error processing image: {e!s}") from e

    def process_cbz(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> None:
        """Process a CBZ file with the given quality.

        Args:
            input_path: Path to input CBZ file
            output_path: Path to output CBZ file
            progress_callback: Optional callback function for progress updates
        """
        try:
            with zipfile.ZipFile(input_path, "r") as zf:
                file_list = [
                    f
                    for f in zf.namelist()
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                ]
                total_files = len(file_list)

                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as out_zip:
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = []
                        for i, filename in enumerate(file_list, 1):
                            image_data = zf.read(filename)
                            future = executor.submit(
                                self.process_image, image_data, self.quality
                            )
                            futures.append((future, filename, i))

                        for future, filename, i in futures:
                            try:
                                processed_data = future.result()
                                out_zip.writestr(filename, processed_data)
                                if progress_callback:
                                    progress_callback(total_files, i, filename)
                            except Exception as e:
                                raise RuntimeError(
                                    f"Error processing {filename}: {e!s}"
                                ) from e

        except Exception as e:
            raise RuntimeError(f"Error processing CBZ file: {e!s}") from e

    def get_image_files(self, cbz_path: str) -> Generator[str, None, None]:
        """Get a list of image files in the CBZ archive.

        Args:
            cbz_path: Path to the CBZ file

        Yields:
            Filenames of image files in the archive
        """
        with zipfile.ZipFile(cbz_path, "r") as zf:
            for filename in zf.namelist():
                if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    yield filename
