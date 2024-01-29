import os
import time
from openai import OpenAI
from bs4 import BeautifulSoup

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], organization=os.environ["ORGANIZATION_ID"])

def clean_html_for_spr(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove clearly non-essential elements
    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
        script.decompose()

    # Keep the majority of the content structure intact
    main_content = soup.find('main') or soup.find('article') or soup

    return str(main_content)

def generate_spr(client, assistant_id, cleaned_html, file_name, output_dir):
    # Save the cleaned content to a file
    clean_file_name = f'{os.path.splitext(file_name)[0]}-clean.html'
    with open(os.path.join(output_dir, clean_file_name), 'w') as clean_file:
        clean_file.write(cleaned_html)

    # Step 1: Create a Thread
    thread = client.beta.threads.create()

    # Step 2: Add a Message to the Thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=cleaned_html
    )

    # Step 3: Run the Assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Step 4: Wait for Run completion and retrieve messages
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        time.sleep(0.5)  # Adjust sleep time as necessary

    # Retrieve all messages in the thread
    messages = client.beta.threads.messages.list(
        thread_id=thread.id,
        order="asc"
    )

    return next(
        (
            message.content[0].text.value
            for message in messages.data
            if message.role == "assistant"
        ),
        "No response from assistant."
    )

def save_spr_file(spr_content, file_name, output_dir):
    # Change the file extension from .html to .srp.md
    srp_file_name = f"{os.path.splitext(file_name)[0]}.srp.md"

    with open(os.path.join(output_dir, srp_file_name), 'w') as file:
        file.write(spr_content)

def main(directory_path):
    output_dir = 'SRP-files'
    os.makedirs(output_dir, exist_ok=True)

    assistant_id = "asst_oKlrkMCViaRtcLnFewRQJFUs"

    for file_name in os.listdir(directory_path):
        if file_name.endswith('.html'):
            with open(os.path.join(directory_path, file_name), 'r') as file:
                html_content = file.read()

            cleaned_html = clean_html_for_spr(html_content)
            spr_content = generate_spr(client, assistant_id, cleaned_html, file_name, output_dir)
            save_spr_file(spr_content, file_name, output_dir)

if __name__ == "__main__":
    directory_path = '.'  # Replace with your directory path
    main(directory_path)
