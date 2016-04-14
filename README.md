# B2BackupScript

This is my personal script for backing up files with Backblaze B2.

There are two files which need to be provided: `bucket_name.txt` and `tracked_files.txt`.

`bucket_name.txt` should contain the name of your bucket on a single line.

`tracked_files.txt` should contain all files and folders you wish to backup, with a newline separating each file and folder. The paths may only be denoted with forward slashes, **backward slashes are not allowed in the file- and foldernames**.