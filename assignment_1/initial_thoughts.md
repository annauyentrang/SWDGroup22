# Syed Maisum's Initial Thoughts

- The application will be a web application where volunteers should have a simple registration/login, then a guided profile setup and dashboard that shows upcoming events they’re matched to and participation history. Administrators should have tools to create/manage events and define requirements.
- The application must have a feature for users to register and log-in, there must be a feature for volunteers to be able to customize their profile with information such as location and skills, administrators must have the abillity to create and manage events, there must be some sort of feature that matches volunteers to events, the app should have a feature that sends notifications to volunteers, and the app should track voluneer's history.
- React/JS/HTML/CSS can be used for the front-end, either FastAPI or Django may be used for the back-end, PostgreSQL can be used as the database, and notifications can be sent through Python's built-in smtplib library.

# JC Ubeda's Initial Thoughts
Consider user experience: How will users (volunteers and administrators) interact with the application?
- Volunteer users will interact through a mobile-friendly web interface wherein they can onboard in three steps: register, verify email, and add information to their profile (location, skills, availability, etc.). Once registered, the app will display a dashboard of upcoming events, which includes suggested events that are tailored to the skills and preferences they are proficient in.
- Administrators will be given the ability to create and edit events, view a list of matching volunteers, and view reports on the events that detail volunteer hours and participation.

Identify the key functionalities: What are the essential features the application must have?
- Login and registration with email verification and access based on roles (volunteer and admin)
- Profile management (volunteer)
- Event management (admin)
- Volunteer Matching
- Notifications
- Volunteer history
  
Technology stack: What technologies might you use for front-end, back-end, database, and other components?
- Front-end: next.js, tailwind css
- Back-end: typescript
- Database: postgreSQL
