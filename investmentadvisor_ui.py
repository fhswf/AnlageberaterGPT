from investmentadvisor_be import *

st.title("Investi AI - Digitale Anlageberatung")

antworten = ""

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content":
        """Hallo, ich bin Investi👋 Ich bin Ihr digitaler Anlageberater von der Musterbank eG und möchte Ihnen 
        helfen, maßgeschneiderte Produkte für die Anlage und zur Aufbau Ihres Vermögens zu finden. Wir von der 
        Musterbank eG bieten für die Vermögensverwaltung verschiedene Finanzprodukte an, die auf unterschiedliche 
        Bedürfnisse und Lebenssituationen eingehen. Um Sie beraten zu können, möchte ich Sie mithilfe von ein paar 
        Fragen zunächst genauer kennenlernen. Anschließend möchte ich Ihnen ein passendes Produkt vorstellen. Gerne 
        beantworte ich Ihnen anschließend alle offenen Fragen zum Produkt oder zu anderen Themen. Fangen wir nun mit 
        den Fragen an... 🙂"""}]

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
    "Wieviel möchten Sie anlegen?",
    "Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)?",
    "Wie würden Sie Ihre Risikobereitschaft einschätzen (z. B. kein Risiko, mittleres Risiko, hohes Risiko)?",
    "Haben Sie in der Vergangenheit bereits riskante Investments getätigt (z. B. Aktien, Derivate) und wie haben Sie "
    "sich dabei gefühlt?",
    "Was ist Ihnen wichtiger: keine Kosten oder die Möglichkeit, mehr aus Ihrer Anlage herauszuholen?",
    "Insofern in unserem Produktportfolio vorhanden, interessieren Sie sich für nachhaltige Anlageprodukte?"
]


def increment(key):
    st.session_state.questionCounter += 1
    if st.session_state.questionCounter <= len(questions):
        st.session_state.messages.append({"role": "user", "content": st.session_state[key]})
        st.session_state.answers += questions[st.session_state.questionCounter - 1] + " " + st.session_state[key] + ", "


@st.fragment
def provide_productinformation_sheet():
    path = st.session_state.document_path
    new_path = path.replace('\\', '/')
    with open(new_path, "rb") as pdf_file:
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

    user_input = st.chat_input("Sende eine Nachricht an den digitalen Anlageberater", on_submit=increment,
                               key='chat_key',
                               args=("chat_key",))

elif st.session_state.questionCounter == len(questions):
    with st.spinner("Bitte warten... Ich suche Ihr passendes Anlageprodukt"):
        call_graph(st.session_state.answers)
        produktempfehlung = st.session_state.messages[-1]
        with st.chat_message(produktempfehlung["role"]):
            st.write(produktempfehlung["content"])
            # Stelle Produktinformationsblatt bereit
            provide_productinformation_sheet()
            increment("chat_key")
        with st.chat_message("assistant"):
            intro_rag_questions = """Wir hoffen, dass wir mit dem Produkt Ihr Interesse geweckt haben. Sehr gerne 
            möchte ich nun Ihre offenen Fragen zum Produkt beantworten. Wenn Sie fertig sind, können Sie die Seite 
            einfach verlassen. Das empfohlene Produkt habe ich Ihnen in der Übersicht im Online-Banking hinterlegt."""
            st.write(intro_rag_questions)
            st.session_state.messages.append({"role": "assistant", "content": intro_rag_questions})

if st.session_state.questionCounter > len(questions):
    if prompt := st.chat_input("Haben Sie noch weitere Fragen?"):
        with st.chat_message("user"):
            response = st.write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            st.write(answer_with_rag(prompt))
