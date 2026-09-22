from pathlib import Path
from ollama import chat
import json



question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""


## WRITE ##
service_status ={
    "wifi": "operational"
}

state_file = Path("state.json")

if state_file.exists():
    with open("state.json", "r") as file:
        state = json.load(file)
else:
    state ={
        "diagnostic_context": {}
    }

state["diagnostic_context"]["problem"] = question
state["diagnostic_context"]["wifi_status"] = service_status["wifi"]
state["diagnostic_context"]["wifi_check"] = True

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )

with open("state.json", "r") as file:
    state = json.load(file)

print(state)


## SELECT CONTEXT FILES BASED ON QUESTION
## Create the function that takes the student's question, takes some keywords and chooses the relevant files from the knowledge base. Return a list of the selected files.
## For example, if the question has the kyeword "print" or "printer", then the function should return the file "knowledge/printer_setup.txt" in a list.
def select_context(question):
    question = question.lower()
    selected_files =[]

    if "wifi" in question or "wi-fi" in question or "eduroam" in question:
        selected_files.append("knowledge/wifi_setup.txt")
        selected_files.append("knowledge/service_status.txt")

    if "password" in question or "credential" in question:
        selected_files.append("knowledge/password_changes.txt")

    if "print" in question or "printer" in question:
        selected_files.append("knowledge/printing.txt")

    if "email" in question or "mail" in question:
        selected_files.append("knowledge/email_setup.txt")

    if "vpn" in question:
        selected_files.append("knowledge/vpn.txt")

    if "projector" in question or "display" in question:
        selected_files.append("knowledge/classroom_projectors.txt")

    return selected_files


selected_files = select_context(question)

## READ SELECTED FILES and add their contents to the context variable.
context =""

for filename in selected_files:
    context += Path(filename).read_text()
    context += "\n\n"


## 
## COMPRESS CONTEXT
## Add logic to compress the context from above by calling Qwen with "context" and the "question" as the parameter
## The response from Qwen should be the compressed context. Store it in a variable called "compressed_context" 

def compress_context(context, question):
    prompt = f"""
The student's question is:

{question}

Below is university support information:

{context}

Extract only the information that is relevant to the student's question.
Do not add information that is not in the context.
Return only the relevant information.
"""

    response = chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content


compressed_context = compress_context(context, question)


## Print the length of the compressed context
print(len(compressed_context))

## Now, call Qwen again with the compressed context and the student's question. Store the response in a variable called "response" and print the response from Qwen.
## Ensure the model produces a structured output 
relevant_state = {
    "wifi_status": state["diagnostic_context"]["wifi_status"],
    "wifi_check": state["diagnostic_context"]["wifi_check"]
}

if "model_output" in state["diagnostic_context"]:
    relevant_state["previous_result"] = state["diagnostic_context"]["model_output"]

prompt = f"""
You are a university IT support assistant.

Student question:

{question}

Relevant saved state:

{json.dumps(relevant_state)}

Compressed university information:

{compressed_context}

Use only the information above.

Return only one valid JSON object with exactly this structure:

{{
    "issue": "short description",
    "likely_cause": "short description",
    "recommended_steps": ["step 1", "step 2"],
    "service_status": "short status"
}}

Do not include markdown or any extra text.
"""

response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)


print(response.message.content)

## WRITE the above output in an artifact called "state"
model_output = json.loads(response.message.content)

state["diagnostic_context"]["model_output"] = model_output

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )

## Update the rest of the code so that it uses the "state" artifact as part of the context.
## It is important to ensure that the model uses only the relevant parts from the "state" artifact and not the entire artifact.
## For this, you may have to think of a good structure for the "state" artifact and how to use it in the context.