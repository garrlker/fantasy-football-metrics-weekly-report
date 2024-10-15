import json
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import List, Dict, Optional, Union
from uuid import uuid4
import sys
from requests import get, post

from integrations.base.integration import BaseIntegration
from utilities.logger import get_logger
from utilities.settings import settings

logger = get_logger(__name__, propagate=False)


class GroupMeIntegration(BaseIntegration):

    def __init__(self):
        super().__init__("groupme")

        self.root_dir = Path(__file__).parent.parent

        self.base_url = "https://api.groupme.com/v3"
        self.file_service_base_url = "https://file.groupme.com/v1"

    def _authenticate(self) -> None:
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "ff-metrics-weekly-report/1.0.0",
            "Accept": "*/*",
            "X-Access-Token": settings.integration_settings.groupme_access_token
        }

    def _get_group_id(self, group_name: str) -> Optional[str]:
        for group in self._list_groups():
            if group["name"] == group_name:
                return group["id"]
        raise ValueError(f"Group ID for {group_name} not found.")

    def _list_groups(self) -> List[Dict]:
        return get(
            f"{self.base_url}/groups?omit=memberships",
            headers={
                "Host": "api.groupme.com",
                **self.headers
            }
        ).json()["response"]

    def _upload_file_to_file_service(self, file_path: Path) -> Optional[str]:

        headers = {
            "Host": "file.groupme.com",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",
            **self.headers
        }

        file_upload_response = post(
            f"{self.file_service_base_url}/{self._get_group_id(settings.integration_settings.groupme_group)}/files",
            params={
                "name": file_path.name
            },
            headers=headers,
            data=file_path.read_bytes(),
        ).json()

        file_upload_status_url = file_upload_response["status_url"]

        uploaded_file_id: Optional[str] = None
        incremental_backoff = 1
        while not uploaded_file_id and incremental_backoff <= 5:
            sleep(0.25 * incremental_backoff)
            file_status_response = get(file_upload_status_url, headers=headers).json()

            file_upload_status = file_status_response["status"]
            if file_upload_status == "completed":
                uploaded_file_id = file_status_response["file_id"]

            incremental_backoff += 1

        return uploaded_file_id

    def _post_as_bot(self, message: str, file_path: Optional[Path] = None) -> int:

        post_content = {
            "bot_id": settings.integration_settings.groupme_bot_id,
            "text": message
        }

        if file_path:
            post_content.update({
                "attachments": [
                    {
                        "type": "file",
                        "file_id": self._upload_file_to_file_service(file_path),
                    }
                ]
            })

        return post(f"{self.base_url}/bots/post", json=post_content).status_code

    def _post_as_user(self, message: str, file_path: Optional[Path] = None) -> Dict:

        post_content = {
            "source_guid": str(uuid4()),
            "text": message,
        }

        if file_path:
            post_content.update({
                "attachments": [
                    {
                        "type": "file",
                        "file_id": self._upload_file_to_file_service(file_path),
                    }
                ]
            })

        return post(
            f"{self.base_url}/groups/{self._get_group_id(settings.integration_settings.groupme_group)}/messages",
            headers={
                "Host": "api.groupme.com",
                **self.headers
            },
            json={"message": post_content}
        ).json()

    def post_message(self, message: str) -> Union[int, Dict]:
        logger.debug(f"Posting message to GroupMe: \n{message}")

        if settings.integration_settings.groupme_bot_or_user == "bot":
            return self._post_as_bot(message)
        elif settings.integration_settings.groupme_bot_or_user == "user":
            return self._post_as_user(message)
        else:
            logger.warning(
                f"The \".env\" file contains unsupported GroupMe setting: "
                f"GROUPME_BOT_OR_USER={settings.integration_settings.groupme_bot_or_user}. Please choose \"bot\" or "
                f"\"user\" and try again."
            )
            sys.exit(1)

    def upload_file(self, file_path: Path) -> Union[int, Dict]:
        logger.debug(f"Uploading file to GroupMe: \n{file_path}")

        message = (
            f"\nFantasy Football Report for {file_path.name}\n"
            f"Generated {datetime.now():%Y-%b-%d %H:%M:%S}\n"
        )

        if settings.integration_settings.groupme_bot_or_user == "bot":
            return self._post_as_bot(message, file_path)
        elif settings.integration_settings.groupme_bot_or_user == "user":
            return self._post_as_user(message, file_path)
        else:
            logger.warning(
                f"The \".env\" file contains unsupported GroupMe setting: "
                f"GROUPME_BOT_OR_USER={settings.integration_settings.groupme_bot_or_user}. Please choose \"bot\" or "
                f"\"user\" and try again."
            )
            sys.exit(1)


if __name__ == "__main__":
    reupload_file = Path(__file__).parent.parent / settings.integration_settings.reupload_file_path

    logger.info(f"Re-uploading {reupload_file.name} ({reupload_file}) to GroupMe...")

    groupme_integration = GroupMeIntegration()

    # logger.info(f"{json.dumps(groupme_integration.post_message('test message'), indent=2)}")
    logger.info(f"{json.dumps(groupme_integration.upload_file(reupload_file), indent=2)}")