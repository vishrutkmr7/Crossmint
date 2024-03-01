import itertools
import time
import requests

# Constants
BASE_URL = "https://challenge.crossmint.io/api"
CANDIDATE_ID = "be5531ab-f261-4f70-b3c7-b9478e44cbc3"
RATE_LIMIT_DELAY = 1.0


# Exponential backoff function
def exponential_backoff(attempt):
    wait_time = min(2**attempt, 60)
    time.sleep(wait_time)


# API Call Functions
def create_polyanet(row, column):
    url = f"{BASE_URL}/polyanets"
    payload = {"candidateId": CANDIDATE_ID, "row": row, "column": column}
    return requests.post(url, json=payload, timeout=5)


def delete_polyanet(row, column):
    url = f"{BASE_URL}/polyanets"
    payload = {"candidateId": CANDIDATE_ID, "row": row, "column": column}
    return requests.delete(url, json=payload, timeout=5)


# Create a goal state function
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


def clear_map(grid_size):
    for row, column in itertools.product(range(grid_size), repeat=2):
        response = delete_polyanet(row, column)  # Assuming the API is 0-indexed
        if response.status_code not in [
            200,
            404,
            400,
        ]:  # Including 400 for out-of-bounds
            print(
                f"Failed to clear POLYanet at ({row}, {column}) - Status Code: {response.status_code}, Response: {response.text}"
            )
        time.sleep(RATE_LIMIT_DELAY)


def main():
    goal_state = fetch_goal_state()
    if goal_state is None:
        print("Failed to fetch the goal state.")
        return

    grid_size = max(len(goal_state), len(goal_state[0]))

    # Clear existing POLYanets
    clear_map(grid_size + 1)

    attempt = 0
    for row_idx, row in enumerate(goal_state):
        for col_idx, cell in enumerate(row):
            if cell == "POLYANET":
                while True:
                    response = create_polyanet(row_idx, col_idx)
                    if response.status_code == 200:
                        print(f"POLYanet created at ({row_idx}, {col_idx})")
                        attempt = 0  # Reset attempt count after a successful request
                        time.sleep(
                            RATE_LIMIT_DELAY
                        )  # Delay to comply with rate limiting
                        break
                    elif response.status_code == 429:
                        print("Rate limit hit, waiting to retry...")
                        attempt += 1
                        exponential_backoff(attempt)
                    else:
                        print(
                            f"Failed to create POLYanet at ({row_idx}, {col_idx}) - Status Code: {response.status_code}, Response: {response.text}"
                        )
                        break


if __name__ == "__main__":
    main()
