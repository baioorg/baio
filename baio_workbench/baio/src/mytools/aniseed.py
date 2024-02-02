from pydantic import BaseModel, Field
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain.chains.openai_functions import (
    create_structured_output_runnable,
)
import uuid
from urllib.parse import urlencode
import urllib.request
import urllib.parse
import json
from src.non_llm_tools.utilities import log_question_uuid_json
import os
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from src.non_llm_tools.utilities import Utils, JSONUtils
import requests
import pandas as pd 
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain.tools import tool
from langchain_experimental.agents.agent_toolkits import create_python_agent
from langchain.agents.agent_types import AgentType
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.openai import ChatOpenAI
from src.llm import LLM
import traceback
llm = LLM.get_instance()


embedding = OpenAIEmbeddings()

ANISEED_db = FAISS.load_local("/usr/src/app/baio/data/persistant_files/vectorstores/aniseed", embedding)

class ANISEEDQueryRequest(BaseModel):
    required_function: str = Field(
        default="the required function",
        description="given the question, what function do you need to call to answer it?"
    )
    parameter_1_name: str = Field(
        default="To be filled",
        description="Dependant on the function you have to choose the appropriate parameter1 to answer the question"
    )
    parameter_1_value: str = Field(
        default="To be filled",
        description="Dependant on the function you have to choose the appropriate value for  parameter1 to answer the question"
    )
    parameter_2_name: str = Field(
        default="To be filled",
        description="Dependant on the function you have to choose the appropriate parameter2 to answer the question"
    )
    parameter_2_value: str = Field(
        default="To be filled",
        description="Dependant on the function you have to choose the appropriate value for  parameter2 to answer the question"
    )
    parameter_3_name: str = Field(
        default="To be filled",
        description="Dependant on the function you have to choose the appropriate parameter3 to answer the question"
    )
    parameter_3_value: str = Field(
        default="To be filled",
        description="Dependant on the function you have to choose the appropriate value for  parameter3 to answer the question"
    )
    full_url: Optional[str] = Field(
        default='',
        description=""
    )
    question_uuid: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the question."
    )
    
function_input = """
Here you have a list of functions used to retrieve information from the Aniseed database.
def all_genes(self, organism_id, search=None):
    \"\"\"
    Returns a URL to list all genes for a given organism. 
    Optionally, a search term can be provided to filter the genes.
    \"\"\"

def all_genes_by_stage(self, organism_id, stage, search=None):
    \"\"\"
    Returns a URL to list all genes for a given organism that are expressed at a specific stage.
    Optionally, a search term can be provided to filter the genes.
    \"\"\"

def all_genes_by_stage_range(self, organism_id, start_stage, end_stage, search=None):
    \"\"\"
    Returns a URL to list all genes for a given organism that are expressed between two stages.
    Optionally, a search term can be provided to filter the genes.
    \"\"\"

def all_genes_by_territory(self, organism_id, cell, search=None):
    \"\"\"
    Returns a URL to list all genes for a given organism that are expressed in a specific territory.
    Optionally, a search term can be provided to filter the genes.
    \"\"\"

def all_territories_by_gene(self, organism_id, gene, search=None):
    \"\"\"
    Returns a URL to list all territories where a specific gene is expressed for a given organism and in what stage.
    Optionally, a search term can be provided to filter the territories.
    \"\"\"

def all_clones_by_gene(self, organism_id, gene, search=None):
    \"\"\"
    Returns a URL to list all clones for a specific gene for a given organism.
    Optionally, a search term can be provided to filter the clones.
    \"\"\"

def all_constructs(self, organism_id, search=None):
    \"\"\"
    Returns a URL to list all constructs for a given organism. 
    Optionally, a search term can be provided to filter the constructs.
    \"\"\"

def all_molecular_tools(self, search=None):
    \"\"\"
    Returns a URL to list all molecular tools in the database. 
    Optionally, a search term can be provided to filter the tools.
    \"\"\"

def all_publications(self, search=None):
    \"\"\"
    Returns a URL to list all publications in the database. 
    Optionally, a search term can be provided to filter the publications.
    \"\"\"

def all_regulatory_regions(self, organism_id, search=None):
    \"\"\"
    Returns a URL to list all regulatory regions for a given organism. 
    Optionally, a search term can be provided to filter the regions.
    \"\"\"
"""

