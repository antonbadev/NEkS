*     CTRF 2 SCHOOL COMPOSITION
*     UNDIRECTED NETWORKS

* Housekeeping .................................................................
clear
clear mata
set more off
set memory 2g
set matsize 500
do 000-setup
capture log close
log using "$logs_dir/inhm-04-Python-ctrf-schoolComposition.txt", replace text
set scheme s1color, permanently
set graphics off

use "$clean_data_dir/inhm-final.dta", clear
sort scid id

*checks
table scid race
local scid_mixed_race=12

*-------------------------------------------------------------------------------
*  PREPARATION SYNTHETIC SCHOOLS BLACK AND WHITE FROM SCHOOL 11
*-------------------------------------------------------------------------------

qui sum scid
local nscid=`r(max)'

keep if scid == `scid_mixed_race'
replace scid = 0
label list race_label
keep if race == 1 | race == 2
*low allowances grade <9
drop if grade<10 


*FOCUS ON SOCIAL INTERACTIONS
*replace mom_hs=0
*replace mom_co=0
*replace hhsmokes=0
*replace price=0
*replace income=0


*SYMMETRIC FRIENDS
*forvalues jF=1/10{
*  replace F`jF'  =f`jF'
*  *drop f`jF'
*}


*stop
*duplicate for size effects
expand 2, generate(new_school_2)
expand 2 if new_school_2==1, generate(new_school_3)
expand 2 if new_school_3==1, generate(new_school_4)
gen replica_school_id = new_school_2 + new_school_3 + new_school_4
drop new_school_*

*shift/translate friends ids
forvalues jF=1/10{
  replace F`jF'  =F`jF'  + 1000000000*replica_school_id
  replace f`jF'  =f`jF'  + 1000*replica_school_id
}
replace AID_INT=AID_INT+ 1000000000*replica_school_id
replace id     =id     + 1000*replica_school_id

*checks
*table grade race, c(mean tobacco_30)
*table race, c(mean tobacco_30)
*tab grade race

