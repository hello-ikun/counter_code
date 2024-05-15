import os
import sys
from collections import defaultdict

class CommentRulesRegistry:
    def __init__(self):
        self.rules = {}

    def register(self, language, single_line, multi_line_start=None, multi_line_end=None):
        self.rules[language] = {
            "single_line": single_line,
            "multi_line_start": multi_line_start,
            "multi_line_end": multi_line_end
        }

    def get_rules(self, language):
        return self.rules.get(language)

def detect_language(filename):
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".go": "go",
        ".cpp": "cpp",
        ".h": "cpp",
        ".mod": "go",
        ".java": "java"
    }

    for ext, language in extension_map.items():
        if filename.endswith(ext):
            return language
    return None

def count_lines(filename, language, registry):
    rules = registry.get_rules(language)
    if not rules:
        print(f"No rules registered for language: {language}")
        return 0, 0, 0

    total_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_block_comment = False

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                stripped_line = line.strip()
                total_lines += 1

                if not stripped_line:
                    blank_lines += 1
                    continue

                if in_block_comment:
                    comment_lines += 1
                    if rules["multi_line_end"] and rules["multi_line_end"] in stripped_line:
                        in_block_comment = False
                    continue

                if rules["single_line"] and stripped_line.startswith(rules["single_line"]):
                    comment_lines += 1
                elif rules["multi_line_start"] and rules["multi_line_start"] in stripped_line:
                    comment_lines += 1
                    in_block_comment = True
                    if rules["multi_line_end"] and rules["multi_line_end"] in stripped_line:
                        in_block_comment = False
    except Exception as e:
        print(f"Error processing file {filename}: {e}")
        return 0, 0, 0

    return total_lines, comment_lines, blank_lines

def process_directory(directory, registry):
    language_stats = defaultdict(lambda: [0, 0, 0])

    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            language = detect_language(filepath)
            if language:
                lines, comment_lines, blank_lines = count_lines(filepath, language, registry)
                language_stats[language][0] += lines
                language_stats[language][1] += comment_lines
                language_stats[language][2] += blank_lines

    total_lines = 0
    total_comment_lines = 0
    total_blank_lines = 0

    for language, stats in language_stats.items():
        print(f"Language: {language}")
        print(f"  Total lines: {stats[0]}")
        print(f"  Comment lines: {stats[1]}")
        print(f"  Blank lines: {stats[2]}\n")
        total_lines += stats[0]
        total_comment_lines += stats[1]
        total_blank_lines += stats[2]

    print("Overall summary:")
    print(f"  Total lines: {total_lines}")
    print(f"  Comment lines: {total_comment_lines}")
    print(f"  Blank lines: {total_blank_lines}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_lines.py <filename_or_directory>")
    else:
        registry = CommentRulesRegistry()
        registry.register("python", "#", '"""', '"""')
        registry.register("javascript", "//", "/*", "*/")
        registry.register("go", "//", "/*", "*/")
        registry.register("cpp", "//", "/*", "*/")
        registry.register("java", "//", "/*", "*/")

        path = sys.argv[1]
        if os.path.isdir(path):
            process_directory(path, registry)
        else:
            language = detect_language(path)
            if not language:
                print("Unsupported file type")
            else:
                total_lines, comment_lines, blank_lines = count_lines(path, language, registry)
                print(f"Total lines: {total_lines}")
                print(f"Comment lines: {comment_lines}")
                print(f"Blank lines: {blank_lines}")
