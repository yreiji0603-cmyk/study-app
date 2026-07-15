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
    "📋 クエスト一覧", 
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
            # 前回の選択が有効かチェックしつつデフォルト値を設定
            default_books = [b for b in st.session_state.selected_books if b in available_books]
            selected_books = st.multiselect("2. 対象の参考書を選択:", available_books, default=default_books)
            st.session_state.selected_books = selected_books
        
        num_tasks = st.number_input("今日のタスク数:", min_value=1, max_value=10, value=3)
        
        if st.button("🎲 クエストを生成する", use_container_width=True):
            if not selected_subs or not selected_books:
                st.warning("科目と参考書をそれぞれ1つ以上選択してください。")
            else:
                candidates = []
                # 選択された科目・参考書に絞り込む
                filtered_tasks = uncompleted[
                    (uncompleted["科目"].isin(selected_subs)) & 
                    (uncompleted["参考書"].isin(selected_books))
                ]
                
                # 各参考書ごとに、最も連番が若い（次の）タスクを候補にする
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
            
            # --- 👑 終わったクエストを一番下に並び替える処理 ---
            # 完了状態を判定して、未完了を上に、完了済みを下にソート
            sorted_menu = sorted(
                st.session_state.today_menu,
                key=lambda x: 1 if int(x["ID"]) in today_completed_ids else 0
            )
            
            for task in sorted_menu:
                task_id = int(task["ID"])
                is_done = task_id in today_completed_ids
                
                # 完了しているタスクには「[済]」をつけ、打ち消し線風にする
                label_prefix = "✅ [クリア済み] " if is_done else "⚔️ "
                checked = st.checkbox(
                    f"{label_prefix}【{task['科目']}】 {task['参考書']} ({task['章']}) - {task['タスク名']}", 
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
            # 💡 初期値を空欄に変更しました
            sub = st.text_input("科目", "")
            book = st.text_input("参考書名", "")
        with col2:
            # 💡 初期値を空欄に変更しました
            chapter = st.text_input("章名", "")
            total_num = st.number_input("追加する問題の総数", min_value=1, max_value=100, value=10)
            
        st.write("▼ 例題と練習の比率")
        col3, col4 = st.columns(2)
        with col3:
            ex_pattern = st.number_input("例題が続く数", min_value=1, max_value=50, value=2)
        with col4:
            prac_pattern = st.number_input("その後の練習の数", min_value=1, max_value=50, value=8)
            
        st.write("▼ 番号の引き継ぎ設定")
        continue_numbering = st.checkbox("前回の続きの番号から登録する", value=True, help="チェックを入れると、前回の『例題』『練習』の最後の番号の続きから開始します。")
            
        submit = st.form_submit_button("タスクを一括生成する")
        
        if submit:
            if not sub or not book or not chapter:
                st.error("科目、参考書名、章名はすべて入力してください！")
            else:
                df_tasks = load_tasks()
                
                # 既存のデータフレームに必要なカラムが存在しない場合の互換性処理
                if "タイプ" not in df_tasks.columns:
                    df_tasks["タイプ"] = "例題"
                if "タイプ内番号" not in df_tasks.columns:
                    df_tasks["タイプ内番号"] = df_tasks["連番"]
                    
                start_id = df_tasks["ID"].max() + 1 if not df_tasks.empty else 1
                
                # 開始番号の決定
                start_ex_num = 1
                start_prac_num = 1
                
                if continue_numbering and not df_tasks.empty:
                    # この科目＆参考書で登録済みのタスクを探す
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
                
                for i in range(1, total_num + 1):
                    if current_type == "例題":
                        pattern_counter += 1
                        task_title = f"例題 {ex_idx}"
                        task_type = "例題"
                        type_num = ex_idx
                        ex_idx += 1
                        
                        if pattern_counter >= ex_pattern:
                            current_type = "練習"
                            pattern_counter = 0
                    else:
                        pattern_counter += 1
                        task_title = f"練習 {prac_idx}"
                        task_type = "練習"
                        type_num = prac_idx
                        prac_idx += 1
                        
                        if pattern_counter >= prac_pattern:
                            current_type = "例題"
                            pattern_counter = 0
                    
                    new_rows.append({
                        "ID": start_id,
                        "科目": sub,
                        "参考書": book,
                        "章": chapter,
                        "タスク名": task_title,
                        "連番": i, # この章の中での並び順
                        "完了フラグ": 0,
                        "タイプ": task_type,
                        "タイプ内番号": type_num
                    })
                    start_id += 1
                    
                new_df = pd.DataFrame(new_rows)
                df_tasks = pd.concat([df_tasks, new_df], ignore_index=True)
                save_tasks(df_tasks)
                st.success(f"🎯 【{sub}】のタスクを {total_num} 件生成しました！ (例題は {start_ex_num}〜, 練習は {start_prac_num}〜)")

# --- TAB_LIST: クエスト一覧 ---
with tab_list:
    st.subheader("📋 登録済みのクエスト一覧")
    df_tasks = load_tasks()
    
    if df_tasks.empty:
        st.info("登録されているクエストはありません。「タスク一括登録」から登録してください。")
    else:
        if "タイプ" not in df_tasks.columns:
            df_tasks["タイプ"] = "例題"
        if "タイプ内番号" not in df_tasks.columns:
            df_tasks["タイプ内番号"] = df_tasks["連番"]

        df_display = df_tasks.copy()
        df_display["ステータス"] = df_display["完了フラグ"].apply(lambda x: "✅ 完了" if x == 1 else "⏳ 未完了")
        
        st.write("🔍 **絞り込み**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_sub = st.selectbox("科目で絞り込む:", ["すべて"] + sorted(list(df_tasks["科目"].unique())))
        with col_f2:
            filter_status = st.selectbox("状態:", ["すべて", "未完了のみ", "完了のみ"])
            
        if filter_sub != "すべて":
            df_display = df_display[df_display["科目"] == filter_sub]
            
        if filter_status == "未完了のみ":
            df_display = df_display[df_display["完了フラグ"] == 0]
        elif filter_status == "完了のみ":
            df_display = df_display[df_display["完了フラグ"] == 1]
            
        st.write(f"該当件数: **{len(df_display)}** 件")
        
        st.dataframe(
            df_display[["ID", "ステータス", "科目", "参考書", "章", "タスク名"]], 
            use_container_width=True,
            hide_index=True
        )
        
        st.write("---")
        st.write("⚠️ **クエストの削除（個別・一括）**")
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
        st.success("スケジュールと初期タスク数を記録しました！")
        st.rerun()
        
    st.write("---")
    st.write("📊 **ペース分析**")
    today = datetime.date.today()
    total_days = (end_date - start_date).days + 1
    remaining_days = (end_date - today).days + 1
    
    if remaining_days <= 0:
        st.warning("設定された期間はすでに終了しています。")
    elif config["initial_total"] == 0:
        st.info("スケジュールを保存すると、目標ペースが計算されます。")
    else:
        initial_pace = config["initial_total"] / total_days
        current_pace = uncompleted_count / remaining_days if remaining_days > 0 else 0
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric(label="🗺️ 当初の目標ペース", value=f"{initial_pace:.1f} 問 / 日")
        with col_p2:
            diff = current_pace - initial_pace
            delta_val = f"{diff:+.1f} 問" if diff != 0 else "キープ中"
            st.metric(label="🚀 現在の必要ペース", value=f"{current_pace:.1f} 問 / 日", delta=delta_val, delta_color="inverse")
            
        st.info(f"残り日数: **{remaining_days}日** | 未完了タスク: **{uncompleted_count}問**")

# --- TAB 4: 完了履歴 ---
with tab4:
    st.subheader("📅 日ごとの勉強履歴")
    df_log = load_log()
    
    if df_log.empty:
        st.info("完了したタスクはここに自動で記録されます。")
    else:
        log_dates = sorted(list(df_log["完了日"].unique()), reverse=True)
        selected_date = st.selectbox("確認したい日付を選択:", log_dates)
        day_logs = df_log[df_log["完了日"] == selected_date]
        st.write(f"### 🗓️ {selected_date} の学習内容")
        st.success(f"この日は **{len(day_logs)} 個** のタスクを完了しました！")
        st.dataframe(day_logs[["科目", "参考書", "章", "タスク名"]], use_container_width=True)