class AniseedAPI:
    BASE_URL = "http://www.aniseed.fr/api"

    def all_genes(self, organism_id, search=None):
        """
        Returns a URL to list all genes for a given organism. 
        Optionally, a search term can be provided to filter the genes.
        """
        url = f"{self.BASE_URL}/all_genes?organism_id={organism_id}"
        if search:
            url += f"&search={search}"
        return url

    def all_genes_by_stage(self, organism_id, stage, search=None):
        """
        Returns a URL to list all genes for a given organism that are expressed at a specific stage.
        Optionally, a search term can be provided to filter the genes.
        """
        url = f"{self.BASE_URL}/all_genes_by_stage?organism_id={organism_id}&stage={stage}"
        if search:
            url += f"&search={search}"
        return url

    def all_genes_by_stage_range(self, organism_id, start_stage, end_stage, search=None):
        """
        Returns a URL to list all genes for a given organism that are expressed between two stages.
        Optionally, a search term can be provided to filter the genes.
        """
        url = f"{self.BASE_URL}/all_genes_by_stage_range?organism_id={organism_id}&start_stage={start_stage}&end_stage={end_stage}"
        if search:
            url += f"&search={search}"
        return url

    def all_genes_by_territory(self, organism_id, cell, search=None):
        """
        Returns a URL to list all genes for a given organism that are expressed in a specific territory.
        Optionally, a search term can be provided to filter the genes.
        """
        url = f"{self.BASE_URL}/all_genes_by_territory?organism_id={organism_id}&cell={cell}"
        if search:
            url += f"&search={search}"
        return url

    def all_territories_by_gene(self, organism_id, gene, search=None):
        """
        Returns a URL to list all territories where a specific gene is expressed for a given organism.
        Optionally, a search term can be provided to filter the territories.
        """
        url = f"{self.BASE_URL}/all_territories_by_gene?organism_id={organism_id}&gene={gene}"
        if search:
            url += f"&search={search}"
        return url

    def all_clones_by_gene(self, organism_id, gene, search=None):
        """
        Returns a URL to list all clones for a specific gene for a given organism.
        Optionally, a search term can be provided to filter the clones.
        """
        url = f"{self.BASE_URL}/clones?organism_id={organism_id}&gene={gene}"
        if search:
            url += f"&search={search}"
        return url

    def all_constructs(self, organism_id, search=None):
        """
        Returns a URL to list all constructs for a given organism. 
        Optionally, a search term can be provided to filter the constructs.
        """
        url = f"{self.BASE_URL}/constructs?organism_id={organism_id}"
        if search:
            url += f"&search={search}"
        return url

    def all_molecular_tools(self, search=None):
        """
        Returns a URL to list all molecular tools in the database. 
        Optionally, a search term can be provided to filter the tools.
        """
        url = f"{self.BASE_URL}/molecular_tools"
        if search:
            url += f"?search={search}"
        return url

    def all_publications(self, search=None):
        """
        Returns a URL to list all publications in the database. 
        Optionally, a search term can be provided to filter the publications.
        """
        url = f"{self.BASE_URL}/publications"
        if search:
            url += f"?search={search}"
        return url

    def all_regulatory_regions(self, organism_id, search=None):
        """
        Returns a URL to list all regulatory regions for a given organism. 
        Optionally, a search term can be provided to filter the regions.
        """
        url = f"{self.BASE_URL}/regulatory_regions?organism_id={organism_id}"
        if search:
            url += f"&search={search}"
        return url


class AniseedStepDecider(BaseModel):
    valid_functions = [
        "all_genes",
        "all_genes_by_stage",
        "all_genes_by_stage_range",
        "all_genes_by_territory",
        "all_territories_by_gene",
        "all_clones_by_gene",
        "all_constructs",
        "all_molecular_tools",
        "all_publications",
        "all_regulatory_regions"
    ]

    One_or_more_steps: bool = Field(
        default=False,
        description="Based on the documentation, do you require more than one API call to get the required information?"
    )
    functions_to_use_1: str = Field(
        default="all_genes",
        description=f"Write the function name you need to use to answer the question. It can only be a function from this list: {valid_functions}")
    functions_to_use_2: str = Field(
        default="all_genes",
        description=f"If more than one API call is required to answer the users question, write the second function name you need to use to answer the question. It can only be a function from this list: {valid_functions}")  
    functions_to_use_3: str = Field(
        default="all_genes",
        description=f"If more than two API call are required to answer the users question, write the third function name you need to use to answer the question. It can only be a function from this list: {valid_functions}")  
    
