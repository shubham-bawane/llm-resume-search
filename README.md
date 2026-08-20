# Resume File Assistant

This project implements a small Python-based file assistant for resume processing. It includes file system tools for reading, listing, writing, and searching resume files, as well as an LLM integration layer for natural language queries.

## Project Goals

- Understand LLM function calling/tool use
- Implement structured file-system interfaces
- Handle resume file I/O programmatically
- Parse and search PDF/TXT/DOCX resume documents

## Project Structure

- `fs_tools.py` — file reading, listing, writing, and keyword search utilities
- `llm_file_assistant.py` — LLM integration with tool-calling support
- `demo_resume_assistant.py` — sample script to demonstrate resume scanning
- `resumes/` — sample resume files used for testing/demo
- `tests/test_fs_tools.py` — basic unit tests
- `.env` — stores your OpenAI API key
- `requirements.txt` — Python dependencies

## Setup

1. Open a terminal in the project root.
2. Create and activate a virtual environment (recommended):

   ```bash
   uv venv .venv --python 3.12
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   uv pip install -r requirements.txt
   ```

4. Add your OpenAI API key in `.env`:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Run the sample demo

```bash
uv run python demo_resume_assistant.py
```

### Run the LLM assistant

```bash
uv run python -c "from llm_file_assistant import run_llm_assistant; print(run_llm_assistant('Read all resumes in the resumes folder and find those mentioning Python experience.'))"
```

### Direct function usage

```python
from llm_file_assistant import run_llm_assistant

response = run_llm_assistant(
    "Read all resumes in the resumes folder and find those mentioning Event Coordinator experience."
)
print(response)
```

## Supported File Types

- `.txt`
- `.pdf`
- `.docx`

## Features

- Read resume text from supported files
- List files with optional extension filtering
- Write generated summaries to disk
- Search resume content by keyword with case-insensitive match support
- LLM-driven file querying through tool-calling

## Example Queries

- "Read all resumes in the resumes folder"
- "Find resumes mentioning Python experience"
- "Create a summary file for resume_john_doe.pdf"
- "Find candidates with Event Coordinator experience"

## Notes

- The project includes sample dummy resumes in the `resumes/` folder.
- Search results are case-insensitive.
- The fallback logic in `llm_file_assistant.py` ensures resume keyword searches still work reliably when a model does not invoke tools.

## Demo Video (2-3 minutes)

A short demo can be recorded by following this script:

1. Open the project folder in VS Code.
2. Show the project structure: `fs_tools.py`, `llm_file_assistant.py`, `resumes/`, and `tests/`.
3. Open the terminal and run:

   ```bash
   uv run python demo_resume_assistant.py
   ```

4. Highlight the output showing the resume files being processed and Python matches found.
5. Run the LLM query:

   ```bash
   uv run python -c "from llm_file_assistant import run_llm_assistant; print(run_llm_assistant('Read all resumes in the resumes folder and find those mentioning Event Coordinator experience.'))"
   ```

6. Point out that the assistant returns a matching resume file from the actual folder.
7. Finalize the video with a short summary of the workflow.

This gives a 2-3 minute demonstration of tool calling in action.

## Verification

The project was validated with:

```bash
uv run python -m unittest discover -s tests -q
```

This passed successfully.
