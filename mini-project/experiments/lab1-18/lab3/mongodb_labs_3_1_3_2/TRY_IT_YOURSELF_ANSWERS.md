# Try It Yourself — Lab 3 Activities

## Activity 3.1: Prerequisites between courses

**Requirement:** Track prerequisite relationships between courses. Choose embedding or referencing and justify.

**Decision: Reference prerequisite courses by their unique course codes.** Add a `prerequisites` array to each course, e.g. `{"code": "CS402", "prerequisites": ["CS401"]}`. The `CS401` record is maintained separately in the same `courses` collection. This avoids duplicate course titles, instructors and schedules, and lets prerequisite metadata change in one place. When displaying details, fetch the course codes using `$in` or join with `$lookup`.

**Runnable example:** `python activity_3_1.py`. Creates three sample courses (CS201, CS401, CS402) and resolves prerequisite titles. Uses `connection.py`.

## Activity 3.2: A blog post with 10,000 comments

**Question:** Why would embedding be problematic? What alternative would you use?

Embedding every comment inside one post causes an ever-growing document. Reading a post can transfer far more data than the user needs, large arrays are cumbersome to update, and the post can eventually exceed MongoDB's **16 MB BSON document limit** (the exact number of comments that fits depends on their sizes).

**Decision: Use separate `posts` and `comments` collections.** Each comment stores the post's `_id` as `post_id`. Create an index such as `[("post_id", 1), ("_id", 1)]` and retrieve a small page at a time, e.g. 10 or 20 comments. A `$lookup` remains available for cases requiring a server-side join, but pagination is preferable for a large discussion.

**Runnable example:** `python activity_3_2.py`. Creates one post, inserts **10,000 referenced comments** in batches, and displays the first ten. Uses `connection.py`.

**Note:** The activity scripts reset only their own activity collections, not the main lab collections.
