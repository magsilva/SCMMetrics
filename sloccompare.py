#!/usr/bin/env python
# SLOC Compare
# A tool for visual processing of sloccount(1) output, based on pygame
# Copyright (C) 2003 Josef Spillner <josef@ggzgamingzone.org>
# Published under the GNU GPL

import sys
import re



def build_re_list(expressions_list):
	re_list = []
	for expression in expressions_list:
		re_list.append(re.compile(expression))
	return re_list



def string_matches_re_list(string, re_list):
	for expression in re_list:
		if expression.match(string):
			return True
	return False



def extract_software_history(input_files,include_dirs, exclude_dirs):
	software_history = {}
	counter = 0
	input_file_revision_re = re.compile(".*\.(\d+)$")

	input_files.sort()
	m = input_file_revision_re.match(input_files[0])
	counter = int(m.group(1))
	include_dirs = build_re_list(include_dirs)
	exclude_dirs = build_re_list(exclude_dirs)

	print "Initial revision is %d" % counter
	for filename in input_files:
		software_history[counter] = extract_revision_data(filename,include_dirs,exclude_dirs)
		counter = counter + 1
	print "Final revision is %d" % (counter - 1)

	return software_history


def extract_revision_data(filename, include_dirs, exclude_dirs):
	f = file(filename, "r")
	result = []
	slocmode = 0

	print "Processing file " + filename
	for line in f.readlines():
		line = line.rstrip()
		if line[0:5] == "SLOC " or line[0:5] == "SLOC\t":
			slocmode = 1
		elif slocmode == 1 and line == "SLOC total is zero, no further analysis performed.":
			print "\tNo single line of code to count"
			result.append("(none)")
			slocmode = 0
		elif slocmode == 1 and line == "":
			print "Ok"
			slocmode = 0
		elif slocmode == 1:
			line = re.sub("\ +", " ", line)
			args = line.split(" ")
			if string_matches_re_list(args[1], include_dirs):
				print "\tProcessing directory " + args[1] + ": ",
				languages = args[2].split(",")
				for lang in languages:
					result.append(lang)
					print lang,
				print ""
			else:
				print "\tIgnoring directory " + args[1]
	f.close()
	return result


def main():
	project_name = sys.argv[1]
	include_dirs = [ "src*", "web" ]
	exclude_dirs = []
	input_files = sys.argv[2:]
	output_file = "%s-stats.dat" % project_name

	print "Compiling data for project %s" % project_name
	print "Directories to be analysed: ",
	for i in include_dirs:
		print i,
	print ""

	print "Directories to be excluded: ",
	for i in include_dirs:
		print i,
	print ""

	software_history = extract_software_history(input_files, include_dirs, exclude_dirs)

	gnuplot_data = file(output_file, "w+")
	print "Overall results:"
	for revision in software_history.keys():
		stats = 0
		for lang in software_history[revision]:
			if lang != "(none)":
				stats = stats + int(lang.split("=")[1])
		print "Revision %d: %d" % (revision, stats) 
		gnuplot_data.write(str(revision) + " " + str(stats) + "\n") 


if __name__ == '__main__':
	main()

import sys, os
from svn import core, util, _util, _client

assert(core.SVN_VER_MAJOR, core.SVN_VER_MINOR) >= (1, 3), "Subversion 1.3 or later required"

def usage():
	print "Usage: " + sys.argv[0] + " URL PATH\n"
	sys.exit(0)

clas SVNWorkcopy(object):

	def checkout(self, url, path):
		# Initialize APR and get a POOL.
		_util.apr_initialize()
		pool = util.svn_pool_create(None)

		# Checkout the HEAD of URL into PATH (silently)
		_client.svn_client_checkout(None, None, url, path, -1, 1, None, pool)

		# Cleanup our POOL, and shut down APR.
		util.svn_pool_destroy(pool)
		_util.apr_terminate()


i=0
while [ $i != 350 ]
do
	os.makedirs($i)
	svn checkout -r $i http://www.magsilva.dynalias.net/svn/wikire/trunk $i
	sloccount --duplicates --autogen --addlangall . > stats-trunk.$i
	rm -rf $i
done
