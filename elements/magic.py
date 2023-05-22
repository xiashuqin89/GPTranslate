from typing import Dict, Callable
from functools import wraps

import streamlit as st
from streamlit.server.server import Server
from streamlit.scriptrunner.script_run_context import get_script_run_ctx


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
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': domain,
            'Report a bug': domain,
            'About': title
        }
    )


def get_headers() -> Dict:
    session_id = get_script_run_ctx().session_id
    server = Server.get_current()
    session_info = server._get_session_info(session_id)
    if session_info.ws is None:
        st.markdown("Unable to get session websocket. Please refresh the page.")
        st.stop()
    return session_info.ws.request.headers


def post_compile(title: str, domain: str):
    def deco(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            init_page(title, domain)
            hide_footer()
            func(*args, **kwargs)
        return wrapper
    return deco
