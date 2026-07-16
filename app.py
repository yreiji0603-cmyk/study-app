import streamlit as st
import pandas as pd
import datetime
import random
import os

# --- データベースファイルの定義 ---
TASKS_FILE = "tasks_db.csv"     # タスク一覧
LOG_FILE = "completed_log.csv"  # 完了履歴
CONFIG_FILE = "config_db.csv"   # スケジュール設定

# --- データ読み込み・保存の関数 ---
def load_tasks():
    if os.path.exists(TASKS_FILE):
        return pd.read_csv(TASKS_FILE)
    return pd.DataFrame(columns=["ID", "Subject", "Book", "Chapter", "TaskName", "DoneFlag"])

def save_tasks(df):
    df.to_csv(TASKS_FILE, index=False)

def load_log():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        df['CompletedDate'] = pd.to_datetime(df['CompletedDate']).dt.date
        return df
    return pd.DataFrame(columns=["TaskID", "CompletedDate", "Subject", "Book", "Chapter", "TaskName"])

def save_log(df):
    df.to_csv(LOG_FILE, index=False)

# --- 画面構成の設定 ---
st.set_page_config(page_title="Quest Study", page_icon="🎒", layout="centered")
st.title("🎒 Quest Study Manager")

# 🌐 ブックマーク用のリンクボタン
st.link_button("🌐 アプリのページを開く", "https://share.streamlit.io/", use_container_width=True)

# 2つの大画面を切り替えるタブ
tab_main, tab_register = st.tabs(["🎮 クエストに挑戦 (メイン)", "➕ タスクの登録・削除"])

# データ読み込み
df_tasks = load_tasks()
df_log = load_log()

# --- セッション状態の初期化 ---
if "drill_sub" not in st.session_state:
    st.session_state.drill_sub = None
if "drill_book" not in st.session_state:
    st.session_state.drill_book = None
if "drill_chap" not in st.session_state:
    st.session_state.drill_chap = None
if "today_menu" not in st.session_state:
    st.session_state.today_menu = []

