import sys

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
    # 映射文件扩展名到语言
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
        return

    total_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_block_comment = False

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

    print(f"Total lines: {total_lines}")
    print(f"Comment lines: {comment_lines}")
    print(f"Blank lines: {blank_lines}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_lines.py <filename>")
    else:
        registry = CommentRulesRegistry()
        registry.register("python", "#", '"""', '"""')
        registry.register("javascript", "//", "/*", "*/")
        registry.register("go", "//", "/*", "*/")
        registry.register("cpp", "//", "/*", "*/")
        registry.register("java", "//", "/*", "*/")

        filename = sys.argv[1]
        language = detect_language(filename)
        if not language:
            print("Unsupported file type")
        else:
            count_lines(filename, language, registry)
