
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, status


# Maximum allowed requests per user
MAX_REQUESTS = 15

# Time window in seconds
WINDOW_SECONDS = 60

# Store request timestamps separately for each user
request_history = defaultdict(deque)

# Protect shared data during concurrent requests
rate_limit_lock = Lock()


def check_rate_limit(user_id: int) -> None:
    """
    Allow a maximum of 15 requests per user
    within a rolling 60-second window.
    """

    current_time = time.monotonic()

    with rate_limit_lock:

        user_requests = request_history[user_id]

        # Remove requests older than the time window
        while (
            user_requests
            and current_time - user_requests[0] >= WINDOW_SECONDS
        ):
            user_requests.popleft()

        # Check whether the user exceeded the limit
        if len(user_requests) >= MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Rate limit exceeded.",
                    "limit": MAX_REQUESTS,
                    "window_seconds": WINDOW_SECONDS,
                    "retry_after_seconds": max(
                        1,
                        int(WINDOW_SECONDS - (
                            current_time - user_requests[0]
                        ))
                    )
                }
            )

        # Record the current request
        user_requests.append(current_time)
