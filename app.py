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
        df = pd.read_csv(TASKS_FILE)
        # IDを整数型に保証
        df['ID'] = df['ID'].astype(int)
        return df
    return pd.DataFrame(columns=["ID", "Subject", "Book", "Chapter", "TaskName", "DoneFlag"])

def save_tasks(df):
    df.to_csv(TASKS_FILE, index=False)

def load_log():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        df['CompletedDate'] = pd.to_datetime(df['CompletedDate']).dt.date
        # 勉強時間列がない古いデータへの対策
        if "Minutes" not in df.columns:
            df["Minutes"] = 5  # デフォルトで5分
        return df
    return pd.DataFrame(columns=["TaskID", "CompletedDate", "Subject", "Book", "Chapter", "TaskName", "Minutes"])

def save_log(df):
    df.to_csv(LOG_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        df = pd.read_csv(CONFIG_FILE)
        if not df.empty:
            return df.iloc[0].to_dict()
    return {
        "Deadline": str(datetime.date.today() + datetime.timedelta(days=30)),
        "WeeklyDays": 5
    }

def save_config(deadline, weekly_days):
    df = pd.DataFrame([{"Deadline": str(deadline), "WeeklyDays": int(weekly_days)}])
    df.to_csv(CONFIG_FILE, index=False)

# --- 画面構成の設定 ---
st.set_page_config(page_title="Quest Study", page_icon="🎒", layout="centered")
st.title("🎒 Quest Study Manager")

st.link_button("🌐 アプリのページを開く", "https://share.streamlit.io/", use_container_width=True)

# データ読み込み
df_tasks = load_tasks()
df_log = load_log()
config = load_config()

deadline_date = datetime.datetime.strptime(config["Deadline"], "%Y-%m-%d").date()
weekly_days = int(config["WeeklyDays"])

# 4つのタブ構成
tab_main, tab_report, tab_list, tab_register = st.tabs([
    "🎮 クエストに挑戦", 
    "📊 勉強の記録", 
    "📋 登録タスク一覧",
    "➕ タスクの登録・管理"
])

# --- セッション状態の初期化 ---
if "drill_sub" not in st.session_state:
    st.session_state.drill_sub = None
if "drill_book" not in st.session_state:
    st.session_state.drill_book = None
if "drill_chap" not in st.session_state:
    st.session_state.drill_chap = None
if "today_menu" not in st.session_state:
    st.session_state.today_menu = []
if "show_time_modal" not in st.session_state:
    st.session_state.show_time_modal = None

# --- TAB 1: メイン画面 (ドリルダウン ＆ クエスト) ---
with tab_main:
    # 📈 ペース・スケジュール状況
    st.write("### 📈 スケジュール状況")
    uncompleted_total = len(df_tasks[df_tasks["DoneFlag"] == 0]) if not df_tasks.empty else 0
    today = datetime.date.today()
    days_left = (deadline_date - today).days
    
    if uncompleted_total == 0:
        st.success("🎉 現在、残りのタスクはありません！素晴らしい状態です！")
    elif days_left <= 0:
        st.error(f"🚨 目標期日（{deadline_date}）を過ぎています！期日を再設定しましょう！")
    else:
        day_ratio = weekly_days / 7.0
        active_days_left = max(1, round(days_left * day_ratio))
        required_per_day = uncompleted_total / active_days_left
        
        # 直近7日間の完了数からリアルなペースを算出
        past_7_days = today - datetime.timedelta(days=7)
        recent_done = len(df_log[df_log["CompletedDate"] >= past_7_days])
        actual_per_day = recent_done / weekly_days
        
        col_sch1, col_sch2 = st.columns(2)
        with col_sch1:
            st.metric(label="🎯 期日までに必要なペース", value=f"1日 あたり {required_per_day:.1f} 問")
        with col_sch2:
            st.metric(
                label="🔥 あなたの現在のペース", 
                value=f"1日 あたり {actual_per_day:.1f} 問",
                delta=f"{actual_per_day - required_per_day:.1f} 問"
            )
        st.info(f"📅 目標期日: **{deadline_date}** (残り **{days_left}日** / 勉強予定日数: 残り約 **{active_days_left}日**)")

    st.write("---")
    st.write("### 📂 勉強する場所を選択")

    breadcrumb_cols = st.columns(5)
    with breadcrumb_cols[0]:
        if st.button("🏠 HOME", use_container_width=True):
            st.session_state.drill_sub = None
            st.session_state.drill_book = None
            st.session_state.drill_chap = None
            st.rerun()

    if st.session_state.drill_sub:
        with breadcrumb_cols[1]:
            st.write("＞")
        with breadcrumb_cols[2]:
            if st.button(f"📁 {st.session_state.drill_sub}", use_container_width=True):
                st.session_state.drill_book = None
                st.session_state.drill_chap = None
                st.rerun()

    if st.session_state.drill_book:
        with breadcrumb_cols[3]:
            st.write("＞")
        with breadcrumb_cols[4]:
            if st.button(f"📘 {st.session_state.drill_book}", use_container_width=True):
                st.session_state.drill_chap = None
                st.rerun()

    st.write("---")

    if df_tasks.empty:
        st.info("まずは「タスクの登録・管理」タブからクエストを登録してください！")
        
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

    # 🎯 章選択後のクエスト画面
    else:
        st.write(f"### ⚔️ クエストに挑戦！【{st.session_state.drill_chap}】")
        
        chap_tasks = df_tasks[
            (df_tasks["Subject"] == st.session_state.drill_sub) & 
            (df_tasks["Book"] == st.session_state.drill_book) & 
            (df_tasks["Chapter"] == st.session_state.drill_chap)
        ]
        
        # ID順（登録順 ＆ 間違えて最後尾に送られた順）に並び替える
        uncompleted = chap_tasks[chap_tasks["DoneFlag"] == 0].sort_values(by="ID")
        
        if uncompleted.empty:
            st.success("🎉 この章のすべてのクエストをクリアしました！素晴らしい！")
        else:
            num_tasks = st.number_input("挑戦する問題数を選択してください:", min_value=1, max_value=len(uncompleted), value=1)
            
            if st.button("🎲 クエストを発生させる (順番が早いものから優先選択)", use_container_width=True):
                # 間違えて後ろに回した問題は後に出てくるように、ID順の上位から選出
                candidates = uncompleted.head(num_tasks * 2).to_dict('records')
                random.shuffle(candidates)
                st.session_state.today_menu = candidates[:num_tasks]
            
            # 🕒 完了した時の勉強時間入力ポップアップ（インライン）
            if st.session_state.show_time_modal is not None:
                target_task = st.session_state.show_time_modal
                st.info(f"👉 **「{target_task['TaskName']}」クリアおめでとう！**")
                study_minutes = st.number_input("この問題に何分かかりましたか？", min_value=1, max_value=120, value=5)
                
                if st.button("時間入力を完了して保存する", use_container_width=True):
                    # 完了処理を書き込み
                    task_id = int(target_task["ID"])
                    df_tasks.loc[df_tasks["ID"] == task_id, "DoneFlag"] = 1
                    save_tasks(df_tasks)
                    
                    new_log = pd.DataFrame([{
                        "TaskID": task_id,
                        "CompletedDate": today,
                        "Subject": target_task["Subject"],
                        "Book": target_task["Book"],
                        "Chapter": target_task["Chapter"],
                        "TaskName": target_task["TaskName"],
                        "Minutes": int(study_minutes)
                    }])
                    df_log = pd.concat([df_log, new_log], ignore_index=True)
                    save_log(df_log)
                    
                    st.session_state.show_time_modal = None
                    st.session_state.today_menu = [t for t in st.session_state.today_menu if int(t["ID"]) != task_id]
                    st.success(f"👏 {target_task['TaskName']} を {study_minutes} 分でクリアしました！")
                    st.rerun()
                st.write("---")

            # クエストカード表示
            if st.session_state.today_menu:
                st.write("---")
                for task in st.session_state.today_menu:
                    task_id = int(task["ID"])
                    current_status = df_tasks.loc[df_tasks["ID"] == task_id, "DoneFlag"].values[0]
                    
                    if current_status == 1:
                        continue  # 完了済みのものはスキップ
                    
                    html_code = f"""
                    <div style="
                        background-color: #fffdf0; 
                        border: 2px solid #f1c40f; 
                        padding: 12px; 
                        border-radius: 8px; 
                        margin-bottom: 8px;
                    ">
                        <span style="font-weight: bold; font-size: 13px; color: #f1c40f;">⚔️ 挑戦中</span><br>
                        <span style="font-size: 16px; font-weight: bold; color: #1e1e1e;">📘 {task['Subject']} / {task['Book']}</span><br>
                        <span style="font-size: 13px; color: #555555;">📁 {task['Chapter']}</span><br>
                        <span style="font-size: 15px; font-weight: bold; color: #2c3e50;">🔥 クエスト: {task['TaskName']}</span>
                    </div>
                    """
                    st.markdown(html_code, unsafe_allow_html=True)
                    
                    # ⭕正解 と ❌間違い のボタン
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(f"⭕ 正解！(クリア) [ID: {task_id}]", key=f"ok_{task_id}", use_container_width=True):
                            st.session_state.show_time_modal = task
                            st.rerun()
                            
                    with btn_col2:
                        if st.button(f"❌ 間違えた(章の最後に移動) [ID: {task_id}]", key=f"ng_{task_id}", use_container_width=True):
                            # 「章の最後に移動」させるために、該当タスクのIDをその章の最大ID+1に書き換える
                            all_ids_in_chap = df_tasks[df_tasks["Chapter"] == task["Chapter"]]["ID"].tolist()
                            max_id = max(all_ids_in_chap) if all_ids_in_chap else task_id
                            new_task_id = max_id + 1
                            
                            # タスクのIDをアップデート（新しいIDで並べ直すと一番後ろに回る）
                            df_tasks.loc[df_tasks["ID"] == task_id, "ID"] = new_task_id
                            save_tasks(df_tasks)
                            
                            # 完了履歴のログも整合性を保つため修正
                            if not df_log.empty:
                                df_log.loc[df_log["TaskID"] == task_id, "TaskID"] = new_task_id
                                save_log(df_log)
                            
                            st.session_state.today_menu = [t for t in st.session_state.today_menu if int(t["ID"]) != task_id]
                            st.warning(f"🔄 {task['TaskName']} は章の最後に移動されました。もう一度挑戦しましょう！")
                            st.rerun()


# --- TAB 2: 📊 勉強の記録 ---
with tab_report:
    st.write("### 📊 勉強時間の分析レポート")
    
    if df_log.empty:
        st.info("勉強時間のログがまだありません。クエストをクリアすると自動で集計されます。")
    else:
        one_week_ago = today - datetime.timedelta(days=7)
        df_log_week = df_log[df_log["CompletedDate"] >= one_week_ago]
        
        total_minutes = df_log["Minutes"].sum()
        week_minutes = df_log_week["Minutes"].sum()
        
        st.write("#### ⏳ 合計勉強時間（数字）")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                label="🎒 全体の総勉強時間", 
                value=f"{total_minutes // 60}時間 {total_minutes % 60}分",
                help="アプリを始めてからの累計勉強時間です。"
            )
        with col_m2:
            st.metric(
                label="📅 直近1週間の勉強時間", 
                value=f"{week_minutes // 60}時間 {week_minutes % 60}分",
                help="過去7日間の勉強時間の合計です。"
            )
            
        st.write("---")
        st.write("#### 📈 教科ごとの勉強時間 (棒グラフ)")
        
        graph_period = st.radio("グラフの集計期間：", ["全体期間", "直近1週間"], horizontal=True)
        target_df = df_log_week if graph_period == "直近1週間" else df_log
        
        if target_df.empty:
            st.warning("選択した期間のログがありません。")
        else:
            subject_summary = target_df.groupby("Subject")["Minutes"].sum().reset_index()
            subject_summary.columns = ["教科", "勉強時間(分)"]
            
            st.bar_chart(
                data=subject_summary.set_index("教科"),
                y="勉強時間(分)",
                use_container_width=True
            )


