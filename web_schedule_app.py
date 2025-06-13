import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF
import json
from openpyxl import Workbook
from collections import defaultdict

# === Streamlit Setup ===
st.set_page_config(page_title="Schedule Planner", layout="centered")
st.title("🗓️ Schedule Planner Web App")
st.caption("⏱️ Time Format: Use 12-hour (e.g., 9:00AM or 4:30PM) or 24-hour (e.g., 13:00)")

# === Helper Functions ===

def parse_time(time_str):
    time_str = time_str.strip().lower().replace(" ", "")
    for fmt in ["%I%p", "%I:%M%p", "%H:%M"]:
        try:
            return datetime.strptime(time_str, fmt)
        except:
            pass
        try:
            return datetime.strptime(time_str, "%I:%M%p")
        except:
            pass
        try:
            return datetime.strptime(time_str, "%H:%M")
        except:
            pass
        return None

def get_minutes(start, end):
    delta = end - start
    return max(0, int(delta.total_seconds() // 60))

def get_week_number(start_date, current_date):
    start_sunday = start_date - timedelta(days=start_date.weekday() + 1 if start_date.weekday() != 6 else 0)
    current_sunday = current_date - timedelta(days=current_date.weekday() + 1 if current_date.weekday() != 6 else 0)
    return ((current_sunday - start_sunday).days // 7) + 1

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Work Schedule Report", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.ln(5)

    grouped_weeks = defaultdict(list)
    week_totals = defaultdict(int)
    grand_total = 0

    for row in data:
        week = row['week']
        grouped_weeks[week].append(row)
        week_totals[week] += row['duration']
        grand_total += row['duration']

    for week in sorted(grouped_weeks):
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Week {week}", ln=True)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(30, 10, "Day", 1)
        pdf.cell(30, 10, "Date", 1)
        pdf.cell(40, 10, "Time In", 1)
        pdf.cell(40, 10, "Time Out", 1)
        pdf.cell(50, 10, "Duration", 1)
        pdf.ln()
        pdf.set_font("Arial", "", 11)

        for row in grouped_weeks[week]:
            duration_str = f"{row['duration'] // 60} hrs {row['duration'] % 60} min"
            pdf.cell(30, 10, row['day'], 1)
            pdf.cell(30, 10, row['date'], 1)
            pdf.cell(40, 10, row['time_in'], 1)
            pdf.cell(40, 10, row['time_out'], 1)
            pdf.cell(50, 10, duration_str, 1)
            pdf.ln()

        week_total = week_totals[week_num]
        total_str = f"Week {week} Total: {week_totals[week] // 60} hrs {week_totals[week] % 60} min"
        pdf.cell(0, 10, total_str, ln=True)
        pdf.ln(3)

    pdf.set_font("Arial", "B", 12)
    final_str = f"FINAL TOTAL: {grand_total // 60} hrs {grand_total % 60} min"
    pdf.cell(0, 10, final_str, ln=True, align='C')
    return BytesIO(pdf.output(dest="S").encode('latin1'))

# def generate_excel(data):
#     wb = Workbook()
#     ws = wb.active
#     ws.append(["Date", "Time In", "Time Out", "Minutes Worked"])
#     for row in data:
#         ws.append([row["date"], row["time_in"], row["time_out"], row["duration"]])
#     buffer = BytesIO()
#     wb.save(buffer)
#     buffer.seek(0)
#     return buffer

# def generate_csv(data):
#     buffer = BytesIO()
#     buffer.write("Date,Time In,Time Out,Minutes Worked\n".encode('utf-8'))
#     for row in data:
#         line = f"{row['date']},{row['time_in']},{row['time_out']},{row['duration']}\n"
#         buffer.write(line.encode('utf-8'))
#     buffer.seek(0)
#     return buffer

# def generate_json(data):
#     buffer = BytesIO()
#     buffer.write(json.dumps(data, indent=2).encode('utf-8'))
#     buffer.seek(0)
#     return buffer

# === UI Form Logic ===

schedule_data = []
date_range = st.date_input("Select Date Range", [datetime.today(), datetime.today() + timedelta(days=5)])
use_typical = st.checkbox("Use Typical Hours for Weekdays?")
include_weekends = st.checkbox("Include weekends in schedule?")

if use_typical:
    col1, col2 = st.columns(2)
    with col1:
        default_in = st.text_input("Typical Time In", "9:00AM")
    with col2:
        default_out = st.text_input("Typical Time Out", "5:00PM")

if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    current = start_date

    while current <= end_date:
        st.markdown(f"### {current.strftime('%A, %m/%d/%Y')}")
        entry_index = 1
        add_another = True

        while add_another:
            col1, col2 = st.columns(2)

            if use_typical and current.weekday() < 5 and entry_index == 1:
                time_in_str = default_in
                time_out_str = default_out
                with col1:
                    st.text_input("Auto-filled Time In", value=default_in, key=f"in_{current}_{entry_index}", disabled=True)
                with col2:
                    st.text_input("Auto-filled Time Out", value=default_out, key=f"out_{current}_{entry_index}", disabled=True)
            else:
                with col1:
                    time_in_str = st.text_input(f"Time In ({entry_index}) - {current.strftime('%m/%d/%Y')}", key=f"in_{current}_{entry_index}")
                with col2:
                    time_out_str = st.text_input(f"Time Out ({entry_index}) - {current.strftime('%m/%d/%Y')}", key=f"out_{current}_{entry_index}")

            if time_in_str and time_out_str:
                t_in = parse_time(time_in_str)
                t_out = parse_time(time_out_str)
                if t_in and t_out and t_out > t_in:
                    duration = get_minutes(t_in, t_out)
                    week_number = get_week_number(start_date, current)
                    schedule_data.append({
                        "week": week_number,
                        "day": current.strftime("%A"),
                        "date": current.strftime("%m/%d/%Y"),
                        "time_in": t_in.strftime("%I:%M %p"),
                        "time_out": t_out.strftime("%I:%M %p"),
                        "duration": duration
                    })
                    add_another = st.checkbox(
                        f"➕ Add another entry for {current.strftime('%m/%d/%Y')}?", 
                        key=f"add_more_{current}_{entry_index}"
                    )
                else:
                    st.warning(f"Invalid or reversed times for entry {entry_index}.")
                    add_another = False
            else:
                add_another = False

            entry_index += 1
        current += timedelta(days=1)

# === Output Section ===

if schedule_data:
    st.success("✅ Schedule Data Collected!")
    
    week_groups = defaultdict(list)
    week_totals = defaultdict(int)
    grand_total_minutes = 0

    for row in schedule_data:
        week_groups[row['week']].append(row)
        week_totals[row['week']] += row['duration']
        grand_total_minutes += row['duration']

    for week in sorted(week_groups):
        st.markdown(f"### 🗓️ Week {week}")
        st.table([
            [r['day'], r['date'], r['time_in'], r['time_out'], f"{r['duration']//60} hrs {r['duration']%60} min"]
            for r in week_groups[week]
        ])
        st.info(f"Week {week} Total: {week_totals[week] // 60} hrs {week_totals[week] % 60} min")

    st.success(f"🧾 Final Total: {grand_total_minutes // 60} hrs {grand_total_minutes % 60} min 🕒")

    st.download_button("📄 Download PDF", generate_pdf(schedule_data), file_name="schedule.pdf")
    st.download_button("📊 Download Excel", generate_excel(schedule_data), file_name="schedule.xlsx")
    st.download_button("📑 Download CSV", generate_csv(schedule_data), file_name="schedule.csv")
    st.download_button("🔢 Download JSON", generate_json(schedule_data), file_name="schedule.json")

st.write("App started successfully ✅")
