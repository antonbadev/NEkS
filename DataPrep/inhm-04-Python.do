/*
 *     EXPORT DATA (EDGES & ATTRIBUTES)
 */

* Housekeeping .................................................................
clear
clear mata
set more off
set memory 2g
set matsize 500
do 000-setup
capture log close
log using "$logs_dir/inhm-04-Matlab.txt", replace text
set scheme s1color, permanently
set graphics off

use "$clean_data_dir/inhm-final.dta", clear
sort scid id


*-------------------------------------------------------------------------------
*  PREPARATION
*-------------------------------------------------------------------------------

*count schools
qui sum scid
local nscid=`r(max)'
matrix define mat_temp=I(300)*0
matrix mat_nscid=mat_temp[1..`nscid',1..3]

gen netid=scid
gen int A=0
replace A=tobacco_30
gen int M=0
replace M=marijuana_30
drop tobacco
gen tobacco=tobacco_30


forvalues jscid=1/`nscid'{
    qui count if (scid==`jscid')
    matrix mat_nscid[`jscid',1]=`r(N)'
    qui sum SCID_INT if (scid==`jscid')
    matrix mat_nscid[`jscid',2]=`r(min)'
    matrix mat_nscid[`jscid',3]=`r(max)'
}

*generate action data

local size_mat_sex          =2
local size_mat_race         =5
local size_mat_grade        =6
local size_mat_tobacco      =2
local size_mat_tobacco_30   =2
local size_mat_marijuana    =2
local size_mat_marijuana_30 =2


* AUX DATA
sort netid id
local aux_file="$data4python_dir/aux.py"
capture file close aux_file
file open aux_file using "`aux_file'", write replace
file write aux_file "# Written by inhm-04-Python.do" _n
file write aux_file "   num_net      = `nscid';"     _n
file write aux_file "   vec_size_net = ["    _n
forvalues jscid=1/`nscid'{
    local jnscid       =mat_nscid[`jscid',1]
    local SCID_ORIG_MIN=mat_nscid[`jscid',2]
    local SCID_ORIG_MAX=mat_nscid[`jscid',3]
    local vertical_offset=24
    if (`jnscid'>9){
        local vertical_offset=`vertical_offset'-1
    }
    if (`jnscid'>99){
    local vertical_offset=`vertical_offset'-1
    }
    if (`jnscid'>999){
    local vertical_offset=`vertical_offset'-1
    }

    display `jscid' " " `nscid'
    file write aux_file _column(`vertical_offset') " `jnscid' ,#  " "#scid `jscid' -- SCID_INT `SCID_ORIG_MIN'" _n
}

file write aux_file "    ]"     
file close aux_file


* EDGES DATA
sort netid id
local edges_file="$data4python_dir/edges.csv"
capture file close edges_file
file open edges_file using "`edges_file'", write replace
file write edges_file "netid, id, nominee" _n

local jid_end   = 0 
local jid_begin = 0
sort scid id
forvalues jscid=1/`nscid'{
    local size_scid = mat_nscid[`jscid',1]
    local jid_end   = `jid_end' + `size_scid'
    local jid_begin = `jid_end' - `size_scid' + 1

    di "School ID " `jscid' ", size " `size_scid'
    forvalues jrow=`jid_begin'/`jid_end'{
        local flag_new_row=0
        local jid = `jrow'-`jid_begin'+1
        *file write fortran_file "   "
        forvalues jf = 1/10{
            local jjid = f`jf' in `jrow'
            if (`jjid'!=0){
                local netidout=netid[`jrow']
                file write edges_file "`netidout',`jid',`jjid'" _n
                local flag_new_row=1
            }
        }
    }
}
file close edges_file

* ATTRIBUTES
/*TAKE A NOTE
 income    = dev_ln_income by scid
 price/tax = dev from mean by scid in cents!!!*/

gen male=0
replace male=1 if sex==1
gen black=0
replace black=1 if race==2
gen mom_ed=0
replace mom_ed=mom_hs+mom_co

local attr_file="$data4python_dir/attr.csv"
outsheet netid id sex grade race black income price hhsmokes mom_ed tobacco using "`attr_file'", comma nolabel replace
local attr_file="$data4python_dir/attr2.csv"
outsheet netid id sex grade race black income price income_level price_level deg hhsmokes mom_ed tobacco using "`attr_file'", comma nolabel replace


forvalues jscid=1/`nscid'{
    local jnetid=`jscid'-1
    local attr_file="$data4python_dir/attr_netid_`jnetid'.csv"
    if (`jscid'<10){
        local attr_file="$data4python_dir/attr_netid_0`jnetid'.csv"
    }
outsheet netid id sex grade race black income price hhsmokes mom_ed tobacco using "`attr_file'" if netid==`jscid', comma nolabel replace
}



STOP: END inhm-04-Python.do

