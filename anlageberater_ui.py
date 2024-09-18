import streamlit as st

st.title("AnlageberaterGPT")

with st.chat_message("assistant"):
    st.write("Hallo, ich bin Thomas👋 Ich bin ihr digitaler Anlageberater von der Musterbank eG und möchte Ihnen helfen, maßgeschneiderte Produkte für die Anlage und Aufbau Ihres Vermögens zu finden. Wir von der Musterbank eG bieten für die Vermögensverwaltung verschiedene Finanzprodukte an, die auf unterschiedliche Bedürfnisse und Lebenssituationen eingehen. Um Sie beraten zu können, möchte ich Sie mithilfe von ein paar Fragen zunächst genauer kennenlernen. Anschließend möchte ich Ihnen ein passendes Produkt vorstellen. Gerne beantworte ich Ihnen anschließend alle offenen Fragen zum Produkt oder zu anderen Themen. Fangen wir nun mit den Fragen an... 🙂")

with st.chat_message("assistant"):
    st.write("Wie heißen Sie?")

name = st.chat_input("Wie heißen Sie (Vorname und Nachname)?")

if name:
    with st.chat_message("user"):
        st.write(name)

    with st.chat_message("assistant"):
        st.write("Wieviel möchten Sie anlegen?")
