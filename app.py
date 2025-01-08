import streamlit as st
import pandas as pd
import datetime
import psycopg2

st.image("image_header.png")

# PostgreSQL connection setup
def get_db_connection():
    connection = psycopg2.connect(
        host="34.55.180.159",
        database="temp",
        user="khushal",
        password="postgres108"
    )
    return connection

# Initialize the form data dictionary
form_data = {}

# Collect the number of guests
num_guests = st.number_input("Number of Guests", min_value=1, max_value=10, step=1)

# Dynamic input fields for guest names, ages, contact numbers, and image uploads
guests = []
contact_present = False  # Flag to check if at least one contact number is present
aadhaar_valid = True  # Flag for Aadhaar validation
all_images_uploaded = True  # Flag to check if all guests uploaded an image

for i in range(num_guests):
    guest_name = st.text_input(f"Name of Guest {i+1}")
    guest_age = st.number_input(f"Age of Guest {i+1} (2 digits only)", min_value=10, max_value=99, step=1)

    # Aadhaar Number Field
    guest_aadhaar = st.text_input(f"Aadhaar Number of Guest {i+1} (12 digits)")
    if not guest_aadhaar or not guest_aadhaar.isdigit() or len(guest_aadhaar) != 12:
        aadhaar_valid = False
        st.warning(f"Aadhaar number for Guest {i+1} must be exactly 12 digits and cannot be empty.")

    guest_contact = st.text_input(f"Contact Number of Guest {i+1} (10 digits, optional)")
    if guest_contact:
        contact_present = True
        if len(guest_contact) != 10:
            st.warning(f"Contact number for Guest {i+1} must be exactly 10 digits.")
    
    # Image Upload (Compulsory)
    guest_image = st.file_uploader(f"Upload Image for Guest {i+1} (Max 1 MB)", type=["png", "jpg", "jpeg"])
    
    # Check if image is uploaded
    if not guest_image:
        all_images_uploaded = False

    # Read the image as binary
    image_binary = guest_image.read() if guest_image else None

    guests.append({
        "name": guest_name,
        "age": guest_age,
        "aadhaar": guest_aadhaar,
        "contact": guest_contact,
        "image_binary": image_binary
    })

form_data["guests"] = guests

# Ensure at least one contact number is provided
if not contact_present:
    st.error("Please provide at least one contact number.")

# Ensure all guests uploaded images
if not all_images_uploaded:
    st.error("Please upload an addhar copy for every guest!")

# Mode of travel for arrival
arrival_travel_mode = st.selectbox("Mode of travel for arrival", ["air", "road", "train", "self"])
form_data["arrival_travel_mode"] = arrival_travel_mode

# Conditional fields based on "Self" option
if arrival_travel_mode != "self":
    # Arrival location
    arrival_location = st.text_input("Arrival Location", placeholder="Enter the location of arrival")
    form_data["arrival_location"] = arrival_location

    # Date and time of arrival
    arrival_date = st.date_input("Date of Arrival")
    arrival_time = st.time_input("Time of Arrival", value=datetime.time(22, 0))
    form_data["arrival_date"] = arrival_date
    form_data["arrival_time"] = arrival_time

    # Mode of travel for departure
    departure_travel_mode = st.selectbox("Mode of travel for departure", ["air", "road", "train"])
    form_data["departure_travel_mode"] = departure_travel_mode

    # Date and time of departure
    departure_date = st.date_input("Date of Departure")
    departure_time = st.time_input("Time of Departure", value=datetime.time(22, 0))
    form_data["departure_date"] = departure_date
    form_data["departure_time"] = departure_time
else:
    form_data["arrival_location"] = None
    form_data["arrival_date"] = None
    form_data["arrival_time"] = None
    form_data["departure_travel_mode"] = None
    form_data["departure_date"] = None
    form_data["departure_time"] = None

# Checkout date with restriction and default time logic
checkout_date = st.date_input("Checkout Date", value=datetime.date(2025, 1, 26))

if checkout_date not in [datetime.date(2025, 1, 26), datetime.date(2025, 1, 27)]:
    st.error("Please select a valid checkout date (26th or 27th January 2025).")

# Default checkout time for 27th January 2025
if checkout_date == datetime.date(2025, 1, 27):
    checkout_time = datetime.time(10, 0)
    st.markdown(
        "Default Checkout time :"
        "<span style='font-weight: bold; border-radius: 4px;'>10:00 AM</span> "
        "on 27th January 2025.",
        unsafe_allow_html=True,
    )
else:
    checkout_time = st.time_input("Checkout Time", value=datetime.time(10, 0))

form_data["checkout_date"] = checkout_date
form_data["checkout_time"] = checkout_time

# Button to save the form data to PostgreSQL
if st.button("Submit"):
    # Validate data before submission
    if not contact_present:
        st.error("At least one contact number must be provided.")
    elif checkout_date not in [datetime.date(2025, 1, 26), datetime.date(2025, 1, 27)]:
        st.error("Invalid checkout date. Please select 26th or 27th January 2025.")
    elif arrival_travel_mode != "self" and not form_data["arrival_location"]:
        st.error("Please provide the arrival location.")
    elif not aadhaar_valid:
        st.error("Please ensure all guests have valid 12-digit Aadhaar numbers.")
    elif not all_images_uploaded:
        st.error("Please upload an image for every guest before submitting.")
    else:
        # Convert the form data to a DataFrame
        guests_data = pd.DataFrame(form_data["guests"])

        # Add the other fields to the dataframe
        guests_data['arrival_date'] = form_data["arrival_date"]
        guests_data['arrival_time'] = form_data["arrival_time"]
        guests_data['checkout_date'] = form_data["checkout_date"]
        guests_data['checkout_time'] = form_data["checkout_time"]
        guests_data['departure_date'] = form_data["departure_date"]
        guests_data['departure_time'] = form_data["departure_time"]
        guests_data['arrival_travel_mode'] = form_data["arrival_travel_mode"]
        guests_data['arrival_location'] = form_data["arrival_location"]
        guests_data['departure_travel_mode'] = form_data["departure_travel_mode"]

        # Save the data to PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()

        for index, row in guests_data.iterrows():
            cursor.execute("""
                INSERT INTO guest_data (name, age, aadhaar, contact, arrival_date, arrival_time, arrival_location, 
                                        checkout_date, checkout_time, departure_date, departure_time, 
                                        arrival_travel_mode, departure_travel_mode, image_binary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['name'], row['age'], row['aadhaar'], row['contact'], row['arrival_date'], row['arrival_time'],
                row['arrival_location'], row['checkout_date'], row['checkout_time'], row['departure_date'],
                row['departure_time'], row['arrival_travel_mode'], row['departure_travel_mode'], psycopg2.Binary(row['image_binary'])
            ))

        conn.commit()
        cursor.close()
        conn.close()

        st.success("Data saved successfully. Your Presence is awaited!")
