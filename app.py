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
    return pd.DataFrame(columns=["ID", "科目", "参考書", "章", "タスク名", "連番", "完了フラグ"])

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

tab1, tab2, tab3, tab4 = st.tabs(["🎮 今日のメニュー", "➕ タスク一括登録", "📅 計画設定 & ペース", "📊 完了履歴"])

# --- TAB 1: 今日のメニュー ---
with tab1:
    st.subheader("🔥 今日のクエスト")
    df_tasks = load_tasks()
    df_log = load_log()
    uncompleted = df_tasks[df_tasks["完了フラグ"] == 0]
    
    if uncompleted.empty:
        st.success("🎉 現在、未完了タスクはありません！")
    else:
        subjects = sorted(list(uncompleted["科目"].unique()))
        selected_subs = st.multiselect("挑戦する科目を選択:", subjects, default=st.session_state.selected_subjects)
        st.session_state.selected_subjects = selected_subs
        
        num_tasks = st.number_input("今日のタスク数:", min_value=1, max_value=10, value=3)
        
        if st.button("🎲 クエストを生成する", use_container_width=True):
            candidates = []
            for sub in selected_subs:
                sub_tasks = uncompleted[uncompleted["科目"] == sub]
                for book in sub_tasks["参考書"].unique():
                    book_tasks = sub_tasks[sub_tasks["参考書"] == book]
                    next_task = book_tasks.sort_values(by="連番").iloc[0]
                    candidates.append(next_task.to_dict())
            
            if candidates:
                random.shuffle(candidates)
                st.session_state.today_menu = candidates[:num_tasks]
            else:
                st.warning("選択した科目のタスクがありません。")
                st.session_state.today_menu = []
                
        if st.session_state.today_menu:
            st.write("---")
            today = datetime.date.today()
            today_completed_ids = df_log[df_log["完了日"] == today]["タスクID"].tolist()
            
            for task in st.session_state.today_menu:
                task_id = int(task["ID"])
                is_done = task_id in today_completed_ids
                
                checked = st.checkbox(
                    f"【{task['科目']}】 {task['参考書']} ({task['章']}) - {task['タスク名']}", 
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
            sub = st.text_input("科目", "数学")
            book = st.text_input("参考書名", "青チャート")
        with col2:
            chapter = st.text_input("章名", "第1章")
            total_num = st.number_input("問題の総数", min_value=1, max_value=100, value=10)
            
        st.write("▼ 例題と練習の比率")
        col3, col4 = st.columns(2)
        with col3:
            ex_pattern = st.number_input("例題が続く数", min_value=1, max_value=50, value=2)
        with col4:
            prac_pattern = st.number_input("その後の練習の数", min_value=1, max_value=50, value=8)
            
        submit = st.form_submit_button("タスクを一括生成する")
        
        if submit:
            df_tasks = load_tasks()
            start_id = df_tasks["ID"].max() + 1 if not df_tasks.empty else 1
            
            new_rows = []
            current_type = "例題"
            pattern_counter = 0
            
            for i in range(1, total_num + 1):
                if current_type == "例題":
                    pattern_counter += 1
                    task_title = f"例題 {i}"
                    if pattern_counter >= ex_pattern:
                        current_type = "練習"
                        pattern_counter = 0
                else:
                    pattern_counter += 1
                    task_title = f"練習 {i}"
                    if pattern_counter >= prac_pattern:
                        current_type = "例題"
                        pattern_counter = 0
                
                new_rows.append({
                    "ID": start_id,
                    "科目": sub,
                    "参考書": book,
                    "章": chapter,
                    "タスク名": task_title,
                    "連番": i,
                    "完了フラグ": 0
                })
                start_id += 1
                
            new_df = pd.DataFrame(new_rows)
            df_tasks = pd.concat([df_tasks, new_df], ignore_index=True)
            save_tasks(df_tasks)
            st.success(f"🎯 タスクを {total_num} 件生成しました！")

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