# --- TAB 1: メイン画面 (ドリルダウン ＆ クエスト) ---
with tab_main:
    st.write("### 📂 勉強する場所を選択")

    # 🗺️ Windows風のパンくずリスト (各項目がクリック可能)
    breadcrumb_cols = st.columns(5)
    
    # 階層1: HOME (すべてリセット)
    with breadcrumb_cols[0]:
        if st.button("🏠 HOME", use_container_width=True):
            st.session_state.drill_sub = None
            st.session_state.drill_book = None
            st.session_state.drill_chap = None
            st.rerun()

    # 階層2: 科目名
    if st.session_state.drill_sub:
        with breadcrumb_cols[1]:
            st.write("＞")
        with breadcrumb_cols[2]:
            if st.button(f"📁 {st.session_state.drill_sub}", use_container_width=True):
                st.session_state.drill_book = None
                st.session_state.drill_chap = None
                st.rerun()

    # 階層3: 参考書名
    if st.session_state.drill_book:
        with breadcrumb_cols[3]:
            st.write("＞")
        with breadcrumb_cols[4]:
            if st.button(f"📘 {st.session_state.drill_book}", use_container_width=True):
                st.session_state.drill_chap = None
                st.rerun()

    st.write("---")

    # ⬇️ 選択状況に応じたドリルダウン表示
    if df_tasks.empty:
        st.info("まずは「タスクの登録・削除」タブからクエストを登録してください！")
        
    elif st.session_state.drill_sub is None:
        st.write("#### 1. 科目を選んでください：")
        unique_subs = sorted(list(df_tasks["Subject"].unique()))
        for sub in unique_subs:
            sub_tasks = df_tasks[df_tasks["Subject"] == sub]
            left = len(sub_tasks[sub_tasks["DoneFlag"] == 0])
            total = len(sub_tasks)
            if st.button(f"📁 {sub}  (残り {left}/{total} 問)", key=f"sub_{sub}", use_container_width=True):
                st.session_state.drill_sub = sub
                st.rerun()

    elif st.session_state.drill_book is None:
        st.write(f"#### 2. 「{st.session_state.drill_sub}」の参考書を選んでください：")
        sub_tasks = df_tasks[df_tasks["Subject"] == st.session_state.drill_sub]
        unique_books = sorted(list(sub_tasks["Book"].unique()))
        for book in unique_books:
            book_tasks = sub_tasks[sub_tasks["Book"] == book]
            left = len(book_tasks[book_tasks["DoneFlag"] == 0])
            total = len(book_tasks)
            if st.button(f"📘 {book}  (残り {left}/{total} 問)", key=f"book_{book}", use_container_width=True):
                st.session_state.drill_book = book
                st.rerun()

    elif st.session_state.drill_chap is None:
        st.write(f"#### 3. 「{st.session_state.drill_book}」の章を選んでください：")
        book_tasks = df_tasks[
            (df_tasks["Subject"] == st.session_state.drill_sub) & 
            (df_tasks["Book"] == st.session_state.drill_book)
        ]
        unique_chaps = sorted(list(book_tasks["Chapter"].unique()))
        for chap in unique_chaps:
            chap_tasks = book_tasks[book_tasks["Chapter"] == chap]
            left = len(chap_tasks[chap_tasks["DoneFlag"] == 0])
            total = len(chap_tasks)
            if st.button(f"📄 {chap}  (残り {left}/{total} 問)", key=f"chap_{chap}", use_container_width=True):
                st.session_state.drill_chap = chap
                st.rerun()

    # 🎯 章まで選択されたら、その章のクエストを表示
    else:
        st.write(f"### ⚔️ クエストに挑戦！【{st.session_state.drill_chap}】")
        
        # 選択された章のタスクに絞り込む
        chap_tasks = df_tasks[
            (df_tasks["Subject"] == st.session_state.drill_sub) & 
            (df_tasks["Book"] == st.session_state.drill_book) & 
            (df_tasks["Chapter"] == st.session_state.drill_chap)
        ]
        
        uncompleted = chap_tasks[chap_tasks["DoneFlag"] == 0]
        
        if uncompleted.empty:
            st.success("🎉 この章のすべてのクエストをクリアしました！素晴らしい！")
        else:
            # クエストのランダム抽選
            num_tasks = st.number_input("挑戦する問題数を選択してください:", min_value=1, max_value=len(uncompleted), value=1)
            
            if st.button("🎲 クエストを発生させる", use_container_width=True):
                candidates = uncompleted.to_dict('records')
                random.shuffle(candidates)
                st.session_state.today_menu = candidates[:num_tasks]
            
            # 抽選されたメニューの表示
            if st.session_state.today_menu:
                st.write("---")
                today = datetime.date.today()
                
                # 完了履歴から今日完了したIDを取得
                today_completed_ids = df_log[df_log["CompletedDate"] == today]["TaskID"].tolist()
                
                for task in st.session_state.today_menu:
                    task_id = int(task["ID"])
                    # もし他の画面で更新されていた時のために現在のDoneFlagをチェック
                    current_status = df_tasks.loc[df_tasks["ID"] == task_id, "DoneFlag"].values[0]
                    is_done = (current_status == 1)
                    
                    status_text = "✅ クリア済み" if is_done else "⚔️ 挑戦中"
                    bg_color = "#e8f5e9" if is_done else "#fffdf0"
                    border_color = "#2e7d32" if is_done else "#f1c40f"
                    
                    # クエストカードの描画
                    html_code = f"""
                    <div style="
                        background-color: {bg_color}; 
                        border: 2px solid {border_color}; 
                        padding: 12px; 
                        border-radius: 8px; 
                        margin-bottom: 8px;
                    ">
                        <span style="font-weight: bold; font-size: 13px; color: {border_color};">{status_text}</span><br>
                        <span style="font-size: 16px; font-weight: bold; color: #1e1e1e;">📘 {task['Subject']} / {task['Book']}</span><br>
                        <span style="font-size: 13px; color: #555555;">📁 {task['Chapter']}</span><br>
                        <span style="font-size: 15px; font-weight: bold; color: #2c3e50;">🔥 クエスト: {task['TaskName']}</span>
                    </div>
                    """
                    st.markdown(html_code, unsafe_allow_html=True)
                    
                    # クリア用チェックボックス
                    checked = st.checkbox(
                        f"完了した！ (ID: {task_id})", 
                        value=is_done, 
                        key=f"chk_{task_id}"
                    )
                    
                    # チェックされた時の処理
                    if checked and not is_done:
                        df_tasks.loc[df_tasks["ID"] == task_id, "DoneFlag"] = 1
                        save_tasks(df_tasks)
                        
                        new_log = pd.DataFrame([{
                            "TaskID": task_id,
                            "CompletedDate": today,
                            "Subject": task["Subject"],
                            "Book": task["Book"],
                            "Chapter": task["Chapter"],
                            "TaskName": task["TaskName"]
                        }])
                        df_log = pd.concat([df_log, new_log], ignore_index=True)
                        save_log(df_log)
                        st.success(f"👏 {task['TaskName']} クリア！")
                        st.rerun()
                        
                    # チェックが外された時の処理
                    elif not checked and is_done:
                        df_tasks.loc[df_tasks["ID"] == task_id, "DoneFlag"] = 0
                        save_tasks(df_tasks)
                        
                        df_log = df_log[df_log["TaskID"] != task_id]
                        save_log(df_log)
                        st.warning("クリアを取り消しました。")
                        st.rerun()


