import gradio as gr
from PyPDF2 import PdfReader
import requests
import json
import logging

css = """
body, .gradio-container {
    background-color: #000000; /* Black background */
    color: white; /* White text for contrast */
}

.gr-file-upload, .gr-textbox, .gr-button, .output-textbox {
    background-color: #333333; /* Dark gray background for input areas */
    color: white; /* White text */
    border: 1px solid #444444; /* Slightly lighter border */
}

.gr-button {
    background-color: #444444; /* Darker background for buttons */
    color: white; /* White text on buttons */
}

.gr-file-upload {
    border: 2px dashed #777777; /* Gray dashed border for file upload */
}
"""


# Set up logging
logging.basicConfig(level=logging.DEBUG)

def chat_completion_request(messages):
    # API URL and model details
    url = "https://minihackathon12.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-08-01-preview"  # Replace with your actual API URL
    model = "Mixtral-8x7B-Instruct-v0.1"  # Replace with the required model name

    # Payload structure
    payload = {
        "model": model,
        "max_tokens": 7000,
        "temperature": 0.7,
        "top_k": 40,
        "repetition_penalty": 1.2,
        "messages": messages
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "93b4b17912ed411a98a13accbffb5100"  # Replace with your actual API key
    }

    # Send POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Handle response
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}
    

def evaluate_candidates(pdf_files, job_description, seniority_level, experience_level):
    results = []
    try:
        logging.debug("Starting candidate evaluation.")
        for pdf_file in pdf_files:
            logging.debug(f"Processing file: {pdf_file.name}")

            # Read the PDF file and extract text
            pdf_reader = PdfReader(pdf_file.name)
            candidate_text = ""
            for page_number, page in enumerate(pdf_reader.pages):
                logging.debug(f"Extracting text from page {page_number + 1}")
                page_text = page.extract_text()
                if page_text:
                    candidate_text += page_text
                else:
                    logging.debug(f"No text found on page {page_number + 1}")

            logging.debug(f"Extracted candidate text: {candidate_text[:500]}...")  # Log first 500 chars

            # Prepare messages for the AI model
            messages = [
                {
                    "role": "system",
                    "content": "You are an assistant that helps employers evaluate candidates based on their resume and job requirements."
                },
                {
                    "role": "user",
                    "content": f"""Job Description: {job_description}
Seniority Level: {seniority_level}
Experience Level: {experience_level}

Candidate Resume Text: {candidate_text}

Does this candidate fit the criteria? Please provide a detailed analysis."""
                }
            ]

            logging.debug(f"Prepared messages for AI model: {messages}")

            # Call the AI model
            response = chat_completion_request(messages)

            logging.debug(f"Received response: {response}")

            # Extract the assistant's reply from the response
            if 'choices' in response and len(response['choices']) > 0:
                assistant_reply = response['choices'][0]['message']['content']
                results.append(f"*Analysis for {pdf_file.name}:*\n{assistant_reply}")
            else:
                error_message = response.get('message', 'Unknown error')
                logging.error(f"Error processing {pdf_file.name}: {error_message}")
                results.append(f"Error processing {pdf_file.name}: {error_message}")
        # Combine all results
        return "\n\n---\n\n".join(results)
    except Exception as e:
        logging.exception("An exception occurred during candidate evaluation.")
        return f"An error occurred: {str(e)}"

iface = gr.Interface(
    fn=evaluate_candidates,
    inputs=[
        gr.File(file_types=[".pdf"], label="Upload Candidate Resumes (PDF)", file_count="multiple"),
        gr.Textbox(lines=5, placeholder="Enter Job Description", label="Job Description"),
        gr.Textbox(placeholder="Enter Seniority Level", label="Seniority Level"),
        gr.Textbox(placeholder="Enter Experience Level", label="Experience Level"),
    ],
    outputs="text",
    title="Candidate Evaluation Tool",
    description="Upload multiple candidates' resumes and enter job criteria to evaluate fit."
)

iface.launch()