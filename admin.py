from config import ASSISTANT_MODEL, get_config, proxy_client, save_config


def create_assistant(name, instructions):
    assistant_id = get_assistant_id()
    if not assistant_id:
        new_assistant = proxy_client.beta.assistants.create(
            model=ASSISTANT_MODEL,
            instructions=instructions,
            name=name,
            tools=[
                {
                    "type": "code_interpreter",
                }
            ],
        )
        config = get_config()
        config["assistant_id"] = new_assistant.id
        save_config(config)
    else:
        proxy_client.beta.assistants.update(
            assistant_id=assistant_id, instructions=instructions
        )


def get_assistant_id():
    config = get_config()
    return config["assistant_id"] if "assistant_id" in config else None


def upload_file(chat_id, filename, file):
    config = get_config()
    file_object = proxy_client.files.create(file=(filename, file), purpose="assistants")
    thread = proxy_client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "Для всех вопросов, которые я буду задавать, используй эти данные для анализа",
                "attachments": [
                    {"file_id": file_object.id, "tools": [{"type": "code_interpreter"}]}
                ],
            }
        ]
    )
    if not "threads" in config:
        config["threads"] = {}

    config["threads"][chat_id] = thread.id
    save_config(config)


def get_thread_id(chat_id: str):
    config = get_config()

    if "threads" in config and chat_id in config["threads"]:
        return config["threads"][chat_id]

    return None