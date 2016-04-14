# B2BackupScript

This is my personal script for backing up files with Backblaze B2.

There are two files which need to be provided: `bucket_name.txt` and `tracked_files.txt`.

`bucket_name.txt` should contain the name of your bucket on a single line.

`tracked_files.txt` should contain all files and folders you wish to backup, with a newline separating each file and folder. The paths may only be denoted with forward slashes, **backward slashes are not allowed in the file- and foldernames**.

**You also need to [manually authenticate](https://www.backblaze.com/b2/docs/b2_authorize_account.html) your computer with B2 in order for the script to work.**

## TODO

- Add automatic B2 authentication.
- Handle error codes if B2 interactions fail.
- Make script keep a log file.
  - Add option to make script not to keep a log.