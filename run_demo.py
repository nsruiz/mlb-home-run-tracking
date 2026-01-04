from home_run_pipeline.json_io import load_json, write_json
from home_run_pipeline.collect_home_run_info import process_home_run_data

INPUT = "data/input/sample_home_runs.json"
OUTPUT = "data/output/blender_payload.json"

def main():
    plays = load_json(INPUT)
    selected = process_home_run_data(plays)
    write_json(selected, OUTPUT)

    # Blender Python script is run separately in Blender to update world

if __name__ == "__main__":
    main()