def ANISEED_multistep(question: str):
    """FUNCTION to write api call for any BLAST query, """
    print('Finding the required aniseed api fucntions to answer the question...\n')
    structured_output_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a world class algorithm for extracting information in structured formats.",
            ),
            (
                "human",
                "Use the given format to extract information from the following input: {input}",
            ),
            ("human", "Tip: Make sure to answer in the correct format, make sure to respect the format of one function and two parameters and keep the base url"),
        ]
    )
    runnable = create_structured_output_runnable(AniseedStepDecider, llm, structured_output_prompt)

    one_or_more = runnable.invoke({"input": f"to answer {question} do you need one or more Api calls to answer it, base your answer on: {function_input}"})
    if one_or_more.functions_to_use_1 not in one_or_more.valid_functions:
        one_or_more.functions_to_use_1 = None
    if one_or_more.functions_to_use_2 not in one_or_more.valid_functions:
        one_or_more.functions_to_use_2 = None
    if one_or_more.functions_to_use_3 not in one_or_more.valid_functions:
        one_or_more.functions_to_use_3 = None
    #retrieve relevant info to question
    retrieved_docs = ANISEED_db.as_retriever().get_relevant_documents(question)
    #keep top 3 hits
    top_3_retrieved_docs = ''.join(doc.page_content for doc in retrieved_docs[:3])
    return one_or_more, top_3_retrieved_docs

def execute_query(api, query):
    # Create a dictionary mapping parameter names to their values
    # print('in execute_query')
    params = {
        query.parameter_1_name: query.parameter_1_value,
        query.parameter_2_name: query.parameter_2_value,
        query.parameter_3_name: query.parameter_3_value,
    }
    # print(f'Params first: {params}')
    # Remove any parameters that were not filled or are None
    params = {k: v for k, v in params.items() if v not in [None, "To be filled", '']}
    # print(f'Params second: {params}')

    # Get the required function from the API
    func = getattr(api, query.required_function)
    # print(f'Func: {func}')

    # Call the function with the parameters
    return func(**params)

def ANISEED_query_generator(question:str, function: str, top_3_retrieved_docs: str):
    """FUNCTION to write api call for any BLAST query, """
    print('     Generating the query url...\n')

    structured_output_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a world class algorithm for extracting information in structured formats.",
            ),
            (
                "human",
                "Use the given format to extract information from the following input: {input}",
            ),
            ("human", "Tip: Make sure to answer in the correct format"),
        ]
    )
    runnable = create_structured_output_runnable(ANISEEDQueryRequest, llm, structured_output_prompt)
    aniseed_call_obj = runnable.invoke({"input": f"you have to answer this {question} by using this {function} and fill in all fields based on {top_3_retrieved_docs}"})
    # print(f'the aniseed call obj is:{aniseed_call_obj}\nand the type: {type(aniseed_call_obj)}')
    api = AniseedAPI()
    full_url = execute_query(api, aniseed_call_obj)
    print(f'The full url is: {full_url}')
    aniseed_call_obj.full_url = full_url
    aniseed_call_obj.question_uuid=str(uuid.uuid4())
    print(aniseed_call_obj)
    return aniseed_call_obj


