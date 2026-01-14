import csv
import sys


def calculate_average_lag(file_path, target_topic):
    lags = []

    try:
        with open(file_path, "r", newline="") as f:
            # Attempt to detect the format
            try:
                sample = f.read(2048)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                # Default to basic CSV if sniffing fails
                dialect = "excel"

            # skipinitialspace=True helps with some whitespace handling
            reader = csv.DictReader(f, dialect=dialect, skipinitialspace=True)

            # Clean headers (strip whitespace from keys just in case)
            if reader.fieldnames:
                reader.fieldnames = [h.strip() for h in reader.fieldnames]

            if (
                not reader.fieldnames
                or "TOPIC" not in reader.fieldnames
                or "LAG" not in reader.fieldnames
            ):
                # If Sniffer failed us on the whitespace format, we might be here.
                # But for the CSV file (results.csv), this should work perfectly.
                print(
                    f"Warning: Expected columns 'TOPIC' and 'LAG' not found. Found: {reader.fieldnames}"
                )
                # We continue to try and see if it works anyway or just return?
                # Let's return to avoid confusing errors.
                return

            for row in reader:
                # Get values safely
                topic = row.get("TOPIC")
                lag_str = row.get("LAG")

                if topic and lag_str and topic.strip() == target_topic:
                    try:
                        lag = int(lag_str)
                        lags.append(lag)
                    except ValueError:
                        pass

        if not lags:
            print(f"No partitions found for topic: {target_topic}")
            return

        avg_lag = sum(lags) / len(lags)
        print(f"Topic: {target_topic}")
        print(f"Partitions: {len(lags)}")
        print(f"Total Lag: {sum(lags)}")
        print(f"Average Lag: {avg_lag:.2f}")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 calculate_avg_lag.py <csv_file> <topic_name>")
        sys.exit(1)

    csv_file = sys.argv[1]
    topic_name = sys.argv[2]

    calculate_average_lag(csv_file, topic_name)
