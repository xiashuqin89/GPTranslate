from typing import Dict, Callable
from functools import wraps

import streamlit as st
from streamlit.web.server.websocket_headers import _get_websocket_headers
import extra_streamlit_components as stx

from settings import LOGIN_URL
from exceptions import LoginFailedError


def hide_menu():
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)


def hide_footer():
    hide_footer_style = """
                <style>
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_footer_style, unsafe_allow_html=True)


def init_page(title: str, domain: str):
    st.set_page_config(
        page_title=title,
        layout='wide',
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': domain,
            'Report a bug': domain,
            'About': title
        }
    )


def get_headers():
    # Hack to get the session object from Streamlit.
    return _get_websocket_headers()


def get_cookie_manager():
    return stx.CookieManager()


def get_cookie_val(key: str) -> str:
    cookie_manager = get_cookie_manager()
    return cookie_manager.get(cookie=key)


def post_compile(title: str, domain: str):
    def deco(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            init_page(title, domain)
            hide_footer()
            func(*args, **kwargs)
        return wrapper
    return deco


class Login:
    def __init__(self):
        self.username = get_cookie_val("bk_uid")
        # self.authenticate()

    def debug(self):
        st.json(get_headers())

    def authenticate(self):
        if not self.username:
            st.write(f'''<h1>
            Please login via <a target="_self"
            href="{LOGIN_URL}">Login</a></h1>''', unsafe_allow_html=True)
            self.debug()
            raise LoginFailedError