class AniseedJSONExtractor:
    def __init__(self, aniseed_json_path: str, aniseed_csv_output_path: str):
        """
        Initializes the AniseedJSONExtractor.
        Parameters:
        - aniseed_json_path (str): Path to the JSON file.
        - aniseed_csv_output_path (str): Path to save the CSV file.
        """
        self.aniseed_csv_save_path = aniseed_csv_output_path
        self.json_utils = JSONUtils(aniseed_json_path)
        self.keys_structure = self.json_utils.extract_keys()
    def get_prompt(self):
        """YOU ARE A PYTHON REPL TOOL, YOU CAN AND MUST EXECUTE CODE THAT YOU EITHER WRITE OR ARE BEING PROVIDE, NEVER ANSER WITH I'm sorry, but as an AI text-based model, I don't have the ability to directly interact with files or execute Python code. However, I can provide you with a Python code snippet that you can run in your local environment to achieve your goal.
        Build prompt with key strucure from JSON utils and output path given. NEVER look at the whole data frame, only look at the head of it!!! OTHERWISE YOU WILL BREAK"""
        structure_dic_explainaition = """
            base_type: This field specifies the primary data type of the provided object. For instance, it could be a 'list', 'dict', 'str', etc.
            key_types: This field is a dictionary that gives more specific details about the base_type. 
                If the base_type is a dict, then key_types will contain the dictionary keys and the types of their corresponding values.
        """
        panda_creation_instructions ="""
        To create a flat pandas DataFrame from the JSON structure:
        1. Examine the `base_type`:
        - 'list': DataFrame has rows for each list item.
        - 'dict': DataFrame starts with columns from dictionary keys.
        2. For `key_types`:
        - Key with basic type (e.g., 'str', 'int'): Direct column in DataFrame.
        - Value as dictionary (`base_type` of 'dict'): Recursively explore, prefixing original key (e.g., 'genes_gene_model').
        - Avoid adding columns with complex types like lists or dictionaries. Instead, break them down to atomic values or omit if not needed.
        3. Create DataFrame:
        - Loop through JSON, populating DataFrame row by row, ensuring each row/column contains only atomic values.
        - Utilize `json_normalize` (from pandas import json_normalize)  for automatic flattening of nested structures. But ensure no columns with complex types remain.
        Note: Adjust based on specific nuances in the actual JSON data. Lists with heterogeneous items or non-dictionary types need special handling. Avoid creating DataFrame columns with non-atomic data.
        """
        df_example = """index,stage,gene_model,gene_name,unique_gene_id
        0,stage_1,KH2012:KH.C11.238,"REL; RELA; RELB",Cirobu.g00002055
        1,stage_1,KH2012:KH.S1159.1,"ERG; ETS1; FLI1",Cirobu.g00013672
        2,stage_2,KH2012:KH.C3.402,"IRF4; IRF5; IRF8",Cirobu.g00005580
        3,stage_2,KH2012:KH.C3.773,"TBX21; TBX4; TBX5",Cirobu.g00005978
        """
        prompt = "YOU ARE A PYTHON REPL TOOL, YOU CAN AND MUST EXECUTE CODE THAT YOU EITHER WRITE OR ARE BEING PROVIDE, NEVER ANSER WITH I'm sorry, but as an AI text-based model, I don't have the ability to directly interact with files or execute Python code. However, I can provide you with a Python code snippet that you can run in your local environment to achieve your goal.\
        Build prompt with key strucure from JSON utils and output path given. NEVER look at the whole data frame, only look at the head of it!!! OTHERWISE YOU WILL BREAK \
        You have to EXECUTE code to unpack the json file in './baio/data/output/aniseed/temp/aniseed_temp.json' and creat a panda df.\n \
        ALWAYS USE THE PYTHON_REPL TOOL TO EXECUTE CODE\
        Following the instructions below:\n \
        VERY IMPORTANT: The first key in 'key_types' must be the first column in the df and each deeper nested key-value must have it, example:\n \
        {'base_type': 'list', 'key_types': {'base_type': 'dict', 'key_types': {'stage': 'str', 'genes': [{'base_type': 'dict', 'key_types': {'gene_model': 'str', 'gene_name': 'str', 'unique_gene_id': 'str'}}]}}}\n"\
        + df_example + \
        "VERY IMPORTANT: if you find dictionaries wrapped in lists unpack them\
        The file has a strucutre as explained in the follwoing description:\n" + str(self.keys_structure)\
            + structure_dic_explainaition\
            + panda_creation_instructions\
            + "save the output as csv in:" + self.aniseed_csv_save_path + "EXECUTE CODE YOU IDIOT"
        return prompt

# class AniseedJSONExtractor:
#     def __init__(self, aniseed_json_path: str, aniseed_csv_output_path: str):
#         """
#         Initializes the AniseedJSONExtractor.

