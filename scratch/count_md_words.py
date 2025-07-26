import os
import sys
import re

def count_words_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        words = re.findall(r'\b\w+\b', text)
        return len(words)

def count_words_in_markdown_files(directory):
    total_words = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    total_words += count_words_in_file(filepath)
    return total_words

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python count_md_words.py <directory>")
        sys.exit(1)
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        sys.exit(1)
    total_words = count_words_in_markdown_files(directory)
    total_tokens = int(1.33 * total_words)
    print(f"Total number of words in markdown files: {total_words}")
    print(f"Estimated number of tokens: {total_tokens}") 