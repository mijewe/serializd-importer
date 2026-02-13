"""
Script to delete diary entries from Serializd.

Can delete all entries or only those with a specific tag.

Usage:
    python _clear_all_reviews.py                # Delete ALL entries
    python _clear_all_reviews.py netfliximport  # Delete only entries with this tag
"""

from netflix_to_serializd.serializd_adapter import create_client


def main() -> None:
    import sys

    # Check for tag filter argument
    filter_tag = None
    if len(sys.argv) > 1:
        filter_tag = sys.argv[1]

    print("=" * 70)
    print("Serializd Diary Entry Cleanup")
    print("=" * 70)
    print()

    if filter_tag:
        print(f"🏷️  Filtering by tag: {filter_tag}")
        print()
    else:
        print("⚠️  WARNING: This will delete ALL your diary entries!")
        print()

    # Ask for confirmation
    response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return

    print("\nInitializing Serializd client...")
    client = create_client()

    print("Fetching all reviews...")
    all_reviews = client.get_user_reviews()

    if not all_reviews:
        print("No reviews found.")
        return

    print(f"Found {len(all_reviews)} total diary entries")

    # Filter by tag if specified
    if filter_tag:
        print(f"\nFetching tags for each review to check for '{filter_tag}'...")
        print("(This may take a moment for large collections)\n")

        reviews = []
        for i, review in enumerate(all_reviews, 1):
            review_id = review.get('id')
            if not review_id:
                continue

            # Fetch tags for this review
            try:
                tags = client.get_review_tags(review_id)

                # Check if the filter tag is in the tags list
                # Tags can be with or without # prefix
                tag_match = False
                for tag in tags:
                    if filter_tag in tag or f"#{filter_tag}" == tag or filter_tag == tag.lstrip('#'):
                        tag_match = True
                        break

                if tag_match:
                    # Add the tags to the review object for display later
                    review['tags'] = tags
                    reviews.append(review)
                    print(f"  [{i}/{len(all_reviews)}] Found match: {review.get('showTitle', 'Unknown')} (tags: {', '.join(tags)})")
            except Exception as e:
                print(f"  [{i}/{len(all_reviews)}] ⚠ Warning: Could not fetch tags for review {review_id}: {e}")
                continue

        print(f"\nFound {len(reviews)} diary entries with tag '{filter_tag}' (out of {len(all_reviews)} total)\n")
    else:
        reviews = all_reviews
        print()

    if not reviews:
        print("No matching reviews to delete.")
        return

    # Ask for final confirmation
    response = input(f"Delete {len(reviews)} entries? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return

    print("\nDeleting diary entries...")

    success_count = 0
    error_count = 0

    for i, review in enumerate(reviews, 1):
        review_id = review.get('id')
        show_title = review.get('showTitle', 'Unknown')
        season_num = review.get('seasonNumber', '?')
        episode_num = review.get('episodeNumber', '?')
        tags = review.get('tags', [])

        tag_str = f" [tags: {', '.join(tags)}]" if tags else ""
        print(f"[{i}/{len(reviews)}] Deleting: {show_title} S{season_num}E{episode_num}{tag_str}")

        try:
            success = client.delete_diary_entry(review_id)
            if success:
                success_count += 1
            else:
                print(f"           ✗ Failed to delete (API returned False)")
                error_count += 1
        except Exception as e:
            print(f"           ✗ Error: {e}")
            error_count += 1

    print("\n" + "=" * 70)
    print("Cleanup Summary")
    print("=" * 70)
    print(f"Total entries: {len(reviews)}")
    print(f"Successfully deleted: {success_count}")
    print(f"Errors: {error_count}")
    print()


if __name__ == "__main__":
    main()