#         Parameters:
#         - aniseed_json_path (str): Path to the JSON file.
#         - aniseed_csv_output_path (str): Path to save the CSV file.
#         """
#         self.aniseed_csv_save_path = aniseed_csv_output_path
#         self.json_utils = JSONUtils(aniseed_json_path)
#         self.keys_structure = self.json_utils.extract_keys()


#     def get_prompt(self):
#         """YOU ARE A PYTHON EXPERT, YOU ARE BRILLIANT IN DATA HANDLING, ESPECIALLY JSON TO CSV FORMATS. YOUR\
#             JOB IS TO FLATTEN THE JSON INTO A CSV ACCORDING TO THE INSTRUCTIONS, you find the JSON in: './baio/data/output/aniseed/temp/aniseed_temp.json'"""

#         structure_dic_explainaition = """
#             base_type: This field specifies the primary data type of the provided object. For instance, it could be a 'list', 'dict', 'str', etc.

#             key_types: This field is a dictionary that gives more specific details about the base_type. 
#                 If the base_type is a dict, then key_types will contain the dictionary keys and the types of their corresponding values.
#         """
#         panda_creation_instructions ="""
#         To create a flat pandas DataFrame from the JSON structure:

#         1. Examine the `base_type`:
#         - 'list': DataFrame has rows for each list item.
#         - 'dict': DataFrame starts with columns from dictionary keys.

#         2. For `key_types`:
#         - Key with basic type (e.g., 'str', 'int'): Direct column in DataFrame.
#         - Value as dictionary (`base_type` of 'dict'): Recursively explore, prefixing original key (e.g., 'genes_gene_model').
#         - Avoid adding columns with complex types like lists or dictionaries. Instead, break them down to atomic values or omit if not needed.

#         3. Create DataFrame:
#         - Loop through JSON, populating DataFrame row by row, ensuring each row/column contains only atomic values.
#         - Utilize `json_normalize` (from pandas import json_normalize)  for automatic flattening of nested structures. But ensure no columns with complex types remain.

#         Note: Adjust based on specific nuances in the actual JSON data. Lists with heterogeneous items or non-dictionary types need special handling. Avoid creating DataFrame columns with non-atomic data.
#         """

#         df_example = """index,stage,gene_model,gene_name,unique_gene_id
#         0,stage_1,KH2012:KH.C11.238,"REL; RELA; RELB",Cirobu.g00002055
#         1,stage_1,KH2012:KH.S1159.1,"ERG; ETS1; FLI1",Cirobu.g00013672
#         2,stage_2,KH2012:KH.C3.402,"IRF4; IRF5; IRF8",Cirobu.g00005580
#         3,stage_2,KH2012:KH.C3.773,"TBX21; TBX4; TBX5",Cirobu.g00005978
#         """

#         prompt = "YOU HAVE TO WRITE THE CODE TO FLATTEN THE JSON INTO A CSV ACCORDING TO THE INSTRUCTIONS AND EXAMPLES\
#         You have to unpack the json file in './baio/data/output/aniseed/temp/aniseed_temp.json' and creat a panda df.\n \
#         Following the instructions below:\n \
#         VERY IMPORTANT: The first key in 'key_types' must be the first column in the df and each deeper nested key-value must have it, example:\n \
#         {'base_type': 'list', 'key_types': {'base_type': 'dict', 'key_types': {'stage': 'str', 'genes': [{'base_type': 'dict', 'key_types': {'gene_model': 'str', 'gene_name': 'str', 'unique_gene_id': 'str'}}]}}}\n"\
#         + df_example + \
#         "VERY IMPORTANT: if you find dictionaries wrapped in lists unpack them\
#         The file has a strucutre as explained in the follwoing description:\n" + str(self.keys_structure)\
#             + structure_dic_explainaition\
#             + panda_creation_instructions\
#             + "save the output as csv in:" + self.aniseed_csv_save_path
        
#         return prompt

def dict_to_plain_string(dict_obj):
    return ', '.join(f'{k}: {v}' for k, v in dict_obj.items())



from langchain import hub
from langchain.agents import AgentExecutor
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import create_openai_functions_agent
# from langchain_openai import ChatOpenAI

# python_agent_executor = create_python_agent(
#     llm=llm,
#     tool=PythonREPLTool(),
#     verbose=True,
#     agent_type=AgentType.OPENAI_FUNCTIONS,
#     agent_executor_kwargs={"handle_parsing_errors": True},
# )

