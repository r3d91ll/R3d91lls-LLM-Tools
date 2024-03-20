# filename: github_issues_analysis.py
import requests

# Define your personal GitHub token and headers
GITHUB_TOKEN = 'your_github_token_here'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

# Define your skills and knowledge
SKILLS = ['python', 'machine learning', 'security', 'deep learning']

# Search for repositories related to AI/ML with a security focus
def search_repositories(query):
    url = f'https://api.github.com/search/repositories?q={query}&sort=stars&order=desc'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['items'][:10]  # Top 10 repositories
    print(f'Error: {response.status_code}')
    return []

# Get issues from a repository
def get_issues(repo_full_name):
    url = f'https://api.github.com/repos/{repo_full_name}/issues'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    print(f'Error: {response.status_code}')
    return []

# Analyze issues to find opportunities to contribute
def analyze_issues(issues):
    opportunities = []
    for issue in issues:
        labels = [label['name'].lower() for label in issue.get('labels', [])]
        if ('help wanted' in labels or 'good first issue' in labels) and any(skill in issue['title'].lower() or skill in issue['body'].lower() for skill in SKILLS):
            opportunities.append(issue)
    return opportunities

# Main function to tie everything together
def main():
    query = 'AI ML security'
    repositories = search_repositories(query)
    for repo in repositories:
        issues = get_issues(repo['full_name'])
        opportunities = analyze_issues(issues)
        for opportunity in opportunities:
            print(f"Repository: {repo['full_name']}")
            print(f"Issue: {opportunity['title']}")
            print(f"URL: {opportunity['html_url']}")
            print('---')

if __name__ == '__main__':
    main()