CREATE TABLE IF NOT EXISTS urls (id bigint PRIMARY KEY GENERATED
                ALWAYS AS IDENTITY, name varchar(255), created_at timestamp);
CREATE TABLE IF NOT EXISTS url_checks (id bigint,
                    url_id bigint GENERATED ALWAYS AS IDENTITY,
                        status_code integer, h1 varchar(255),
                            title varchar(255), description varchar(255),
                                created_at timestamp);