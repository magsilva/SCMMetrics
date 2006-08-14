#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# SCMMetrics
# A tool to collect metrics from projects hosted on Subversion repositories.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# 
# Copyright (C) 2006 Marco Aurélio Graciotto Silva <magsilva@gmail.com>
# 
#
#
# The code to extract the line count was heavily based on "SLOC Compare",
# a tool for visual processing of sloccount(1) output, based on pygame.
# The SLOC Compare is copyrighted by (C) 2003 Josef Spillner
# <josef@ggzgamingzone.org> and published under the GNU GPL.

import os
import re
import svn
import svn.core
import sys
import tempfile

def removeDir(topDir):
	"""Delete everything reachable from the directory named in 'top',
	assuming there are no symbolic links."""
	for root, dirs, files in os.walk(topDir, topdown=False):
		for name in files:
			os.remove(os.path.join(root, name))
		for name in dirs:
			os.rmdir(os.path.join(root, name))


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



class Repository(object):
	pass


class SubversionRepository(Repository):

	DEFAULT_START_REVISION = "HEAD"

	DEFAULT_END_REVISION = "HEAD"

	def __init__(self, url):
		assert(svn.core.SVN_VER_MAJOR, svn.core.SVN_VER_MINOR) >= (1, 3), "Subversion 1.3 or later required"
		self.url = url
	

	def switchUrl(self, url):
		self.url = url

	def checkout(self, destDir, revision = "HEAD"):
		if type(revision) == str:
                        revision = self.convertRevisionStringToInt("HEAD")

		# Initialize APR and get a POOL.
		svn._util.apr_initialize()
		pool = svn.util.svn_pool_create(None)

		# Checkout the HEAD of URL into PATH (silently)
		svn.client.svn_client_checkout(None, self.url, destDir, revision, 1, None, pool)

		# Cleanup our POOL, and shut down APR.
		svn.util.svn_pool_destroy(pool)
		svn._util.apr_terminate()


	def export(self, destDir, revision = "HEAD"):
		if type(revision) == str:
                        revision = self.convertRevisionStringToInt("HEAD")

		# Initialize APR and get a POOL.
		svn._util.apr_initialize()
		pool = svn.util.svn_pool_create(None)

		# Checkout the HEAD of URL into PATH (silently)
		svn._client.svn_client_export(None, self.url, destDir, revision, 1, None, pool)

		# Cleanup our POOL, and shut down APR.
		svn.util.svn_pool_destroy(pool)
		svn._util.apr_terminate()


	def convertRevisionStringToInt(self, revision):
		return -1


	def getRevisionRange(self, startRevision, endRevision):
		if type(startRevision) == str:
			startRevision = self.convertRevisionStringToInt(startRevision)
		if type(endRevision) == str:
			endRevision = self.convertRevisionStringToInt(endRevision)
		return range(startRevision, endRevision)



class MetricsCollector(object):

	def __init__(self, project, workDir = None, startRevision = None, endRevision = None):
		self.project = project
		if workDir == None:
			self.workDir = tempfile.mkdtemp()
		else:
			self.workDir = workDir

		if startRevision == None:
			self.startRevision = project.repository.DEFAULT_START_REVISION
		else:
			self.startRevision = startRevision

		if endRevision == None:
			self.endRevision = project.repository.DEFAULT_END_REVISION
		else:
			self.endRevision = endRevision

		self.ignoreDirs = build_re_list(project.getFilesTaggedAs("VendorCode"))


	def extract_revision_data(self, revision):
		destDir = os.path.join(self.workDir, revision)
		project.repository.export(destDir, revision)
		filename = os.path.join(self.workDir, "stats.%s" % revision)
		sys.execlp("sloccount --duplicates --autogen --addlangall %s > %s" % (destDir, filename))
		removeDir(destDir)

		f = file(filename, "r")
		result = []
		slocmode = 0
		print "Processing file %s" % filename
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
				if not string_matches_re_list(args[1], excludeDirs):
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


	def collectData(self):
		locHistory = {}

		for revision in self.project.repository.getRevisionRange(self.startRevision, self.endRevision):
			print "\nRevision %s" % revision
			locHistory[revision] = self.collectDataFromRevision(revision)

		return locHistory


	def run(self):
		print "Compiling data for project %s, from version %s to %s" % (self.project.name, self.startRevision, self.endRevision)
		print "Directories to be ignored: ",
		for i in self.project.getFilesTaggedAs("VendorCode"):
			print i,
		print ""

		# Collect metrics
		locHistory = self.collectData()

		# Compile data to build the graph (Gnuplot)
		outputFile = os.path.join(self.workDir, "%s-stats.dat" % self.project.name)
		gnuplotData = file(outputFile, "w+")
		print "Overall results:"
		for revision in locHistory.keys():
			stats = 0
			for lang in softwareHistory[revision]:
				if lang != "(none)":
					stats = stats + int(lang.split("=")[1])
			print "Revision %s: %d" % (revision, stats) 
			gnuplotData.write(str(revision) + " " + str(stats) + "\n") 



class Project(object):

	def __init__(self, name):
		self.name = name
		self.tagXfile = {}
		self.fileXtags = {}


	def setRepository(self, repository):
		self.repository = repository


	def tag(self, file, tag ):
		if not self.tagXfile.has_key(tag):
			self.tagXfile = []
		if not self.fileXtag.has_key(file):
			self.fileXtag = []

		self.tagXfile[tag].append(file)
		self.fileXtag[file].append(tag)	


	def unttag(self, file, tag ):
		if self.tagXfile.has_key(tag):
			self.tagXfile[tag].remove(file)
		if self.fileXtag.has_key(file):
			self.fileXtag[file].remove(tag)	

		if len(self.tagXfile[tag]) == 0:
			del(self.tagXfile[tag])
		if len(self.fileXtag[file]) == 0:
			del(self.fileXtag[file])


	def getTagsForFile(self, file):
		if self.fileXtag.has_key(file):
			return self.fileXtag[file]
		else:
			return []


	def getFilesTaggedAs(self, tag):
		if self.tagXfile.has_key(tag):
			return self.tagXfile[tag]
		else:
			return []


	def collectMetrics(self):
		metrics = MetricsCollector(self)
		metrics.run()
		print "\n\nData is available at %s" % (metrics.workDir)



def usage():
	print "Usage: " + sys.argv[0] + " <PROJECT NAME> <URL PATH> <IGNORE DIRS>\n"
	sys.exit(0)


def main():
	if len(sys.argv) < 3:
		usage()

	project = Project(sys.argv[1])

	repository = SubversionRepository(sys.argv[2])
	project.setRepository(repository)

	for dir in sys.argv[3:]:
		project.tag(dir, "VendorCode")

	project.collectMetrics()


if __name__ == '__main__':
	main()
