import sys
import json
import os
import streamlit as st
from langchain_community.document_loaders.text import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain

# Global variables
DB_FAISS_PATH = "POC/vectorstore/db_faiss"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
GEMINI_TOKEN = 'your token'
TRANSCRIPT_PATH = '../Transcription_server/data/transcript_dump.txt'
st.set_page_config(page_title="BITS Lecture Assistant Chatbot", page_icon="🎓")

# Initialize chat history as a list of tuples
if 'qa_history' not in st.session_state:
    st.session_state.qa_history = []

# Define function to handle user input and generate response
def handle_input(query, query1):
    transcript=None
    with open(file=TRANSCRIPT_PATH) as file:
        transcript = file.readlines()
    loader = TextLoader(file_path=TRANSCRIPT_PATH, encoding="utf-8")
    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks = text_splitter.split_documents(data)
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    docsearch = FAISS.from_documents(text_chunks, embeddings)
    llm_2 = ChatGoogleGenerativeAI(google_api_key=GEMINI_TOKEN, model='gemini-1.0-pro',
                                   convert_system_message_to_human=True, temperature=0.5, top_p=0.95, top_k=10)
    qa = ConversationalRetrievalChain.from_llm(llm_2, retriever=docsearch.as_retriever())

    if query.strip() == 'exit':
        st.write('Exiting')
        sys.exit()
    elif query.strip() == '':
        st.write("Please give a valid input")
    else:
        curr_query=query
        query = f'''
 --------------------- Class Meeting Transcripts So Far ---------

 {json.dumps(transcript,indent=2)}

 -------------

 {query}
 '''
        try:
            result = qa({"base-prompt": query1, "question": query, "chat_history": []})
            st.session_state.qa_history.append((curr_query, result['answer']))  # Append question-answer tuple
            st.write("Response: ", result['answer'])
        except ValueError as e:
            st.error(f"Error: {e}")

# Main Streamlit app
def main():
    st.title("Hello students! 👋")
    st.write("I am your lecture assistant chatbot and will answer all your doubts related to this lecture. Please ask anything on today's lecture 🤖")


    # Input form for user query
    with st.form(key='user_input'):
        query = st.text_input("Ask me anything...📚")
        submit_button = st.form_submit_button(label='Submit')

    # Handle user input upon form submission
    if submit_button:
        query1 = '''
            Base-Prompt:
            You are a Learning co-pilot, You need to make sure you answer to the questions that are being asked keeping in mind the context.
            1. Answer the questions - to the point .
            2. You are just like a very knowledgeable student who is attending the class along with the others.
            3. Try to make sure that with your own Knowledge base, you take the data that is fed to you as a primary context.'''
        
        handle_input(query, query1)

    # Display chat history
    st.subheader("Chat History:")
    for question, answer in st.session_state.qa_history:
        st.write(f"Question: {question}")
        st.write(f"Answer: {answer}")
# Run the Streamlit app
if __name__ == "__main__":
    main()
