from fastapi import APIRouter, HTTPException,status
from fastapi.responses import JSONResponse
from engine.orchestraator import call_orchestrator
from database.db_operations import DatabaseOps
from passlib.hash import bcrypt
import hashlib
from engine.schema_class import Chat,Login
from database.db_operations import DatabaseOps
from engine.utils import insert_msgs
from engine.generate_log import logger
import uuid
api_router = APIRouter()


@api_router.post('/login',response_model=dict,description="Get the session by entering you mobile number")
async def get_session_id(creds:Login):
    try:
        db_obj = DatabaseOps()
        mobile_number = creds.mobile_number
        password = creds.password
        get_customer_details_query = "SELECT * FROM customers WHERE phone =?"
        params = (mobile_number,)
        logger.info(f"mobile number:{mobile_number}")
        logger.info(f"password:{password}")
        q_status,customer_details = db_obj.get_data(query=get_customer_details_query,params=params)
        if q_status :
           if len(customer_details)>0:
                is_password_valiad = bcrypt.verify(password, customer_details[0]['password'])
                if is_password_valiad:
                    hex_string = hashlib.md5(mobile_number.encode("UTF-8")).hexdigest()
                    session_id =str(uuid.UUID(hex=hex_string))
                    result  = {"message":"Login Successful","status":True,"session_id":session_id}
                    logger.info(f"Login successful")
                    return JSONResponse(content=result,status_code=status.HTTP_200_OK)
                else:
                    logger.info("incorrect password error")
                    result  = {"message":"Login UnSuccessful.Please check your password","status":False}
                    return JSONResponse(content=result,status_code=status.HTTP_401_UNAUTHORIZED)
           else:
               logger.info("No user found with given mobile number")
               result  = {"message":"No user Found","status":"failed","session_id":[]}
               return JSONResponse(content=result,status_code=status.HTTP_404_NOT_FOUND)
        else:
            logger.info("Login failed due to query status is false")
            result  = {"message":"Login Failed","status":False,"session_id":[]}
            return JSONResponse(content=result,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        result  = {"message":f"Login Failed due to {e}","status":False,"session_id":[]}
        logger.exception(f"Exception occurred while logging in {e}")
        return JSONResponse(content=result,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
@api_router.post("/chat",response_model=dict, description="Resolve user query through orchestrator")
async def orchestrator(data :Chat):
    try: 
        user_query = data.query
        session_id=data.session_id
        logger.info(f"user query is -------{user_query}")
        insert_msgs(session_id=str(session_id),content=user_query,role="user")
        ai_response= await call_orchestrator(user_query,str(session_id))
        logger.info(f"ai msg ------{str(ai_response)}")
        if ai_response:
            result={
                        'status': True,
                        'message': 'Task Completed Successfully',
                        'ai_response': ai_response.replace("TERMINATE",""),
                    }
            return JSONResponse(content=result, status_code=status.HTTP_200_OK)
        else:
            result={
                        'status': False,
                        'message': 'Task Failed',
                    }
            return JSONResponse(content=result, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        response = {
            'status': False,
            'message': 'Task Failed',
            'error': str(e)
        }
        logger.exception(f"Exception occurred in chat---{e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)