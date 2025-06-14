from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from azure.core.credentials import AzureKeyCredential
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import AgentExecutor
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_tool_calling_agent
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import asyncio

PROVIDERS = {"OpenRouter":0, "Azure AI Foundry":1}
MODELS = { "OpenRouter": "deepseek/deepseek-r1-0528:free", "Azure AI Foundry": "DeepSeek-R1-0528" }

class Agent:
    def __init__(self, provider, endpoint_url, api_key, model):
        self.set_connection_config(provider, endpoint_url, api_key, model)
        self.prompt_template = self._init_prompt_template()
        self.vectorstore = VectorStore()
        self.server_params = self._init_server_params()
        self.memory = {}
        self.vectorstore.load("resources/vectorstore")

    # Initializes the chat model based on the provider.
    def _initialize_chat_model(self):
        if self.provider == "Azure AI Foundry":
            return AzureAIChatCompletionsModel(
                endpoint=self.endpoint_url,
                credential=AzureKeyCredential(self.api_key),
                model=self.model
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
    # Sets the connection configuration for the agent.
    def set_connection_config(self, provider, endpoint_url, api_key, model):
        self.provider = provider
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.model = model
        self.chat_model = self._initialize_chat_model()
        
    # Initializes the prompt template for the agent.
    def _init_prompt_template(self):
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "You are a financial advisor."
                "Use context provided to answer the question. Context: \n{context}"
                ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}")
            ])

        return prompt_template

    # Initializes the server parameters for the MCP server.
    def _init_server_params(self):
        return StdioServerParameters(
            command="python",
            args=["app/server.py"]
        )
    
    def invoke(self, prompt):
        context = self._get_context(prompt)
        context = ', '.join([doc.page_content for doc in context])
        chain = self.prompt_template | self.chat_model
        chain_with_history = RunnableWithMessageHistory(
            chain,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        response = chain_with_history.invoke({
            "context": context,
            "input": prompt
        },
        config={"configurable": {"session_id": "<foo>"}}
        )
        return response.content
        
        
    async def init_agent_with_memory(self):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)

                agent = create_tool_calling_agent(self.chat_model, tools, self.prompt_template)

                executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True
                )
                self.agent_with_memory = RunnableWithMessageHistory(
                    executor,
                    self._get_session_history,
                    input_messages_key="input",
                    history_messages_key="chat_history"
                )

            
    async def new_ainvoke(self, prompt):
        context = self._get_context(prompt)
        context = ', '.join(context)
        response = await self.agent_with_memory.ainvoke({
            "context": context,
            "input": prompt
        },
        config={"configurable": {"session_id": "<foo>"}}
        )
        return response['output']
            
    # Runs the agent with the given prompt.
    async def ainvoke(self, prompt):
        context = self._get_context(prompt)
        context = ', '.join(context)
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)

                agent = create_tool_calling_agent(self.chat_model, tools, self.prompt_template)

                executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True
                )
                agent_with_memory = RunnableWithMessageHistory(
                    executor,
                    self._get_session_history,
                    input_messages_key="input",
                    history_messages_key="chat_history"
                )

                response = await agent_with_memory.ainvoke({
                    "context": context,
                    "input": prompt
                },
                config={"configurable": {"session_id": "<foo>"}}
                )
                return response['output']

    def test_connection(self):
        try:
            # Attempt to get a response from the model
            response = self.chat_model.invoke(
                [SystemMessage(content="Answer by one sentence."),
                 HumanMessage(content="Hello, world!")],
                config={
                    "generation_config": {
                        "max_tokens": 10
                    }
                }
            )
            return True, response.content
        except Exception as e:
            return False, str(e)
        
    def _get_session_history(self, session_id):
        if session_id not in self.memory:
            self.memory[session_id] = ChatMessageHistory()
        return self.memory[session_id]
        
    # Adds documents to the vector store.
    def add_documents(self, documents):
        self.vectorstore.add_documents(documents)

    # Searches the vector store with a given prompt.
    def _get_context(self, prompt, k=5):
        return self.vectorstore.search(prompt, k=k)

class VectorStore:
    def __init__(self):
        self.embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        dummy_doc = Document(page_content="This is a dummy document for initializing the vector store.")
        self.db = FAISS.from_documents([dummy_doc], self.embedding)
        self.db.index.reset()
        self.db.docstore._dict.clear()
        self.db.index_to_docstore_id.clear()

    def add_documents(self, documents):
        docs = []
        text_spliter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separator="\n")
        docs = text_spliter.split_documents(documents)
        self.db.add_documents(docs)

    def search(self, prompt, k=5):
        results = self.db.similarity_search(prompt, k=k)
        return results
    
    def save(self, path):
        self.db.save_local(path)

    def load(self, path):
        self.db = FAISS.load_local(path, self.embedding, allow_dangerous_deserialization=True)
