import time
from collections import defaultdict
from game.services.match import enter_match

MATCH_QUEUES = defaultdict(list)
QUEUE_TIMEOUT = 15  # seconds


def enqueue_player(user, stake, ip_address=None):
    queue = MATCH_QUEUES[stake]

    # Remove expired players
    now = time.time()
    queue[:] = [q for q in queue if now - q["time"] < QUEUE_TIMEOUT]

    # Try to match
    for q in queue:
        opponent = q["user"]
        player1_ip = q.get("ip")
        queue.remove(q)
        return enter_match(
            player1=opponent,
            player2=user,
            stake=stake,
            player1_ip=player1_ip,
            player2_ip=ip_address,
        )

    # No match found → enqueue
    queue.append({
        "user": user,
        "time": now,
        "ip": ip_address,
    })

    return None
