from database.db_operations import DatabaseOps
from dotenv import load_dotenv
import os
from semantic_kernel.functions import kernel_function

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from engine.generate_log import logger

load_dotenv()

service_endpoint = os.environ["AI_INDEX_END_POINT"]
index_name = os.environ["INDEX_NAME"]
key = os.environ["AI_INDEX_KEY"]


class KnowledgePlugin:
    @kernel_function(description="This function retrives the relevant information from Azure AI Search based the provided user_query by user")
    def get_data_from_ai_search(self,search_query):
        try:
            logger.info(f"retrivig data for for query{search_query}")
            client = SearchClient(endpoint=service_endpoint,
                                index_name=index_name,
                                credential=AzureKeyCredential(key))
            results = client.search(search_query,top=5)
            results_list = [result['content'] for result in results]
            return results_list
        except Exception as e:
            logger.exception(f"Error occorred while retriving data from index:{e}")




class CardManagerPlugin:
    @kernel_function(description="This function helps in validating the card number and updating the database with the card status i.e either activate or deactivate based on the user request")
    def update_card_status(self, details):
        try:
            card_number = details.get("card_number")
            new_status = details.get("status")

            logger.info(f"Card number is {card_number}")

            db_ops = DatabaseOps()
            query = "SELECT * FROM cards WHERE card_number=?"
            params = (card_number,)
            status, rows = db_ops.get_data(query, params=params)

            logger.info(f"Database query status is {status}")

            if not status:
                return {"message": "Failed to get card data. Please check the card number provided.", "status": False}

            current_status = rows[0]['is_active']

            if (current_status == 1 and new_status == "activate") or (current_status == 0 and new_status == "deactivate"):
                return {"message": f"The card is already {new_status}d."}

            updates = {"is_active": 1 if new_status == "activate" else 0}
            condition = {"card_number": card_number}
            update_card = db_ops.update_data(table="cards", data=updates, condition=condition)

            logger.info(f"Update card status is {update_card}")

            if update_card:
                return {"message": f"Successfully {new_status}d the card.", "status": True}
            else:
                return {"message": f"{new_status} of the card failed.", "status": False}

        except Exception as e:
            logger.exception(f"Error in updating card status: {e}")
            return {"message": "An error occurred while updating the card status.", "status": False}

            


