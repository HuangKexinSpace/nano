from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import os
import time

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Load API key and assistant ID from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Initialize OpenAI client with your API key
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    # Retrieve the assistant dynamically in the route to handle errors gracefully
    try:
        assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
        assistant_name = assistant.name
    except Exception as e:
        assistant_name = "Error loading assistant"
        print(f"Error: {str(e)}")  # Log the error

    return render_template('index.html', assistant_name=assistant_name)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_message = data['message']
    
    try:
        # Create a new thread for each conversation
        thread = client.beta.threads.create()

        # Send user message to the thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        # Execute the run using the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Polling the thread to check run status
        while True:
            time.sleep(5)  # Delay to prevent excessive API calls
            run_steps = client.beta.threads.runs.steps.list(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_steps.data[-1].status == 'completed':
                break
            if run_steps.data[-1].status in ['expired', 'cancelled', 'failed']:
                raise ValueError("Run did not complete successfully")

        thread_messages = client.beta.threads.messages.list(thread.id)
        reply = thread_messages.data[0].content[0].text.value

        return jsonify({'reply': reply, 'error': None})
    except Exception as e:
        return jsonify({'reply': None, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.getenv("PORT", 5000))


# Gesture and its role in classroom communication: an issue for the personalised learning agenda