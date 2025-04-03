import requests


def check_redirection(url):
    """
    Check if a URL redirects to another URL using a HEAD request.

    Args:
        url (str): The URL to check for redirection.

    Returns:
        str: The final redirected URL after following redirects, or the original URL if no redirection.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    except requests.RequestException:
        return url  # In case of error, return the original URL
