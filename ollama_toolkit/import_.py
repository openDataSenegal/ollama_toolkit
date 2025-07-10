#!/usr/bin/env python3
"""
Ollama Model Importer

This script allows you to import a previously exported Ollama model stored in a `.tar.gz` archive.
It will extract the archive and recreate the model locally using `ollama create`.

Usage:
    python ollama_importer.py path/to/file.tar.gz model_name

If `model_name` is not provided, the script will attempt to infer it from the archive file name
(e.g. `phi_latest.tar.gz` → `phi:latest`).
"""

import tarfile
import argparse
import tempfile
import subprocess
import os
import sys
from pathlib import Path

def extract_tar_gz(archive_path: Path, extract_to: Path):
    """
    Extracts the `.tar.gz` archive to a specified directory.

    Args:
        archive_path (Path): Path to the .tar.gz archive.
        extract_to (Path): Destination directory to extract the content.
    """
    print(f"📦 Décompression de {archive_path} vers {extract_to}...")
    try:
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(path=extract_to)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la décompression : {e}")

def run_ollama_create(model_name: str, model_dir: Path):
    """
    Runs `ollama create` in the directory containing the Modelfile and layers.

    Args:
        model_name (str): Name to assign to the model (e.g. llama2:7b).
        model_dir (Path): Directory that contains the Modelfile and model layers.

    Raises:
        FileNotFoundError: If the Modelfile is not found.
        RuntimeError: If the `ollama` command fails or is not available.
    """
    modelfile_path = model_dir / 'Modelfile'
    if not modelfile_path.exists():
        raise FileNotFoundError("Modelfile not found in the extracted archive.")

    print(f"🚀 Creating model '{model_name}' avec Ollama...")
    try:
        subprocess.run(
            ['ollama', 'create', model_name, '-f', str(modelfile_path)],
            cwd=str(model_dir),
            check=True
        )
    except FileNotFoundError:
        raise RuntimeError("❌ The 'ollama' command was not found. Make sure Ollama is installed and available in your PATH.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"❌  Failed to create model : {e.stderr or e}")

def main():
    parser = argparse.ArgumentParser(
        description='Import an Ollama model from a .tar.gz archive and recreate it locally.',
        epilog="Example: python ollama_importer.py llama2_7b.tar.gz llama2:7b"
    )
    parser.add_argument('archive_path', type=str, help='Path to the exported .tar.gz archive')
    parser.add_argument('model_name', type=str, nargs='?', default='', help='Name of the model to create (e.g. llama2:7b)')

    args = parser.parse_args()

    archive_path = Path(args.archive_path)
    tags_model = args.archive_path.split("_")

    # Infer model name if not provided
    if(len(args.model_name)<2):
        if(len(tags_model)>1):
            args.model_name = tags_model[0]+":"+tags_model[-1].split(".")[0]
    
    if not archive_path.exists():
        print(f"❌ File not found : {archive_path}")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        extract_path = Path(tmpdir)
        try:
            extract_tar_gz(archive_path, extract_path)
            run_ollama_create(args.model_name, extract_path)
            print(f"✅ Modèle '{args.model_name}' importé avec succès !")
        except Exception as e:
            print(f"❌ Error : {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()