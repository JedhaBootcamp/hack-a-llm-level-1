import os
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts import SYSTEM_PROMPT


# ---------- LangChain setup (no deprecated memory) ---------- #

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

# Prompt: system + history + latest user input
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history", optional=True),
    ("human", "{input}"),
])

llm = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=OPENAI_API_KEY,
    temperature=0.7,
    max_tokens=1000,
    streaming=True,  # IMPORTANT for .stream()
)

# LCEL chain: prompt -> model
chain = prompt | llm


# ---------- Streamlit config ---------- #

st.set_page_config(
    page_title="LLM from XYZ consulting",
    page_icon="🤖",
    layout="wide"
)

st.title("XYZ-PT 🏢")


# ---------- Chat history in Streamlit ---------- #

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello there, how can I help you today?"}
    ]


def build_history(k: int = 3):
    """
    Convert Streamlit messages into a list of (role, content) tuples
    for the last k turns (user+assistant).
    """
    msgs = [m for m in st.session_state.messages if m["role"] in ("user", "assistant")]
    msgs = msgs[-2 * k:]  # last k turns (user+assistant → 2 messages/turn)

    history = [
        ("human" if m["role"] == "user" else "ai", m["content"])
        for m in msgs
    ]
    return history


# ---------- Display past messages ---------- #

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# ---------- Streaming generator for st.write_stream ---------- #

def stream_llm_response(user_input: str, history):
    """
    Wrap chain.stream so that we can feed tokens/chunks
    directly into st.write_stream.
    """
    for chunk in chain.stream({"history": history, "input": user_input}):
        # chunk is an AIMessageChunk; chunk.content is the incremental text
        if chunk.content:
            yield chunk.content


# ---------- User input + streaming answer ---------- #

user_prompt = st.chat_input()

if user_prompt:
    # Store + display user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # Build history window (similar to previous ConversationBufferWindowMemory k=3)
    history = build_history(k=3)

    # Stream assistant response
    with st.chat_message("assistant"):
        with st.spinner("loading..."):
            # st.write_stream returns the concatenated final text
            ai_response = st.write_stream(
                stream_llm_response(user_prompt, history)
            )

    # Save assistant reply
    st.session_state.messages.append(
        {"role": "assistant", "content": ai_response}
    )
