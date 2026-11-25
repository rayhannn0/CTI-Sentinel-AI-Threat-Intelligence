"""Lab 3.1: Embedded university courses and prerequisite references."""
from connection import get_database


def main():
    client, db = get_database('university_lab_db')
    try:
        db.drop_collection('courses')  # Demo reset: removes previous lab data.
        db.create_collection('courses', validator={'$jsonSchema': {
            'bsonType': 'object',
            'required': ['title', 'code', 'instructor', 'schedule'],
            'properties': {
                'title': {'bsonType': 'string'},
                'code': {'bsonType': 'string', 'pattern': '^CS[0-9]{3}$'},
                'instructor': {'bsonType': 'string'},
                'schedule': {'bsonType': 'array', 'items': {
                    'bsonType': 'object', 'required': ['day', 'time', 'room'],
                    'properties': {'day': {'bsonType': 'string'}, 'time': {'bsonType': 'string'}, 'room': {'bsonType': 'string'}}}},
                'students': {'bsonType': 'array', 'items': {
                    'bsonType': 'object', 'required': ['id', 'name', 'grade'],
                    'properties': {'id': {'bsonType': 'string'}, 'name': {'bsonType': 'string'}, 'grade': {'bsonType': 'string'}}}},
                'prerequisites': {'bsonType': 'array', 'items': {'bsonType': 'string'}}
            }
        }})
        courses = db.courses
        courses.create_index('code', unique=True)
        courses.insert_many([
            {'title': 'Database Management Systems', 'code': 'CS401', 'instructor': 'Dr. Kumar',
             'schedule': [{'day': 'Monday', 'time': '09:00', 'room': 'A101'}, {'day': 'Wednesday', 'time': '09:00', 'room': 'A101'}],
             'students': [{'id': 'S101', 'name': 'Arun', 'grade': 'A'}, {'id': 'S102', 'name': 'Priya', 'grade': 'B'}], 'prerequisites': ['CS201']},
            {'title': 'Artificial Intelligence', 'code': 'CS402', 'instructor': 'Dr. Sharma',
             'schedule': [{'day': 'Tuesday', 'time': '10:00', 'room': 'B202'}],
             'students': [{'id': 'S103', 'name': 'Rahul', 'grade': 'A'}], 'prerequisites': ['CS401']},
            {'title': 'Machine Learning', 'code': 'CS403', 'instructor': 'Dr. Kumar',
             'schedule': [{'day': 'Monday', 'time': '11:00', 'room': 'C303'}],
             'students': [{'id': 'S104', 'name': 'Sneha', 'grade': 'B'}], 'prerequisites': ['CS402']}
        ])
        print('\nCourses on Monday:')
        for c in courses.find({'schedule.day': 'Monday'}):
            print(f"- {c['code']}: {c['title']}")
        print('\nStudents in courses taught by Dr. Kumar:')
        for c in courses.find({'instructor': 'Dr. Kumar'}):
            for s in c['students']:
                print(f"- {s['id']} {s['name']} ({s['grade']}) — {c['code']}")
        print('\nActivity 3.1 — prerequisite course codes (references):')
        for c in courses.find():
            print(f"- {c['code']} requires: {', '.join(c['prerequisites']) or 'None'}")
        print('Why reference? Courses exist independently; embedding their full records would duplicate data.')
    finally:
        client.close()


if __name__ == '__main__':
    main()
