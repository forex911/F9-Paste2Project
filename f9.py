import os
import sys
from pathlib import Path

def get_level(line):
    """Count indentation level ignoring tree graphics"""
    tree_chars = "│ ├─└ "
    indent = 0
    for char in line:
        if char in tree_chars:
            indent += 1
        elif char == ' ':
            indent += 1
        else:
            break
    return indent // 4

def clean_name(line):
    """Extract clean filename/dirname"""
    return line.strip("│ ├─└ ─").rstrip("/").strip()

def create_structure(lines):
    stack = []
    paths = []
    
    for i, line in enumerate(lines):
        line = line.rstrip()
        if not line or line.isspace():
            continue
            
        level = get_level(line)
        name = clean_name(line)
        if not name:
            continue
            
        is_dir = line.rstrip().endswith('/')
        
        # Pop stack to correct level
        while len(stack) > level:
            stack.pop()
            paths.pop()
        
        # Root case
        if not stack:
            if is_dir:
                Path(name).mkdir(exist_ok=True)
                print(f"DIR:  {name}")
                stack.append(name)
                paths.append(Path(name))
            else:
                Path(name).touch()
                print(f"FILE: {name}")
            continue
        
        # Build path
        parent = paths[-1]
        path = parent / name
        
        if is_dir:
            path.mkdir(parents=True, exist_ok=True)
            print(f"DIR:  {path}")
            stack.append(name)
            paths.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            print(f"FILE: {path}")

def main():
    print("Paste structure → CTRL+Z → ENTER")
    print("-" * 40)
    lines = sys.stdin.readlines()
    create_structure(lines)
    print("-" * 40)
    print("✅ COMPLETE")

if __name__ == "__main__":
    main()
