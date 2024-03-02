import itertools
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()


class MegaverseAPI:
    """A class to interact with the Crossmint Megaverse API."""

    BASE_URL = "https://challenge.crossmint.io/api"

    def __init__(self, candidate_id):
        self.candidate_id = candidate_id
        self.created_polyanets = set()  # Cache to store created POLYanets

    def make_request(self, endpoint, method="post", **kwargs):
        """Generic method for making API requests with rate limit handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        payload = {"candidateId": self.candidate_id, **kwargs}

        # Check cache to avoid duplicate requests
        if (
            endpoint == "polyanets"
            and (kwargs["row"], kwargs["column"]) in self.created_polyanets
        ):
            print(
                f"POLYanet at ({kwargs['row']}, {kwargs['column']}) already created. Skipping..."
            )
            return None

        for attempt in range(5):
            response = requests.request(method, url, json=payload, timeout=5)
            if response.status_code == 200:
                if endpoint == "polyanets":
                    self.created_polyanets.add(
                        (kwargs["row"], kwargs["column"])
                    )  # Cache successful creation
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2**attempt))
                time.sleep(retry_after)
            else:
                print(f"Request failed: {response.text}")
                return None

    def clear_map(self, grid_size):
        """Clears the entire map before creating new objects."""
        for row, column in itertools.product(range(grid_size), repeat=2):
            self.make_request("polyanets", method="delete", row=row, column=column)

    def fetch_goal_state(self):
        """Fetches the goal state for the megaverse creation."""
        if response := self.make_request("map/{candidateId}/goal", method="get"):
            return response.get("goal")
        return None


def main():
    candidate_id = os.environ.get("CANDIDATE_ID")
    api = MegaverseAPI(candidate_id)

    goal_state = api.fetch_goal_state()
    if not goal_state:
        print("Failed to fetch the goal state.")
        return

    grid_size = max(len(goal_state), len(goal_state[0]))
    api.clear_map(grid_size)  # Clear the map based on the inferred grid size

    for row_idx, row in enumerate(goal_state):
        for col_idx, cell in enumerate(row):
            if cell == "POLYANet":
                api.make_request("polyanets", row=row_idx, column=col_idx)


if __name__ == "__main__":
    main()
