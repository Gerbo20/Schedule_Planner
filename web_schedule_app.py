import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF
import csv
import json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

st.set_page_config(page_title="Schedule Planner", layout="centered")
st.title("🗓️ Schedule Planner Web App")
st.write("App started successfully")

# === Helper Functions ===

def parse_time(time_str):
    time_str = time_str.strip().lower().replace(" ", "")
    try:
        return datetime.strptime(time_str, "%I%p")         # e.g., "12pm"
    except:
        pass
    try:
        return datetime.strptime(time_str, "%I:%M%p")      # e.g., "12:00pm"
    except:
        pass
    try:
        return datetime.strptime(time_str, "%H:%M")        # e.g., "12:00" (24hr)
    except:
        pass
    return None

def get_minutes(start, end):
    delta = end - start
    return max(0, int(delta.total_seconds() // 60))

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Work Schedule Report", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.ln(5)

    for row in data:
        line = f"{row['date']} - {row['time_in']} to {row['time_out']} = {row['duration']} minutes"
        pdf.cell(0, 10, line, ln=True)

    # Proper in-memory PDF output
    pdf_bytes = pdf.output(dest='S').encode('latin1')  # <- Important fix
    return BytesIO(pdf_bytes)

def generate_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Schedule"
    ws.append(["Date", "Time In", "Time Out", "Minutes Worked"])

    for row in data:
        ws.append([row["date"], row["time_in"], row["time_out"], row["duration"]])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def generate_csv(data):
    buffer = BytesIO()
    buffer.write("Date,Time In,Time Out,Minutes Worked\n".encode('utf-8'))
    for row in data:
        line = f"{row['date']},{row['time_in']},{row['time_out']},{row['duration']}\n"
        buffer.write(line.encode('utf-8'))
    buffer.seek(0)
    return buffer

def generate_json(data):
    buffer = BytesIO()
    buffer.write(json.dumps(data, indent=2).encode('utf-8'))
    buffer.seek(0)
    return buffer

st.subheader("Enter Your Work Schedule")
st.caption("⏱️ Time Format: Use 12-hour (e.g., 9:00AM or 4:30PM) or 24-hour (e.g., 13:00)")

# === UI Inputs ===

schedule_data = []
date_range = st.date_input("Select Date Range", [datetime.today(), datetime.today() + timedelta(days=5)])

# ✅ Define checkboxes before using them
use_typical = st.checkbox("✅ Use Typical Hours for Weekdays?")
include_weekends = st.checkbox("Include weekends in schedule?")

if use_typical:
    default_in = st.text_input("Typical Time In", "9:00AM")
    default_out = st.text_input("Typical Time Out", "5:00PM")

if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    current = start_date
    
    while current <= end_date:
        day_name = current.strftime('%A')

        # ✅ This now works correctly
        if not include_weekends and day_name in ["Saturday", "Sunday"]:
            current += timedelta(days=1)
            continue

        st.markdown(f"**{day_name}, {current.strftime('%m/%d/%Y')}**")
        
        if use_typical and current.weekday() < 5:  # Weekdays only
            time_in = default_in
            time_out = default_out
            st.markdown(f"Auto-filled: {time_in} to {time_out}")
        else:
            time_in = st.text_input(f"Time In ({current})", key=f"in_{current}")
            time_out = st.text_input(f"Time Out ({current})", key=f"out_{current}")


        if time_in and time_out:
            t_in = parse_time(time_in)
            t_out = parse_time(time_out)
            if t_in and t_out and t_out > t_in:
                duration = get_minutes(t_in, t_out)
                schedule_data.append({
                    "date": current.strftime("%m/%d/%Y"),
                    "time_in": t_in.strftime("%I:%M %p"),
                    "time_out": t_out.strftime("%I:%M %p"),
                    "duration": duration
                })
            else:
                st.warning(f"Invalid times on {current}. Must be valid and Time Out after Time In.")
        current += timedelta(days=1)

# === Output Section ===

if schedule_data:
    st.success("✅ Schedule Data Collected!")

    total_minutes = sum(row['duration'] for row in schedule_data)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    st.info(f"🕒 Total Time Worked: {hours} hrs {minutes} min")

    pdf_data = generate_pdf(schedule_data)
    excel_data = generate_excel(schedule_data)

    csv_data = generate_csv(schedule_data)
    json_data = generate_json(schedule_data)

    st.download_button("Download PDF", pdf_data, file_name="schedule.pdf")
    st.download_button("Download Excel", excel_data, file_name="schedule.xlsx")

    st.download_button("Download CSV", csv_data, file_name="schedule.csv")
    st.download_button("Download JSON", json_data, file_name="schedule.json")

