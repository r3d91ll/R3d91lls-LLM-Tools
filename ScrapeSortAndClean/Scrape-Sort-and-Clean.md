
# Scrape-Sort-and-Clean Script Documentation

## Overview

The Scrape-Sort-and-Clean script is designed for web scraping, processing scraped content, managing duplicate files, and cleaning content using regular expressions. It operates in several stages, including scraping web pages, identifying and handling duplicates, and cleaning Markdown files based on user-defined regex patterns.

## How to Use the Script

1. **Web Scraping**:
   - Start the script and enter the start URL, allowed domains, and the directory to save documents.
   - The script will scrape content from the given URL within the allowed domains and save the content in the specified directory.

2. **Duplicate File Management**:
   - The script identifies duplicate files in the saved documents.
   - You will be prompted to choose which file to keep, with the others being deleted.

3. **Content Cleaning**:
   - If a regex file path is provided, the script uses it to clean Markdown files in the specified directory.
   - The regex patterns are applied to each file to remove or replace matching content.

## Setting Up the Regex Patterns File

Create a `regex_patterns.txt` file with your desired regex patterns, one per line. These patterns will be used to clean the Markdown files. For example:

``` text
[😀-🙏🌀-🗿🚀-🛿🇠-🇿✂-➰Ⓜ-🉑]+
[ Edit this page.*?]\(.*?\)
[ Previous .*?]\(.*?\)
[ Next .*?]\(.*?\)
[.*?]\(https://discord.gg/.*?\)
[.*?]\(https://twitter.com/.*?\)
[ Privacy and Cookies.*?]\(.*?\)
\` ctrl \` \` K \`
Copyright ©.*
⏱
^\s*####\s*$
^\s#* * *\s*$
```

### Understanding the Regex Patterns

- **Unicode Emoji Removal**: `[😀-🙏🌀-🗿🚀-🛿🇠-🇿✂-➰Ⓜ-🉑]+`
  - This pattern is used to remove emojis from the text. It matches a range of Unicode characters typically used for emojis.
- **Link and Metadata Removal**:
  - Patterns like `\[ Edit this page.*?\]\(.*?\)` are used to remove specific links or metadata often found in web-scraped content.
- **Special Characters and Blank Lines**:
  - Patterns like `^\s*####\s*$` and `^\s#* * *\s*$` are for removing special characters and unnecessary blank lines in the content.

## Conclusion

This script offers a comprehensive solution for web scraping, duplicate file management, and content cleaning. By setting up the regex patterns file as described, you can tailor the content cleaning process to your specific needs.
