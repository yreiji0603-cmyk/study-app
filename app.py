import streamlit as st
import pandas as pd
import datetime
import random
import os

# --- データベースファイルの定義 ---
TASKS_FILE = "tasks_db.csv"     # タスク一覧
LOG_FILE = "completed_log.csv"  # 完了履歴
CONFIG_FILE = "config_db.csv"   # 目標・期間設定

# --- データ読み込み・保存の関数 ---
def load_tasks():
    if os.path.exists(TASKS_FILE):
        return pd.read_csv(TASKS_FILE)
    return pd.DataFrame(columns=["ID", "科目", "参考書", "章", "タスク名", "連番", "完了フラグ", "タイプ", "タイプ内番号"])

def save_tasks(df):
    df.to_csv(TASKS_FILE, index=False)

def load_log():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        df['完了日'] = pd.to_datetime(df['完了日']).dt.date
        return df
    return pd.DataFrame(columns=["タスクID", "完了日", "科目", "参考書", "章", "タスク名"])

def save_log(df):
    df.to_csv(LOG_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        df = pd.read_csv(CONFIG_FILE)
        return {
            "start_date": datetime.datetime.strptime(df.loc[0, "start_date"], "%Y-%m-%d").date(),
            "end_date": datetime.datetime.strptime(df.loc[0, "end_date"], "%Y-%m-%d").date(),
            "initial_total": int(df.loc[0, "initial_total"])
        }
    return {
        "start_date": datetime.date(2026, 7, 20),
        "end_date": datetime.date(2026, 8, 31),
        "initial_total": 0
    }

def save_config(start, end, initial_total):
    df = pd.DataFrame([{
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "initial_total": initial_total
    }])
    df.to_csv(CONFIG_FILE, index=False)

# --- 画面構成 ---
st.set_page_config(page_title="クエスト勉強管理", page_icon="🎒", layout="centered")

# 🌐 アプリの本番ページに飛ぶボタン
st.link_button("🌐 アプリのページを開く（ブックマーク用）", "https://share.streamlit.io/", use_container_width=True)

st.title("🎒 クエスト型 勉強タスク管理")

if "today_menu" not in st.session_state:
    st.session_state.today_menu = []
if "selected_subjects" not in st.session_state:
    st.session_state.selected_subjects = []
if "selected_books" not in st.session_state:
    st.session_state.selected_books = []

tab1, tab2, tab_list, tab3, tab4 = st.tabs([
    "🎮 今日のメニュー", 
    "➕ タスク一括登録", 
    "📋 タスク一覧", 
    "📅 計画設定 & ペース", 
    "📊 完了履歴"
])

# --- TAB 1: 今日のメニュー ---
with tab1:
    st.subheader("🔥 今日のクエスト")
    df_tasks = load_tasks()
    df_log = load_log()
    uncompleted = df_tasks[df_tasks["完了フラグ"] == 0]
    
    if uncompleted.empty:
        st.success("🎉 現在、未完了タスクはありません！")
    else:
        # STEP 1: 科目を選択
        subjects = sorted(list(uncompleted["科目"].unique()))
        selected_subs = st.multiselect("1. 挑戦する科目を選択:", subjects, default=st.session_state.selected_subjects)
        st.session_state.selected_subjects = selected_subs
        
        # STEP 2: 選択された科目に紐づく参考書を選択
        selected_books = []
        if selected_subs:
            available_books = sorted(list(uncompleted[uncompleted["科目"].isin(selected_subs)]["参考書"].unique()))
            default_books = [b for b in st.session_state.selected_books if b in available_books]
            selected_books = st.multiselect("2. 対象の参考書を選択:", available_books, default=default_books)
            st.session_state.selected_books = selected_books
        
        num_tasks = st.number_input("今日のタスク数:", min_value=1, max_value=10, value=1)
        
        if st.button("🎲 クエストを生成する", use_container_width=True):
            if not selected_subs or not selected_books:
                st.warning("科目と参考書をそれぞれ1つ以上選択してください。")
            else:
                candidates = []
                filtered_tasks = uncompleted[
                    (uncompleted["科目"].isin(selected_subs)) & 
                    (uncompleted["参考書"].isin(selected_books))
                ]
                
                for book in filtered_tasks["参考書"].unique():
                    book_tasks = filtered_tasks[filtered_tasks["参考書"] == book]
                    next_task = book_tasks.sort_values(by="連番").iloc[0]
                    candidates.append(next_task.to_dict())
                
                if candidates:
                    random.shuffle(candidates)
                    st.session_state.today_menu = candidates[:num_tasks]
                else:
                    st.warning("条件に合う未完了タスクがありません。")
                    st.session_state.today_menu = []
                
        if st.session_state.today_menu:
            st.write("---")
            today = datetime.date.today()
            today_completed_ids = df_log[df_log["完了日"] == today]["タスクID"].tolist()
            
            sorted_menu = sorted(
                st.session_state.today_menu,
                key=lambda x: 1 if int(x["ID"]) in today_completed_ids else 0
            )
            
            for task in sorted_menu:
                task_id = int(task["ID"])
                is_done = task_id in today_completed_ids
                
                status_text = "✅ クリア済み" if is_done else "⚔️ 挑戦中"
                bg_color = "#e8f5e9" if is_done else "#fffdf0"
                border_color = "#2e7d32" if is_done else "#f1c40f"
                
                html_code = f"""
                <div style="
                    background-color: {bg_color}; 
                    border: 2px solid {border_color}; 
                    padding: 12px; 
                    border-radius: 8px; 
                    margin-bottom: 8px;
                ">
                    <span style="font-weight: bold; font-size: 13px; color: {border_color};">{status_text}</span><br>
                    <span style="font-size: 16px; font-weight: bold; color: #1e1e1e;">📘 {task['科目']} / {task['参考書']}</span><br>
                    <span style="font-size: 13px; color: #555555;">📁 {task['章']}</span><br>
                    <span style="font-size: 15px; font-weight: bold; color: #2c3e50;">🔥 クエスト: {task['タスク名']}</span>
                </div>
                """
                st.markdown(html_code, unsafe_allow_html=True)
                
                checked = st.checkbox(
                    f"完了したらチェック！ (ID: {task_id})", 
                    value=is_done, 
                    key=f"chk_{task_id}"
                )
                
                if checked and not is_done:
                    df_tasks.loc[df_tasks["ID"] == task_id, "完了フラグ"] = 1
                    save_tasks(df_tasks)
                    new_log = pd.DataFrame([{
                        "タスクID": task_id,
                        "完了日": today,
                        "科目": task["科目"],
                        "参考書": task["参考書"],
                        "章": task["章"],
                        "タスク名": task["タスク名"]
                    }])
                    df_log = pd.concat([df_log, new_log], ignore_index=True)
                    save_log(df_log)
                    st.success(f"👏 {task['タスク名']} クリア！")
                    st.rerun()
                elif not checked and is_done:
                    df_tasks.loc[df_tasks["ID"] == task_id, "完了フラグ"] = 0
                    save_tasks(df_tasks)
                    df_log = df_log[df_log["タスクID"] != task_id]
                    save_log(df_log)
                    st.warning("クリアを取り消しました。")
                    st.rerun()

# --- TAB 2: タスク一括登録 ---
with tab2:
    st.subheader("📝 章単位の一括登録")
    with st.form("bulk_register"):
        col1, col2 = st.columns(2)
        with col1:
            sub = st.text_input("科目", "")
            book = st.text_input("参考書名", "")
        with col2:
            chapter = st.text_input("章名", "")
            total_num = st.number_input("追加する問題の総数", min_value=1, max_value=100, value=1)
            
        st.write("▼ 例題と練習の比率")
        col3, col4 = st.columns(2)
        with col3:
            ex_pattern = st.number_input("例題が続く数", min_value=1, max_value=50, value=1)
        with col4:
            prac_pattern = st.number_input("その後の練習の数", min_value=1, max_value=50, value=1)
            
        st.write("⚠️ **解かなくていい問題（スキップする番号）**")
        skip_inputs = st.text_input(
            "スキップする番号（半角カンマ区切り。例: 3, 5, 12）", 
            value="",
            help="ここに入力した番号は、一括生成の際に登録されずスキップされます。"
        )
            
        st.write("▼ 番号の引き継ぎ設定")
        continue_numbering = st.checkbox("前回の続きの番号から登録する", value=True, help="チェックを入れると、前回の『例題』『練習』の最後の番号の続きから開始します。")
            
        submit = st.form_submit_button("タスクを一括生成する")
        
        if submit:
            if not sub or not book or not chapter:
                st.error("科目、参考書名、章名はすべて入力してください！")
            else:
                df_tasks = load_tasks()
                
                # スキップする番号のリストを作成
                skip_list = []
                if skip_inputs.strip():
                    try:
                        skip_list = [int(x.strip()) for x in skip_inputs.split(",") if x.strip().isdigit()]
                    except ValueError:
                        st.warning("スキップ番号の指定に正しくない文字が含まれていました。無視して登録します。")
                
                if "タイプ" not in df_tasks.columns:
                    df_tasks["タイプ"] = "例題"
                if "タイプ内番号" not in df_tasks.columns:
                    df_tasks["タイプ内番号"] = df_tasks["連番"]
                    
                start_id = df_tasks["ID"].max() + 1 if not df_tasks.empty else 1
                
                start_ex_num = 1
                start_prac_num = 1
                
                if continue_numbering and not df_tasks.empty:
                    history = df_tasks[(df_tasks["科目"] == sub) & (df_tasks["参考書"] == book)]
                    if not history.empty:
                        ex_history = history[history["タイプ"] == "例題"]
                        prac_history = history[history["タイプ"] == "練習"]
                        
                        if not ex_history.empty:
                            start_ex_num = int(ex_history["タイプ内番号"].max()) + 1
                        if not prac_history.empty:
                            start_prac_num = int(prac_history["タイプ内番号"].max()) + 1

                new_rows = []
                current_type = "例題"
                pattern_counter = 0
                
                ex_idx = start_ex_num
                prac_idx = start_prac_num
                
                # 指定された総数の『有効なタスク』が生成されるまでループ
                created_count = 0
                serial_counter = 1
                
                # 最大1000回ループ（無限ループ防止用。総数より多いループが必要になるため）
                for _ in range(1000):
                    if created_count >= total_num:
                        break
                        
                    is_skipped = False
                    
                    if current_type == "例題":
                        pattern_counter += 1
                        task_title = f"例題 {ex_idx}"
                        task_type = "例題"
                        type_num = ex_idx
                        
                        # 例題の番号がスキップ対象に入っているか確認
                        if type_num in skip_list:
                            is_skipped = True
                        
                        ex_idx += 1
                        
                        if pattern_counter >= ex_pattern:
                            current_type = "練習"
                            pattern_counter = 0
                    else:
                        pattern_counter += 1
                        task_title = f"練習 {prac_idx}"
                        task_type = "練習"
                        type_num = prac_idx
                        
                        # 練習の番号がスキップ対象に入っているか確認
                        if type_num in skip_list:
                            is_skipped = True
                            
                        prac_idx += 1
                        
                        if pattern_counter >= prac_pattern:
                            current_type = "例題"
                            pattern_counter = 0
                    
                    # スキップ対象でなければ登録用の行に追加
                    if not is_skipped:
                        new_rows.append({
                            "ID": start_id,
                            "科目": sub,
                            "参考書": book,
                            "章": chapter,
                            "タスク名": task_title,
                            "連番": serial_counter,
                            "完了フラグ": 0,
                            "タイプ": task_type,
                            "タイプ内番号": type_num
                        })
                        start_id += 1
                        created_count += 1
                        serial_counter += 1
                
                if new_rows:
                    new_df = pd.DataFrame(new_rows)
                    df_tasks = pd.concat([df_tasks, new_df], ignore_index=True)
                    save_tasks(df_tasks)
                    st.success(f"🎯 【{sub}】のタスクを {created_count} 件生成しました！（スキップした番号は除外されています）")

# --- TAB_LIST: タスク一覧 (ドリルダウン選択UIに変更) ---
with tab_list:
    st.subheader("📋 登録済みのタスク一覧")
    df_tasks = load_tasks()
    
    if df_tasks.empty:
        st.info("登録されているタスクはありません。")
    else:
        # ドリルダウン選択用のセッション状態を管理
        if "drill_sub" not in st.session_state:
            st.session_state.drill_sub = None
        if "drill_book" not in st.session_state:
            st.session_state.drill_book = None

        # 1. 戻るボタンやパンくずリストの表示
        if st.session_state.drill_sub is not None:
            cols_nav = st.columns([1, 4])
            with cols_nav[0]:
                if st.button("⬅️ 戻る", use_container_width=True):
                    if st.session_state.drill_book is not None:
                        st.session_state.drill_book = None
                    else:
                        st.session_state.drill_sub = None
                    st.rerun()
            with cols_nav[1]:
                path_text = f"📍 {st.session_state.drill_sub}"
                if st.session_state.drill_book is not None:
                    path_text += f" ＞ {st.session_state.drill_book}"
                st.info(path_text)

        # 段階1: 科目の選択画面
        if st.session_state.drill_sub is None:
            st.write("📂 **まずは科目を選択してください:**")
            unique_subs = sorted(list(df_tasks["科目"].unique()))
            
            for sub_name in unique_subs:
                sub_tasks = df_tasks[df_tasks["科目"] == sub_name]
                uncompleted_sub_count = len(sub_tasks[sub_tasks["完了フラグ"] == 0])
                total_sub_count = len(sub_tasks)
                
                sub_btn_label = f"📁 {sub_name}  ({uncompleted_sub_count}/{total_sub_count} 未完了)"
                if st.button(sub_btn_label, key=f"sub_btn_{sub_name}", use_container_width=True):
                    st.session_state.drill_sub = sub_name
                    
                    # 💡 参考書が1つだけかどうか、この時点で先回りで判定
                    books_in_sub = sorted(list(sub_tasks["参考書"].unique()))
                    if len(books_in_sub) == 1:
                        st.session_state.drill_book = books_in_sub[0]  # 1つだけなら自動セットしてスキップ
                    else:
                        st.session_state.drill_book = None
                        
                    st.rerun()
                    
        # 段階2: 参考書の選択画面 (複数ある場合のみここに到達する)
        elif st.session_state.drill_book is None:
            sub_tasks = df_tasks[df_tasks["科目"] == st.session_state.drill_sub]
            books_in_sub = sorted(list(sub_tasks["参考書"].unique()))
            
            st.write(f"📖 **{st.session_state.drill_sub} の参考書を選択してください:**")
            for book_name in books_in_sub:
                book_tasks = sub_tasks[sub_tasks["参考書"] == book_name]
                uncompleted_book_count = len(book_tasks[book_tasks["完了フラグ"] == 0])
                total_book_count = len(book_tasks)
                
                book_btn_label = f"📖 {book_name}  ({uncompleted_book_count}/{total_book_count} 未完了)"
                if st.button(book_btn_label, key=f"book_btn_{book_name}", use_container_width=True):
                    st.session_state.drill_book = book_name
                    st.rerun()
                    
        # 段階3: 絞り込まれたタスクの一覧表示
        else:
            df_display = df_tasks[
                (df_tasks["科目"] == st.session_state.drill_sub) & 
                (df_tasks["参考書"] == st.session_state.drill_book)
            ]
            
            st.write("---")
            st.write("🔍 **ステータスで絞り込み**")
            filter_status = st.selectbox("進行度:", ["すべて", "未完了のみ", "完了のみ"])
            
            if filter_status == "未完了のみ":
                df_display = df_display[df_display["完了フラグ"] == 0]
            elif filter_status == "完了のみ":
                df_display = df_display[df_display["完了フラグ"] == 1]
                
            st.write(f"該当件数: **{len(df_display)}** 件")
            st.write("---")
            
            for index, row in df_display.iterrows():
                status_emoji = "✅ [完了]" if row["完了フラグ"] == 1 else "⏳ [未完了]"
                bg_color = "#e8f5e9" if row["完了フラグ"] == 1 else "#f5f5f5"
                border_color = "#2e7d32" if row["完了フラグ"] == 1 else "#9e9e9e"
                
                html_code_list = f"""
                <div style="
                    background-color: {bg_color}; 
                    border: 1px solid {border_color}; 
                    padding: 12px; 
                    border-radius: 8px; 
                    margin-bottom: 10px;
                ">
                    <span style="font-weight: bold; font-size: 14px; color: {border_color};">{status_emoji} (ID: {row['ID']})</span><br>
                    <span style="font-size: 16px; font-weight: bold; color: #1e1e1e;">📘 {row['科目']} / {row['参考書']}</span><br>
                    <span style="font-size: 14px; color: #555555;">📁 章: {row['章']}</span><br>
                    <span style="font-size: 15px; font-weight: bold; color: #2c3e50;">⚔️ クエスト: {row['タスク名']}</span>
                </div>
                """
                st.markdown(html_code_list, unsafe_allow_html=True)
            
            st.write("---")
            st.write("⚠️ **タスクの削除（個別・一括）**")
            delete_option = st.selectbox("削除方法:", ["選択しない", "個別に削除", "すべて削除"])
            
            if delete_option == "個別に削除":
                delete_id = st.selectbox(
                    "削除するタスクを選択:", 
                    options=df_display["ID"].tolist(),
                    format_func=lambda x: f"ID {x}: {df_tasks.loc[df_tasks['ID'] == x, '科目'].values[0]} - {df_tasks.loc[df_tasks['ID'] == x, 'タスク名'].values[0]}"
                )
                if st.button("🚨 選択したタスクを削除する", use_container_width=True):
                    df_tasks = df_tasks[df_tasks["ID"] != delete_id]
                    save_tasks(df_tasks)
                    st.success("削除しました！")
                    st.rerun()
                    
            elif delete_option == "すべて削除":
                st.warning("登録されているすべてのクエストが削除され、元に戻せなくなります。")
                confirm = st.checkbox("本当にすべてのクエストを削除することに同意します")
                if confirm:
                    if st.button("🔥 すべてのクエストを完全削除する", use_container_width=True):
                        df_empty = pd.DataFrame(columns=["ID", "科目", "参考書", "章", "タスク名", "連番", "完了フラグ", "タイプ", "タイプ内番号"])
                        save_tasks(df_empty)
                        # ドリルダウンセッションもクリア
                        st.session_state.drill_sub = None
                        st.session_state.drill_book = None
                        st.success("すべてのタスクをリセットしました！")
                        st.rerun()

# --- TAB 3: 計画設定 & ペース計算 ---
with tab3:
    st.subheader("📅 スケジュールと2つのペース")
    config = load_config()
    df_tasks = load_tasks()
    uncompleted_count = len(df_tasks[df_tasks["完了フラグ"] == 0])
    
    st.write("✏️ **夏休みのスケジュールを設定**")
    col_s, col_e = st.columns(2)
    with col_s:
        start_date = st.date_input("夏休み開始日", config["start_date"])
    with col_e:
        end_date = st.date_input("夏休み最終日", config["end_date"])
        
    if st.button("スケジュールを保存する"):
        total_tasks = len(df_tasks)
        save_config(start_date, end_date, total_tasks)
        st.success("スケジュールと初期タスク数を
