import json
import os
import re
from typing import Any, Dict, List

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

from fs_tools import list_files, read_file, search_in_file, write_file

if load_dotenv is not None:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a local document file and return structured metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute or relative path to the document file."}
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory and optionally filter by extension.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan."},
                    "extension": {"type": "string", "description": "Optional extension like .pdf or .txt."},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a path, creating directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Target file path."},
                    "content": {"type": "string", "description": "Text content to write."},
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search for a keyword in a file and return relevant surrounding text context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the document to search."},
                    "keyword": {"type": "string", "description": "Keyword to find in case-insensitive mode."},
                },
                "required": ["filepath", "keyword"],
            },
        },
    },
]


def execute_tool(tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    tool_map = {
        "read_file": read_file,
        "list_files": list_files,
        "write_file": write_file,
        "search_in_file": search_in_file,
    }

    if tool_name not in tool_map:
        return {"status": "error", "error": f"Unsupported tool: {tool_name}"}

    return tool_map[tool_name](**kwargs)


def analyze_resume_folder_for_keyword(keyword: str, folder: str = "resumes") -> List[Dict[str, Any]]:
    """Return resume files whose content matches the given keyword."""
    if not keyword:
        return []

    collection = []
    for ext in (".pdf", ".txt", ".docx"):
        collection.extend(list_files(folder, extension=ext))

    matches = []
    for file in sorted(collection, key=lambda item: item["name"].lower()):
        result = search_in_file(file["path"], keyword)
        if result.get("match_count", 0) > 0:
            matches.append({
                "file": file["name"],
                "path": file["path"],
                "match_count": result["match_count"],
                "matches": result.get("matches", []),
            })
    return matches


def extract_keyword_from_query(user_query: str) -> str:
    query = user_query.strip()
    patterns = [
        r"mentioning\s+(.+?)\s+experience",
        r"find\s+(?:files|resumes|candidates)?\s*(?:mentioning|with|for)\s+(.+?)(?:\.|$)",
        r"search(?:ing)?\s+(?:for|with)\s+(.+?)(?:\.|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            keyword = match.group(1).strip().strip('"\'')
            if keyword:
                return keyword
    return ""


def run_llm_assistant(user_query: str, api_key: str = None, model: str = "gpt-4o-mini") -> str:
    """
    Use an LLM to reason over the user query and call the file tools when needed.
    Resume queries are checked directly against the resume folder before the model call so
    the assistant can actually search file contents and avoid generic PDF refusals.
    """
    keyword = extract_keyword_from_query(user_query)
    if "resume" in user_query.lower() and keyword:
        matches = analyze_resume_folder_for_keyword(keyword)
        if matches:
            files = ", ".join(item["file"] for item in matches)
            return (
                f"I found {len(matches)} resume(s) mentioning '{keyword}': {files}. "
                f"The matching files are: {files}."
            )
        return f"I checked the resumes in the 'resumes' folder and did not find any mention of '{keyword}'."

    if OpenAI is None:
        return (
            "The openai package is not installed. Install dependencies with: pip install -r requirements.txt. "
            "Then set OPENAI_API_KEY before calling run_llm_assistant()."
        )

    resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_api_key:
        return (
            "No OpenAI API key found. Create a .env file in the project root with OPENAI_API_KEY=your_key_here, "
            "or pass api_key=... to run_llm_assistant()."
        )

    client = OpenAI(api_key=resolved_api_key)
    messages = [{"role": "user", "content": user_query}]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message
    tool_calls = assistant_message.tool_calls or []

    if not tool_calls:
        keyword = extract_keyword_from_query(user_query)
        if "resume" in user_query.lower() and keyword:
            matches = analyze_resume_folder_for_keyword(keyword)
            if matches:
                files = ", ".join(item["file"] for item in matches)
                return (
                    f"I found {len(matches)} resume(s) mentioning '{keyword}': {files}. "
                    f"The matching files are: {files}."
                )
            return f"I checked the resumes in the 'resumes' folder and did not find any mention of '{keyword}'."
        return assistant_message.content or "I could not generate a response."

    messages.append({
        "role": "assistant",
        "content": assistant_message.content,
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in tool_calls
        ],
    })

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        result = execute_tool(function_name, **arguments)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False),
        })

    final_response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    return final_response.choices[0].message.content or "No final response was returned by the model."


if __name__ == "__main__":
    sample_query = "Read all resumes in the resumes folder and find those mentioning Python experience."
    print(run_llm_assistant(sample_query))
