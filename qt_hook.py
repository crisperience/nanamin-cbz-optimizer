import os
import sys

if sys.platform == "darwin":
    # Set the Qt plugins path to be relative to the application bundle
    qt_plugin_path = os.path.join(
        os.path.dirname(os.path.abspath(sys.argv[0])), "..", "PlugIns"
    )
    os.environ["QT_PLUGIN_PATH"] = qt_plugin_path
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
        qt_plugin_path, "platforms"
    )
    # Set Qt style to Fusion
    os.environ["QT_STYLE_OVERRIDE"] = "fusion"
