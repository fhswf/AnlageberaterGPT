from investmentadvisor_be import *

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

if 'produktnummer' not in st.session_state:
    st.session_state.produktnummer = int()

if 'document_path' not in st.session_state:
    st.session_state.document_path = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Liste der Fragen
questions = [
    "Wie heißen Sie?",
    "Wieviel möchten Sie anlegen?",
    "Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)?",
    "Wie hoch ist Ihre Bereitschaft, Verluste in Kauf zu nehmen?",
]


def increment(key):
    st.session_state.questionCounter += 1
    if st.session_state.questionCounter < len(questions):
        st.session_state.messages.append({"role": "user", "content": st.session_state[key]})
    st.session_state.answers += ", " + st.session_state[key]


@st.fragment
def provide_productinformation_sheet():
    with open(st.session_state.document_path, "rb") as pdf_file:
        pdfbyte = pdf_file.read()
        st.download_button(label="Download Produktinformationsblatt",
                           icon=":material/download:",
                           data=pdfbyte,
                           file_name="produktinformationsblatt.pdf",
                           mime='application/octet-stream')


if st.session_state.questionCounter < len(questions):
    with st.chat_message("assistant"):
        st.write(questions[st.session_state.questionCounter])
        st.session_state.messages.append({"role": "assistant", "content": questions[st.session_state.questionCounter]})

    user_input = st.chat_input(questions[st.session_state.questionCounter], on_submit=increment, key='chat_key',
                               args=("chat_key",))

elif st.session_state.questionCounter == len(questions):
    with st.spinner("Bitte warten... Ich suche ihr passendes Anlageprodukt"):
        # ToDo: Produktinformationsblatt als PDF anbieten
        call_graph(st.session_state.answers)
        produktempfehlung = st.session_state.messages[-1]
        with st.chat_message(produktempfehlung["role"]):
            st.write(produktempfehlung["content"])
            # Stelle Produktinformationsblatt bereit
            provide_productinformation_sheet()
            increment("chat_key")
        with st.chat_message("assistant"):
            st.write("Haben Sie noch weitere Fragen?")
            st.session_state.messages.append({"role": "assistant", "content": "Haben Sie noch weitere Fragen?"})

if st.session_state.questionCounter > len(questions):
    if prompt := st.chat_input("Haben Sie noch weitere Fragen?"):
        with st.chat_message("user"):
            response = st.write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            st.write(answer_with_rag(prompt))