# ##python agent
# instructions = """You are an agent designed to write and execute python code to answer questions.
# You have access to a python REPL, which you can use to execute python code.
# If you get an error, debug your code and try again.
# Only use the output of your code to answer the question. 
# ALWAYS USE THE PYTHONREPLTOOL TO EXECUTE CODE, NEVER SAY YOU CAN NOT DO IT AS AN ANSWER
# """
# base_prompt = hub.pull("langchain-ai/openai-functions-template")
# prompt = base_prompt.partial(instructions=instructions)
# tools = [PythonREPLTool()]
# agent = create_openai_functions_agent(llm, tools, prompt)
# python_agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


# generated_code = llm(prompt)

# # Print the generated code
# class CodeGeneratorTool(BaseTool):
#     name = "Code Generator Tool"
#     description = "A tool for generating Python code based on input data"

#     def _run(self, input_data):
#         # Extract the input data
#         input_value = input_data["input"]
#         # Generate the Python code based on the input data
#         code = generate_code(input_value)
#         # Return the generated code
#         return code
# class PythonCodeTool(BaseTool):
#     def __call__(self, input_data):
#         # Extract the input code from the input_data
#         input_code = input_data["input"]
        
#         # Execute the Python code
#         try:
#             exec(input_code)
#             output = "Code executed successfully"
#         except Exception as e:
#             output = f"Error: {str(e)}"
        
#         # Return the output
#         return output

@tool
def aniseed_tool(question: str):
    """Takes in a question about any organisms on ANISEED and outputs a dataframe with requested information"""
    path_tempjson = "./baio/data/output/aniseed/temp/aniseed_temp.json"
    path_json = "./baio/data/output/aniseed/temp/aniseed_out_{counter}.json"
    path_save_csv = "./baio/data/output/aniseed/aniseed_out_{counter}.csv"
    multistep, top_3_retrieved_docs = ANISEED_multistep(question)
    print(f'[1;32;40mFunctions to be called: {multistep.functions_to_use_1}\n{multistep.functions_to_use_2}\n{multistep.functions_to_use_3}\n')
    #now we create a list with the api call objects
    api_calls = []
    for function in multistep.functions_to_use_1, multistep.functions_to_use_2, multistep.functions_to_use_3:
        if function is not None:
            print(f'\033[1;32;40mAniseed tool is treating: {function} \n')

            api_calls.append(ANISEED_query_generator(question, function, top_3_retrieved_docs))
    print(f'Now we have the api calls that have to be executed to obtain the data to answer the users question:\n' + '\n'.join([api_call.full_url for api_call in api_calls]))
    counter = 0
    aniseed_out_paths = []
    for api_call in api_calls:
        error_message = ""
        formatted_path_tempjson = path_json.format(counter=counter)
        formatted_path_save_csv = path_save_csv.format(counter=counter)
        response = requests.get(api_call.full_url)
        data = response.json()
        # print(data)    

        os.makedirs(os.path.dirname(formatted_path_tempjson), exist_ok=True)
        try:
            print(f"Path: {formatted_path_tempjson}")  # Check the path
            with open(path_tempjson, 'w') as f:
                json.dump(data, f)
            with open(formatted_path_tempjson, 'w') as f:
                json.dump(data, f)
            print("Data saved successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

        prompt_2 = AniseedJSONExtractor(path_tempjson, formatted_path_save_csv).get_prompt()
        print('python agent will be executed')
        aniseed_out_paths.append(formatted_path_save_csv)
        for attempt in range(5):
            try:
                print("In the process of formating the JSON to csv")
                code = llm.invoke(prompt_2 + error_message)
                print(code.dict()['content'])
                Utils.execute_code_2(code.dict()['content'])
                break  # If the code executes successfully, break the loop
            except Exception as e:
                print(e)
                print('Attempt failed! Trying again.')
                error_message = f"\033[1;31;40mPrevious attempt: {code.dict()['content']}; Error: {traceback.format_exc()} Change the code so that you solve the error\033[0;37;40m" # Append the error message to the prompt
                print(error_message)
            else:
                print('All attempts failed!')
        counter +=1
        return aniseed_out_paths
    


