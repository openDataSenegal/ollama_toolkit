import io
import sys
import pytest
import builtins
import unittest
import tempfile
import argparse
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Importer les fonctions du script
import ollama_toolkit.import_ as ollama_importer  # Remplacez par le vrai nom du module si différent

class TestOllamaImporter(unittest.TestCase):

    @patch("tarfile.open")
    def test_extract_tar_gz_success(self, mock_tarfile_open):
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        archive_path = Path("/fake/path/model.tar.gz")
        extract_to = Path("/fake/extract/dir")

        ollama_importer.extract_tar_gz(archive_path, extract_to)
        mock_tar.extractall.assert_called_once_with(path=extract_to)
        mock_tarfile_open.assert_called_once_with(archive_path, 'r:gz')

    @patch("tarfile.open", side_effect=Exception("corrupted archive"))
    def test_extract_tar_gz_failure(self, mock_tarfile_open):
        with self.assertRaises(RuntimeError) as context:
            ollama_importer.extract_tar_gz(Path("/fake/path"), Path("/fake/extract"))
        self.assertIn("Erreur lors de la décompression", str(context.exception))

    @patch("pathlib.Path.exists", return_value=True)
    @patch("subprocess.run")
    def test_run_ollama_create_success(self, mock_subprocess_run, mock_exists):
        model_dir = Path("/fake/extract")
        model_name = "llama2:7b"
        ollama_importer.run_ollama_create(model_name, model_dir)
        mock_subprocess_run.assert_called_once_with(
            ['ollama', 'create', model_name, '-f', str(model_dir / 'Modelfile')],
            cwd=str(model_dir),
            check=True
        )

    @patch("pathlib.Path.exists", return_value=False)
    def test_run_ollama_create_modelfile_missing(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            ollama_importer.run_ollama_create("model:name", Path("/fake/dir"))

    @patch("pathlib.Path.exists", return_value=True)
    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_run_ollama_create_ollama_missing(self, mock_subprocess_run, mock_exists):
        with self.assertRaises(RuntimeError) as context:
            ollama_importer.run_ollama_create("model:name", Path("/fake/dir"))
        self.assertIn("The 'ollama' command was not found", str(context.exception))

    @patch("pathlib.Path.exists", return_value=True)
    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ['ollama']))
    def test_run_ollama_create_subprocess_fail(self, mock_subprocess_run, mock_exists):
        with self.assertRaises(RuntimeError) as context:
            ollama_importer.run_ollama_create("model:name", Path("/fake/dir"))
        self.assertIn("Failed to create model", str(context.exception))

    @patch("ollama_toolkit.import_.extract_tar_gz")
    @patch("ollama_toolkit.import_.run_ollama_create")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("tempfile.TemporaryDirectory")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_with_args(
        self, mock_print, mock_sys_exit, mock_tempdir, mock_exists,
        mock_run_ollama_create, mock_extract_tar_gz
    ):
        # Simule TemporaryDirectory context manager
        mock_tempdir.return_value.__enter__.return_value = "/tmp/fake_dir"

        testargs = ["ollama_importer.py", "model_1.tar.gz", "custom:model"]
        with patch.object(sys, 'argv', testargs):
            ollama_importer.main()

        mock_extract_tar_gz.assert_called_once()
        mock_run_ollama_create.assert_called_once_with("custom:model", Path("/tmp/fake_dir"))
        mock_print.assert_any_call("✅ Modèle 'custom:model' importé avec succès !")
        mock_sys_exit.assert_not_called()

    @patch("ollama_toolkit.import_.extract_tar_gz", side_effect=RuntimeError("boom"))
    @patch("pathlib.Path.exists", return_value=True)
    @patch("tempfile.TemporaryDirectory")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_extraction_failure(
        self, mock_print, mock_sys_exit, mock_tempdir, mock_exists, mock_extract_tar_gz
    ):
        mock_tempdir.return_value.__enter__.return_value = "/tmp/fake_dir"
        testargs = ["ollama_importer.py", "model_1.tar.gz", "model:name"]
        with patch.object(sys, 'argv', testargs):
            ollama_importer.main()

        mock_print.assert_any_call("❌ Error : boom")
        mock_sys_exit.assert_called_once_with(1)

    def test_model_name_infer_logic(self):
        # Si pas de model_name donné, inférence via nom fichier
        args = argparse.Namespace(archive_path="phi_latest.tar.gz", model_name="")
        tags_model = args.archive_path.split("_")
        if len(args.model_name) < 2:
            if len(tags_model) > 1:
                args.model_name = tags_model[0] + ":" + tags_model[-1].split(".")[0]
        self.assertEqual(args.model_name, "phi:latest")

if __name__ == "__main__":
    unittest.main()
