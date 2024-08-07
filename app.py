import streamlit as st
from langchain.vectorstores import FAISS
from qa.retrieval_and_generation import get_groq_llm, get_response_llm
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

if "GROQ_API_KEY" not in os.environ:
    st.error("Please set the GROQ_API_KEY environment variable.")
    st.stop()

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

st.set_page_config(page_title="QA with DOC", page_icon="📚")

st.header("📚 Chatbot")

# Add custom CSS for text wrapping
st.markdown("""
    <style>
    .source-container {
        overflow-wrap: break-word;
        word-wrap: break-word;
        hyphens: auto;
        white-space: normal;
    }
    </style>
    """, unsafe_allow_html=True)

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = {"messages": [], "chat_history": []}
if "new_chat" not in st.session_state:
    st.session_state.new_chat = False

def start_new_chat():
    st.session_state.conversation_history.append(st.session_state.current_conversation)
    st.session_state.current_conversation = {"messages": [], "chat_history": []}
    st.session_state.new_chat = True

def load_chat(index):
    st.session_state.current_conversation = st.session_state.conversation_history[index]
    st.session_state.new_chat = True

with st.sidebar:
    st.subheader("Conversations")
    if st.button("Start New Chat"):
        start_new_chat()

    for i, conv in enumerate(st.session_state.conversation_history):
        if st.button(f"Load Chat {i+1}"):
            load_chat(i)

faiss_index = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
llm = get_groq_llm()

# Display existing messages
for message in st.session_state.current_conversation["messages"]:
    role = message['role']
    content = message['content']
    if role == "user":
        st.chat_message("user").write(content)
    else:
        st.chat_message("assistant").write(content)
        if "sources" in message:
            with st.expander("Sources"):
                for source in message["sources"].split("\n\n"):
                    st.markdown(f"<div class='source-container'>{source.strip()}</div>", unsafe_allow_html=True)

# Handle new user input
if prompt := st.chat_input("Ask a question from the PDF files"):
    st.session_state.current_conversation["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Processing..."):
        chat_history = [(msg["content"], msg["content"]) for msg in st.session_state.current_conversation["messages"] if msg["role"] == "assistant"]

        response = get_response_llm(llm, faiss_index, prompt, chat_history)

        st.chat_message("assistant").write(response['answer'])

        assistant_msg = {
            "role": "assistant",
            "content": response["answer"],
            "sources": response["sources"]
        }
        st.session_state.current_conversation["messages"].append(assistant_msg)

        with st.expander("Sources"):
            for source in response["sources"].split("\n\n"):
                st.markdown(f"<div class='source-container'>{source.strip()}</div>", unsafe_allow_html=True)
