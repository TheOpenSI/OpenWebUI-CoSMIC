import sys, os, dotenv, shutil, yaml

# Add CoSMIC to the system path
ROOT = os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/../../../..")
sys.path.append(ROOT)

from src.opensi_cosmic import OpenSICoSMIC
from pydantic import BaseModel
from typing import List


class Pipeline:
    class Valves(BaseModel):
        pass

    # A class-level dictionary to keep track of user queries. 
    # Key: user_id, Value: number of queries asked.
    user_queries_count = {}

    def __init__(self):
        self.name = "OpenSI-CoSMIC"
        self.root = ROOT
        self.config_path = os.path.join(self.root, "scripts/configs/config_updated.yaml")
        self.env_path = os.path.abspath(os.path.join(self.root, ".env"))

        if not os.path.exists(self.config_path):
            config_path = os.path.join(self.root, "scripts/configs/config.yaml")
            shutil.copyfile(config_path, self.config_path)

        self.config_modify_timestamp = str(os.path.getmtime(self.config_path))
        self.MAX_QUERIES_PER_USER = 5

        # Check if vector database is valid.
        with open(self.config_path, "r") as file:
            config = yaml.safe_load(file)

        if not os.path.exists(config["rag"]["vector_db_path"]):
            config["rag"]["vector_db_path"] = \
                f"{self.root}/data/backend/data/vector_db_cosmic"

        with open(self.config_path, "w") as file:
            yaml.safe_dump(config, file)

        # Set OPENAI_API_KEY first before constructing OpenSICoSMIC since this config will
        # be directly used in OpenSICoSMIC().
        self.update_openai_key()
        self.opensi_cosmic = OpenSICoSMIC(config_path=self.config_path)
        self.openai_api_status = self.check_openai_key()

    def update_openai_key(self):
        # Set up OPENAI_API_KEY globally through root's .env.
        envs = dotenv.dotenv_values(self.env_path)

        if "OPENAI_API_KEY" in envs.keys():
            self.openai_api_key = envs["OPENAI_API_KEY"]
        else:
            self.openai_api_key = ""

        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        self.valves = self.Valves(**{"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")})

    def check_openai_key(self):
        llm_name = self.opensi_cosmic.config.llm_name
        query_analyser_llm_name = self.opensi_cosmic.config.query_analyser.llm_name

        is_llm_name_gpt = llm_name.find("gpt") > -1
        is_query_analyser_llm_name_gpt = query_analyser_llm_name.find("gpt") > -1

        llm_name_list = []
        if is_llm_name_gpt: llm_name_list.append(llm_name)
        if is_query_analyser_llm_name_gpt and (query_analyser_llm_name not in llm_name_list):
            llm_name_list.append(query_analyser_llm_name)

        count = len(llm_name_list)

        if (count > 0) and (self.openai_api_key == ""):
            if count == 1: answer = f"{llm_name_list[0]} is"
            elif count == 2: answer = f"{llm_name_list[0]} and {llm_name_list[1]} are"
            answer = f"Since {answer} used, please add valid OPENAI_API_KEY\n" \
                f"in [account]/Settings/Admin Settings/Configs/[OpenAI API Key] then save."
        else:
            answer = ""

        return answer

    async def on_startup(self):
        print(f"on_startup:{__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        self.opensi_cosmic.quit()

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ):
        current_config_modify_timestamp = str(os.path.getmtime(self.config_path))
        current_openai_api_key = os.environ["OPENAI_API_KEY"]

        if (current_config_modify_timestamp != self.config_modify_timestamp) \
            or (current_openai_api_key != self.openai_api_key):
            self.opensi_cosmic.quit()
            self.openai_api_key = current_openai_api_key
            self.config_modify_timestamp = current_config_modify_timestamp
            os.environ["OPENAI_API_KEY"] = self.openai_api_key
            self.opensi_cosmic = OpenSICoSMIC(config_path=self.config_path)
            print('Reconstruct OpenSICoSMIC due to changed configs.')
            self.update_openai_key()
            self.openai_api_status = self.check_openai_key()

        # Extract user_id from body. Adjust if user_id is available elsewhere.
        user_id = body["user"]["id"]
        user_role = body["user"]["role"]

        # Set user ID to use a specific vector database.
        # For the same user, the QA instance will not change.
        self.opensi_cosmic.set_up_qa(str(user_id))

        # Check how many queries this user has already made
        current_count = self.user_queries_count.get(user_id, 0)

        if (user_role != "admin") and (current_count >= self.MAX_QUERIES_PER_USER):
            # Return a message indicating the limit has been reached
            return "You have reached the maximum number of queries allowed."

        # Increment the count for this user
        self.user_queries_count[user_id] = current_count + 1

        # Proceed as normal
        if self.openai_api_status != "":
            answer = self.openai_api_status
        else:
            # Find the key word for adding file to vector database.
            if user_message.find("</files>") > -1:
                splits = user_message.split("</files>")

                # Extract the original question.
                user_message = splits[1]

                # The directory storing uploaded files.
                file_dir = f"{self.root}/data/backend/data/uploads/{user_id}"

                # Extract the files.
                files = splits[0].split("<files>")[-1]
                files = [os.path.join(file_dir, v) for v in files.split(',') if v != ""]

                for file in files:
                    # Form a prompt to update vector database.
                    user_message_vector_db_update = \
                        f"Add the following file to the vector database: {file}"

                    # Update vector database.
                    answer = self.opensi_cosmic(user_message_vector_db_update)[0]

            answer = self.opensi_cosmic(user_message)[0]
            if answer is None: answer = 'Successfully!'

        return answer