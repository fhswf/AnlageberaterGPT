import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

st.title("AnlageberaterGPT")

# ToDo: Implementiere UI fuer Chatbot

# Initialisiere Chat Message Historie
chat_history = StreamlitChatMessageHistory()

# Liste der Fragen
questions = [
    "Wie heißen Sie?",
    "Wieviel möchten Sie anlegen?",
    "Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)?",
    "Wie hoch ist Ihre Bereitschaft, Verluste in Kauf zu nehmen?",
    "Bevorzugen Sie bestimmte Anlageformen (z. B. Immobilien, Aktien, Anleihen, Kryptowährungen)?",
]

# Initialisiere Session-State
if 'questionCounter' not in st.session_state:
    st.session_state.questionCounter = 0


def increment(key):
    st.session_state.questionCounter += 1
    chat_history.add_user_message(st.session_state[key])
    print(chat_history.messages)


if len(chat_history.messages) == 0:
    chat_history.add_ai_message(
        "Hallo, ich bin Thomas👋 Ich bin ihr digitaler Anlageberater von der Musterbank eG und möchte Ihnen helfen, "
        "maßgeschneiderte Produkte für die Anlage und Aufbau Ihres Vermögens zu finden. Wir von der Musterbank eG "
        "bieten für die Vermögensverwaltung verschiedene Finanzprodukte an, die auf unterschiedliche Bedürfnisse und "
        "Lebenssituationen eingehen. Um Sie beraten zu können, möchte ich Sie mithilfe von ein paar Fragen zunächst "
        "genauer kennenlernen. Anschließend möchte ich Ihnen ein passendes Produkt vorstellen. Gerne beantworte ich "
        "Ihnen anschließend alle offenen Fragen zum Produkt oder zu anderen Themen. Fangen wir nun mit den Fragen "
        "an... 🙂")

for message in chat_history.messages:
    with st.chat_message(message.type):
        st.write(message.content)

if st.session_state.questionCounter < len(questions):
    with st.chat_message("assistant"):
        st.write(questions[st.session_state.questionCounter])
        chat_history.add_ai_message(questions[st.session_state.questionCounter])

    user_input = st.chat_input(questions[st.session_state.questionCounter], on_submit=increment, key='chat_key',
                               args=("chat_key",))
else:
    print(chat_history.messages)
    st.write("Ende")
