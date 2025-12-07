import os

from admin import get_assistant_id, get_thread_id
from config import proxy_client


def process_message(chat_id: str, message: str) -> list[dict]:
    assistant_id = get_assistant_id()
    thread_id = get_thread_id(chat_id)
    if not thread_id:
        raise ValueError("Thread not found")

    proxy_client.beta.threads.messages.create(
        thread_id=thread_id, content=message, role="user"
    )

    run = proxy_client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    answer = []

    if run.status == "completed":
        messages = proxy_client.beta.threads.messages.list(
            thread_id=thread_id, run_id=run.id
        )
        for message in messages:
            if message.role == "assistant":
                for block in message.content:
                    if block.type == "text":
                        answer.insert(0, {"type": "text", "text": block.text.value})
                        if block.text.annotations:
                            for annotation in block.text.annotations:
                                if annotation.type == "file_path":
                                    answer.insert(
                                        0,
                                        {
                                            "type": "file",
                                            "file": download_file(
                                                annotation.file_path.file_id
                                            ),
                                            "filename": os.path.basename(
                                                annotation.text.split(":")[-1]
                                            ),
                                        },
                                    )
                    elif block.type == "image_file":
                        answer.insert(
                            0,
                            {
                                "type": "image",
                                "file": download_file(block.image_file.file_id),
                            },
                        )

    return answer


def download_file(file_id: str) -> str:
    file_content = proxy_client.files.content(file_id)
    content = file_content.read()
    with open(f"/tmp/{file_id}", "wb") as f:
        f.write(content)
    return f"/tmp/{file_id}"