# --- TAB 3: 📋 登録タスク一覧 (科目別に整理!) ---
with tab_list:
    st.write("### 📋 登録タスク一覧")
    
    if df_tasks.empty:
        st.info("現在登録されているタスクはありません。")
    else:
        st.write("登録されているタスクを科目別にまとめて表示しています。アコーディオンを開くと詳細を確認できます。")
        
        # 表示用の加工
        df_display = df_tasks.copy()
        df_display["状況"] = df_display["DoneFlag"].apply(lambda x: "✅ クリア済" if x == 1 else "⏳ 未完了")
        df_display = df_display.rename(columns={
            "ID": "タスクID",
            "Subject": "科目",
            "Book": "参考書",
            "Chapter": "章名",
            "TaskName": "タスク名"
        })
        
        # 登録されている科目のユニーク値を取得してループ処理
        unique_subjects = sorted(df_display["科目"].unique())
        
        for sub in unique_subjects:
            df_sub = df_display[df_display["科目"] == sub]
            total_count = len(df_sub)
            completed_count = len(df_sub[df_sub["状況"] == "✅ クリア済"])
            
            # 科目ごとのアコーディオンを設置（デフォルトで開く設定）
            with st.expander(f"📁 {sub} (クリア数: {completed_count}/{total_count} 問)", expanded=True):
                st.dataframe(
                    df_sub[["タスクID", "参考書", "章名", "タスク名", "状況"]].sort_values(by="タスクID"),
                    use_container_width=True,
                    hide_index=True
                )


