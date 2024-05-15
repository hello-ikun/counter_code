import os
import sys
from collections import defaultdict
from tabulate import tabulate
from colorama import init, Fore, Style

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

class CounterCodeInfo:
    def __init__(self,files:list,register:CommentRulesRegistry) -> None:
        self.language_stats=defaultdict(lambda:[0,0,0])
        self.files=files
        self.read_files=[]
        self.non_read_files=[]
        self.register=register
    def run(self):
        for filename in self.files:
            if not os.path.exists(filename):
                self.non_read_files.append(filename)
                print(f"Error processing file {filename}: not exist")
            else:
                if os.path.isdir(filename):
                    self.process_directory(filename)
                else:
                    self.process_file(filename)
    def detect_language(self,filename):
        
        extension_map = {
            "py": "python",
            "js": "javascript",
            "go": "go",
            "cpp": "cpp",
            "h": "cpp",
            "mod": "go",
            "java": "java"
        }
        
        filename_split=filename.rsplit('\\')[-1].rsplit('.')[-1]
        if filename_split in extension_map:
            self.read_files.append(filename)
            return extension_map[filename_split]
        self.non_read_files.append(filename)
        return None

    def count_lines(self,filename, language):
        rules = self.register.get_rules(language)
        if not rules:
            print(f"No rules registered for language: {language}")
            return 0, 0, 0

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
           

        return total_lines, comment_lines, blank_lines

    def process_directory(self,directory):
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                language = self.detect_language(filepath)
                if language:
                    lines, comment_lines, blank_lines = self.count_lines(filepath, language)
                    self.language_stats[language][0] += lines
                    self.language_stats[language][1] += comment_lines
                    self.language_stats[language][2] += blank_lines
             

    def process_file(self,filename):
        language = self.detect_language(filename)
        if language:
            total_lines, comment_lines, blank_lines =self.count_lines(filename, language)
            self.language_stats[language][0] += total_lines
            self.language_stats[language][1] += comment_lines
            self.language_stats[language][2] += blank_lines

    def show(self):
        print(f"Files source: {self.files}")
        print(f"Total files: {len(self.read_files)+len(self.non_read_files)}")
        print(f"Processed files: {len(self.read_files)}")
        print(f"Skipped files: {len(self.non_read_files)}")
        total_lines = 0
        total_comment_lines = 0
        total_blank_lines = 0

        table_data = []
        for language, stats in self.language_stats.items():
            table_data.append([
                Fore.CYAN + language + Style.RESET_ALL, 
                Fore.GREEN + str(stats[0]) + Style.RESET_ALL, 
                Fore.YELLOW + str(stats[1]) + Style.RESET_ALL, 
                Fore.MAGENTA + str(stats[2]) + Style.RESET_ALL
            ])
            total_lines += stats[0]
            total_comment_lines += stats[1]
            total_blank_lines += stats[2]

        table_data.append([
            Fore.RED + "Total" + Style.RESET_ALL, 
            Fore.GREEN + str(total_lines) + Style.RESET_ALL, 
            Fore.YELLOW + str(total_comment_lines) + Style.RESET_ALL, 
            Fore.MAGENTA + str(total_blank_lines) + Style.RESET_ALL
        ])
        headers = [
            Fore.CYAN + "Language" + Style.RESET_ALL, 
            Fore.GREEN + "Total lines" + Style.RESET_ALL, 
            Fore.YELLOW + "Comment lines" + Style.RESET_ALL, 
            Fore.MAGENTA + "Blank lines" + Style.RESET_ALL
        ]
        print(tabulate(table_data, headers, tablefmt="grid"))

if __name__ == "__main__":
    init(autoreset=True)  # Initialize colorama
    registry = CommentRulesRegistry()
    registry.register("python", "#", '"""', '"""')
    registry.register("javascript", "//", "/*", "*/")
    registry.register("go", "//", "/*", "*/")
    registry.register("cpp", "//", "/*", "*/")
    registry.register("java", "//", "/*", "*/")

    
    if len(sys.argv) < 2:
        print("Usage: python count_lines.py <filename_or_directory>")
    else:
        
        path = sys.argv[1:]
        cci=CounterCodeInfo(path,register=registry)
        cci.run()
        cci.show()

        
