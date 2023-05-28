import random
from app import app, db
from app import User, Post, Comment
from werkzeug.security import generate_password_hash



# Tworzenie tabel w bazie danych

# Przykładowe dane
users_data = [
    {'email': 'john.doe@example.com', 'password': 'password123'},
    {'email': 'jane.smith@example.com', 'password': 'password456'},
    {'email': 'michael.brown@example.com', 'password': 'password789'},
    {'email': 'emily.johnson@example.com', 'password': 'passwordabc'},
    {'email': 'david.wilson@example.com', 'password': 'passworddef'},
    {'email': 'olivia.jones@example.com', 'password': 'passwordghi'},
    {'email': 'william.davis@example.com', 'password': 'passwordjkl'},
    {'email': 'sophia.miller@example.com', 'password': 'passwordmno'},
    {'email': 'james.anderson@example.com', 'password': 'passwordpqr'},
    {'email': 'ava.thomas@example.com', 'password': 'passwordstu'}
]

posts_data = [
    {'title': 'Introduction to Python', 'content': 'Python is a versatile programming language.'},
    {'title': 'Web Development Basics', 'content': 'Learn the fundamentals of web development.'},
    {'title': 'Data Analysis Techniques', 'content': 'Explore various data analysis methods.'},
    {'title': 'Machine Learning Algorithms', 'content': 'Discover popular machine learning algorithms.'},
    {'title': 'Introduction to Artificial Intelligence', 'content': 'Learn about the basics of AI.'},
    {'title': 'Database Management Systems', 'content': 'Understand the concepts of DBMS.'},
    {'title': 'Front-end Frameworks Comparison', 'content': 'Compare popular front-end frameworks.'},
    {'title': 'Cloud Computing Technologies', 'content': 'Explore different cloud computing platforms.'},
    {'title': 'Cybersecurity Best Practices', 'content': 'Learn how to protect your data.'},
    {'title': 'Mobile App Development Tools', 'content': 'Discover tools for mobile app development.'},
    {'title': 'Software Testing Techniques', 'content': 'Ensure the quality of your software.'},
    {'title': 'Agile Project Management', 'content': 'Implement Agile methodologies in your projects.'},
    {'title': 'UI/UX Design Principles', 'content': 'Create user-friendly interfaces.'},
    {'title': 'Data Visualization with Python', 'content': 'Visualize data using Python libraries.'},
    {'title': 'Network Protocols Overview', 'content': 'Understand common network protocols.'},
    {'title': 'Introduction to Robotics', 'content': 'Learn the basics of robotics.'},
    {'title': 'JavaScript Fundamentals', 'content': 'Explore the core concepts of JavaScript.'},
    {'title': 'Artificial Neural Networks', 'content': 'Understand ANNs and their applications.'},
    {'title': 'Mobile Security Guidelines', 'content': 'Secure your mobile applications.'},
    {'title': 'Web Scraping Techniques', 'content': 'Extract data from websites using Python.'}
]

comments_data = [
    {'content': 'Great post!'},
    {'content': 'Very informative.'},
    {'content': 'I have a question: ...'},
    {'content': 'Thanks for sharing.'},
    {'content': 'Helpful article.'},
    {'content': 'I learned something new.'},
    {'content': 'Well explained.'},
    {'content': 'Looking forward to more posts.'},
    {'content': 'I enjoyed reading this.'},
    {'content': 'Can you provide more examples?'}
]
with app.app_context():
    db.create_all()
    users = []
    for user_data in users_data:
        user = User(email=user_data['email'], password_hash=generate_password_hash(user_data['password']))
        users.append(user)
        db.session.add(user)

    posts = []
    for post_data in posts_data:
        post = Post(title=post_data['title'], content=post_data['content'], author=random.choice(users))
        posts.append(post)
        db.session.add(post)


    for comment_data in comments_data:
        comment = Comment(content=comment_data['content'], author=random.choice(users), post=random.choice(posts))
        db.session.add(comment)

    db.session.commit()

    print('Użytkownicy:')
    for user in User.query.all():
        print(f'ID: {user.id}, Email: {user.email}, Password: {user.password_hash}')

    print('Posty:')
    for post in Post.query.all():
        print(f'ID: {post.id}, Title: {post.title}, Content: {post.content}, Author: {post.author.email}')

    print('Komentarze:')
    for comment in Comment.query.all():
        print(f'ID: {comment.id}, Content: {comment.content}, Author: {comment.author.email}, Post: {comment.post.title}')
