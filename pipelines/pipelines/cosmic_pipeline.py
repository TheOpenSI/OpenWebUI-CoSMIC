# pipelines/cosmic_pipeline.py
import sys, os

# Add CoSMIC to the system path
ROOT = f"{os.path.dirname(os.path.abspath(__file__))}/../.."

if os.path.exists(f"{ROOT}/../CoSMIC"):
    sys.path.append(f"{ROOT}/..")
    from CoSMIC.src.opensi_cosmic import OpenSICoSMIC
else:
    sys.path.append(f"{ROOT}/../..")
    from src.opensi_cosmic import OpenSICoSMIC

from pydantic import BaseModel
from typing import List, Union, Generator, Iterator


class Pipeline:
    class Valves(BaseModel):
        pass

    # A class-level dictionary to keep track of user queries. 
    # Key: user_id, Value: number of queries asked.
    user_queries_count = {}

    def __init__(self):
        self.name = "OpenSI-CoSMIC"
        self.valves = self.Valves(**{"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")})
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root = f"{current_dir}/../.."

        config_path = os.path.join(
            root, 
            "shared/config_updated.yaml"
        )
        self.opensi_cosmic = OpenSICoSMIC(config_path=config_path)

    async def on_startup(self):
        print(f"on_startup:{__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        self.opensi_cosmic.quit()

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:

        # Extract user_id from body. Adjust if user_id is available elsewhere.
        user_id = body.get("user_id", "default_user")

        # Check how many queries this user has already made
        current_count = self.user_queries_count.get(user_id, 0)
        MAX_QUERIES_PER_USER = 5

        if current_count >= MAX_QUERIES_PER_USER:
            # Return a message indicating the limit has been reached
            return "You have reached the maximum number of queries allowed."

        # Increment the count for this user
        self.user_queries_count[user_id] = current_count + 1

        # Proceed as normal
        answer, raw_answer, score = self.opensi_cosmic(user_message)

        if answer is None:
            answer = 'Successfully!'
        return answer