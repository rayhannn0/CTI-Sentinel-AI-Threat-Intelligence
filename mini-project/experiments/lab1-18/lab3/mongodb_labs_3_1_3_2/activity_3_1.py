"""Lab 3.1 — Try it yourself: prerequisites as course-code references."""
from connection import get_database


def main():
    client, db = get_database('university_lab_db')
    try:
        courses = db['activity_3_1_courses']
        courses.drop()  # Resets ONLY this activity's demo collection.
        courses.insert_many([
            {'code': 'CS201', 'title': 'Programming Fundamentals', 'prerequisites': []},
            {'code': 'CS401', 'title': 'Database Management Systems', 'prerequisites': ['CS201']},
            {'code': 'CS402', 'title': 'Artificial Intelligence', 'prerequisites': ['CS401']},
        ])
        courses.create_index('code', unique=True)

        # References are course codes. Resolve them to their course titles.
        for course in courses.find({}, {'_id': 0}):
            codes = course['prerequisites']
            required_courses = list(courses.find({'code': {'$in': codes}}, {'_id': 0, 'code': 1, 'title': 1}))
            names = [f"{p['code']} ({p['title']})" for p in required_courses]
            print(f"{course['code']}: {course['title']}")
            print('  Prerequisites:', ', '.join(names) if names else 'None')

        print('\nDESIGN CHOICE: Reference prerequisites using their unique course codes.')
        print('WHY: Each course is stored once; changing a prerequisite title does not')
        print('require updating embedded copies in multiple course documents.')
    finally:
        client.close()


if __name__ == '__main__':
    main()
