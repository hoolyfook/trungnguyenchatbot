from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
from astrapy import DataAPIClient
from langchain_openai import OpenAIEmbeddings
import astrapy
from constant import template, chat_history, N_LAST_PROMPT, N_SIMILAR_QUERY
import json
import os
from utils import get_href_from_main, extract_urls
from copy import deepcopy

load_dotenv()
ASTRA_DB_API_ENDPOINT = os.getenv('ASTRA_DB_API_ENDPOINT')
ASTRA_DB_APPLICATION_TOKEN = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
st.title("Trung Nguyen Legend Coffee")
#st.sidebar.image("https://trungnguyenlegend.com/wp-content/uploads/2018/04/tnl.png", use_column_width=True)
st.markdown(
    """
    <div style="position: fixed; top: 12%; left: 0;width: 30%;">
        <img src="https://trungnguyenlegend.com/wp-content/uploads/2018/04/tnl.png" 
             alt="logo" 
             style="width: 500px; height: auto;">
    </div>
    """,
    unsafe_allow_html=True
)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
data_client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = data_client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection("trungnguyen")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

if "messages" not in st.session_state:
    st.session_state.messages = deepcopy(chat_history)

# Function to display chat messages
def display_chat():
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def query_similar_data(user_input, collection: astrapy.Collection = None):
    embeded_vector = embeddings.embed_query(user_input)
    results = collection.find(
        sort={"$vector": embeded_vector},
        limit=N_SIMILAR_QUERY,
        projection={"content": True},
        include_similarity=True,
    )
    return results

def parse_data(query_results):
    rag_content = ''
    for document in query_results:
        input_text = document['content']
        rag_content += input_text + '\n'
    return rag_content

def get_data_rag_query(history, prompt, n_last=N_LAST_PROMPT):
    user_hist = []
    for hist in history:
        if hist["role"] == "user":
            user_hist.append(hist["content"])
    
    if len(user_hist) < n_last:
        n_last = len(user_hist)
        
    ret_value = ','.join(x for x in user_hist[-n_last:]) + ',' + prompt
    return ret_value

# Display chat messages initially
display_chat()

if prompt := st.chat_input("What is up?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    data_for_rag_query = get_data_rag_query(st.session_state.messages, prompt)
    rag_query = query_similar_data(data_for_rag_query, collection)
    rag_data = parse_data(rag_query)
    request_data = template.format(data=rag_data, question=prompt)
    st.session_state.messages.append({"role": "user", "content": request_data})
    with st.chat_message("assistant"):
        stream = openai_client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.pop()
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display images if any
    img_urls = extract_urls(response)
    if img_urls:
        image_html = ""
        for img_url in img_urls:
            if img_url:
                href = get_href_from_main(img_url)
                if href:
                    image_html += f'<img src="{href}" style="max-width: 100%; margin-bottom: 10px;">'
        if image_html:
            st.markdown(
                f"""
                <div style="position: fixed; right: 5%; bottom: 10%; width: 300px; background-color: white; padding: 10px; box-shadow: -2px 0 5px rgba(0,0,0,0.1); overflow-y: auto; max-height: 100%;">
                    {image_html}
                </div>
                """,
                unsafe_allow_html=True
            )

    st.session_state.messages.append({"role": "assistant", "content": response})

