from logging import Logger
from typing import Tuple, Optional, Dict

import requests


def ping_DeepAAS_server(
    log_to: Logger, url: str
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Ping a ML server at the root endpoint to check if it's alive.

    Args:
        log_to: A Logger instance

    Returns:
        Tuple containing:
        - Boolean indicating if the server is alive
        - Response data as a dictionary if successful, None otherwise
        - Error message if any, None otherwise
    """
    try:
        # Construct URL for the root endpoint
        log_to.info(f"Pinging DeepAAS server at {url}")
        log_to.debug(f"url: {url}")

        # Make GET request to the root endpoint
        response = requests.get(url, timeout=10)
        log_to.debug(f"Response status: {response.status_code}")

        if not response.ok:
            error_msg = f"Ping failed: {response.status_code} - {response.reason}"
            log_to.error(error_msg)
            return False, None, error_msg

        try:
            # Parse the JSON response if available
            response_data = response.json() if response.content else {}
            # Log success
            log_to.info(f"Successfully pinged server at {url}")
            return True, response_data, None

        except Exception as e:
            error_msg = f"Error parsing JSON response: {str(e)}"
            log_to.error(error_msg)
            return False, None, error_msg

    except Exception as e:
        error_msg = f"Error sending ping request: {str(e)}"
        log_to.error(error_msg)
        return False, None, error_msg