# --- TAB 2: 管理・一括登録画面 (案Bベース) ---
with tab_register:
    st.write("### 📝 タスクの追加・整理")
    
    # --- 1. 一括登録フォーム ---
    st.write("#### ➕ 連続登録 (案B)")
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            reg_sub = st.text_input("1. 科目名 (例: 数学)", "")
            reg_book = st.text_input("2. 参考書名 (例: 青チャート)", "")
            reg_chap = st.text_input("3. 章名 (例: 第1章)", "")
        with col2:
            reg_prefix = st.selectbox("4. 種類を選んでください", ["例題", "練習"])
            start_num = st.number_input("5. 開始番号 (例: 15 から開始)", min_value=1, value=1)
            total_count = st.number_input("6. 生成する個数 (例: 5問分)", min_value=1, max_value=100, value=5)
            
        submit_btn = st.form_submit_button("上記の設定で連続登録する")
        
        if submit_btn:
            if not reg_sub or not reg_book or not reg_chap:
                st.error("科目、参考書、章はすべて入力してください！")
            else:
                start_id = df_tasks["ID"].max() + 1 if not df_tasks.empty else 1
                new_rows = []
                
                # 指定された開始番号から、個数分だけ連続生成
                for i in range(total_count):
                    current_num = start_num + i
                    new_rows.append({
                        "ID": start_id,
                        "Subject": reg_sub,
                        "Book": reg_book,
                        "Chapter": reg_chap,
                        "TaskName": f"{reg_prefix} {current_num}",
                        "DoneFlag": 0
                    })
                    start_id += 1
                
                new_df = pd.DataFrame(new_rows)
                df_tasks = pd.concat([df_tasks, new_df], ignore_index=True)
                save_tasks(df_tasks)
                st.success(f"🎯 {reg_sub} / {reg_book} / {reg_chap} に「{reg_prefix} {start_num}〜{start_num + total_count - 1}」を登録しました！")
                st.rerun()

    st.write("---")

    # --- 2. 個別削除フォーム (飛び番・使わない単元の整理用) ---
    st.write("#### 🗑️ 不要なタスクを個別に消す (飛び番対策)")
    if df_tasks.empty:
        st.info("まだ登録されているタスクがありません。")
    else:
        # 削除したいタスクを「科目」「参考書」「章」で絞り込んで選べるようにする
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            del_sub = st.selectbox("削除元の科目:", ["全て"] + list(df_tasks["Subject"].unique()))
            
        filtered_del = df_tasks if del_sub == "全て" else df_tasks[df_tasks["Subject"] == del_sub]
        
        with col_del2:
            del_book_opts = ["全て"] + list(filtered_del["Book"].unique())
            del_book = st.selectbox("削除元の参考書:", del_book_opts)
            
        if del_book != "全て":
            filtered_del = filtered_del[filtered_del["Book"] == del_book]
            
        # 削除対象となるタスクのリストを表示
        selected_delete_task = st.selectbox(
            "削除するクエストを選択してください:",
            options=filtered_del["ID"].tolist(),
            format_func=lambda x: f"ID: {x} | {df_tasks.loc[df_tasks['ID'] == x, 'Subject'].values[0]} - {df_tasks.loc[df_tasks['ID'] == x, 'Book'].values[0]} - {df_tasks.loc[df_tasks['ID'] == x, 'TaskName'].values[0]}"
        )
        
        if st.button("🚨 選択したクエストを削除する", use_container_width=True):
            df_tasks = df_tasks[df_tasks["ID"] != selected_delete_task]
            save_tasks(df_tasks)
            # もし抽選中メニューに入っていたら削除する
            st.session_state.today_menu = [t for t in st.session_state.today_menu if t["ID"] != selected_delete_task]
            st.success("指定したクエストを削除しました！")
            st.rerun()

    st.write("---")
    
    # --- 3. 完全初期化 ---
    st.write("#### 🔥 データの全削除 (初期化)")
    confirm_reset = st.checkbox("本当にすべての登録データを削除してやり直す場合はチェックを入れてください")
    if confirm_reset:
        if st.button("🚨 データベースを完全に初期化する", use_container_width=True):
            df_empty = pd.DataFrame(columns=["ID", "Subject", "Book", "Chapter", "TaskName", "DoneFlag"])
            save_tasks(df_empty)
            
            # 完了履歴もリセット
            df_log_empty = pd.DataFrame(columns=["TaskID", "CompletedDate", "Subject", "Book", "Chapter", "TaskName"])
            save_log(df_log_empty)
            
            # 選択中のステートもクリア
            st.session_state.drill_sub = None
            st.session_state.drill_book = None
            st.session_state.drill_chap = None
            st.session_state.today_menu = []
            
            st.success("すべてのデータを完全消去し、リセットしました！")
            st.rerun()