* FIX THE SEED
set seed 1273741827
local racial_swap_ratio=0
generate inverse_race = 6-race
qui count
local school_size=`r(N)'

*matrix define swap_grid = (0 \ 0.25 \ 0.5)
matrix define swap_grid = (0 \ 0.10 \ 0.20 \ 0.30 \ 0.40 \ 0.50)

local size_swap_grid    = rowsof(swap_grid)
forvalues jscid=1/`size_swap_grid'{
*forvalues jscid=6/6{

    local racial_swap_ratio  = swap_grid[`jscid',1]
    local racial_swap_size   = floor(`racial_swap_ratio' * `school_size' / 2 )
    display "======================================================"
    display `jscid' "  " `racial_swap_ratio' "  " `racial_swap_size' "  " `school_size'
    display "======================================================"

    *racial_swap_size Whites go to school Black
    capture drop random_uniform
    capture drop whites_to_swap
    capture drop blacks_to_swap
    generate random_uniform = runiform()
    sort scid race random_uniform
    generate whites_to_swap = (_n <= `racial_swap_size' & scid==0)

    capture drop random_uniform
    generate random_uniform = runiform()
    sort scid inverse_race random_uniform
    generate blacks_to_swap = (_n <=  `racial_swap_size' & scid==0)


    *count if whites_to_swap==1
    *count if blacks_to_swap==1

    *CHECKS (1=whites,2=black)
    capture drop check1 check2
    gen check1 = whites_to_swap & race==2
    gen check2 = blacks_to_swap & race==1
    sum check1 check2

    *Generate school white
    capture drop sch_1 sch_2
    generate sch_1=0
    generate sch_2=0
    replace sch_1=1 if scid==0 & race==1 & whites_to_swap !=1
    replace sch_1=1 if scid==0 & race==2 & blacks_to_swap ==1
    replace sch_2=1 if scid==0 & race==1 & whites_to_swap ==1
    replace sch_2=1 if scid==0 & race==2 & blacks_to_swap !=1
    

    *generate white school
    expand 2 if scid==0 & sch_1==1, generate(new_school)
    replace scid=(`jscid'-1)*2+1 if new_school==1
    drop new_school
        
    *generate black school
    expand 2 if scid==0 & sch_2==1, generate(new_school)
    replace scid=(`jscid'-1)*2+2 if new_school==1
    drop new_school

}

drop if scid==0
table scid, c(count grade)
table scid race, c(count grade)
table scid race, c(mean tobacco_30)
table scid, c(mean tobacco_30)

*STOP A

*-------------------------------------------------------------------------------
*  RE-INDEX
*-------------------------------------------------------------------------------

*double index for each id-observation
sort scid id
rename id id_old
capture drop id_tmp
gen int id_tmp=1
by scid, sort: gen id = sum(id_tmp)
drop id_tmp

*re-index friends
sort scid id
forvalues jF=1/10{
    rename f`jF' f`jF'_old
    gen int f`jF'=0
}

sort scid id
qui summarize scid
local num_scid=`r(max)'
local jid_begin = 0
local jid_end   = 0 
forvalues jscid=1/`num_scid'{
    qui sum id if scid==`jscid'
    local size_scid = `r(max)'
    local jid_begin = `jid_end' + 1
    local jid_end   = `jid_begin' + `size_scid' - 1
    di "School ID " `jscid' ", size " `size_scid' ", begin/end " `jid_begin' "/" `jid_end'
    
    forvalues jrow=`jid_begin'/`jid_end'{
        forvalues jF=1/10{
			forvalues jjrow=`jid_begin'/`jid_end'{            
                if f`jF'_old[`jrow']==id_old[`jjrow'] {
                    qui replace f`jF'=id[`jjrow'] in `jrow'
				*	continue, break
                    *di f`jF' " " `jjid' " " id[`jjid'] " " `jrow'
                }
            }

        }
    }
}

**                if F`jF'[`jrow']==AID_INT[`jjrow'] {

*move re-indexed freinds to the left




*  PREPARATION
*  EXPORT

*count schools
qui sum scid
local nscid=`r(max)'

*generate action data
gen int A=0
replace A=tobacco_30
gen int M=0
replace M=marijuana_30

matrix define mat_temp=I(300)*0
matrix mat_nscid=mat_temp[1..`nscid',1..3]

forvalues jscid=1/`nscid'{
    qui count if (scid==`jscid')
    matrix mat_nscid[`jscid',1]=`r(N)'
    qui sum SCID_INT if (scid==`jscid')
    matrix mat_nscid[`jscid',2]=`r(min)'
    matrix mat_nscid[`jscid',3]=`r(max)'
}

* EDGES DATA
gen netid=scid
sort netid id
local edges_file="$data4python_dir/edges-ctrfSchoolComposition.csv"
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

    di "School ID " `jscid' ", size " `size_scid' ", begin/end " `jid_begin' "/" `jid_end'
    forvalues jrow=`jid_begin'/`jid_end'{
        local jid = `jrow'-`jid_begin'+1
        *file write fortran_file "   "
        forvalues jF = 1/10{
            local jjid = f`jF' in `jrow'
            if (f`jF'[`jrow']>0){
                local netidout=netid[`jrow']
                file write edges_file "`netidout',`jid',`jjid'" _n
            }
        }
    }
}
file close edges_file

* ATTRIBUTES
*TAKE A NOTE
* income    = dev_ln_income by scid
* price/tax = dev from mean by scid in cents!!!

gen male=0
replace male=1 if sex==1
gen black=0
replace black=1 if race==2
gen mom_ed=0
replace mom_ed=mom_hs+mom_co

local attr_file="$data4python_dir/attr-ctrfSchoolComposition.csv"
outsheet netid id sex grade race black income price hhsmokes mom_ed tobacco using "`attr_file'", comma nolabel replace
*forvalues jscid=1/`nscid'{
*    local jnetid=`jscid'-1
*    local attr_file="$data4python_dir/attr_netid_`jnetid'.csv"
*    if (`jscid'<10){
*        local attr_file="$data4python_dir/attr_netid_0`jnetid'.csv"
*    }
*outsheet netid id sex grade race black income price hhsmokes mom_ed tobacco using "`attr_file'" if *netid==`jscid', comma nolabel replace
*}

STOP: END inhm-04-Python-ctrf-schoolComposition.do
