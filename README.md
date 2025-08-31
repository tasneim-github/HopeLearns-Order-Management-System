# Hope Learns Order Management System

> ⚠️ **Disclaimer**  
> This project was created as part of my CS50 Final Project.  
> It is published here **for educational and portfolio purposes only**.  
> Please do not copy or submit this code as your own work in CS50 or any other course.  
> Respect the course policies and academic honesty guidelines.

### Video Demo:  (https://youtu.be/OX5ZMfU8kSk)
### Description

### What is this project about?
This project is a Web Application for ordering Hope Learns art pieces.
#### Problem to solve
When sending orders via social media, the required information is not always provided, orders are not organized and can be overlooked. This application ensures that every order has all the required information, is organized, and is not overlooked.
#### Target Audience
This application is made for myself and any clients willing to order art pieces from my account. Therefore, two interfaces are available: the admin interface and the client interface. The admin could be me or anyone whom I ask for help managing orders.

### What does each of the files written for the project contain and do?
#### styles.css
This is the styling sheet. It was used to add all the styles used in the web application and reuse them throughout the application, making the application more user-friendly.
#### login.html
This page allows the user to login to their account which already exists, prompting them for their username and password.
#### register.html
This page allows the client to create a new account. It prompts them for their username, password, password confirmation, and email.
#### layout.html
Provides the base structure for all pages, ensuring consistency across the application. Adapted from the CS50 finance problem set with stylistic improvements.
#### apology.html
This is the HTML file displayed to the user when an error occurs.\
This file is similar to the one used in the finance problem set. However, the image used as a background was changed to one drawn by myself to match the theme of the web application.
#### contact-me.html
This html page is used to give the users a list of all the social media accounts I own.
#### edit-order-price.html
This is an HTML file that can only be accessed by admins. It is used to edit the price of the orders received based on the description provided by the client.
#### edit-order
This file is used by the client only. It enables clients to update their order details before an admin assigns a price.
#### index.html
This is the main dashboard for both admins and clients. Admins can use this page to view all the orders of all the clients, while clients can only view their orders. This page handles the different options available to the client and the admin depending on the current order status. An admin also has access to a filtered version of the index page to see only the accepted orders, ordered by the due date.
#### place-order.html
This HTML page is only accessible to a client and allows them to place a new order. It is a form that requires the client to enter certain details about the art piece they are requesting me to draw. It includes fields for order names, descriptions, colors, character references, background references, and more.
#### app.py
The main application file, is responsible for routing, handling user requests, and interacting with the database. It Includes input validation to ensure all forms are completed correctly, authentication mechanisms to differentiate between clients and admins, and error handling for invalid inputs or unauthorized actions.
#### helpers.py
Include all the required helper functions. Such as:
* is_valid_order_id(): Ensures the order ID is valid and belongs to the correct user.
- process_files(): Handles secure file uploads.
+ is_valid_color(): Validates color inputs in hex format.\

### Certain design choices I debated and why I made them
#### Database Design Choice
A major issue I faced was storing multivalued attributes like colors and reference images in the orders table.
I decided to create separate tables for color_palette, character_references, and background_references, each linked to the orders table with foreign keys. I chose this approach since it adheres to database best practices and ensures scalability.\
#### Validation of order_id
The order_id value comes from a hidden input in forms, making it vulnerable to manipulation. Therefore,
I implemented a helper function, is_valid_order_id(), to validate the ID before use. This centralized validation reduces redundancy and improves security.
 #### Accepted Orders Page
 I debated whether I should create an accepted orders tab since it seemed redundant since all orders can be viewed on the main page. I then opted for adding a dedicated page to improve usability, providing myself with a clear to-do list for viewing accepted orders so that I could start creating them.
 ### Final Notes
 ChatGPT was used as an aid throughout the process of writing the project.  It was mainly used to assist with debugging, styling improvements, and ensuring best practices. Also, race conditions were not considered in the implementation of this project.
