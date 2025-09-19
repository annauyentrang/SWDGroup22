The main elements of the front-end will include the following:
- A login and registration page that will collect information such as a username in password to be stored into the database.
- A profile management UI, avaliability calendar, and dashboard accessible by volunteer users that will display data coming from information stored in the database.
- An event management UI, a matching volunteer list view, view and export report option, and dashboard accesible by admins.

The main elements of the back-end will include:
- An email authentication proesses that will check if a account has been email authenticated and will store email information into the database.
- An profile/event management code that will take in the information from the front-end UI and store and update information within the database.
- Event creation and editing capabilities that will take information from the UI and allow users to add and update backend data.
- A volunteer matching module that uses and algorithm to determine which users are most suitable for different volunteering opportunities.
- A volunteer hours and participation module that stores this information after it is inputted using the front-end UI.
- A reports generation module that fetches data from the backend to display to users on the front end.
- An event suggestions algorithm that determines whether or not to show an event on a volunteer dashboard in the front end based on a matching score between a volunteer profile and an event based on data stored in the database.
- An email notification system that emails users based on the volunteer time and event data stored in the database gathered from the front-end.

Our database will store information including:
- User data
- Profile/Event management data
- Event volunteer and participation records

- User will log in. If not registered, they are prompted to input an email address, followed by email authentication. Verified users are logged in and are identified as either volunteer or admin.
- Volunteers can manage their profile, view the availability calendar, and event suggestions on the dashboard. They manage their profile through the profile management UI, from which they can update their general availability calendar, view suggested events, receive notifications, or track their hours and participation.
- Admins log in to the event management UI, where they can create and edit events, access the volunteer matching module, assign tasks, view results, and generate reports on volunteer participation.
- All information will be stored in the database, which will ensure smooth communication between both front-end and back-end.
