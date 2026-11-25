"""Lab 3.2: Referenced posts/comments, $lookup, and embedded migration."""
from connection import get_database


def main():
    client, db = get_database('blog_lab_db')
    try:
        for name in ('posts', 'comments', 'embedded_posts'):
            db.drop_collection(name)  # Demo reset: removes previous lab data.
        posts, comments, embedded = db.posts, db.comments, db.embedded_posts
        posts.insert_many([{'_id': i, 'title': title} for i, title in enumerate([
            'Introduction to MongoDB', 'Python Programming', 'Artificial Intelligence',
            'Machine Learning', 'Data Science'], start=1)])
        comments.insert_many([{'post_id': i, 'user': f'User{j}', 'text': f'Comment {j} on post {i}'}
                              for i in range(1, 6) for j in range(1, 3)])
        comments.create_index('post_id')
        lookup = {'$lookup': {'from': 'comments', 'localField': '_id', 'foreignField': 'post_id', 'as': 'comments'}}
        print('\nReferenced design with $lookup:')
        for post in posts.aggregate([{'$match': {'_id': 1}}, lookup]):
            print(f"{post['title']}: {len(post['comments'])} comments")
            for comment in post['comments']:
                print(f"- {comment['user']}: {comment['text']}")
        # Migration using aggregation pipeline and $merge.
        list(posts.aggregate([lookup, {'$merge': {'into': 'embedded_posts', 'whenMatched': 'replace', 'whenNotMatched': 'insert'}}]))
        print('\nEmbedded design after migration:')
        post = embedded.find_one({'_id': 1})
        print(f"{post['title']}: {len(post['comments'])} comments")
        print(f"Migrated {embedded.count_documents({})} posts and {sum(len(p['comments']) for p in embedded.find())} comments")
        print('\nQuery counts for displaying one post with comments:')
        print('Referenced, separate fetches: 2 database queries')
        print('Referenced, $lookup aggregation: 1 database query (server-side join)')
        print('Embedded: 1 database query')
        print('\nActivity 3.2: For 10,000 comments, use a separate indexed comments collection')
        print('with post_id and pagination; embedding causes unbounded growth and risks the 16 MB BSON limit.')
    finally:
        client.close()


if __name__ == '__main__':
    main()
