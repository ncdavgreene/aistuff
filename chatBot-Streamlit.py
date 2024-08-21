import streamlit as st
import requests
import json
import time

# Configuration
base_url = "http://localhost:8283/"
admin_password = "KEY"  # Replace with your actual admin password
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {admin_password}"
}

st.title("SadisticAI Chat")

# Check if MemGPT server and agents are available
agent_details_URL = base_url + "api/agents"
response = requests.get(agent_details_URL, headers=headers)

try:
    agents_data = response.json()
    if 'agents' in agents_data and isinstance(agents_data['agents'], list):
        agents = agents_data['agents']
        agent_name = st.selectbox("Choose agent", [agent['name'] for agent in agents], index=0)
        agent_id = [agent['id'] for agent in agents if agent['name'] == agent_name][0]
    else:
        st.warning('Unexpected response format from MemGPT server', icon="⚠️")
        print(agents_data)  # To understand what the server is returning
except ValueError:
    st.warning('Failed to parse the response from MemGPT server as JSON', icon="⚠️")
    print(response.text)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Add animated "Thinking..." indicator
    with st.chat_message("assistant"):
        thinking_message_placeholder = st.empty()

        # Start the animation loop
        for _ in range(10):  # Adjust the range for the duration of the animation
            for dots in range(1, 4):  # Cycles through 1, 2, 3 dots
                thinking_message_placeholder.markdown(f"**Thinking{'.' * dots}**")
                time.sleep(0.5)  # Adjust speed of animation
            thinking_message_placeholder.markdown("**Thinking...**")  # Reset dots

    # Send message to the MemGPT agent
    send_message_URL = f"{base_url}api/agents/{agent_id}/messages"
    payload = {
        "agent_id": agent_id,
        "message": prompt,
        "stream": False,
        "role": "user"
    }
    response = requests.post(send_message_URL, json=payload, headers=headers)
    if response.status_code != 200:
        st.warning('Failed to communicate with MemGPT', icon="⚠️")
    else:
        try:
            response_data = response.json()
            print("Full response from MemGPT:", response_data)

            assistant_message = None
            for msg in response_data.get('messages', []):
                if "function_call" in msg and msg["function_call"]["name"] == "send_message":
                    arguments = json.loads(msg["function_call"]["arguments"])
                    assistant_message = arguments.get("message")

            if not assistant_message:
                st.warning('Missing assistant message in response', icon="⚠️")
                thinking_message_placeholder.empty()  # Remove the "Thinking..." indicator
            else:
                # Replace "Thinking..." with the actual assistant response
                thinking_message_placeholder.markdown(assistant_message)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})

        except ValueError:
            st.warning('Failed to parse the assistant response from MemGPT server as JSON', icon="⚠️")
            thinking_message_placeholder.empty()  # Remove the "Thinking..." indicator
            print(response.text)
