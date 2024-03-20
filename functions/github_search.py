# filename: github_search.py
import requests

def search_github_repositories(query, per_page=10):
    url = "https://api.github.com/search/repositories"
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': per_page
    }
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"GitHub API returned status code: {response.status_code}")
    return None

# Search for repositories related to AI/LLM and security
query = 'AI LLM security'
if repositories := search_github_repositories(query):
    print("Top repositories related to AI/LLM and security:")
    for repo in repositories['items']:
        print(f"Name: {repo['name']}")
        print(f"URL: {repo['html_url']}")
        print(f"Description: {repo['description']}")
        print(f"Stars: {repo['stargazers_count']}")
        print('-' * 60)