import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QProgressBar,
    QSlider,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QToolButton,
    QStyle,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from utils.compressor import CBZCompressor
import zipfile
import shutil
import time
from pathlib import Path


class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(25)
        self.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #4C566A;
                border-radius: 5px;
                text-align: center;
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;
                border-radius: 3px;
            }
        """
        )


class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
            QPushButton:disabled {
                background-color: #3B4252;
                color: #4C566A;
            }
        """
        )
        self.setMinimumHeight(35)


class ModernGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4C566A;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ECEFF4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #88C0D0;
            }
        """
        )


class CompressionWorker(QThread):
    progress = pyqtSignal(
        int, int, int, str, float
    )  # total, processed, current_file, speed
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    aborted = pyqtSignal()

    def __init__(self, input_files, output_dir, quality):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.quality = quality
        self.compressor = CBZCompressor(quality)
        self._is_aborted = False

    def abort(self):
        self._is_aborted = True

    def run(self):
        try:
            results = {
                "total_files": len(self.input_files),
                "total_original_size": 0,
                "total_compressed_size": 0,
                "savings": 0,
                "processed_files": 0,
            }

            total_images = 0
            # First pass: count total images
            for input_file in self.input_files:
                temp_dir = Path(self.output_dir) / "temp_processing"
                temp_dir.mkdir(exist_ok=True)
                try:
                    with zipfile.ZipFile(input_file, "r") as zip_ref:
                        zip_ref.extractall(temp_dir)
                        for root, _, files in os.walk(temp_dir):
                            for file in files:
                                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                                    total_images += 1
                finally:
                    shutil.rmtree(temp_dir)

            processed_images = 0
            start_time = time.time()

            for i, input_file in enumerate(self.input_files):
                if self._is_aborted:
                    self.aborted.emit()
                    return

                # Calculate original size
                original_size = self.compressor.get_file_size(input_file)
                results["total_original_size"] += original_size

                # Create output path
                output_file = os.path.join(
                    self.output_dir, os.path.basename(input_file)
                )

                # Compress file and get progress updates
                for (
                    file_total_images,
                    file_processed_images,
                    current_file,
                    speed,
                ) in self.compressor.compress_file(input_file, output_file):
                    if self._is_aborted:
                        self.aborted.emit()
                        return

                    processed_images += 1
                    total_progress = int((processed_images / total_images) * 100)
                    self.progress.emit(
                        total_images, processed_images, i + 1, current_file, speed
                    )

                # Calculate compressed size
                compressed_size = self.compressor.get_file_size(output_file)
                results["total_compressed_size"] += compressed_size
                results["processed_files"] += 1

            # Calculate total savings
            results["savings"] = self.compressor.calculate_savings(
                results["total_original_size"], results["total_compressed_size"]
            )

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nanamin - CBZ Optimizer")
        self.setMinimumSize(900, 700)

        # Set window icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon not found at {icon_path}")

        # Set application style
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #2E3440;
            }
            QLabel {
                color: #ECEFF4;
                font-size: 12px;
            }
            QSpinBox, QSlider {
                color: #ECEFF4;
                background-color: #3B4252;
                border: 1px solid #4C566A;
                border-radius: 3px;
                padding: 2px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #4C566A;
                height: 8px;
                background: #3B4252;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #88C0D0;
                border: 1px solid #4C566A;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QMessageBox {
                background-color: #2E3440;
            }
            QMessageBox QLabel {
                color: #ECEFF4;
            }
            QMessageBox QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #81A1C1;
            }
        """
        )

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # File selection group
        file_group = ModernGroupBox("Files")
        file_layout = QVBoxLayout()
        file_layout.setSpacing(10)

        # Input files
        input_layout = QHBoxLayout()
        self.input_label = QLabel("No files selected")
        input_button = ModernButton("Select CBZ Files")
        input_button.clicked.connect(self.select_input_files)
        input_button.setToolTip("Select one or more CBZ files to compress")
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(input_button)
        file_layout.addLayout(input_layout)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_label = QLabel("No output directory selected")
        output_button = ModernButton("Select Output Directory")
        output_button.clicked.connect(self.select_output_directory)
        output_button.setToolTip("Select where to save compressed files")
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(output_button)
        file_layout.addLayout(output_layout)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Compression settings group
        settings_group = ModernGroupBox("Compression Settings")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)

        # Quality slider
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_value = QSpinBox()
        self.quality_value.setRange(1, 100)
        self.quality_value.setValue(85)
        self.quality_slider.valueChanged.connect(self.quality_value.setValue)
        self.quality_value.valueChanged.connect(self.quality_slider.setValue)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value)
        settings_layout.addLayout(quality_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Progress information
        progress_group = ModernGroupBox("Progress")
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)

        # Progress bar
        self.progress_bar = ModernProgressBar()
        progress_layout.addWidget(self.progress_bar)

        # Detailed progress labels
        self.file_progress_label = QLabel("File: 0/0")
        self.image_progress_label = QLabel("Images: 0/0")
        self.current_file_label = QLabel("Current: -")
        self.speed_label = QLabel("Speed: 0.0 images/sec")

        progress_layout.addWidget(self.file_progress_label)
        progress_layout.addWidget(self.image_progress_label)
        progress_layout.addWidget(self.current_file_label)
        progress_layout.addWidget(self.speed_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Compress button
        self.compress_button = ModernButton("Compress")
        self.compress_button.clicked.connect(self.start_compression)
        self.compress_button.setToolTip("Start compression process")
        button_layout.addWidget(self.compress_button)

        # Abort button
        self.abort_button = ModernButton("Abort")
        self.abort_button.clicked.connect(self.abort_compression)
        self.abort_button.setEnabled(False)
        self.abort_button.setToolTip("Abort current compression")
        button_layout.addWidget(self.abort_button)

        # New Batch button
        self.new_batch_button = ModernButton("New Batch")
        self.new_batch_button.clicked.connect(self.reset_for_new_batch)
        self.new_batch_button.setToolTip("Start a new batch of files")
        self.new_batch_button.setEnabled(False)
        button_layout.addWidget(self.new_batch_button)

        layout.addLayout(button_layout)

        # Initialize variables
        self.input_files = []
        self.output_dir = ""
        self.worker = None

    def select_input_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select CBZ Files", "", "CBZ Files (*.cbz);;All Files (*)"
        )
        if files:
            self.input_files = files
            self.input_label.setText(f"{len(files)} file(s) selected")

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", ""
        )
        if directory:
            self.output_dir = directory
            self.output_label.setText(directory)

    def start_compression(self):
        if not self.input_files:
            self.status_label.setText("Please select input files")
            return
        if not self.output_dir:
            self.status_label.setText("Please select output directory")
            return

        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(True)
        self.status_label.setText("Compressing...")
        self.progress_bar.setValue(0)
        self.file_progress_label.setText("File: 0/0")
        self.image_progress_label.setText("Images: 0/0")
        self.current_file_label.setText("Current: -")
        self.speed_label.setText("Speed: 0.0 images/sec")

        self.worker = CompressionWorker(
            self.input_files, self.output_dir, self.quality_value.value()
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.compression_finished)
        self.worker.error.connect(self.compression_error)
        self.worker.aborted.connect(self.compression_aborted)
        self.worker.start()

    def abort_compression(self):
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.status_label.setText("Aborting...")
            self.abort_button.setEnabled(False)

    def update_progress(
        self, total_images, processed_images, current_file_num, current_file, speed
    ):
        total_files = len(self.input_files)
        self.progress_bar.setValue(int((processed_images / total_images) * 100))
        self.file_progress_label.setText(f"File: {current_file_num}/{total_files}")
        self.image_progress_label.setText(f"Images: {processed_images}/{total_images}")
        self.current_file_label.setText(f"Current: {current_file}")
        self.speed_label.setText(f"Speed: {speed:.1f} images/sec")

    def reset_for_new_batch(self):
        """Reset the UI for a new batch of files"""
        self.input_files = []
        self.input_label.setText("No files selected")
        self.output_label.setText("No output directory selected")
        self.output_dir = ""
        self.progress_bar.setValue(0)
        self.file_progress_label.setText("File: 0/0")
        self.image_progress_label.setText("Images: 0/0")
        self.current_file_label.setText("Current: -")
        self.speed_label.setText("Speed: 0.0 images/sec")
        self.status_label.setText("Ready")
        self.compress_button.setEnabled(True)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(False)

    def compression_finished(self, results):
        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(True)
        self.status_label.setText("Compression completed")
        self.progress_bar.setValue(100)

        # Show compression results
        message = (
            f"Compression completed!\n\n"
            f"Files processed: {results['processed_files']}/{results['total_files']}\n"
            f"Original size: {results['total_original_size']:.2f} MB\n"
            f"Compressed size: {results['total_compressed_size']:.2f} MB\n"
            f"Space saved: {results['savings']:.1f}%\n\n"
            f"Click 'New Batch' to compress more files."
        )
        QMessageBox.information(self, "Compression Results", message)

    def compression_error(self, error):
        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(True)
        self.status_label.setText(f"Error: {error}")
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error}")

    def compression_aborted(self):
        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(True)
        self.status_label.setText("Compression aborted")
        QMessageBox.information(self, "Aborted", "Compression was aborted by user.")


def main():
    # Initialize necessary directories
    home = str(Path.home())
    app_data = os.path.join(home, ".nanamin")
    os.makedirs(app_data, exist_ok=True)
    os.chmod(app_data, 0o755)

    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Set application palette for Nord theme
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(46, 52, 64))  # nord0
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.Base, QColor(59, 66, 82))  # nord1
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(46, 52, 64))  # nord0
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(46, 52, 64))  # nord0
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.Button, QColor(59, 66, 82))  # nord1
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.BrightText, QColor(191, 97, 106))  # nord11
    palette.setColor(QPalette.ColorRole.Link, QColor(94, 129, 172))  # nord10
    palette.setColor(QPalette.ColorRole.Highlight, QColor(94, 129, 172))  # nord10
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(236, 239, 244))  # nord6
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
