CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    is_admin BOOLEAN DEFAULT FALSE
    );
CREATE UNIQUE INDEX username ON users (username);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL,
    order_name VARCHAR(255) NOT NULL,
    character_part VARCHAR(50) NOT NULL,
    preferred_style VARCHAR(50) NOT NULL,
    pose_view VARCHAR(50) NOT NULL,
    pose_description TEXT NOT NULL,
    character_features_description TEXT,
    outfit_description TEXT,
    has_background BOOLEAN NOT NULL,
    background_description TEXT,
    price NUMERIC DEFAULT NULL,
    status VARCHAR(10) CHECK (status IN ('pending', 'reviewed', 'accepted', 'completed')) DEFAULT 'pending',
    order_due_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX order_id ON orders (order_id);


CREATE TABLE color_palette (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    order_id INTEGER NOT NULL,
    color_hex VARCHAR(7) NOT NULL, -- Store color in hex format, e.g., "#FFFFFF"
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);


CREATE TABLE character_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    order_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE background_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    order_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

