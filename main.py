"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""
# ----- main.py の最上部（この上に他の import を置かない）-----
import sys, importlib

def ensure_sqlite335_or_newer():
    # まず標準sqlite3のバージョンを確認
    import sqlite3 as _std_sqlite3
    try:
        ver_tuple = tuple(map(int, _std_sqlite3.sqlite_version.split(".")))
    except Exception:
        ver_tuple = (0, 0, 0)

    if ver_tuple >= (3, 35, 0):
        # 十分新しい → 何もしない（ローカルは多くがこれ）
        print("[sqlite] using stdlib:", _std_sqlite3.sqlite_version, flush=True)
        return

    # 古い場合のみ pysqlite3 に差し替え（Cloud など）
    try:
        sqlite3 = importlib.import_module("pysqlite3.dbapi2")
        sys.modules["sqlite3"] = sqlite3
        sys.modules["sqlite3.dbapi2"] = sqlite3
        sys.modules["sqlite"] = sqlite3
        print("[sqlite] shimmed to pysqlite3:", sqlite3.sqlite_version, flush=True)
    except Exception as e:
        # ここに来るのは「古いのに pysqlite3 が入っていない」ケース
        raise RuntimeError(
            "sqlite3 < 3.35 かつ pysqlite3-binary 未導入です。"
            "requirements.txt に pysqlite3-binary を追加してください。"
        ) from e

ensure_sqlite335_or_newer()

import sys, os, traceback, logging
logging.basicConfig(level=logging.INFO)
print("BOOT: reached top of script", flush=True)

############################################################
# ライブラリの読み込み
############################################################
from dotenv import load_dotenv
import logging
import streamlit as st
import utils
from initialize import initialize
import components as cn
import constants as ct


############################################################
# 設定関連
############################################################
st.set_page_config(
    page_title=ct.APP_NAME
)

load_dotenv()

logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 初期化処理
############################################################
try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE))
    st.stop()

# アプリ起動時のログ出力
if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)


############################################################
# 初期表示
############################################################
# タイトル表示
cn.display_app_title()

# AIメッセージの初期表示
cn.display_initial_ai_message()


############################################################
# 会話ログの表示
############################################################
try:
    cn.display_conversation_log()
except Exception as e:
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE))
    st.stop()


############################################################
# チャット入力の受け付け
############################################################
chat_message = st.chat_input(ct.CHAT_INPUT_HELPER_TEXT)


############################################################
# チャット送信時の処理
############################################################
if chat_message:
    # ==========================================
    # 1. ユーザーメッセージの表示
    # ==========================================
    logger.info({"message": chat_message})

    with st.chat_message("user", avatar=ct.USER_ICON_FILE_PATH):
        st.markdown(chat_message)

    # ==========================================
    # 2. LLMからの回答取得
    # ==========================================
    res_box = st.empty()
    with st.spinner(ct.SPINNER_TEXT):
        try:
            result = st.session_state.retriever.invoke(chat_message)
        except Exception as e:
            logger.error(f"{ct.RECOMMEND_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.RECOMMEND_ERROR_MESSAGE))
            st.stop()
    
    # ==========================================
    # 3. LLMからの回答表示
    # ==========================================
    with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
        try:
            cn.display_product(result)
            
            logger.info({"message": result})
        except Exception as e:
            logger.error(f"{ct.LLM_RESPONSE_DISP_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.LLM_RESPONSE_DISP_ERROR_MESSAGE))
            st.stop()

    # ==========================================
    # 4. 会話ログへの追加
    # ==========================================
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": result})