from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat
from semantic_kernel.agents.strategies import (
    KernelFunctionSelectionStrategy,
    KernelFunctionTerminationStrategy,
)
from semantic_kernel.contents.chat_history import ChatHistory
import uuid
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from database.db_operations import DatabaseOps
import re
import json
from engine.plugin import CardManagerPlugin , KnowledgePlugin
import os
import yaml
from dotenv import load_dotenv
from engine.utils import *
load_dotenv()


endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version=os.getenv("AZURE_OPENAI_API_VERSION")
api_key = os.getenv("AZURE_OPENAI_API_KEY")

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)
 
CARD_MANAGER_AGENT_NAME = config['CARD_MANAGER_AGENT_NAME']
KNOWLEDGEBOT_AGENT_NAME = config['KNOWLEDGEBOT_AGENT_NAME']
ORCHESTRATOR_NAME = config['ORCHESTRATOR_NAME']
selection_function_prompt = config['prompts']['selection_function_prompt']
termination_function_prompt =  config['prompts']['termination_function_prompt']
orchestrator_instructions_prompt =  config['prompts']['orchestrator_instructions_prompt']
cardmanager_agent_instructions_prompt = config['prompts']['cardmanager_agent_instructions_prompt']
knowledge_agent_instructions_prompt = config['prompts']['knowledge_agent_instructions_prompt']


async def _create_kernel_with_chat_completion(function_name: str) -> Kernel:
    try:
        kernel = Kernel()
        kernel.add_service(
            AzureChatCompletion(
                service_id=function_name,
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
            )
        )
        logger.info(f"Kernel created with chat completion service: {function_name}")
        return kernel
    except Exception as e:
        logger.exception(f"Error creating kernel with chat completion service: {function_name}")
        raise
    
    
    
async def make_functions():
    try:
        selection_function = KernelFunctionFromPrompt(function_name="selection",
                                                      prompt = selection_function_prompt.format(ORCHESTRATOR_NAME=ORCHESTRATOR_NAME,CARD_MANAGER_AGENT_NAME=CARD_MANAGER_AGENT_NAME,KNOWLEDGEBOT_AGENT_NAME=KNOWLEDGEBOT_AGENT_NAME))
        termination_function = KernelFunctionFromPrompt(
            function_name="termination",
            prompt=termination_function_prompt.format(ORCHESTRATOR_NAME=ORCHESTRATOR_NAME)
        )
        return selection_function, termination_function
    except Exception as e:
        logger.exception(f"Error creating functions: {str(e)}")
        raise


async def make_orchestrator(prompt,session_id, selection_function, termination_function):
    try:
        uniqueId = uuid.uuid4()
        path=os.getcwd()
        output_file = f"{path}/chat_output_dito_{uniqueId}.md"
        logger.info(f" Output file : {output_file}")
        kernel = await _create_kernel_with_chat_completion("shared_kernel")
        kernel.add_plugin(CardManagerPlugin())
        kernel.add_plugin(KnowledgePlugin())
        chat_session_history =  get_messages(session_id=str(session_id))
        if chat_session_history and len(chat_session_history)>0 :
            chat_json_str = json.dumps(chat_session_history[0])
            chat_json_str = re.sub(r'TERMINATE', '', chat_json_str)
            history=ChatHistory().restore_chat_history(chat_json_str)
        else:
            history=ChatHistory()
            
        orchestrator = ChatCompletionAgent(
            kernel=kernel,
            name=ORCHESTRATOR_NAME,
            instructions=orchestrator_instructions_prompt.format(CARD_MANAGER_AGENT_NAME=CARD_MANAGER_AGENT_NAME,KNOWLEDGEBOT_AGENT_NAME=KNOWLEDGEBOT_AGENT_NAME,history=history),
        )
        
        CardManager = ChatCompletionAgent(
            kernel=kernel,
            name="CardManager",
            instructions=cardmanager_agent_instructions_prompt,
            # plugins=[CardManagerPlugin()]
            )

        KnowledgeAgent = ChatCompletionAgent(
            kernel=kernel,
            name="KnowledgeAgent",
            instructions=knowledge_agent_instructions_prompt,
            # plugins=[KnowledgePlugin()]
        )

        selection_strategy = KernelFunctionSelectionStrategy(
                function=selection_function,
                kernel=kernel,
                result_parser=lambda result: str(result.value[0]) if result.value else ORCHESTRATOR_NAME,
                history_variable_name="history",
            )

        termination_strategy = KernelFunctionTerminationStrategy(
            agents=[orchestrator],
            function=termination_function,
            kernel=kernel,
            result_parser=lambda result: str(result.value[0]).strip().upper() == "TERMINATE",
            history_variable_name="history",
            maximum_iterations=20,
        )

        chat = AgentGroupChat(
            agents=[orchestrator,CardManager, KnowledgeAgent],
            selection_strategy=selection_strategy,
            termination_strategy=termination_strategy,
            chat_history=history
        )
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Chat Output - {uniqueId}\n\n")
        except Exception as e:
            logger.exception(f"Error creating output file. File path may not be appropriate: {str(e)}")

        user_input =  prompt.strip() 
        await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=user_input))
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"## {AuthorRole.USER}\n'{user_input}'\n\n")
        last_message = await process_chat_step(chat, history, output_file)
        user_input =  prompt.strip() 
        await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=user_input))
        insert_msg = insert_msgs(session_id=str(session_id),content=last_message,role ="assistant")
        logger.info(insert_msg)
        await chat.reset()
        return last_message
    except Exception as e:
        logger.exception(f"error occurred in ochestration:{e}")
        raise


async def process_chat_step(chat: AgentGroupChat, chat_history: ChatHistory, output_file: str):
    try:
        logger.info(f"Inside process_chat_step function")
        async for content in chat.invoke():
            with open(output_file, 'a', encoding='utf-8') as f:
                role = content.role
                name = content.name or '*'
                message = content.content
                f.write(f"## {role} - {name}\n'{message}'\n\n")
            logger.info(f"Agent response: {role} - {name}: {message}")
        return chat_history.messages[-1].content if chat_history.messages else ""
    except Exception as e:
        logger.exception(f"Error processing chat step: {str(e)}")

    


async def call_orchestrator(prompt,session_id):
    try:
        selection_function, termination_function = await make_functions()
        result = await make_orchestrator(prompt,str(session_id), selection_function, termination_function)
        return result
    except Exception as e:
        logger.exception(f"error in call_orchestrator function{e}")
        return None
    







        