# --- TAB 4: 管理・一括登録画面 ---
with tab_register:
    st.write("### 📝 タスクの追加・整理")
    
    # --- 1. スケジュール設定 ---
    st.write("#### 📅 目標期日の設定")
    with st.form("schedule_form"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            new_deadline = st.date_input("目標期日", deadline_date)
        with col_s2:
            new_weekly_days = st.slider("週に何日勉強するか", min_value=1, max_value=7, value=weekly_days)
            
        save_sch_btn = st.form_submit_button("スケジュールを設定する")
        if save_sch_btn:
            save_config(new_deadline, new_weekly_days)
            st.success("スケジュール設定を保存しました！")
            st.rerun()
            
    st.write("---")
    
    # --- 2. 一括登録フォーム ---
    st.write("#### ➕ クエストをまとめて登録")
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            reg_sub = st.text_input("1. 科目名 (例: 数学)", value="")
            reg_book = st.text_input("2. 参考書名 (例: 青チャート)", value="")
            reg_chap = st.text_input("3. 章名 (例: 第1章)", value="")
        with col2:
            reg_prefix = st.selectbox("4. 種類を選んでください", ["例題", "練習"])
            start_num = st.number_input("5. 開始番号", min_value=1, value=1)
            total_count = st.number_input("6. 生成する個数", min_value=1, max_value=100, value=5)
            
        submit_btn = st.form_submit_button("上記の設定で連続登録する")
        
        if submit_btn:
            if not reg_sub or not reg_book or not reg_chap:
                st.error("科目、参考書、章はすべて入力してください！")
            else:
                start_id = df_tasks["ID"].max() + 1 if not df_tasks.empty else 1
                new_rows = []
                
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

    # --- 3. 個別削除フォーム ---
    st.write("#### 🗑️ 不要なタスクを個別に消す (飛び番対策)")
    if df_tasks.empty:
        st.info("まだ登録されているタスクがありません。")
    else:
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            del_sub = st.selectbox("削除元の科目:", ["全て"] + list(df_tasks["Subject"].unique()))
            
        filtered_del = df_tasks if del_sub == "全て" else df_tasks[df_tasks["Subject"] == del_sub]
        
        with col_del2:
            del_book_opts = ["全て"] + list(filtered_del["Book"].unique())
            del_book = st.selectbox("削除元の参考書:", del_book_opts)
            
        if del_book != "全て":
            filtered_del = filtered_del[filtered_del["Book"] == del_book]
            
        selected_delete_task = st.selectbox(
            "削除するクエストを選択してください:",
            options=filtered_del["ID"].tolist(),
            format_func=lambda x: f"ID: {x} | {df_tasks.loc[df_tasks['ID'] == x, 'Subject'].values[0]} - {df_tasks.loc[df_tasks['ID'] == x, 'Book'].values[0]} - {df_tasks.loc[df_tasks['ID'] == x, 'TaskName'].values[0]}"
        )
        
        if st.button("🚨 選択したクエストを削除する", use_container_width=True):
            df_tasks = df_tasks[df_tasks["ID"] != selected_delete_task]
            save_tasks(df_tasks)
            st.session_state.today_menu = [t for t in st.session_state.today_menu if t["ID"] != selected_delete_task]
            st.success("指定したクエストを削除しました！")
            st.rerun()

    st.write("---")
    
    # --- 4. 完全初期化 ---
    st.write("#### 🔥 データの全削除 (初期化)")
    confirm_reset = st.checkbox("本当にすべての登録データを削除してやり直す場合はチェックを入れてください")
    if confirm_reset:
        if st.button("🚨 データベースを完全に初期化する", use_container_width=True):
            df_empty = pd.DataFrame(columns=["ID", "Subject", "Book", "Chapter", "TaskName", "DoneFlag"])
            save_tasks(df_empty)
            
            df_log_empty = pd.DataFrame(columns=["TaskID", "CompletedDate", "Subject", "Book", "Chapter", "TaskName", "Minutes"])
            save_log(df_log_empty)
            
            st.session_state.drill_sub = None
            st.session_state.drill_book = None
            st.session_state.drill_chap = None
            st.session_state.t
