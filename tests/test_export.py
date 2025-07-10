import io
import sys
import builtins
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import ollama_toolkit.export as exporter  # adapte selon ton projet


def test_extract_layer_paths():
    content = """
    FROM /path/to/layer1
    RUN something
    FROM /another/layer2
    """
    layers = exporter.extract_layer_paths(content)
    assert layers == ['/path/to/layer1', '/another/layer2']

def test_validate_layer_paths(tmp_path):
    # Crée un fichier layer existant
    file1 = tmp_path / "layer1"
    file1.write_text("data")
    # Un chemin qui n'existe pas
    missing_path = tmp_path / "layer2"
    
    with patch("builtins.print") as mock_print:
        valid_paths = exporter.validate_layer_paths([str(file1), str(missing_path)])
    
    assert file1 in valid_paths
    assert all(isinstance(p, Path) for p in valid_paths)
    # Vérifie que print a été appelé avec le message de succès et d'erreur
    calls = [call[0][0] for call in mock_print.call_args_list]
    assert any("Layer trouvé" in c for c in calls)
    assert any("Layer introuvable" in c for c in calls)

@patch("subprocess.run")
def test_get_model_file_content_success(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="Modelfile content\n", stderr="")
    result = exporter.get_model_file_content("llama2:7b")
    assert result == "Modelfile content"

@patch("subprocess.run")
def test_get_model_file_content_fail_calledprocesserror(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="ollama show", stderr="error message")
    with pytest.raises(RuntimeError, match="Failed to retrieve model"):
        exporter.get_model_file_content("fake:model")

@patch("subprocess.run")
def test_get_model_file_content_fail_filenotfound(mock_run):
    mock_run.side_effect = FileNotFoundError()
    with pytest.raises(RuntimeError, match="Ollama is not installed"):
        exporter.get_model_file_content("llama2:7b")

def test_main_no_layers(monkeypatch):
    monkeypatch.setattr(exporter, "get_model_file_content", lambda model_name: "FROM layer1\n")
    monkeypatch.setattr(exporter, "extract_layer_paths", lambda content: ["layer1"])
    monkeypatch.setattr(exporter, "validate_layer_paths", lambda paths: [])

    monkeypatch.setattr(sys, "argv", ["ollama_exporter.py", "llama2:7b"])

    printed = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(" ".join(map(str, args))))

    with pytest.raises(SystemExit) as excinfo:
        exporter.main()
    assert excinfo.value.code == 1
    assert any("No valid layers found" in s for s in printed)

def test_main_keyboard_interrupt(monkeypatch):
    monkeypatch.setattr(exporter, "get_model_file_content", lambda model_name: (_ for _ in ()).throw(KeyboardInterrupt))
    monkeypatch.setattr(sys, "argv", ["ollama_exporter.py", "llama2:7b"])

    printed = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(" ".join(map(str, args))))

    with pytest.raises(SystemExit) as excinfo:
        exporter.main()
    assert excinfo.value.code == 1
    assert any("Operation cancelled by user" in s for s in printed)
