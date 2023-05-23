import os
import json

import streamlit as st
from langdetect import detect

from settings import DOMAIN, LANGUAGE
from elements.magic import (
    post_compile, Login
)
from exceptions import LoginFailedError
from utils.db import RedisClient
from log import logger

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Engine(Login):
    def __init__(self):
        super(Engine, self).__init__()
        self.input_type = 'Text'
        self.project = ''
        self.language = ''
        self.rc = RedisClient(env="prod")

    def get_project(self):
        project = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project:{self.username}')
        if not project:
            return []
        return [json.loads(item)['project_name'] for item in project]

    def get_term(self, project_name: str):
        return self.rc.redis_client.hkeys(f'{APP_CODE}:{APP_ENV}:term:{project_name}')

    def menu(self):
        st.sidebar.text(self.username)
        st.sidebar.title('Menu')
        project = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project:{self.username}')
        project = [json.loads(item)['project_name'] for item in project]
        self.project = st.sidebar.selectbox('Project', tuple(project))
        self.input_type = st.sidebar.selectbox("Input Type", ('Text', 'File'))

    def text_translate(self):
        option_col1, option_col2, _ = st.columns([2, 2, 8])
        with option_col1:
            language = st.selectbox('', tuple(LANGUAGE))
        with option_col2:
            term = st.multiselect('', self.get_term(self.project))

        input_col1, input_col2 = st.columns(2)
        with input_col1:
            user_input = st.text_area('Your input', height=30)
            if user_input != '':
                language = detect(user_input)
                st.write(f'Lang:  {language}')

        with input_col2:
            status = 'waiting for input'
            if user_input != '':
                status = 'translating...'
            output = st.text_area('Chinese', placeholder=status)

    def file_translate(self):
        uploaded_file = st.file_uploader("Choose a file")
        if uploaded_file is not None:
            # To read file as bytes:
            msg = st.empty()
            msg.info('translating...')
            bytes_data = uploaded_file.getvalue()
            st.write(bytes_data)

    def render(self):
        self.menu()
        st.title('Debug')
        if self.input_type == 'Text':
            self.text_translate()
        elif self.input_type == 'File':
            self.file_translate()


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Engine().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
