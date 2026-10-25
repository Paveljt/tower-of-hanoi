"""Tower of Hanoi solving algorithms."""


def solve(n, source=0, destination=2, spare=1):
    """Yield the optimal moves from a complete starting stack."""
    if n == 0:
        return

    yield from solve(n - 1, source, spare, destination)
    yield source, destination
    yield from solve(n - 1, spare, destination, source)


def solve_from_state(pegs, disk_count, destination=2):
    """Return a solution from any legal board position."""
    simulated = [stack.copy() for stack in pegs]
    moves = []

    def gather(number, target):
        if number == 0:
            return

        source = next(
            index
            for index, stack in enumerate(simulated)
            if number in stack
        )

        if source == target:
            gather(number - 1, target)
            return

        spare = 3 - source - target

        gather(number - 1, spare)

        simulated[target].append(simulated[source].pop())
        moves.append((source, target))

        gather(number - 1, target)

    gather(disk_count, destination)
    return moves