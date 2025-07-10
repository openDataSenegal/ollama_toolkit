# Documentation — `ollama-toolkit`

**`ollama-toolkit`** is a Python CLI utility for **exporting** and **importing** Ollama models (`.tar.gz`) to streamline **backups**, **sharing**, or **migration** across machines.

> Designed for developers, researchers, and ML teams looking to package and deploy local Ollama models with ease.

---

## What’s It For?

* Backup a custom model locally with all its layers
* Transfer models to another environment without re-downloading
* Archive models for offline or long-term use
* Recreate a complete Ollama model from a `.tar.gz` archive

---

## Key Features

* Export a model with all necessary files
* Generate a self-contained `.tar.gz` archive
* Automatically recreate the model using `ollama create`
* Built-in progress bar via `tqdm`
* Compatible with any locally installed Ollama model

---

## Installation

### Requirements

* Python ≥ 3.7
* [Ollama](https://ollama.com/download) installed and accessible from your terminal
* `tqdm` (installed automatically)

### Install from PyPI or Source

Install via PyPI:

```bash
pip install ollama-panongbene
```

Or install from source:

```bash
git clone https://github.com/openDataSenegal/ollama_toolkit.git
cd ollama-toolkit
pip install .
```

Once installed, two global CLI commands are available:

```bash
ollama-export <model_name>
ollama-import <archive.tar.gz> <model_name>
```

---

## CLI Commands

### `ollama-export`

Exports an Ollama model to a `.tar.gz` archive including the `Modelfile` and all binary layers.

```bash
ollama-export <model_name> [-o OUTPUT] [-v]
```

#### Arguments

| Argument        | Description                                            |
| --------------- | ------------------------------------------------------ |
| `model_name`    | Name of the model to export (e.g., `phi:latest`)       |
| `-o, --output`  | Optional output filename for the archive (`.tar.gz`)   |
| `-v, --verbose` | Enable detailed logs (e.g., Modelfile content, layers) |

#### Example

```bash
ollama-export llama3:instruct -o llama3_instruct.tar.gz -v
```

---

### `ollama-import`

Imports a model from a `.tar.gz` archive and recreates it via `ollama create`.

```bash
ollama-import <archive.tar.gz> <model_name>
```

#### Arguments

| Argument         | Description                                              |
| ---------------- | -------------------------------------------------------- |
| `archive.tar.gz` | Path to the archive containing model files               |
| `model_name`     | Name to assign to the model (used during model creation) |

#### Example

```bash
ollama-import phi_latest.tar.gz phi:latest
```

---

## Archive Structure

Each export archive includes:

```
phi_latest.tar.gz
├── Modelfile
├── layer0.bin
├── layer1.bin
├── ...
```

This structure allows full offline restoration.

---

## Use Cases

* Seamless model transfers across machines or teams
* Use Ollama in offline or air-gapped environments
* Archive models for reproducibility and long-term access
* Avoid redundant large downloads
* Share custom `Modelfile` setups and binary layers

---

### Can I Store Archives on External Drives or Git?

Yes — archives are fully portable.
You can version them using Git LFS or store them on external media for future reuse.

---

### Are Custom or Private Models Supported?

Absolutely.
As long as the model is installed locally in Ollama, you can export and re-import it — including custom layers and any `Modelfile` configuration.

---

## Author

* Developed and maintained by [Panongbene Sawadogo](https://panongbene.com)
* Contact: [amet1900@gmail.com](mailto:amet1900@gmail.com)

---

## License

**MIT License** — Free for commercial and educational use.

---