from fs_tools import list_files, read_file, search_in_file, write_file


def list_resume_files(folder: str = "resumes"):
    all_files = []
    for extension in (".pdf", ".txt", ".docx"):
        all_files.extend(list_files(folder, extension=extension))
    return sorted(all_files, key=lambda item: item["name"].lower())


def read_all_resumes(folder: str = "resumes"):
    results = []
    for item in list_resume_files(folder):
        result = read_file(item["path"])
        results.append({"file": item["name"], "status": result.get("status"), "content": result.get("content", "")})
    return results


def find_resumes_with_keyword(keyword: str = "python", folder: str = "resumes"):
    matches = []
    for file in list_resume_files(folder):
        result = search_in_file(file["path"], keyword)
        if result.get("match_count", 0) > 0:
            matches.append({
                "file": file["name"],
                "matches": result.get("matches", []),
            })
    return matches


def create_summary_file(summary_path: str = "output/resume_summary.txt"):
    resumes = read_all_resumes()
    summary_lines = ["Resume Summary\n"]
    for resume in resumes:
        summary_lines.append(f"- {resume['file']}: {'found' if resume['content'] else 'missing content'}")

    summary_text = "\n".join(summary_lines)
    write_file(summary_path, summary_text)
    return {"status": "success", "filepath": summary_path, "content": summary_text}


if __name__ == "__main__":
    resumes = read_all_resumes()
    print("All resumes:")
    for resume in resumes:
        print(f"- {resume['file']}: {resume['status']}")

    python_matches = find_resumes_with_keyword("python")
    print("\nPython matches:")
    for match in python_matches:
        print(f"- {match['file']} ({len(match['matches'])} match(es))")

    summary = create_summary_file()
    print(f"\nSummary created: {summary['filepath']}")
