import oracledb
import pandas as pd
from sqlalchemy import create_engine
from langchain_ollama import ChatOllama
from langchain_experimental.agents import create_pandas_dataframe_agent
import utils 
import logging 
import sys


class OllamaService:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    
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
        self.query = utils.INVOICE_HEADER_DETAIL_QUERY
        # self.headerQuery = utils.INVOICE_HEADER_QUERY
        # self.detailQuery = utils.INVOCIE_DETAIL_QUERY

    def get_agent(self, buyerId: int, supplierNumber: str, startDate: str, endDate: str, invoiceNumber: str):
        key = f"{buyerId}_{supplierNumber}_{invoiceNumber}"
        if key not in self.agent_map:
              logging.debug(f"query db and create agent for {key}")
              invoices = pd.read_sql(self.query, self.db, params={'buyerId': buyerId, 'supplierNumber': supplierNumber, 'startDate': startDate, 'endDate': endDate})
              print(invoices.to_markdown())
              self.agent_map[key] = create_pandas_dataframe_agent(
                    self.llm, invoices, agent_type='openai-tools', verbose=True, allow_dangerous_code=True, prefix=utils.INVOICE_PROMPT)
            
            #   header = pd.read_sql(self.headerQuery, self.db, params={'buyerId': buyerId, 'supplierNumber': supplierNumber, 'startDate': startDate, 'endDate': endDate})
            #   detail = pd.read_sql(self.detailQuery, self.db, params={'buyerId': buyerId, 'supplierNumber': supplierNumber, 'startDate': startDate, 'endDate': endDate})
            #   combined = pd.merge(header, detail, on='invoice_id', how='inner')
            #   self.agent_map[key] = create_pandas_dataframe_agent(
            #         self.llm, [header,detail], agent_type='openai-tools', verbose=True, allow_dangerous_code=True, prefix=utils.INVOICE_PROMPT) 
        return self.agent_map[key]

    def chat_ollama(self, buyerId: int, supplierNumber: str, startDate: str, endDate: str, invoiceNumber: str, message: str):
          response = self.get_agent(buyerId, supplierNumber, startDate, endDate, invoiceNumber).invoke(message)
          return response

