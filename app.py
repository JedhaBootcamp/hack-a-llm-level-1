import os
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# On Hugging Face, the system prompt (which contains the flags) is a Space secret,
# so students cannot read it in the "Files" tab. Locally, it comes from prompts.py.
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")
if not SYSTEM_PROMPT:
    from prompts import SYSTEM_PROMPT

# ---------- Streamlit config ---------- #
st.set_page_config(
    page_title="LLM from XYZ consulting",
    page_icon="🤖",
    layout="wide"
) #[cite: 2]

# ---------- Logique d'authentification ---------- #
def check_password():
    """Retourne True si l'utilisateur a entré le bon mot de passe."""
    
    def password_entered():
        """Vérifie si le mot de passe entré correspond."""
        # Il est recommandé de passer ce mot de passe en variable d'environnement
        # Par exemple : os.environ.get("APP_PASSWORD", "jedha_secret")
        correct_password = os.environ.get("APP_PASSWORD", "J3DH4G4P3TR41N1NG5") 
        
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            # On supprime le mot de passe de la session par sécurité
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Premier chargement : on affiche le champ
        st.title("🔒 Accès Restreint")
        st.text_input("Veuillez entrer le mot de passe pour accéder à l'exercice :", type="password", on_change=password_entered, key="password")
        return False
    
    elif not st.session_state["password_correct"]:
        # Mot de passe incorrect : on réaffiche le champ avec une erreur
        st.title("🔒 Accès Restreint")
        st.text_input("Veuillez entrer le mot de passe pour accéder à l'exercice :", type="password", on_change=password_entered, key="password")
        st.error("😕 Mot de passe incorrect.")
        return False
    
    else:
        # Mot de passe correct
        return True

# ---------- Application Principale ---------- #
# On ne lance l'app LLM que si le mot de passe est bon
if check_password():
    
    # ---------- LangChain setup (no deprecated memory) ---------- #
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna") #[cite: 2]

    if not OPENAI_API_KEY:
        raise RuntimeError("Please set the OPENAI_API_KEY environment variable.") #[cite: 2]

    # Prompt: system + history + latest user input
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{input}"),
    ]) #[cite: 2]

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        reasoning_effort="none",  # gpt-6-luna is a reasoning model: no temperature allowed
        max_tokens=1000,
        streaming=True,  # IMPORTANT for .stream()
    ) #[cite: 2]

    # LCEL chain: prompt -> model
    chain = prompt | llm #[cite: 2]

    st.title("XYZ-PT 🏢") #[cite: 2]

    # ---------- Chat history in Streamlit ---------- #
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello there, how can I help you today?"}
        ] #[cite: 2]

    def build_history(k: int = 3):
        """
        Convert Streamlit messages into a list of (role, content) tuples
        for the last k turns (user+assistant).
        """
        msgs = [m for m in st.session_state.messages if m["role"] in ("user", "assistant")]
        msgs = msgs[-2 * k:]  # last k turns (user+assistant → 2 messages/turn) #[cite: 2]

        history = [
            ("human" if m["role"] == "user" else "ai", m["content"])
            for m in msgs
        ]
        return history #[cite: 2]

    # ---------- Display past messages ---------- #
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"]) #[cite: 2]

    # ---------- Streaming generator for st.write_stream ---------- #
    def stream_llm_response(user_input: str, history):
        """
        Wrap chain.stream so that we can feed tokens/chunks
        directly into st.write_stream.
        """
        for chunk in chain.stream({"history": history, "input": user_input}):
            # chunk is an AIMessageChunk; chunk.content is the incremental text
            if chunk.content:
                yield chunk.content #[cite: 2]

    # ---------- User input + streaming answer ---------- #
    user_prompt = st.chat_input() #[cite: 2]

    if user_prompt:
        # Store + display user message
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt) #[cite: 2]

        # Build history window (similar to previous ConversationBufferWindowMemory k=3)
        history = build_history(k=3) #[cite: 2]

        # Stream assistant response
        with st.chat_message("assistant"):
            with st.spinner("loading..."):
                # st.write_stream returns the concatenated final text
                ai_response = st.write_stream(
                    stream_llm_response(user_prompt, history)
                ) #[cite: 2]

        # Save assistant reply
        st.session_state.messages.append(
            {"role": "assistant", "content": ai_response}
        ) #[cite: 2]
