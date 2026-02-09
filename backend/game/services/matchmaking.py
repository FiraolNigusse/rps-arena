import time
from collections import defaultdict
from game.services.match import enter_match

MATCH_QUEUES = defaultdict(list)
QUEUE_TIMEOUT = 15  # seconds


def enqueue_player(user, stake):
    queue = MATCH_QUEUES[stake]

    # Remove expired players
    now = time.time()
    queue[:] = [q for q in queue if now - q["time"] < QUEUE_TIMEOUT]

    # Try to match
    for q in queue:
        opponent = q["user"]
        queue.remove(q)
        return enter_match(user, opponent, stake)

    # No match found → enqueue
    queue.append({
        "user": user,
        "time": now
    })

    return None
