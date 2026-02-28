def count_down(n: int) -> None:
    """Counts down from n to 1, printing each number.

    Args:
        n: The starting number for the countdown.

    Returns:
        None
    """
    while n > 0:
        print(n)
        n -= 1  # Fixed: Decrement n to avoid infinite loop