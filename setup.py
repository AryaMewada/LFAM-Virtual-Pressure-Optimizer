"""
Setup script for py2app packaging.
"""
from setuptools import setup
import os
import glob

# Gather profile files dynamically so we don't miss any
materials = glob.glob('src/profiles/materials/*.json')
machines = glob.glob('src/profiles/machines/*.json')

APP = ['main.py']
DATA_FILES = [
    ('src/profiles/materials', materials),
    ('src/profiles/machines', machines)
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'app_icon.icns',
    'packages': ['PyQt6', 'pyqtgraph', 'numpy'],
    'includes': ['src'],
    'plist': {
        'CFBundleName': 'AMLFAMO V1',
        'CFBundleDisplayName': 'AMLFAMO V1',
        'CFBundleIdentifier': 'com.addon.amlfamo',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True
    }
}

setup(
    app=APP,
    name='AMLFAMO V1',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
