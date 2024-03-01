import itertools
import time
import requests

# Constants
BASE_URL = "https://challenge.crossmint.io/api"
CANDIDATE_ID = "be5531ab-f261-4f70-b3c7-b9478e44cbc3"
RATE_LIMIT_DELAY = 1.0


def make_request(func, *args, **kwargs):
    """
    Wrapper to handle rate limiting and retry logic for any API call.
    """
    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
        response = func(*args, **kwargs)
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            time.sleep(retry_after)
            attempt += 1
        else:
            print(f"Request failed: {response.text}")
            break
    return None


# API Call Functions
def create_polyanet(row, column):
    url = f"{BASE_URL}/polyanets"
    payload = {"candidateId": CANDIDATE_ID, "row": row, "column": column}
    return requests.post(url, json=payload, timeout=5)


def delete_polyanet(row, column):
    url = f"{BASE_URL}/polyanets"
    payload = {"candidateId": CANDIDATE_ID, "row": row, "column": column}
    return requests.delete(url, json=payload, timeout=5)


def create_soloon(row, column, color):
    url = f"{BASE_URL}/soloons"
    payload = {
        "candidateId": CANDIDATE_ID,
        "row": row,
        "column": column,
        "color": color,
    }
    return requests.post(url, json=payload, timeout=5)


def create_cometh(row, column, direction):
    url = f"{BASE_URL}/comeths"
    payload = {
        "candidateId": CANDIDATE_ID,
        "row": row,
        "column": column,
        "direction": direction,
    }
    return requests.post(url, json=payload, timeout=5)


def clear_map(grid_size):
    for row, column in itertools.product(range(grid_size), repeat=2):
        response = delete_polyanet(row, column)
        if response.status_code not in [
            200,
            404,
            400,
        ]:  # Including 400 for out-of-bounds
            print(
                f"Failed to clear element at ({row}, {column}) - Status Code: {response.status_code}, Response: {response.text}"
            )
        time.sleep(RATE_LIMIT_DELAY)


def fetch_goal_state():
    url = f"{BASE_URL}/map/{CANDIDATE_ID}/goal"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        goal_data = response.json()
        return goal_data["goal"]  # Assuming 'goal' is the key in the response
    else:
        print(
            f"Failed to fetch goal state - Status Code: {response.status_code}, Response: {response.text}"
        )
        return None


def main():
    goal_state = fetch_goal_state()
    if goal_state is None:
        print("Failed to fetch the goal state.")
        return

    grid_size = max(len(goal_state), len(goal_state[0]))
    created_objects = set()  # Cache to store created object positions and types

    clear_map(grid_size)

    for row_idx, row in enumerate(goal_state):
        for col_idx, cell in enumerate(row):
            obj_type, *details = cell.split("_")
            identifier = (row_idx, col_idx, obj_type)

            if identifier in created_objects:
                continue  # Skip if already created

            if obj_type == "POLYANET":
                make_request(create_polyanet, row_idx, col_idx)
            elif obj_type == "SOLOON":
                color = details[0].lower()
                make_request(create_soloon, row_idx, col_idx, color)
            elif obj_type == "COMETH":
                direction = details[0].lower()
                make_request(create_cometh, row_idx, col_idx, direction)

            created_objects.add(identifier)  # Mark as created


if __name__ == "__main__":
    main()
