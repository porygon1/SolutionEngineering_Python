# Project Setup

This guide describes how to set up the development environment for the project.

## Prerequisites

- Python 3.8 or higher
- pip (Python Package Manager)

## Setting up a Virtual Environment

### Windows

1. Open Command Prompt (cmd) or PowerShell
2. Navigate to the project directory:
   ```bash
   cd path/to/project
   ```
3. Create a new virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```

### Linux/macOS

1. Open Terminal
2. Navigate to the project directory:
   ```bash
   cd path/to/project
   ```
3. Create a new virtual environment:
   ```bash
   python3 -m venv venv
   ```
4. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

## Installing Dependencies

After activating the virtual environment, you can install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Verifying the Installation

To verify that everything is set up correctly:

1. Make sure the virtual environment is activated (you should see `(venv)` in your command line)
2. Run `python --version` to check the Python version
3. Run `pip list` to see installed packages

## Deactivating the Virtual Environment

When you want to end your work session:

```bash
deactivate
```