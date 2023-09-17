import streamlit as st
import os
import requests
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    Language,
)
from langchain.chat_models import ChatOpenAI
from prompts_collection import unit_tests_generator
from langchain.schema.output_parser import StrOutputParser
import shutil

st.set_page_config(layout="wide", )


# Create a text input box to allow the user to enter the download folder path
download_folder = os.path.join("streamlit_apps", "data")
code_folder = 'streamlit_apps/code_files'

openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key (mandatory)", type="password")
st.sidebar.divider()
openai_model = st.sidebar.selectbox("Model", options=["gpt-3.5-turbo","gpt-3.5-turbo-16k", "gpt-4.0"])
openai_temperature = st.sidebar.slider(label="Temperature", min_value=0.0, max_value=1.0, step=0.05, value=1.0)
st.sidebar.divider()


openai_data = {
    "openai_api_key":openai_api_key,
    "openai_model":openai_model,
    "openai_temperature":openai_temperature
}

st.sidebar.write("Code Splitting Parameters")
chunk_size = st.sidebar.number_input(label="Chunk Size",min_value=100, max_value=3500, step=100, value=1000)
chunk_overlap = st.sidebar.number_input(label="Chunk Size",min_value=0, max_value=3500, step=10, value=100)
# Create the target directory to save the code files
os.makedirs(code_folder, exist_ok=True)

# Create a dictionary variable to map file extensions to languages
file_extensions = {
    '.py': {'language': 'Python', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},
    '.js': {'language': 'JavaScript', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.JS, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},
    '.jsx': {'language': 'JavaScript', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.JS, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},    
    '.java': {'language': 'Java', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.JAVA, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},
    '.ts': {'language': 'TypeScript', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.JS, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},    
    '.cpp': {'language': 'C++', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.CPP, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},    
    '.go': {'language': 'Go', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.GO, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},    
    '.rb': {'language': 'Ruby', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.RUBY, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},
    '.php': {'language': 'PHP', 'splitter': RecursiveCharacterTextSplitter.from_language(language=Language.PHP, chunk_size=chunk_size, chunk_overlap=chunk_overlap)},
    '.cs': {'language': 'C#', 'splitter': RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)}          
}

# Function to delete the temp folder and its contents
def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
        # st.write(f"Deleted folder: {folder_path}")
    except Exception as e:
        st.write(f"Error deleting folder: {e}")


def get_document_details(document):
    extension = "."+os.path.basename(document.metadata["source"]).split('.')[1]

    spliiter = file_extensions.get(extension, {"splitter": None}).get("splitter")
    language = file_extensions.get(extension, {"language": None}).get("language") 
    
    return spliiter, language

@st.cache_data
def convert_to_api_url(github_repo_url):
    # Extract the username/organization and repository name
    username_repo = github_repo_url.split('github.com/')[1].split('/')

    # Extract the folder path
    folder_path = github_repo_url.split(f'github.com/{username_repo[0]}/{username_repo[1]}/')[1]

    # Construct the GitHub API URL
    api_url = f"https://api.github.com/repos/{username_repo[0]}/{username_repo[1]}/contents"
    
    return api_url


@st.cache_data
# Function to fetch and save files
def fetch_and_save_files(api_url, path=''):
    # Send a GET request to the GitHub API
    response = requests.get(api_url)

    # Check if the request was successful
    if response.status_code == 200:
        contents = response.json()
        for item in contents:
            if item['type'] == 'file':
                file_url = item['download_url']
                file_name = item['name']

                # Check if the file extension is in the valid_ext array
                file_extension = os.path.splitext(file_name)[1]
                if file_extension in list(file_extensions.keys()):
                    # Create subdirectories if needed
                    os.makedirs(os.path.join(code_folder, path), exist_ok=True)

                    # Send a GET request to the raw file URL
                    file_response = requests.get(file_url)

                    # Save the file as a text document
                    with open(os.path.join(code_folder, path, file_name), 'w', encoding='utf-8') as code_file:
                        code_file.write(file_response.text)
            elif item['type'] == 'dir':
                # Recursively fetch and save files from subfolders
                fetch_and_save_files(item['url'], os.path.join(path, item['name']))

    print(f'All valid files saved in the {code_folder} directory.')


@st.cache_data
# Create a function to download the uploaded files
def upload_files(uploaded_files):

    for uploaded_file in uploaded_files:
        with open(os.path.join(code_folder, uploaded_file.name), 'wb') as f:
            f.write(uploaded_file.getbuffer())

# Load all downloaded files
@st.cache_data
def load_docs(code_folder):
    print("Loading the file!!")
    loader = DirectoryLoader(code_folder)
    docs = loader.load()
    return docs

# Split all loaded docs
def split_docs(docs):
    
    splitted_docs =[]

    for doc in docs:
        splitter, language = get_document_details(doc)

        if not splitter:
            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        doc_split = splitter.split_documents(documents=docs)
        splitted_docs.extend(doc_split)
    # print(len(python_docs))
    print(splitted_docs[0])  
    return splitted_docs 

# Create a function to save all the file names in a dictionary variable
def save_file_names(code_folder):
    file_names = {}
    for file in os.listdir(code_folder):
        if os.path.splitext(file)[1] in file_extensions:
            file_names[file] = file_extensions[os.path.splitext(file)[1]]
    return file_names

def generate_unit_tests(document, openai_data):

    model = ChatOpenAI(openai_api_key=openai_data["openai_api_key"], model=openai_data["openai_model"], temperature=openai_data["openai_temperature"])
    prompt = unit_tests_generator()
    chain = prompt | model | StrOutputParser()
    
    splitter, language = get_document_details(document)

    answer = chain.invoke({"code":document.page_content, "language":language})    

    return answer

def main():




    # Streamlit UI

    st.title(":test_tube: Unit Test Generator")

    st.caption(body="Either add Github Repo URL or Upload Code Files")


    col1, col2 = st.columns(2)

    with col1:
        github_url = st.text_area("Enter Public :globe_with_meridians: GitHub Repository URL:", placeholder="github repo url", height=50)
    if github_url:
        api_url = convert_to_api_url(github_url)
        st.success(f"API URL: {api_url}")
    
    
    if not github_url:
        with col2:
            uploaded_files = st.file_uploader('Upload files', accept_multiple_files=True)
    
    generate = st.button('Generate Unit Tests') 

    if generate:

        if github_url:
            api_url = convert_to_api_url(github_url)
            fetch_and_save_files(api_url)
    
        elif not github_url and uploaded_files:
            upload_files(uploaded_files)      
        
        docs = load_docs(code_folder)
        splitted_docs = split_docs(docs)

        with st.expander(f"There will be approximately {len(splitted_docs)} API call(s) made to OpenAI and upto {len(splitted_docs)*4000} tokens used. Are you sure you want to continue?"):
            col1, col2 = st.columns(2)
            with col1:
                confirmation_button = st.button("Yes, continue")
            with col2:
                cancel_button = st.button("Cancel")
            if confirmation_button:
                for document in splitted_docs:
                    splitter, language = get_document_details(document)
                    st.write(f"FileName: {os.path.basename(document.metadata['source'])}")
                    st.code(generate_unit_tests(document, openai_data), language=language)
            if cancel_button:
                pass                
    delete_folder(code_folder)
    
if __name__ == "__main__":
    main()
