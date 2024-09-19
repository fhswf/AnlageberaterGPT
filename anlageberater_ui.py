import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

st.title("AnlageberaterGPT")

# Initialisiere Chat message Historie
chat_history = StreamlitChatMessageHistory()

# Setze initial einen Step-Zaehler in session_state

step = 1

with st.chat_message("assistant"):
    st.write(
        "Hallo, ich bin Thomas👋 Ich bin ihr digitaler Anlageberater von der Musterbank eG und möchte Ihnen helfen, "
        "maßgeschneiderte Produkte für die Anlage und Aufbau Ihres Vermögens zu finden. Wir von der Musterbank eG "
        "bieten für die Vermögensverwaltung verschiedene Finanzprodukte an, die auf unterschiedliche Bedürfnisse und "
        "Lebenssituationen eingehen. Um Sie beraten zu können, möchte ich Sie mithilfe von ein paar Fragen zunächst "
        "genauer kennenlernen. Anschließend möchte ich Ihnen ein passendes Produkt vorstellen. Gerne beantworte ich "
        "Ihnen anschließend alle offenen Fragen zum Produkt oder zu anderen Themen. Fangen wir nun mit den Fragen "
        "an... 🙂")

if step == 1:
    print(step)
    with st.chat_message("assistant"):
        st.write("Wie heißen Sie?")

    name = st.chat_input("Wie heißen Sie (Vorname und Nachname)?")

    if name:
        print("TestName + Steps")
        with st.chat_message("user"):
            st.write(name)
        step += 1

if step == 2:
    print(step)
    with st.chat_message("assistant"):
        st.write("Wieviel möchten Sie anlegen?")

    value = st.chat_input("Wieviel möchten Sie anlegen (in Euro)?")

    if value:
        print("TestValue + Steps")
        with st.chat_message("user"):
            st.write(value)
        step += 1

if step == 3:
    print(step)
    with st.chat_message("assistant"):
        st.write("Wie hoch ist Ihre Risikobereitschaft?")

    riskTolerance = st.chat_input("Wie hoch ist Ihre Risikobereitschaft??")

    if riskTolerance:
        print("TestRisk + Steps")
        with st.chat_message("user"):
            st.write(riskTolerance)
        step += 1
