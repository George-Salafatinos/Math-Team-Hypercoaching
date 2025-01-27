# test_data_manager.py

from src.data_manager import create_meet, get_meet

# Create a new meet
meet_id = create_meet("First Test Meet")
print("Created Meet ID:", meet_id)

# Retrieve the same meet
meet_obj = get_meet(meet_id)
print("Retrieved Meet:", meet_obj)
