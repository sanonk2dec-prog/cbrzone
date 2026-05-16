import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("🎓 Student Record Management (SQLite3 CRUD)")

# --- DATABASE SETUP ---
DB_FILE = "students.db"


def init_db():
    """Database aur Table banane ke liye function"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            grade TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_all_students():
    """Database se saara data padhne (Read) ke liye"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT id AS 'Student ID', name AS 'Full Name', age AS 'Age', grade AS 'Grade' FROM students", conn)
    conn.close()
    return df


# Database ko initialize karein
init_db()

# --- SIDEBAR: ADD NEW RECORD (CREATE) ---
st.sidebar.header("📝 Add New Student")

with st.sidebar.form(key="add_student_form", clear_on_submit=True):
    name = st.text_input("Full Name", placeholder="e.g. Rahul Sharma")
    age = st.number_input("Age", min_value=5, max_value=100, value=18)
    grade = st.selectbox("Grade", ["A", "B", "C", "D", "F"])

    submit_btn = st.form_submit_button("Add to Database")

# Handle insertion (Create)
if submit_btn:
    if name.strip() == "":
        st.sidebar.error("Name khali nahi ho sakta!")
    else:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, age, grade) VALUES (?, ?, ?)", (name.strip(), int(age), grade))
        conn.commit()
        conn.close()
        st.toast(f"{name} ko database mein save kar diya gaya hai!", icon="✅")
        st.rerun()

# --- MAIN SCREEN: DIRECTORY & LIVE EDITING (READ, UPDATE, DELETE) ---
st.subheader("📋 Student Directory")

# Current data read karein
df_current = get_all_students()

if df_current.empty:
    st.info("Database khali hai. Naya student add karne ke liye sidebar ka use karein!")
else:
    # Summary Dashboard Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Registered", len(df_current))
    col2.metric("Average Class Age", f"{round(df_current['Age'].astype(float).mean(), 1)}")

    st.markdown("### Interactive Data Table")
    st.caption(
        "💡 **Tip:** Kisi bhi cell par double click karke edit karein (Update). Row select karke keyboard ka `Delete` button dabayein (Delete).")

    # Display editable table
    edited_df = st.data_editor(
        df_current,
        num_rows="dynamic",  # Rows ko delete karne ki permission deta hai
        use_container_width=True,
        column_config={
            "Student ID": st.column_config.TextColumn("Student ID", disabled=True),  # ID ko lock kiya
            "Full Name": st.column_config.TextColumn("Full Name", required=True),
            "Age": st.column_config.NumberColumn("Age", min_value=5, max_value=100, step=1),
            "Grade": st.column_config.SelectboxColumn("Grade", options=["A", "B", "C", "D", "F"]),
        },
        key="db_directory_editor"
    )

    # --- TRACK AND SYNC CHANGES (UPDATE & DELETE) ---
    # Agar user ne table mein koi badlav kiya hai
    if not edited_df.equals(df_current):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 1. Check for Deletions (Jo IDs pehle thin par ab nahi hain)
        current_ids = set(df_current["Student ID"].tolist())
        edited_ids = set(edited_df["Student ID"].dropna().astype(int).tolist())
        deleted_ids = current_ids - edited_ids

        for d_id in deleted_ids:
            cursor.execute("DELETE FROM students WHERE id = ?", (int(d_id),))

        # 2. Check for Updates (Bache hue records ko check karein)
        for index, row in edited_df.iterrows():
            # Agar naye rows add kiye hain bina form ke toh skip karein (Form prefered hai)
            if pd.isna(row["Student ID"]):
                continue

            s_id = int(row["Student ID"])
            new_name = row["Full Name"]
            new_age = int(row["Age"])
            new_grade = row["Grade"]

            # Database mein update query chalayein
            cursor.execute("""
                UPDATE students 
                SET name = ?, age = ?, grade = ? 
                WHERE id = ?
            """, (new_name, new_age, new_grade, s_id))

        conn.commit()
        conn.close()
        st.rerun()

    # Clear Everything Control
    st.write("---")
    if st.button("⚠️ Clear Entire Database", type="primary"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students")  # Saara data delete karne ke liye
        conn.commit()
        conn.close()
        st.toast("Saara data database se delete kar diya gaya!", icon="🗑️")
        st.rerun()