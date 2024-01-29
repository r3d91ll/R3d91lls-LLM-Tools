import requests
import json
import os

# List of notebook names
notebooks = [
    "Async_human_input.ipynb",
    "agentchat_MathChat.ipynb",
    "agentchat_RetrieveChat.ipynb",
    "agentchat_agentoptimizer.ipynb",
    "agentchat_auto_feedback_from_code_execution.ipynb",
    "agentchat_autobuild.ipynb",
    "agentchat_chess.ipynb",
    "agentchat_compression.ipynb",
    "agentchat_dalle_and_gpt4v.ipynb",
    "agentchat_function_call.ipynb",
    "agentchat_function_call_async.ipynb",
    "agentchat_function_call_currency_calculator.ipynb",
    "agentchat_graph_modelling_language_using_select_speaker.ipynb",
    "agentchat_groupchat.ipynb",
    "agentchat_groupchat_RAG.ipynb",
    "agentchat_groupchat_research.ipynb",
    "agentchat_groupchat_vis.ipynb",
    "agentchat_guidance.ipynb",
    "agentchat_hierarchy_flow_using_select_speaker.ipynb",
    "agentchat_human_feedback.ipynb",
    "agentchat_inception_function.ipynb",
    "agentchat_langchain.ipynb",
    "agentchat_lmm_gpt-4v.ipynb",
    "agentchat_lmm_llava.ipynb",
    "agentchat_microsoft_fabric.ipynb",
    "agentchat_oai_assistant_function_call.ipynb",
    "agentchat_oai_assistant_groupchat.ipynb",
    "agentchat_oai_assistant_retrieval.ipynb",
    "agentchat_oai_assistant_twoagents_basic.ipynb",
    "agentchat_oai_code_interpreter.ipynb",
    "agentchat_planning.ipynb",
    "agentchat_qdrant_RetrieveChat.ipynb",
    "agentchat_stream.ipynb",
    "agentchat_teachability.ipynb",
    "agentchat_teaching.ipynb",
    "agentchat_two_users.ipynb",
    "agentchat_video_transcript_translate_with_whisper.ipynb",
    "agentchat_web_info.ipynb",
    "agenteval_cq_math.ipynb",
    "oai_chatgpt_gpt4.ipynb",
    "oai_client_cost.ipynb",
    "oai_completion.ipynb",
    "oai_openai_utils.ipynb",
]

# URL prefix
url_prefix = "https://raw.githubusercontent.com/microsoft/autogen/main/notebook/"

# Function to download notebook
def download_notebook(notebook_name):
    url = url_prefix + notebook_name
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to download {notebook_name}: HTTP Status Code {response.status_code}")

# Function to convert notebook to markdown (from previous code)
def notebook_to_markdown(notebook_content):
    """ Convert Jupyter Notebook content to Markdown format. """
    notebook_json = json.loads(notebook_content)
    markdown_output = []

    for cell in notebook_json['cells']:
        if cell['cell_type'] == 'code':
            # Code cells are wrapped in triple backticks for Markdown code blocks
            code_content = '\n'.join(cell['source'])
            markdown_output.append(f"```python\n{code_content}\n```")
        elif cell['cell_type'] == 'markdown':
            # Markdown cells are used as is
            markdown_output.append('\n'.join(cell['source']))

    return '\n'.join(markdown_output)

# Main loop to process each notebook
for notebook in notebooks:
    try:
        # Download notebook
        notebook_content = download_notebook(notebook)
        
        # Convert to markdown
        markdown_content = notebook_to_markdown(notebook_content)

        # Save as markdown file
        markdown_filename = os.path.join("/home/todd6585/git/Ops-Tooling/AtlasProject/python3.10/output", notebook.replace(".ipynb", ".md"))
        with open(markdown_filename, "w") as md_file:
            md_file.write(markdown_content)
        
        print(f"Processed {notebook} successfully.")
    except Exception as e:
        print(f"Error processing {notebook}: {e}")
