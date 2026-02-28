x = 10
# Variable mal nommée, pas de docstring, logique inutile
def f(z: int) -> bool:
    """Check if value is within range (0, 100).

    Args:
        z: The value to check.

    Returns:
        bool: True if value is between 0 and 100 (exclusive), False otherwise.
    """
    return 0 < z < 100