import html
import re
# import requests
# from bs4 import BeautifulSoup
import streamlit as st
from langchain.callbacks.base import BaseCallbackHandler
import sys
import os
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)
bot_avt = "https://th.bing.com/th/id/R.dec45b829bcadab7124de8e1a5df2263?rik=eoFrojBvo%2f3heg&pid=ImgRaw&r=0"
user_avt = "https://ps.w.org/user-avatar-reloaded/assets/icon-128x128.png?rev=2540745"
font_size = 14
avt_size = 100

# def get_page_title(url):
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
#     return soup.title.string

def format_message(text):
    """
    This function is used to format the messages in the chatbot UI.

    Parameters:
    text (str): The text to be formatted.
    """
    text_blocks = re.split(r"```[\s\S]*?```", text)
    code_blocks = re.findall(r"```([\s\S]*?)```", text)

    text_blocks = [html.escape(block) for block in text_blocks]

    formatted_text = ""
    for i in range(len(text_blocks)):
        formatted_text += text_blocks[i].replace("\n", "<br>")
        if i < len(code_blocks):
            formatted_text += f'<pre style="white-space: pre-wrap; word-wrap: break-word;"><code>{html.escape(code_blocks[i])}</code></pre>'

    return formatted_text


def message_func(text, is_user=False, is_df=False):
    """
    This function is used to display the messages in the chatbot UI.

    Parameters:
    text (str): The text to be displayed.
    is_user (bool): Whether the message is from the user or not.
    is_df (bool): Whether the message is a dataframe or not.
    """
    if is_user:
        message_alignment = "flex-end"
        message_bg_color = "linear-gradient(135deg, #00B2FF 0%, #006AFF 100%)"
        avatar_class = "user-avatar"
        st.write(
            f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%; font-size: {font_size}px --important;">
                        {text} \n </div>
                    <img src="{user_avt}" class="{avatar_class}" alt="avatar" style="width: {avt_size}px; height: {avt_size}px;" />
                </div>
                """,
            unsafe_allow_html=True,
        )
    else:
        message_alignment = "flex-start"
        message_bg_color = "#71797E"
        avatar_class = "bot-avatar"

        if is_df:
            st.write(
                f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                        <img src="{bot_avt}" class="{avatar_class}" alt="avatar" style="width: {avt_size}px; height: {avt_size}px;" />
                    </div>
                    """,
                unsafe_allow_html=True,
            )
            st.write(text)
            return
        

        st.write(
            f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <img src="{bot_avt}" class="{avatar_class}" alt="avatar" style="width: {avt_size}px; height: {avt_size}px;" />
                    <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%; font-size: {font_size}px --important;">
                        {text} \n </div>
                </div>
                """,
            unsafe_allow_html=True,
        )

def message_func_stream(text, placeholder):
    message_alignment = "flex-start"
    message_bg_color = "#71797E"
    avatar_class = "bot-avatar"
    placeholder.markdown(
        f"""
            <div style="font-size: {font_size}px --important; display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                <img src="{bot_avt}" class="{avatar_class}" alt="avatar" style="width: {avt_size}px; height: {avt_size}px;" />
                <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%;">
                    {text} \n </div>
            </div>
            """,
        unsafe_allow_html=True,
    )
    return placeholder

def create_messenge(text):
    message_alignment = "flex-start"
    message_bg_color = "#71797E"
    avatar_class = "bot-avatar"
    messenger = f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <img src="{bot_avt}" class="{avatar_class}" alt="avatar" style="width: {avt_size}px; height: {avt_size}px;" />
                    <div style="background: {message_bg_color}; color: white; border-radius: 40px; padding: 10px; margin-right: 5px; max-width: 75%; font-size: {font_size}px --important;">
                        {text} \n </div>
                </div>
                """
    return messenger

class StreamlitUICallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.token_buffer = []
        self.placeholder = None
        self.has_streaming_ended = False

    def _get_bot_message_container(self, text):
        """Generate the bot's message container style for the given text."""
        message_alignment = "flex-start"
        message_bg_color = "#71797E"
        avatar_class = "bot-avatar"
    
        container_content = f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                <img src="{bot_avt}" class="{avatar_class}" alt="avatar" style="width: {avt_size}px; height: {avt_size}px;" />
                <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%; font-size: {font_size}px --important;">
                    {text} \n </div>
            </div>
        """
        return container_content

    def on_llm_new_token(self, token, run_id, parent_run_id=None, **kwargs):
        """
        Handle the new token from the model. Accumulate tokens in a buffer and update the Streamlit UI.
        """
        self.token_buffer.append(token)
        complete_message = "".join(self.token_buffer)
        if self.placeholder is None:
            container_content = self._get_bot_message_container(complete_message)
            self.placeholder = st.markdown(container_content, unsafe_allow_html=True)
        else:
            # Update the placeholder content
            container_content = self._get_bot_message_container(complete_message)
            self.placeholder.markdown(container_content, unsafe_allow_html=True)

    def display_dataframe(self, df):
        """
        Display the dataframe in Streamlit UI within the chat container.
        """
        message_alignment = "flex-start"
        avatar_class = "bot-avatar"

        st.write(
            f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                <img src="{bot_avt}" class="{avatar_class}" alt="avatar" style="width: {avt_size}px; height: {avt_size}px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(df)

    def on_llm_end(self, response, run_id, parent_run_id=None, **kwargs):
        """
        Reset the buffer when the LLM finishes running.
        """
        self.token_buffer = []  # Reset the buffer
        self.has_streaming_ended = True

    def __call__(self, *args, **kwargs):
        pass