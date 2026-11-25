"""Lab 3.2 — Try it yourself: 10,000 comments with references and pagination."""
from pymongo import InsertOne
from connection import get_database

TOTAL_COMMENTS = 10_000
PAGE_SIZE = 10


def main():
    client, db = get_database('blog_lab_db')
    try:
        posts = db['activity_3_2_posts']
        comments = db['activity_3_2_comments']
        posts.drop()       # Resets ONLY this activity's demo collections.
        comments.drop()
        posts.insert_one({'_id': 1, 'title': 'A popular post with many comments'})
        comments.create_index([('post_id', 1), ('_id', 1)])

        # Generate a realistic high-volume comment set without embedding it in the post.
        batch = []
        for i in range(1, TOTAL_COMMENTS + 1):
            batch.append(InsertOne({'_id': i, 'post_id': 1,
                                    'user': f'User{i}', 'text': f'Comment number {i}'}))
            if len(batch) == 1000:
                comments.bulk_write(batch, ordered=False)
                batch = []
        if batch:
            comments.bulk_write(batch, ordered=False)

        print('Post:', posts.find_one({'_id': 1})['title'])
        print('Total comments:', comments.count_documents({'post_id': 1}))
        print(f'First page ({PAGE_SIZE} comments):')
        # Seek pagination avoids expensive large skips on later pages.
        for comment in comments.find({'post_id': 1}).sort('_id', 1).limit(PAGE_SIZE):
            print(f"  {comment['_id']}: {comment['text']}")

        print('\nWHY NOT EMBED 10,000 COMMENTS?')
        print('The post document grows without bound, increasing transfer/read cost')
        print('and risking the MongoDB 16 MB maximum BSON document size.')
        print('BETTER: Store comments separately, index post_id + _id, and paginate.')
        print('The application loads a post and only the requested page of comments.')
    finally:
        client.close()


if __name__ == '__main__':
    main()
