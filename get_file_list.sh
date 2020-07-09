#!/bin/sh

#
#   $1 = trgsetupname
#   $2 = production
#   $3 = storage  (NFS, local, HPSS
#   $4 = limit ... set to 0 for all files
#

trg="trgsetupname=$1"
prod="production=$2"
stor="storage=$3"
general="filename~st_physics,filetype=daq_reco_picoDst,sanity=1"

limit=$4


get_file_list.pl -keys 'path,filename' -cond "$general,$trg,$prod,$stor" -limit $limit -delim "/"

