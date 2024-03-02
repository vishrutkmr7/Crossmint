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
        self.created_objects = set()  # Cache to store created object identifiers

    def make_request(self, endpoint, method="post", **kwargs):
        """Generic method for making API requests with rate limit handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        payload = {"candidateId": self.candidate_id, **kwargs}

        # Create a unique identifier for the object to check for duplicates
        obj_identifier = (endpoint, tuple(kwargs.items()))
        if obj_identifier in self.created_objects:
            print(f"Skipping duplicate request for {obj_identifier}")
            return None

        for attempt in range(5):
            response = requests.request(method, url, json=payload, timeout=5)
            if response.status_code == 200:
                self.created_objects.add(obj_identifier)  # Mark as created
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2**attempt))
                time.sleep(retry_after)
            else:
                print(f"Request failed: {response.text}")
                break
        return None

    def create_object(self, obj_type, row, column, **kwargs):
        """Creates astral objects (POLYanet, SOLoon, COMETH) in the megaverse."""
        return self.make_request(obj_type.lower(), row=row, column=column, **kwargs)

    def clear_map(self, grid_size):
        """Clears the entire megaverse grid."""
        for row, column in itertools.product(range(grid_size), repeat=2):
            self.make_request("polyanets", method="delete", row=row, column=column)

    def fetch_goal_state(self):
        """Fetches the goal state for the megaverse."""
        response = requests.get(
            f"{self.BASE_URL}/map/{self.candidate_id}/goal", timeout=5
        )
        if response.status_code == 200:
            return response.json().get("goal")
        print(
            f"Failed to fetch goal state - Status Code: {response.status_code}, Response: {response.text}"
        )
        return None


def main():
    candidate_id = os.environ.get("CANDIDATE_ID")
    api = MegaverseAPI(candidate_id)
    goal_state = api.fetch_goal_state()
    if goal_state is None:
        return

    grid_size = max(len(goal_state), len(goal_state[0]))
    api.clear_map(grid_size)

    for row_idx, row in enumerate(goal_state):
        for col_idx, cell in enumerate(row):
            obj_type, *details = cell.split("_")
            if obj_type in ["POLYANET", "SOLOON", "COMETH"]:
                if obj_type == "SOLOON":
                    api.create_object(
                        obj_type, row=row_idx, column=col_idx, color=details[0].lower()
                    )
                elif obj_type == "COMETH":
                    api.create_object(
                        obj_type,
                        row=row_idx,
                        column=col_idx,
                        direction=details[0].lower(),
                    )
                else:
                    api.create_object(obj_type, row=row_idx, column=col_idx)


if __name__ == "__main__":
    main()
