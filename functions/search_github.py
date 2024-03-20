import requests

def validate_repo_name(repo_name):
    """
    Validates the given repository name.

    :param repo_name: The repository name to validate.
    :return: True if valid, False otherwise.
    """
    return isinstance(repo_name, str) and bool(repo_name.strip())

def search_github_repository(repo_name):
    """
    Searches GitHub for repositories matching the given name.
    
    :param repo_name: Name of the GitHub repository to search for.
    :return: JSON response containing repository details if successful, None otherwise.
    """
    url = f"https://api.github.com/search/repositories?q={repo_name}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch data from GitHub. Status code: {response.status_code}")
        return None

    return response.json()

def display_repository_info(results, repo_name):
    """
    Displays information about the repositories found in the search results.

    :param results: JSON response containing repository details.
    :param repo_name: The repository name used for the search.
    """
    if results and results['total_count'] > 0:
        for repo in results['items']:
            print(f"Repository Name: {repo['name']}")
            print(f"Description: {repo['description']}")
            print(f"URL: {repo['html_url']}")
            print(f"Stars: {repo['stargazers_count']}")
            print(f"Forks: {repo['forks_count']}")
            print(f"Open Issues: {repo['open_issues_count']}")
            print(f"Last Updated: {repo['updated_at']}\n")
    else:
        print(f"No repository found with the name '{repo_name}'.")

if __name__ == "__main__":
    repo_name = input("Enter the repository name to search: ")
    if validate_repo_name(repo_name):
        results = search_github_repository(repo_name)
        display_repository_info(results, repo_name)
    else:
        print("Invalid repository name. Please provide a valid string.")
