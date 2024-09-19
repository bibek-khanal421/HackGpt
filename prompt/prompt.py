def set_var(prompt: str, vars: dict):
    """
    Replaces placeholders in a prompt string with values from a dictionary.

    Args:
        prompt (str): The input string containing placeholders.
        vars (dict): A dictionary containing key-value pairs to replace placeholders.

    Returns:
        str: The input string with placeholders replaced by corresponding values.
    """
    for key, value in vars.items():
        prompt = prompt.replace(f"{{{key}}}", value)
    return prompt


def get_prompt(path, vars):
    """
    Reads a prompt from a file and replaces placeholders with values from a dictionary.
    Args:
        path (str): The path to the file containing the prompt.
        vars (dict): A dictionary containing key-value pairs to replace placeholders.
    Returns:
        str: The prompt string with placeholders replaced by corresponding values.
    """
    try:
        with open(path, "r") as file:
            prompt = file.read()
            prompt = set_var(prompt, vars)
        return prompt
    except Exception as e:
        raise RuntimeError(f"Error getting prompt: {e}")
