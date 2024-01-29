from bs4 import BeautifulSoup

def clean_html_for_spr(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove scripts, styles, and non-essential tags
    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
        script.decompose()

    # Isolate the main content area if identifiable (e.g., <main> or <article> tags)
    main_content = soup.find('main') or soup.find('article') or soup

    # Create a new soup object with only the relevant tags
    clean_soup = BeautifulSoup(features='html.parser')
    for elem in main_content.find_all(['h1', 'h2', 'h3', 'p', 'code']):
        clean_soup.append(elem)

    return str(clean_soup)