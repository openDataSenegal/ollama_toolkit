from setuptools import setup, find_packages

setup(
    name='ollama-toolkit',
    version='0.1.0',
    description='Import/Export Ollama Models',
    author='Panongbene Sawadogo',
    author_email='amet1900@gmail.com',
    packages=find_packages(),
    install_requires=[
        'tqdm'
    ],
    entry_points={
        'console_scripts': [
            'ollama-import=cli:import_cli',
            'ollama-export=cli:export_cli',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
