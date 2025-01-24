import oracledb
import pandas as pd
from sqlalchemy import create_engine
from langchain_ollama import ChatOllama
from langchain_experimental.agents import create_pandas_dataframe_agent
from utils import getInvoiceQuety, getInvoiceDetailQuery
from logging import getLogger

class OllamaService:
    logger = getLogger(__name__)
    def __init__(self):
        self.llm = ChatOllama(
            model="llama3.1",
            temperature=0)
        self.connection = oracledb.connect(
            user='docpadmin',
            password='dofi2000',
            host='localhost',
            port=1521,
            service_name='auto')
        self.db = create_engine('oracle+oracledb://', creator=lambda: self.connection)
        self.agent_map = {}
        # self.query = getInvoiceQuety()
        self.query = getInvoiceDetailQuery()

    def get_agent(self, buyerId: int, supplierNumber: str, startDate: str, endDate: str):
        key = f"{buyerId}_{supplierNumber}"
        if key not in self.agent_map:
              OllamaService.logger.info(f"Creating agent for {key}")
              invoices = pd.read_sql(self.query, self.db, params={'buyerId': buyerId, 'supplierNumber': supplierNumber, 'startDate': startDate, 'endDate': endDate})
              self.agent_map[key] = create_pandas_dataframe_agent(
                    self.llm, invoices, agent_type='tool-calling', verbose=True, allow_dangerous_code=True)
        return self.agent_map[key]

    def chat_ollama(self, buyerId: int, supplierNumber: str, startDate: str, endDate: str, message: str):
          response = self.get_agent(buyerId, supplierNumber, startDate, endDate).invoke(message)
          return response

