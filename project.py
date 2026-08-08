import os
from database import (
    init_db, add_complaint, get_all_complaints, get_complaint_by_id,
    update_status, get_category_counts, get_status_counts, filter_complaints,
    get_resolution_times
)
import statistics
from classifier import classify_complaint


def get_complaint():
    description = input("Describe the problem: ").strip()
    while description == "":
        print("Description cannot be empty. Please try again.")
        description = input("Describe the problem: ").strip()

    location = input("Enter the location: ").strip()
    while location == "":
        print("Location cannot be empty. Please try again.")
        location = input("Enter the location: ").strip()

    image_path = input("Path to a photo (press Enter to skip): ").strip()
    if image_path == "":
        image_path = None
    elif not os.path.exists(image_path):
        print("That file wasn't found — continuing without a photo.")
        image_path = None

    return description, location, image_path


def submit_complaint():
    description, location, image_path = get_complaint()
    category = classify_complaint(description)
    complaint_id = add_complaint(description, location, image_path, category)
    print(f"\n✅ Complaint #{complaint_id} received!")
    print(f"AI Category: {category}\n")


def view_complaints():
    rows = get_all_complaints()
    if not rows:
        print("\nNo complaints submitted yet.\n")
        return
    print(f"\n--- {len(rows)} complaint(s) ---")
    for row in rows:
        print(f"#{row['complaint_id']} | {row['date']} | {row['status']} | {row['category']} | {row['location']} | {row['description']}")
    print()


def view_single_complaint():
    complaint_id = input("Enter complaint ID: ").strip()
    if not complaint_id.isdigit():
        print("Please enter a valid number.\n")
        return
    row = get_complaint_by_id(int(complaint_id))
    if row is None:
        print("No complaint found with that ID.\n")
        return
    print(f"\n#{row['complaint_id']} | {row['date']} | {row['status']}")
    print(f"Category: {row['category']}")
    print(f"Location: {row['location']}")
    print(f"Description: {row['description']}")
    print(f"Photo: {row['image_path'] if row['image_path'] else 'None'}\n")


def change_status():
    complaint_id = input("Enter complaint ID: ").strip()
    if not complaint_id.isdigit():
        print("Please enter a valid number.\n")
        return
    print("Valid statuses: Open, Assigned, In Progress, Resolved")
    new_status = input("New status: ").strip()
    if new_status not in ["Open", "Assigned", "In Progress", "Resolved"]:
        print("Not a valid status.\n")
        return
    success = update_status(int(complaint_id), new_status)
    if success:
        print(f"✅ Complaint #{complaint_id} updated to '{new_status}'.\n")
    else:
        print("No complaint found with that ID.\n")

def show_statistics():
    total = len(get_all_complaints())
    if total == 0:
        print("\nNo complaints yet — nothing to analyze.\n")
        return

    category_counts = get_category_counts()
    status_counts = get_status_counts()

    print(f"\n--- Statistics ({total} total complaints) ---")

    print("\nBy Category:")
    for category, count in category_counts.most_common():
        percent = (count / total) * 100
        print(f"  {category}: {count} ({percent:.1f}%)")

    print("\nBy Status:")
    for status, count in status_counts.most_common():
        percent = (count / total) * 100
        print(f"  {status}: {count} ({percent:.1f}%)")

    most_common_category = category_counts.most_common(1)[0]
    print(f"\nMost reported problem: {most_common_category[0]} ({most_common_category[1]} complaints)")

    # --- Resolution time statistics ---
    resolution_hours = get_resolution_times()
    print("\nResolution Time (in hours):")
    if len(resolution_hours) == 0:
        print("  No resolved complaints yet — nothing to calculate.")
    else:
        mean_val = statistics.mean(resolution_hours)
        median_val = statistics.median(resolution_hours)
        min_val = min(resolution_hours)
        max_val = max(resolution_hours)
        print(f"  Mean: {mean_val:.2f} hrs")
        print(f"  Median: {median_val:.2f} hrs")
        print(f"  Min: {min_val:.2f} hrs")
        print(f"  Max: {max_val:.2f} hrs")

        if len(resolution_hours) > 1:
            stdev_val = statistics.stdev(resolution_hours)
            variance_val = statistics.variance(resolution_hours)
            print(f"  Standard Deviation: {stdev_val:.2f} hrs")
            print(f"  Variance: {variance_val:.2f}")
        else:
            print("  (Need at least 2 resolved complaints for std deviation/variance)")

    print()
def search_complaints():
    print("\nLeave blank to skip a filter.")
    category = input("Filter by category (Road/Water/Drainage/Waste/Electricity/Safety): ").strip()
    status = input("Filter by status (Open/Assigned/In Progress/Resolved): ").strip()

    category = category if category else None
    status = status if status else None

    rows = filter_complaints(category, status)

    if not rows:
        print("\nNo complaints match that filter.\n")
        return

    print(f"\n--- {len(rows)} matching complaint(s) ---")
    for row in rows:
        print(f"#{row['complaint_id']} | {row['date']} | {row['status']} | {row['category']} | {row['location']} | {row['description']}")
    print()


def main():
    init_db()
    while True:
        print("1. Submit a complaint")
        print("2. View all complaints")
        print("3. View a single complaint")
        print("4. Update complaint status")
        print("5. Show statistics")
        print("6. Search/filter complaints")
        print("7. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            submit_complaint()
        elif choice == "2":
            view_complaints()
        elif choice == "3":
            view_single_complaint()
        elif choice == "4":
            change_status()
        elif choice == "5":
            show_statistics()
        elif choice == "6":
            search_complaints()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.\n")


if __name__ == "__main__":
    main()