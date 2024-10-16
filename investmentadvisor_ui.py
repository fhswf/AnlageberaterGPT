import streamlit as st
from investmentadvisor_be import *
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

st.title("AnlageberaterGPT")

antworten = ""

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content":
        "Hallo, ich bin Thomas👋 Ich bin ihr digitaler Anlageberater von der Musterbank eG und möchte Ihnen helfen, "
        "maßgeschneiderte Produkte für die Anlage und Aufbau Ihres Vermögens zu finden. Wir von der Musterbank eG "
        "bieten für die Vermögensverwaltung verschiedene Finanzprodukte an, die auf unterschiedliche Bedürfnisse und "
        "Lebenssituationen eingehen. Um Sie beraten zu können, möchte ich Sie mithilfe von ein paar Fragen zunächst "
        "genauer kennenlernen. Anschließend möchte ich Ihnen ein passendes Produkt vorstellen. Gerne beantworte ich "
        "Ihnen anschließend alle offenen Fragen zum Produkt oder zu anderen Themen. Fangen wir nun mit den Fragen "
        "an... 🙂"}]

# Initialisiere Session-State
if 'questionCounter' not in st.session_state:
    st.session_state.questionCounter = 0

if 'answers' not in st.session_state:
    st.session_state.answers = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Liste der Fragen
questions = [
    "Wie heißen Sie?",
    "Wieviel möchten Sie anlegen?",
    # "Wie hoch ist Ihre Bereitschaft, Verluste in Kauf zu nehmen?",
    # "Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)?"
]


def increment(key):
    st.session_state.questionCounter += 1
    st.session_state.messages.append({"role": "user", "content": st.session_state[key]})
    st.session_state.answer += st.session_state[key]


if st.session_state.questionCounter < len(questions):
    with st.chat_message("assistant"):
        st.write(questions[st.session_state.questionCounter])
        st.session_state.messages.append({"role": "assistant", "content": questions[st.session_state.questionCounter]})

    user_input = st.chat_input(questions[st.session_state.questionCounter], on_submit=increment, key='chat_key',
                               args=("chat_key",))

elif st.session_state.questionCounter == len(questions):
    # ToDo: Produktempfehlung auf Basis der Antworten
    with st.spinner("Bitte warten... Ich suche ihr passendes Anlageprodukt"):
        # call_graph()
        # ToDo: Antworten formatieren und Logik übergeben
        print(st.session_state.answers)
        produktempfehlung = st.session_state.messages[-1]
        with st.chat_message(produktempfehlung["role"]):
            st.markdown(produktempfehlung["content"])
        increment("chat_key")
        print(st.session_state.messages)

# ToDo: RAG mit Produkt
