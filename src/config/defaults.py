"""
Default configuration values for edge-detection toolkit.

These defaults are used as fallback values when configuration parameters
are not specified in user config files or environment variables.
"""

import os
from pathlib import Path


def get_default_config_path() -> Path:
    """Get default user configuration directory path."""
    config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    return Path(config_home) / 'edge-detection'


def get_default_cache_path() -> Path:
    """Get default cache directory path."""
    cache_home = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
    return Path(cache_home) / 'edge-detection'


DEFAULT_CONFIG = {
    'model': {
        'name': 'yolov8n',
        'path': None,  # Will be auto-downloaded if None
        'cache_dir': str(get_default_cache_path() / 'models'),
    },
    'device': {
        'type': 'auto',  # auto, cpu, cuda, cuda:0, mps, tpu
        'auto_detect': True,
    },
    'detection': {
        'confidence_threshold': 0.25,
        'iou_threshold': 0.45,
        'max_detections': 300,
    },
    'input': {
        'image_size': [640, 640],
        'letterbox': True,
        'normalize': True,
    },
    'output': {
        'save_dir': './output',
        'format': 'jpg',  # jpg, png
        'show_confidence': True,
        'show_labels': True,
    },
    'logging': {
        'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        'format': 'text',  # text, json
        'file': None,  # Log to file if path specified
    },
    'performance': {
        'half_precision': False,  # FP16
        'batch_size': 1,
        'workers': 4,
    },
}
