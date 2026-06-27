from src.utils.file_manager import (
    build_json_path,
    save_json,
)

sample_data = [
    {
        "message_id": 1,
        "text": "Paracetamol",
        "price": "250 ETB",
    }
]

file_path = build_json_path(
    channel_name="CheMed",
    date="2025-06-27"
)

save_json(sample_data, file_path)

print(f"Saved successfully to:\n{file_path}")