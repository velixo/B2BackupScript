#!/usr/bin/python

# =======================================================================
# For all calls to B2, the HTTP status code returned indicates success or
# failure. A status of 200 (OK) means success. Any code in the 400 or 500
# range is a failure.
# =======================================================================

# popup: start backup?
# upload newly created or updated files
# set locally deleted files as hidden in bucket

# if error:
#   create log file with errors
#   show taskbar popup that error occurred
# else:
#   show taskbar popup that upload occurred

import os
import hashlib
import json
from subprocess import Popen, PIPE

bucketName = ""
bucketSource = "bucket_name.txt"
trackedPathsFilename = "tracked_files.txt"
localFileSha1Dic = dict()  # [filename][sha]
b2FileSha1Dic = dict()
# The size of the chunks that the files are broken into when
# their checksum in calcSha1
BUF_SIZE = 65536


def loadCredentials():
	global bucketName
	bucketName = open(bucketSource, 'r').read().strip()


def sysCmd(cmd=None):
	p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	outs, errs = p.communicate()
	outs = outs.decode('utf-8')
	errs = errs.decode('utf-8')
	return (outs, errs)


def authB2():
	# TODO implement
	pass


def getB2Data():
	outs, errs = sysCmd("b2 list_file_names " + bucketName)
	if errs == '':
		jsonData = json.loads(outs)
		numOfFiles = len(jsonData["files"])
		for i in range(0, numOfFiles):
			filename = jsonData["files"][i]["fileName"]
			sha1Sum = jsonData["files"][i]["contentSha1"]
			b2FileSha1Dic[filename] = sha1Sum
	else:
		# TODO handle error correctly
		pass


def getLocallyTrackedFiles():
	files = list()
	folders = list()

	# extract files and folders from trackedPathsFilename
	trackedPathsFile = open(trackedPathsFilename, 'r')
	trackedPaths = trackedPathsFile.read().splitlines()
	for p in trackedPaths:
		if os.path.isfile(p):
			files.append(p)
		elif os.path.isdir(p):
			folders.append(p)
		else:
			print("Error: '" + p + "' is not a valid file or directory.")

	# recursively get all files in the folders in trackedFiles
	for folder in folders:
		for root, dirs, subFiles in os.walk(folder):
			for sf in subFiles:
				files.append(os.path.join(root, sf).replace("\\", "/"))

	for f in files:
		localFileSha1Dic[f] = calcSha1(f)


def calcSha1(file):
	# Calculates the SHA1 system without loading entire file into RAM at once,
	# only in 64kB chunks
	sha1 = hashlib.sha1()
	with open(file, 'rb') as f:
		while True:
			data = f.read(BUF_SIZE)
			if not data:
				break
			sha1.update(data)

	return sha1.hexdigest()


def hideFile(filename):
	print("Hiding file \"" + filename + "\"...", end='')
	cmd = "b2 hide_file \"" + bucketName + "\" \"" + filename + "\""
	outs, errs = sysCmd(cmd)
	if errs != '':
		# TODO handle error correctly
		print("\nError occured while hiding locally deleted file in B2:")
		print("\"" + cmd + "\"")
		print(errs)
		return False
	else:
		print(" Done.")
		return True


def uploadFile(f):
	print("Uploading file \"" + f + "\"...", end='')
	cmd = "b2 upload_file \"" + bucketName + "\" \"" + f + "\" \"" + f + "\""
	outs, errs = sysCmd(cmd)
	if errs != '':
		# TODO handle error correctly
		print("\nError occured while uploading file to B2:")
		print("\"" + cmd + "\"")
		print(errs)
		return False
	else:
		print(" Done.")
		return True


def main():
	loadCredentials()
	authB2()
	getLocallyTrackedFiles()
	getB2Data()
	localFileNames = localFileSha1Dic.keys()
	b2FileNames = b2FileSha1Dic.keys()
	locallyDeletedFiles = list()
	newLocalFiles = list()

	print("Files under tracking:")
	for lf in localFileNames:
		print("    " + lf)

	for lf in localFileNames:
		if lf not in b2FileNames:
			newLocalFiles.append(lf)

	for bf in b2FileNames:
		if bf not in localFileNames:
			locallyDeletedFiles.append(bf)

	errorOccured = False
	filesDeleted = 0
	filesUploaded = 0
	filesUnchanged = 0

	# hide locally deleted files in B2
	for lf in locallyDeletedFiles:
		success = hideFile(lf)
		if success:
			filesDeleted += 1
		else:
			errorOccured = True

	# upload new local files to B2
	for lf in newLocalFiles:
		success = uploadFile(lf)
		if success:
			filesUploaded += 1
		else:
			errorOccured = True

	# clear localFileSha1Dic from newly uploaded files
	for lf in newLocalFiles:
		del localFileSha1Dic[lf]

	# compare checksums, upload to b2 if local version has different checksum
	for lf in localFileNames:
		if localFileSha1Dic[lf] != b2FileSha1Dic[lf]:
			success = uploadFile(lf)
			if success:
				filesUploaded += 1
			else:
				errorOccured = True
		else:
			filesUnchanged += 1

	if not errorOccured:
		print("Backup successful. " + str(filesUploaded) + " files uploaded, "
								+ str(filesDeleted) + " files deleted, "
								+ str(filesUnchanged) + " files unchanged.")

if __name__ == "__main__":
	main()
