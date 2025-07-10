#!/usr/bin/env python3
"""
Ollama Model Exporter

Exports an Ollama model into a `.tar.gz` file containing the Modelfile and all necessary model layers.

Requirements:
    pip install tqdm  # Optional, for progress bar
"""

import argparse
import subprocess
import tarfile
import zipfile
import sys
import os
import io
from pathlib import Path
from typing import List

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


def get_model_file_content(model_name: str) -> str:
    """
    Retrieves the Modelfile content of the specified Ollama model.

    Args:
        model_name (str): The name of the Ollama model (e.g. llama2:7b)

    Returns:
        str: Content of the Modelfile

    Raises:
        RuntimeError: If `ollama show` fails or Ollama is not available
    """
    try:
        result = subprocess.run(
            ['ollama', 'show', model_name, '--modelfile'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to retrieve model '{model_name}': {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("Ollama is not installed or not available in PATH.")


def extract_layer_paths(model_file_content: str) -> List[str]:
    """
    Parses the Modelfile content and extracts referenced layer paths.

    Args:
        model_file_content (str): Contents of the Modelfile

    Returns:
        List[str]: A list of layer file paths
    """
    layer_paths = []
    for line in model_file_content.split('\n'):
        stripped_line = line.strip()
        if stripped_line.startswith('FROM'):
            tokens = stripped_line.split()
            if len(tokens) >= 2:
                layer_paths.append(tokens[1])
    return layer_paths


def validate_layer_paths(layer_paths: List[str]) -> List[Path]:
    """
    Validates the existence of each referenced layer.

    Args:
        layer_paths (List[str]): List of paths to validate

    Returns:
        List[Path]: List of existing layer paths
    """
    valid_paths = []
    for layer_path in layer_paths:
        path = Path(layer_path)
        if path.exists():
            valid_paths.append(path)
            print(f"✓ Layer trouvé : {path}")
        else:
            print(f"❌ Layer introuvable : {path}")
    return valid_paths


class _ProgressFileWrapper:
    """
    Wraps a file object and reports read progress via callback.
    """
    def __init__(self, file_obj, callback):
        self.file_obj = file_obj
        self.callback = callback

    def read(self, size=-1):
        data = self.file_obj.read(size)
        if data:
            self.callback(len(data))
        return data

    def __getattr__(self, name):
        return getattr(self.file_obj, name)


def create_model_tar(model_name: str, model_file_content: str, layer_paths: List[Path]) -> str:
    """
    Creates a .tar.gz archive containing the model layers and Modelfile.

    Args:
        model_name (str): Name of the model
        model_file_content (str): Modelfile content
        layer_paths (List[Path]): Validated layer paths

    Returns:
        str: Path to the generated .tar.gz archive
    """
    if not TQDM_AVAILABLE:
        return create_model_tar_simple(model_name, model_file_content, layer_paths)

    safe_model_name = model_name.replace(':', '_').replace('/', '_')
    output_tar = f"{safe_model_name}.tar.gz"

    total_size = len(model_file_content.encode('utf-8'))
    for layer_path in layer_paths:
        if layer_path.exists():
            total_size += layer_path.stat().st_size

    print(f"📦 Total size to compress : {total_size / (1024*1024):.2f} MB")

    with tarfile.open(output_tar, 'w:gz') as tar:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Creating tar.gz") as pbar:
            
            for i, layer_path in enumerate(layer_paths, 1):
                model_file_content = model_file_content.replace(str(layer_path), layer_path.name)
                pbar.set_postfix(fichier=f"Layer {i}/{len(layer_paths)}: {layer_path.name}")
                def progress_callback(chunk_size):
                    pbar.update(chunk_size)
                with open(layer_path, 'rb') as src:
                    tarinfo = tar.gettarinfo(layer_path, arcname=layer_path.name)
                    tar.addfile(tarinfo, _ProgressFileWrapper(src, progress_callback))

            modelfile_data = model_file_content.encode('utf-8')
            modelfile_info = tarfile.TarInfo(name='Modelfile')
            modelfile_info.size = len(modelfile_data)
            tar.addfile(modelfile_info, io.BytesIO(modelfile_data))
            pbar.update(len(modelfile_data))
            pbar.set_postfix(fichier="Modelfile")

    return output_tar


def create_model_tar_simple(model_name: str, model_file_content: str, layer_paths: List[Path]) -> str:
    """
    Fallback exporter using ZIP format (if `tqdm` is not available).

    Args:
        model_name (str): Model name
        model_file_content (str): Modelfile content
        layer_paths (List[Path]): Layer files to include

    Returns:
        str: Path to the generated ZIP file
    """
    safe_model_name = model_name.replace(':', '_').replace('/', '_')
    output_zip = f"{safe_model_name}.zip"

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:

        for i, layer_path in enumerate(layer_paths, 1):
            print(f"📁 Ajout du layer {i}/{len(layer_paths)}: {layer_path.name} ({layer_path.stat().st_size / (1024*1024):.2f} MB)")
            model_file_content.replace(layer_paths, layer_path.name)
            zipf.write(layer_path, arcname=layer_path.name)
            print(f"✓ Layer ajouté : {layer_path.name}")

        zipf.writestr('Modelfile', model_file_content)
        print(f"✓ Modelfile ajouté au zip")
        
    return output_zip


def main():
    parser = argparse.ArgumentParser(
        description='Export an Ollama model as a .tar.gz archive.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ollama_exporter.py llama2:7b
  python ollama_exporter.py qwen2:4b
        """
    )
    parser.add_argument('model_name', type=str, help='Ollama model name (e.g. qwen2:4b, llama2:7b)')
    parser.add_argument('-o', '--output', type=str, help='Output file name (optional)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    try:
        print(f"🔍 Retrieving info for model '{args.model_name}'...")
        model_file_content = get_model_file_content(args.model_name)

        if args.verbose:
            print(f"📄 Modelfile content:\n{model_file_content}\n")

        layer_paths = extract_layer_paths(model_file_content)
        print(f"📦 Detected {len(layer_paths)} layer(s) détecté(s)")

        valid_layer_paths = validate_layer_paths(layer_paths)

        if not valid_layer_paths:
            print("❌ No valid layers found. Make sure the model is installed locally.")
            sys.exit(1)

        print(f"📁 Creating archive...")
        output_tar = create_model_tar(args.model_name, model_file_content, valid_layer_paths)

        tar_size = Path(output_tar).stat().st_size
        print(f"✅ Export completed successfully!")
        print(f"📁 File created: {output_tar}")
        print(f"📏 Size : {tar_size / (1024*1024):.2f} MB")

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()