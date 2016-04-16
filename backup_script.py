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

import collections
import os
import hashlib
import json
import datetime
from subprocess import Popen, PIPE

bucketName = ""
scriptRoot = "C:/B2BackupScript/"
bucketFilename = scriptRoot + "bucket_name.txt"
trackedPathsFilename = scriptRoot + "tracked_files.txt"
logFilename = scriptRoot + "log.txt"
logFile = ''
localFileSha1Dic = collections.OrderedDict()  # [filename][sha]
b2FileSha1Dic = dict()
# The size of the chunks that the files are broken into when
# their checksum in calcSha1
BUF_SIZE = 65536


def log(s, end=None):
	if end is None:
		print(s)
	else:
		print(s, end=end)

	s = s.strip()
	dt = datetime.datetime.now()
	YY = str(dt.year)
	MM = str(dt.month) if dt.month >= 10 else '0' + str(dt.month)
	DD = str(dt.day) if dt.day >= 10 else '0' + str(dt.day)
	hh = str(dt.hour) if dt.hour >= 10 else '0' + str(dt.hour)
	mm = str(dt.minute) if dt.minute >= 10 else '0' + str(dt.minute)
	ss = str(dt.second) if dt.second >= 10 else '0' + str(dt.second)
	timestamp = YY + '-' + MM + '-' + DD + ' ' + hh + ':' + mm + ':' + ss
	logFile.write(timestamp + ' ' + s + '\n')


def loadCredentials():
	global bucketName
	bucketName = open(bucketFilename, 'r').read().strip()


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
			log("Error: '" + p + "' is not a valid file or directory.")

	# recursively get all files in the folders in trackedFiles
	for folder in folders:
		for root, dirs, subFiles in os.walk(folder):
			for sf in subFiles:
				files.append(os.path.join(root, sf).replace("\\", "/"))

	# populate localFileSha1Dic with filenames as keys and the SHA1-hash of the
	# file content as values
	files.sort()
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
	log("Hiding file \"" + filename + "\"...", end='')
	cmd = "b2 hide_file \"" + bucketName + "\" \"" + filename + "\""
	outs, errs = sysCmd(cmd)
	if errs != '':
		# TODO handle error correctly
		log("\nError occured while hiding locally deleted file in B2:")
		log("\"" + cmd + "\"")
		log(errs)
		return False
	else:
		log(" Done.")
		return True


def uploadFile(f, currUploadIndex, totalToUpload):
	log("Uploading file " + str(currUploadIndex) + "/" + str(totalToUpload)
					+ ": \"" + f + "\"... ", end='')
	cmd = "b2 upload_file \"" + bucketName + "\" \"" + f + "\" \"" + f + "\""
	outs, errs = sysCmd(cmd)
	if errs != '':
		# TODO handle error correctly
		log("\nError occured while uploading file to B2:")
		log("\"" + cmd + "\"")
		log(errs)
		return False
	else:
		log("Done.")
		return True


def main():
	global logFile
	logFile = open(logFilename, 'a')
	loadCredentials()
	authB2()
	log("Getting file data from B2... ", end='')
	getB2Data()
	log("Done.")
	log("Get all tracked files and their hashes... ", end='')
	getLocallyTrackedFiles()
	log("Done.")
	localFileNames = localFileSha1Dic.keys()
	b2FileNames = b2FileSha1Dic.keys()

# 	log("Files under tracking:")
# 	for lf in localFileNames:
# 		log("    " + lf)

	# create list of new local files
	newLocalFiles = list()
	for lf in localFileNames:
		if lf not in b2FileNames:
			newLocalFiles.append(lf)

	# create list of deleted local files
	locallyDeletedFiles = list()
	for bf in b2FileNames:
		if bf not in localFileNames:
			locallyDeletedFiles.append(bf)

	# clear localFileSha1Dic from newly uploaded files
	for lf in newLocalFiles:
		del localFileSha1Dic[lf]

	# count no of files that need updating
	filesNeedingUpdate = 0
	for lf in localFileNames:
		if localFileSha1Dic[lf] != b2FileSha1Dic[lf]:
			filesNeedingUpdate += 1

	log(str(filesNeedingUpdate) + " changed files, " + str(len(newLocalFiles))
					+ " new files to upload, " + str(len(locallyDeletedFiles))
					+ " deleted files to hide.")

	totalFilesToUpload = filesNeedingUpdate + len(newLocalFiles)
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
		success = uploadFile(lf, filesUploaded + 1, totalFilesToUpload)
		if success:
			filesUploaded += 1
		else:
			errorOccured = True

	# compare checksums, upload to b2 if local version has different checksum
	for lf in localFileNames:
		if localFileSha1Dic[lf] != b2FileSha1Dic[lf]:
			success = uploadFile(lf, filesUploaded + 1, totalFilesToUpload)
			if success:
				filesUploaded += 1
			else:
				errorOccured = True
		else:
			filesUnchanged += 1

	if not errorOccured:
		log("Backup successful. " + str(filesUploaded) + " files uploaded, "
						+ str(filesDeleted) + " files deleted, "
						+ str(filesUnchanged) + " files unchanged.")

	logFile.close()

if __name__ == "__main__":
	main()
