import hashlib

import streamlit as st
import chromadb
import pypdf
from ollama import chat


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Sophia — AI Business Analyst",
    page_icon="🤖",
    layout="centered"
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
        max-width: 850px;
    }

    .sophia-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sophia-subtitle {
        text-align: center;
        color: #777;
        font-size: 1.05rem;
        margin-bottom: 2.2rem;
    }

    .welcome-card {
        padding: 1.3rem 1.5rem;
        border-radius: 14px;
        background-color: rgba(128, 128, 128, 0.08);
        margin-bottom: 1.5rem;
    }

    .user-message {
        background-color: rgba(128, 128, 128, 0.08);
        padding: 0.8rem 1rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# MÉMOIRE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "document_name" not in st.session_state:
    st.session_state.document_name = "Aucun document"

if "document_hash" not in st.session_state:
    st.session_state.document_hash = None


# ============================================================
# CHROMADB
# ============================================================

client_chroma = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client_chroma.get_or_create_collection(
    name="company_report"
)


# ============================================================
# FONCTION D'INDEXATION
# ============================================================

def index_pdf(uploaded_file):

    reader = pypdf.PdfReader(uploaded_file)

    chunks = []
    metadatas = []
    ids = []

    chunk_size = 1200
    overlap = 150

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        if not text.strip():
            continue

        text = " ".join(
            text.split()
        )

        start = 0
        chunk_number = 0

        while start < len(text):

            end = start + chunk_size

            chunk = text[start:end].strip()

            if chunk:

                chunk_id = (
                    f"{uploaded_file.name}-"
                    f"page-{page_number}-"
                    f"chunk-{chunk_number}"
                )

                chunks.append(
                    chunk
                )

                metadatas.append(
                    {
                        "document": uploaded_file.name,
                        "page": page_number,
                        "chunk_id": chunk_id
                    }
                )

                ids.append(
                    chunk_id
                )

                chunk_number += 1

            start += chunk_size - overlap


    # Supprimer l'ancien document indexé
    if collection.count() > 0:
        collection.delete(
            ids=collection.get()["ids"]
        )


    # Ajouter le nouveau document
    batch_size = 50

    for start in range(
        0,
        len(chunks),
        batch_size
    ):

        end = start + batch_size

        collection.upsert(
            ids=ids[start:end],
            documents=chunks[start:end],
            metadatas=metadatas[start:end]
        )


    return (
        len(chunks),
        len(reader.pages)
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="sophia-title">🤖 Sophia</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sophia-subtitle">AI Business Analyst</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🤖 Sophia")

    st.write(
        "Votre AI Business Analyst locale."
    )

    st.divider()

    st.subheader("📄 Document")

    uploaded_file = st.file_uploader(
        "Ajouter un document PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )


    # --------------------------------------------------------
    # INDEXATION DU PDF
    # --------------------------------------------------------

    if uploaded_file is not None:

        file_bytes = uploaded_file.getvalue()

        file_hash = hashlib.sha256(
            file_bytes
        ).hexdigest()


        if (
            st.session_state.document_hash
            != file_hash
        ):

            with st.spinner(
                "📄 Sophia prépare le document..."
            ):

                chunk_count, page_count = index_pdf(
                    uploaded_file
                )


            st.session_state.document_name = (
                uploaded_file.name
            )

            st.session_state.document_hash = (
                file_hash
            )

            st.session_state.messages = []


            st.success(
                f"Document prêt · "
                f"{page_count} pages · "
                f"{chunk_count} passages"
            )


    st.write(
        f"**Document actuel :** "
        f"{st.session_state.document_name}"
    )

    st.caption(
        f"{collection.count()} passages indexés"
    )

    st.divider()

    st.subheader("🧠 Technologie")

    st.caption("Recherche : ChromaDB")
    st.caption("Modèle : Sophia")
    st.caption("Exécution : locale")

    st.divider()

    if st.button(
        "🗑️ Nouvelle conversation",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# MESSAGE D'ACCUEIL
# ============================================================

if not st.session_state.messages:

    if st.session_state.document_name == "Aucun document":

        st.markdown(
            """
            <div class="welcome-card">

            Bonjour 👋

            Je suis **Sophia**, votre AI Business Analyst.

            Ajoutez un document PDF dans la barre latérale
            pour commencer.

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            """
            <div class="welcome-card">

            Bonjour 👋

            Je suis **Sophia**, votre AI Business Analyst.

            Je peux analyser le contenu du document et répondre
            à vos questions en m'appuyant sur les informations
            pertinentes retrouvées dans celui-ci.

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# HISTORIQUE
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div class="user-message">
            {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        with st.chat_message(
            "assistant",
            avatar="🤖"
        ):

            st.markdown(
                message["content"]
            )

            if message.get("sources"):

                with st.expander(
                    "📚 Sources utilisées"
                ):

                    for i, source in enumerate(
                        message["sources"],
                        start=1
                    ):

                        st.markdown(
                            f"**📄 Page {source['page']}**"
                        )

                        st.write(
                            source["document"]
                        )

                        if i < len(message["sources"]):
                            st.divider()


# ============================================================
# BARRE DE QUESTION
# ============================================================

if st.session_state.document_name != "Aucun document":

    question = st.chat_input(
        "Demander à Sophia..."
    )

else:

    question = None


# ============================================================
# TRAITEMENT
# ============================================================

if question and question.strip():

    question = question.strip()


    # --------------------------------------------------------
    # QUESTION
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="user-message">
        {question}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    # --------------------------------------------------------
    # RECHERCHE
    # --------------------------------------------------------

    status_placeholder = st.empty()

    status_placeholder.info(
        "🤖 Sophia analyse les informations..."
    )


    results = collection.query(
        query_texts=[question],
        n_results=10,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )


    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]


    # --------------------------------------------------------
    # SÉLECTION DES PASSAGES
    # --------------------------------------------------------

    selected_documents = []
    selected_metadatas = []
    selected_distances = []

    seen_texts = set()

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        text_key = document[:300].strip().lower()

        if text_key in seen_texts:
            continue

        selected_documents.append(
            document
        )

        selected_metadatas.append(
            metadata
        )

        selected_distances.append(
            distance
        )

        seen_texts.add(
            text_key
        )

        if len(selected_documents) >= 5:
            break


    documents = selected_documents
    metadatas = selected_metadatas
    distances = selected_distances


    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    context_parts = []
    sources = []

    for i, (
        document,
        metadata
    ) in enumerate(
        zip(
            documents,
            metadatas
        ),
        start=1
    ):

        page = metadata.get(
            "page",
            "?"
        )

        context_parts.append(
            f"""
SOURCE {i}
PAGE : {page}

{document}
"""
        )

        sources.append(
            {
                "page": page,
                "document": document,
                "distance": distances[i - 1]
            }
        )


    context = "\n\n".join(
        context_parts
    )


    # --------------------------------------------------------
    # MÉMOIRE
    # --------------------------------------------------------

    conversation_history = ""

    for message in st.session_state.messages[-6:]:

        if message["role"] == "user":

            conversation_history += (
                f"Utilisateur : "
                f"{message['content']}\n"
            )

        elif message["role"] == "assistant":

            conversation_history += (
                f"Sophia : "
                f"{message['content']}\n"
            )


    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
Tu es Sophia, une assistante spécialisée en
Business Intelligence, Data Analysis et analyse
de documents d'entreprise.

Réponds à la question actuelle en utilisant
le contexte documentaire et l'historique récent.

RÈGLES :

- Les informations du document sont prioritaires.
- N'invente aucune information.
- Si le document ne permet pas de répondre,
  indique-le clairement.
- Utilise l'historique pour comprendre les références
  comme "il", "elle", "celui-ci", "ce risque", etc.
- Réponds dans la même langue que la question.
- Si l'utilisateur change de langue, adapte-toi.
- Sois naturelle, claire et professionnelle.
- Va directement à l'essentiel.
- Évite les répétitions.
- Ne répète pas inutilement la conversation.
- Lorsque c'est pertinent, indique les pages sources.
- Ne parle pas de ton fonctionnement interne.

HISTORIQUE RÉCENT :

{conversation_history}

QUESTION ACTUELLE :

{question}

CONTEXTE DOCUMENTAIRE :

{context}
"""


    # --------------------------------------------------------
    # RÉPONSE
    # --------------------------------------------------------

    status_placeholder.empty()

    with st.chat_message(
        "assistant",
        avatar="🤖"
    ):

        response_placeholder = st.empty()

        response_placeholder.markdown(
            "🤖 **Sophia analyse les informations...**"
        )

        answer = ""

        stream = chat(
            model="sophia",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=True
        )

        first_token = True

        for chunk in stream:

            content = chunk.message.content

            if content:

                answer += content

                if first_token:

                    response_placeholder.markdown(
                        "..."
                    )

                    first_token = False

                response_placeholder.markdown(
                    answer
                )


    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    with st.expander(
        "📚 Sources utilisées"
    ):

        for i, source in enumerate(
            sources,
            start=1
        ):

            st.markdown(
                f"**📄 Page {source['page']}**"
            )

            st.write(
                source["document"]
            )

            if i < len(sources):
                st.divider()


    # --------------------------------------------------------
    # MÉMOIRE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources
        }
    )