import streamlit as st
import pandas as pd

file_button_counter = 0

def increment_counter():
    global file_button_counter
    return_value = file_button_counter
    file_button_counter += 1
    return return_value

st.title("Investing in the Future: A Deep Dive into the Stock Market")


# Sidebar configuration
with st.sidebar:
    st.header("📊 Stock Market Analysis")
    st.write("Explore the latest trends and insights in the stock market.")
    st.write("Use the sidebar to navigate through different sections.")

# Initialize session state for messages if not already present
if "messages" not in st.session_state:
    st.session_state.setdefault("messages", [])

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["files"]:
            files = [st.download_button(label=file["name"], data=file["data"], file_name=file["name"], icon="📄", key=f"file_btn_{increment_counter()}") for file in message["files"]]

# Chat input for user interaction
if prompt := st.chat_input("Start a conversation",
                           accept_file="multiple",
                           file_type=["pdf", "csv", "txt"]):
    # Store user input in session state
    with st.chat_message("user"):
        req_prompt = ""
        files = []
        files_dict = []
        if prompt.text:
            req_prompt = prompt["text"]
            st.markdown(req_prompt)
        if prompt.files:
            files = [st.download_button(label=file.name, data=file, file_name=file.name, icon="📄", key=f"file_btn_{increment_counter()}") for file in prompt.files]
            files_dict = [{"name": file.name, "data": file} for file in prompt.files]
        st.session_state.messages.append({"role": "user", "content": req_prompt, "files": files_dict})
        
    # Simulate a response from a model (placeholder)
    with st.chat_message("assistant"):
        ans = "This is a placeholder response. Replace with actual model response."
        st.session_state.messages.append({"role": "assistant", "content": ans, "files": []})
        st.markdown(ans)