import json

import chains.prompts as prompts
import utils
import os

from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)


class Chains:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    @classmethod
    def setLlm(cls, model, openai_api_key=os.environ["OPENAI_API_KEY"], temperature=0):
        cls.llm = ChatOpenAI(
            model=model, openai_api_key=openai_api_key, temperature=temperature
        )

    @classmethod
    def getChain(cls, system_template="", human_template="", **kwargs):
        prompts = []
        if system_template:
            prompts.append(SystemMessagePromptTemplate.from_template(system_template))
        if human_template:
            prompts.append(HumanMessagePromptTemplate.from_template(human_template))
        chat_prompt = ChatPromptTemplate.from_messages(prompts)
        return LLMChain(llm=cls.llm, prompt=chat_prompt).run(**kwargs)

    @classmethod
    def langchain(cls, inputs, instruction, function_name):
        res = cls.getChain(
            system_template=prompts.code.system_template,
            human_template=prompts.code.human_template,
            instruction=instruction,
            inputs=inputs,
        )
        templates = json.loads(res)
        run_call = "{}"
        if len(inputs) > 0:
            run_call = ", ".join([f"{var}={var}" for var in inputs])

        temperature = 0 if templates.get("variety", "False") == "False" else 0.7

        code = f"""
        def {function_name}({str(inputs)[2:-2]}):
            chat = ChatOpenAI(
                temperature={temperature}
            )
            system_template = {templates['system_template']}
            system_message_prompt = SystemMessagePromptTemplate.from_template(template)
            human_template = {templates['template']}
            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            chat_prompt = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
            )

            chain = LLMChain(llm=chat, prompt=chat_prompt)
            result = chain.run({run_call})
            return result # returns string                            
        """
        return code

    @classmethod
    def streamlit(cls, instruction, inputs, function_name):
        code = cls.getChain(
            human_template=prompts.streamlit.human_template,
            instruction=instruction,
            inputs=inputs,
            function_name=function_name,
        )
        return utils.refine(code)

    @classmethod
    def inputs(cls, instruction):
        return cls.getChain(
            human_template=prompts.system_inputs.human_template, instruction=instruction
        )

    @classmethod
    def buttonText(cls, instruction):
        return cls.getChain(
            human_template=prompts.button_text.human_template, instruction=instruction
        )
    
    @classmethod
    def helpers(cls, instruction):
        system_inputs = Chains.inputs(instruction)
        button_text = Chains.buttonText(instruction)
        return system_inputs, button_text 
    
    @classmethod
    def plan(cls, instruction):
        return cls.getChain(
            system_template = prompts.plan.system_template,
            human_template=prompts.plan.human_template,
            instruction=instruction
        )
    
    @classmethod
    def draft(cls, instruction,plan):
        return cls.getChain(
            system_template=prompts.draft.system_template,
            human_template=prompts.draft.human_template,
            instruction=instruction,
            plan=plan
        )

    @classmethod
    def tasks(cls, instruction, plan):
        task_list = cls.getChain(
            system_template=prompts.tasks.system_template,
            human_template=prompts.tasks.human_template,
            instruction=instruction,
            plan=plan
        )
        return json.loads(task_list)

    @classmethod
    def explain(cls, instruction, task_list):
        return cls.getChain(
            human_template=prompts.explain.human_template,
            instruction=instruction,
            task_list=task_list,
        )

    @classmethod
    def final(cls, **kwargs):
        code = cls.getChain(human_template=prompts.final.human_template, **kwargs)
        return utils.refine(code)
