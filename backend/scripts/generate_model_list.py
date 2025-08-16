import json
from pathlib import Path
import sys

try:
    import ijson
except ImportError:
    print("ijson is not installed. Please run: pip install ijson")
    sys.exit(1)

# Add project root to sys.path to allow for relative imports
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.utils.logger import get_logger

log = get_logger("script.generate_model_list")

# Define paths relative to the script's location
DATA_DIR = project_root / "data" / "model_result" / "DemandForecast_Product_Customer"
SOURCE_FILE = DATA_DIR / "all_model_results.json"
OUTPUT_FILE = DATA_DIR / "models_list.json"

def generate_model_list():
    """
    Reads the large all_model_results.json file, extracts unique model names,
    and saves them to a smaller models_list.json file.
    """
    if not SOURCE_FILE.exists():
        log.error(f"Source file not found: {SOURCE_FILE}")
        return

    log.info(f"Reading source file: {SOURCE_FILE}")
    
    models = set()
    
    try:
        with SOURCE_FILE.open('rb') as f:
            # Use ijson to stream-parse the file, iterating through items in the root array
            records = ijson.items(f, 'item')
            for record in records:
                model_name = record.get("Model") or record.get("model")
                if model_name:
                    models.add(model_name)
    except ijson.JSONError as e:
        log.error(f"Error parsing JSON stream from {SOURCE_FILE}: {e}")
        log.error("This might be due to a severe syntax error in the JSON file.")
        return

    except json.JSONDecodeError as e:
        log.error(f"Error decoding JSON from {SOURCE_FILE}: {e}")
        return
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")
        return

    sorted_models = sorted(list(models))
    
    try:
        with OUTPUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(sorted_models, f, indent=2, ensure_ascii=False)
        log.info(f"Successfully generated model list with {len(sorted_models)} models.")
        log.info(f"Output file: {OUTPUT_FILE}")
    except Exception as e:
        log.error(f"Error writing to output file {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    generate_model_list()
