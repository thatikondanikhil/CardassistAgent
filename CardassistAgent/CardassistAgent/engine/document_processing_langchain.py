import os
import uuid
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from generate_log import logger
load_dotenv()

MAX_SECTION_LENGTH = 3500
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 350

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
AZURE_SEARCH_ENDPOINT = os.getenv("AI_INDEX_END_POINT")
AZURE_SEARCH_KEY = os.getenv("AI_INDEX_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")
 
pdf_file_name = "global_card_access_user_guide.pdf"
current_directory = os.getcwd()
pdf_file_path = os.path.join(current_directory, pdf_file_name)
search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name="test4-agents", credential=AzureKeyCredential(AZURE_SEARCH_KEY))
embedding_model = AzureOpenAIEmbeddings(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment=AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME,
    api_key=AZURE_OPENAI_API_KEY,
    model=AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME
)
 
 

def extract_data_from_doc(pdf_path):
    try:
        logger.info(f"Loading the documents for the path {pdf_path}")
        loader = PDFPlumberLoader(pdf_path)
        data = loader.load()
        texts = [doc.page_content for doc in data if doc.page_content.strip()] 
        logger.info(f"--------texts--------{texts}")
        return texts
    except Exception as e:
        logger.exception(f"Exception occurred while loading docs:{e}")
        raise 
    
    
def split_text(texts):
    try:
        SENTENCE_ENDINGS = [".", "!", "?"]
        WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]
 
        all_text = "".join(texts)
        length = len(all_text)
        start = 0
        end = length
        chunks = []
 
        while start + SECTION_OVERLAP < length:
            last_word = -1
            end = start + MAX_SECTION_LENGTH
 
            if end > length:
                end = length
            else:
                # Try to find the end of the sentence
                while (
                    end < length
                    and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT
                    and all_text[end] not in SENTENCE_ENDINGS
                ):
                    if all_text[end] in WORDS_BREAKS:
                        last_word = end
                    end += 1
                if end < length and all_text[end] not in SENTENCE_ENDINGS and last_word > 0:
                    end = last_word
            if end < length:
                end += 1
 
            # Try to find the start of the sentence or at least a whole word boundary
            last_word = -1
            while (
                start > 0
                and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT
                and all_text[start] not in SENTENCE_ENDINGS
            ):
                if all_text[start] in WORDS_BREAKS:
                    last_word = start
                start -= 1
            if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
                start = last_word
            if start > 0:
                start += 1
 
            section_text = all_text[start:end]
            chunks.append(section_text)
 
            last_table_start = section_text.rfind("<table")
            if (
                last_table_start > 2 * SENTENCE_SEARCH_LIMIT
                and last_table_start > section_text.rfind("</table")
            ):
                start = min(end - SECTION_OVERLAP, start + last_table_start)
            else:
                start = end - SECTION_OVERLAP
 
        if start + SECTION_OVERLAP < end:
            chunks.append(all_text[start:end])
 
        return chunks
    except Exception as e:
        print("Exception occurred in split_text_from_extracted_data --- " + str(e))
        return []
 
def create_embeddings(docs):
    try:
        embeddings = embedding_model.embed_documents(docs)
        return embeddings
    except Exception as e:
        logger.exception(f"Exception occurred while creating embeddings for docs:{e}")
        raise

def create_documents(docs, embeddings, pdf_file_name):
    prepared_docs = []
    for i, doc in enumerate(docs):
        prepared_docs.append({
            "id": str(uuid.uuid4()),
            "content": str(doc),
            "embedding": embeddings[i],
            "sourcefile": str(pdf_file_name),

        })
    return prepared_docs

def upload_documents(prepared_docs, batch_size: int = 1000):
    try:
        for i in range(0, len(prepared_docs), batch_size):
            batch = prepared_docs[i:i + batch_size]
            result = search_client.upload_documents(documents=batch)
            logger.info("docs uploaded successfully in to index")
    except Exception as e:
        logger.exception(f"Exception occurred while uploading docs:{e}")
        raise
    
    
def process_pdf(file_path: str, file_name: str):
    texts = extract_data_from_doc(file_path)
    docs = split_text(texts)
    embeddings = create_embeddings(docs)
    prepared_docs = create_documents(docs, embeddings, file_name)
    upload_documents(prepared_docs)
    
    
    
#process_pdf(file_path=pdf_file_path,file_name=pdf_file_name)
