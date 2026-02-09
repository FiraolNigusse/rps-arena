import time

# match_id → round data
ACTIVE_ROUNDS = {}


def start_round(match_id):
    ACTIVE_ROUNDS[match_id] = {
        "start_time": time.time(),
        "moves": {}
    }


def submit_move(match_id, user_id, move):
    if match_id not in ACTIVE_ROUNDS:
        return False

    ACTIVE_ROUNDS[match_id]["moves"][user_id] = move
    return True


def get_round(match_id):
    return ACTIVE_ROUNDS.get(match_id)


def end_round(match_id):
    if match_id in ACTIVE_ROUNDS:
        del ACTIVE_ROUNDS[match_id]
