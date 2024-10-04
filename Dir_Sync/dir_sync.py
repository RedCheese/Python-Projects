import os
import shutil
import filecmp
import argparse
from tqdm import tqdm
from datetime import datetime
import schedule 
import time

log_dir = "log"
interval = 1

# Function to write the log
def write_log(text):
    log_path = os.path.join(log_dir, "log.log")
    # Check if the log file exists and creates if doesnt
    if not os.path.exists(log_path):
        os.makedirs(log_dir)
        f = open(log_path, 'w')
    #Write the changes in the log
    with open(log_path, 'a') as f:
        f.write("{}\n".format(text))
    return

# Function to check if the source and destination directories exist
def check_directories(source_dir, replica_dir):
    # Check if the source directory exists
    if not os.path.exists(source_dir):
        text_false = f"\nSource directory '{source_dir}' does not exist."
        print(f"\nSource directory '{source_dir}' does not exist.")
        write_log(text_false)
        return False
    # Create the destination directory if it does not exist
    if not os.path.exists(replica_dir):
        os.makedirs(replica_dir)
        text_true = f"\nDestination directory '{replica_dir}' created."
        print(f"\nDestination directory '{replica_dir}' created.")
        write_log(text_true)
    return True

# Function to synchronize files between two directories
def sync_directories(source_dir, replica_dir, delete=False):
    sync_time = datetime.now().strftime("%H_%M_%d_%m_%Y")
    write_log(f"***** {sync_time} *****")
    # Get a list of all files and directories in the source directory
    files_to_sync = []
    for root, dirs, files in os.walk(source_dir):
        for directory in dirs:
            files_to_sync.append(os.path.join(root, directory))
        for file in files:
            files_to_sync.append(os.path.join(root, file))

    # Iterate over each file in the source directory with a progress bar
    with tqdm(total=len(files_to_sync), desc="Syncing files", unit="file") as pbar:
        # Iterate over each file in the source directory
        for source_path in files_to_sync:
            # Get the corresponding path in the replica directory
            replica_path = os.path.join(replica_dir, os.path.relpath(source_path, source_dir))

            # Check if path is a directory and create it in the replica directory if it does not exist
            if os.path.isdir(source_path):
                if not os.path.exists(replica_path):
                    os.makedirs(replica_path)
            # Copy all files from the source directory to the replica directory
            else:
                # Check if the file exists in the replica directory and if it is different from the source file
                if not os.path.exists(replica_path) or not filecmp.cmp(source_path, replica_path, shallow=False):
                    # Set the description of the progress bar and print the file being copied
                    pbar.set_description(f"Processing '{source_path}'")
                    print(f"\nCopying {source_path} to {replica_path}")

                    # Copy the file from the source directory to the replica directory
                    shutil.copy2(source_path, replica_path)
                    write_log(f"{source_path} copied to {replica_path}")

            # Update the progress bar
            pbar.update(1)

    # Clean up files in the destination directory that are not in the source directory, if delete flag is set
    if delete:
        # Get a list of all files in the destination directory
        files_to_delete = []
        for root, dirs, files in os.walk(replica_dir):
            for directory in dirs:
                files_to_delete.append(os.path.join(root, directory))
            for file in files:
                files_to_delete.append(os.path.join(root, file))

        # Iterate over each file in the destination directory with a progress bar
        with tqdm(total=len(files_to_delete), desc="Deleting files", unit="file") as pbar:
            # Iterate over each file in the destination directory
            for replica_path in files_to_delete:
                # Check if the file exists in the source directory
                source_path = os.path.join(replica_dir, os.path.relpath(replica_path, replica_dir))
                if not os.path.exists(source_path):
                    # Set the description of the progress bar
                    pbar.set_description(f"Processing '{replica_path}'")
                    print(f"\nDeleting {replica_path}")

                    # Check if the path is a directory and remove it
                    if os.path.isdir(replica_path):
                        shutil.rmtree(replica_path)
                    else:
                        # Remove the file from the destination directory
                        os.remove(replica_path)
                    write_log(f"{replica_path} deleted")

                # Update the progress bar
                pbar.update(1)

    print("\nSynchronization complete.")
    write_log("***** ***** ***** ***** *****")

    # Main function to parse command line arguments and synchronize directories
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Synchronize files between two directories.")
    parser.add_argument("source_directory", help="The source directory to synchronize from.")
    parser.add_argument("destination_directory", help="The destination directory to synchronize to.")
    parser.add_argument("sync_interval", default=1, type=int, help="Time in minutes for schedule.")
    parser.add_argument("log_directory", default="log", help="Location for the log file.")
    parser.add_argument("-d", "--delete", action="store_true",
                        help="Delete files in destination that are not in source.")
    args = parser.parse_args()

    # If the delete flag is set, print a warning message
    if args.delete:
        print("\nExtraneous files in the destination will be deleted.")

    # Check the source and destination directories
    if not check_directories(args.source_directory, args.destination_directory):
        exit(1)

    if args.log_directory:
        log_dir = args.log_directory

    if args.sync_interval:
        interval = args.sync_interval


    # Synchronize the directories
    sync_directories(args.source_directory, args.destination_directory, args.delete)
    # Schedule that will call the function every N minutes
    schedule.every(interval).minutes.do(lambda: sync_directories(args.source_directory, args.destination_directory, args.delete)) 
    
    # Schedule loop
    while True: 
        schedule.run_pending()
        time.sleep(1)