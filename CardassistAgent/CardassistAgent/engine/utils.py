from database.db_operations import DatabaseOps
import uuid
from engine.generate_log import logger


def get_messages(session_id):
    try:
        db_obj=DatabaseOps()
        query =  "SELECT content FROM messages WHERE session_id = ? ORDER BY timestamp ASC;"
        params =(session_id,)
        status,msgs = db_obj.get_data(query=query,params=params)
        if status:
            return msgs
        else:
            return []
    except Exception as e:
        logger.exception(f"error occurred: in getting data:{e}")


def insert_msgs(session_id,content,role,customer_id=None):
    try:
        customer_id=1
        db_obj = DatabaseOps()
        insert_data = {"session_id":session_id,
                    "message_id":str(uuid.uuid4()),
                    "content":content,
                    "role":role,
                    "customer_id":customer_id
                    }

        insertion =  db_obj.insert_data(table="messages",data=insert_data)
        return insertion
    except Exception as e:
        logger.exception(f"error occurred in insetrt_msgs:{e}")
        
        
        
        
        
