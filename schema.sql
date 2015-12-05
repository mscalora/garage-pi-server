CREATE TABLE log (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  type        TEXT NOT NULL,
  detail      TEXT NOT NULL,
  timestamp   TEXT NOT NULL
);

CREATE TABLE user
(
  id     INTEGER PRIMARY KEY NOT NULL,
  userid TEXT                NOT NULL COLLATE NOCASE,
  pwhash TEXT                NOT NULL,
  admin  BOOLEAN DEFAULT 0   NOT NULL
);
