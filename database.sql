CREATE TABLE IF NOT EXISTS urls (id bigint PRIMARY KEY GENERATED
                ALWAYS AS IDENTITY, name varchar(255), created_at timestamp)
CREATE TABLE IF NOT EXISTS url_checks (id bigint,
                    url_id bigint GENERATED ALWAYS AS IDENTITY,
                        status_code integer, h1 varchar(255),
                            title varchar(255), description varchar(255),
                                created_at timestamp)
SELECT id, name FROM urls ORDER BY id DESC
SELECT created_at, status_code FROM url_checks
                    WHERE url_id=(SELECT max(url_id) FROM url_checks WHERE
                        id=%s)
SELECT id, name FROM urls WHERE name = %s
INSERT INTO urls (name, created_at) VALUES (%s,%s)
SELECT id FROM urls WHERE created_at = %s
SELECT name FROM urls WHERE id=%s
INSERT INTO url_checks (id, created_at, status_code, h1,
                        title, description) VALUES (%s,%s,%s,%s,%s,%s)
SELECT name, created_at FROM urls WHERE id = %s
SELECT url_id, status_code, created_at, h1,
                           title, description FROM url_checks
                            WHERE id = %s ORDER BY url_id DESC