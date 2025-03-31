import os

# Folders to exclude
EXCLUDE_DIRS = {
    "node_modules", ".next", ".git", "__pycache__", "venv", "env", ".venv", "migrations"
}

# File patterns to exclude
EXCLUDE_FILE_SUFFIXES = {".pyc", ".log"}
EXCLUDE_FILE_NAMES = {".env", ".DS_Store"}

def should_exclude(name, is_dir):
    if is_dir and name in EXCLUDE_DIRS:
        return True
    if not is_dir:
        if any(name.endswith(suffix) for suffix in EXCLUDE_FILE_SUFFIXES):
            return True
        if name in EXCLUDE_FILE_NAMES:
            return True
    return False

def generate_tree(path=".", prefix=""):
    tree_lines = []
    entries = sorted(os.listdir(path))
    entries = [e for e in entries if not should_exclude(e, os.path.isdir(os.path.join(path, e)))]
    
    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        is_dir = os.path.isdir(full_path)
        connector = "├── " if index < len(entries) - 1 else "└── "
        tree_lines.append(f"{prefix}{connector}{entry}")
        if is_dir:
            extension = "│   " if index < len(entries) - 1 else "    "
            tree_lines.extend(generate_tree(full_path, prefix + extension))
    return tree_lines


if __name__ == "__main__":
    tree = generate_tree(".")
    with open("code_tree.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(tree))
    print("✅ code_tree.txt generated successfully.")
