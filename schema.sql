drop table if exists users;
create table users (
  uid integer primary key autoincrement,
  username text not null unique,
  password text not null,
  storage real default 1048576 not null,
  used_storage real default 0 not null
);