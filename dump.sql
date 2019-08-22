CREATE USER db_username WITH PASSWORD 'db_password';
CREATE DATABASE db_name;
GRANT ALL PRIVILEGES ON DATABASE db_name TO db_username;

CREATE TABLE activity (
    username VARCHAR(30),
    day DATE,
    messages INT
);
