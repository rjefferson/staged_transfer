#!/usr/bin/env python

"""

Simple file to search an alien path for specified named file (default=root_archive.zip)
For each file found, check if it is on selected storage element. 

"""

import sys
if sys.version[0:3] < '2.7':
    print ("Python version 2.7 or greater required (found: %s)." % sys.version[0:5])
    sys.exit(-1)


import math, os, pprint, re, shlex, shutil, socket, stat, time
from shutil import copyfile
from datetime import datetime
from signal import alarm, signal, SIGALRM, SIGKILL, SIGTERM
from subprocess import Popen, PIPE, STDOUT
import argparse
#from ConfigParser import RawConfigParser
from process_commands import process_commands
import json

#---- Gobal defaults ---- Can be overwritten with commandline arguments 


#----------------------------------------

class prep_to_stage:
    """ application class """

    def __init__(self, args):
        self.args = args
        self.inputfile = args.input_file
	self.outfile = ".".join([self.inputfile,"sh"])
        self.storage = args.storage
        self.outdir = args.outdir
	self.xrdurl = args.xrdurl
        self.testit = args.testit
	self.storetype = self._checkstorage()
        self.proc_c = process_commands(args.verbosity)

#------------------------
    def _unixT(self):
        return int(time.mktime((datetime.now()).timetuple()))

#-----------------------------------

    def _checkstorage(self):
	if self.storage == "local":
           self.prepend = self.xrdurl
	   return 1
	elif self.storage == "NFS":
           self.prepend = "/gpfs01"
	   return 2
	elif self.storage == "HPSS":
           self.prepend = ""
	   return 3
	return 0

#-----------------------------------

    def update_control_file(self,control_name,path,filename):

        cname="/".join([path,control_name])
	cname+="_"
	cname+=self.storage
        with open(cname,"a") as myfile:
            myfile.write(filename)
            myfile.close()

#-----------------------------------

    def update_transfer_file(self,path, filename):
        self.update_control_file("transfer_file", path, filename)
        
#-----------------------------------

    def update_stage_file(self, path, filename):
        self.update_control_file("stage_file", path, filename)

#-----------------------------------

    def prep_output(self,filename):

	self.proc_c.log("current filename is %s " % (filename), 1)
        fname = self.prepend+filename.rstrip()  #  filecatalog doesn't include the /gpfs01 for nfs or xdrurl for xrootd
	ipath = fname.split("/reco/")
	if len(ipath) != 2:
	     return
	rpath = ipath[1]
        idir = rpath.rfind("/")
	stage_path = "/".join([self.outdir,rpath[0:idir]])
	stage_name = "/".join([self.outdir,rpath])
        stage_name += "\n"
        cmd="mkdir -p %s" % (stage_path)
        self.proc_c.log("Running command = %s" % (cmd), 1)
        s, o, e = self.proc_c.comm(cmd)
        if s == 0:
            self.update_transfer_file(stage_path,stage_name)
            destcmd=""
	    if self.storetype == 1:	
	       destcmd="xrdcp %s %s" % (fname,stage_name)
	    elif self.storetype == 2:
	       destcmd="ln -s %s %s " % (fname,stage_name)
	    self.update_stage_file(stage_path,destcmd)

        return None

#-----------------------------------

    def readinput(self):

	fin = open(self.inputfile,"r")
	for line in fin:
	    yield line


#-----------------------------------
    def go(self):

        icount = 0
        for filename in self.readinput():
            icount += 1
	    fname = filename.rstrip()
	    if fname is None:
		return
	    self.prep_output(filename)


def main():
    """ Generic program structure to parse args, initialize and start application """
    desc = """ find files on given SE """
    
    p = argparse.ArgumentParser(description=desc, epilog="None")
    p.add_argument("--input-file",dest="input_file",default=None,help="list of files to stage")
    p.add_argument("--storage",dest="storage",default=None,help="where files are - NFS, local, HPSS")
    p.add_argument("--outdir",dest="outdir",default=None,help="path to stage area.SHOULD end in *reco*")
    p.add_argument("--xrdurl",dest="xrdurl",default="root://xrdstar.rcf.bnl.gov:1095//",help="xrootd url")

    p.add_argument("-t",action="store_true",dest="testit",default=False,help="testit with 2 loops and exit")
    p.add_argument("-v", "--verbose", action="count", dest="verbosity", default=0,                                                                                                 help="be verbose about actions, repeatable")
    p.add_argument("--config-file",dest="config_file",default="None",help="override any configs via a json config file")


    args = p.parse_args()
    if args.input_file is None:
        print ("Required input file  is not specified")
        return -1
    if args.storage is None:
        print ("Required storage type is not specified")
        return -1
    if args.outdir is None:
        print ("Required outdir is not specified")
        return -1



#-------- parse config file to override input and defaults
    val=vars(args)
    if not args.config_file == "None":
        try:
            print ("opening ", args.config_file)
            with open(args.config_file) as config_file:
                configs=json.load(config_file)
            for key in configs:
                if key in val:
                    if isinstance(configs[key],unicode):
                        val[key]=configs[key].encode("ascii")
                    else:
                        val[key]=configs[key]
        except:
            p.error(" Could not open or parse the configfile ")
            return -1

    try:
        myapp = prep_to_stage(args)
        return(myapp.go())
    except (Exception), oops:
        if args.verbosity >= 2:
            import traceback
            traceback.print_exc()
        else:
            print (oops)
            return -1
                                                                                                                                                                
if __name__ == "__main__":                      
    sys.exit(main())


