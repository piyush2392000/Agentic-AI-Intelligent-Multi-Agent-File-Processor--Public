# config/memory_config.py

# Define the keys that will be used for metadata in the vector store.
# This allows for easy changes to the metadata schema in the future without
# having to change the tool's implementation logic.
METADATA_KEYS = {
    "FILE": "file_path",
    "AGENT": "agent_id"
}