/*
 *     IN-HOME DATA
 */

* Housekeeping
clear
clear mata
set more off
set memory 2g
set matsize 500
do 000-setup
capture log close
log using "$logs_dir/inhm-01.txt", replace text
set graphics off

cd $stata_code_dir

*-------------------------------------------------------------------------------
* DATA I. SCHOOL INFORMATION DATA (ICPSR-27021-DS22)
*-------------------------------------------------------------------------------
use "$raw_data_dir/ICPSR_27021/DS0022/27021-0022-Data-REST.dta", clear
do "$raw_data_dir/ICPSR_27021/DS0022/27021-0022-Supplemental_syntax-REST.do"

*! clean : restricted sample
sort SCID
*saturated school sample
keep if SAT_SCHL==1
***special needs schoool (the smallest one) !!!
***also does not have reciprocal nominations
drop if SCID=="001"
***drop the biggest school !!!
drop if SCID=="077"
***drop the smallest school n=20
drop if SCID=="115"

*grades offered in schools
gen int grades=GRADES
la var grades "Grades offered"

replace grades=1 if (GRADES==10)
replace grades=2 if (GRADES==8)
replace grades=3 if (GRADES==1)
replace grades=4 if (GRADES==3)
replace grades=5 if (GRADES==5)
replace grades=6 if (GRADES==7)

label define grades_label 1 "K-8"
label define grades_label 2 "6-8", add
label define grades_label 3 "K-12", add
label define grades_label 4 "9-12", add
label define grades_label 5 "10-12", add
label define grades_label 6 "Special", add
label values grades grades_label

*check reassignment
*forvalues i=1/6{
*    tab GRADES if (grades==`i')
*}


*RE-INDEX schools according to the grades offered
sort grades SCID
destring SCID, gen(SCID_INT)
by grades SCID, sort: gen scid_tmp = (_n==1)
gen int scid = sum(scid_tmp)
drop scid_tmp
drop GRADES
sort SCID

*RE-INDEX 2
/*SCID 28 mixed race   --> one-before last
SCID 58 second biggest --> last
*/
gen scid_old=scid
drop scid
replace scid_old=1000 if SCID_INT==28
replace scid_old=1001 if SCID_INT==58
by scid_old, sort: gen scid_tmp = (_n==1)
gen int scid = sum(scid_tmp)
drop scid_tmp

sort SCID
save "$clean_data_dir/d1-school-info.dta", replace


*-------------------------------------------------------------------------------
* DATA II. IN-HOME QUESTIONAIRE DATA (ICPSR-27021-DS1)
*-------------------------------------------------------------------------------
quietly{
use "$raw_data_dir/ICPSR_27021/DS0001/27021-0001-Data-REST.dta", clear
do  "$raw_data_dir/ICPSR_27021/DS0001/27021-0001-Supplemental_syntax-REST.do"
}

sort AID
*drop missing ID's !!!
drop if AID==""
*drop missing GRADE !!!
des H1GI20
drop if H1GI20==.
gen grade=H1GI20
*!!!!!   clean - restrict sample   !!!!!
*drop the kids in lower grades in the big schools (very very very few; has to be error) !
tab grade if SCID=="058"
tab grade if SCID=="077"
*clean 5 students
*grades 9-12, scid=6
drop if (SCID=="058" & grade<9)
*grades 6-8, scid=9
drop if (SCID=="106" & grade>8)
*grades K-8, scid=11
drop if (SCID=="126" & grade>8)
*grades K-8, scid=13
drop if (SCID=="194" & grade>8)
*drop if (SCID=="077" & grade<10)

*create birth month-year, interview month-year, age
gen int bmonth=H1GI1M
gen int byear=H1GI1Y
drop if bmonth==.
drop if byear==.
gen float age = IYEAR-byear + (IMONTH-bmonth)/12
la var grade "SCHOOL GRADE"
la var age "AGE W1 IN-HOME"
la var bmonth "MONTH OF BIRTH"
la var byear "YEAR OF BIRTH"

*sex
rename BIO_SEX sex

* RACE - White, African American, Asian, Hispanic, Other
* Use race as identified by the respondant (H1GI6A-D), and
* wheather hispanic as identified by the respondent (H1GI4)
* NOTE. Alternatively one can use race identified by the interviewer:
*       H1GI9 - Interviewer: Please code the race of the respondent from your own observation alone.
*       It seems more relevant for ones choice how one perceives herself.
*       Moreover, results do not change if this alternative is adopted.

gen int race=0
label define race_label 0 "Missing"
label define race_label 1 "White", add
label define race_label 2 "African American", add
label define race_label 3 "Asian", add
label define race_label 4 "Hispanic", add
label define race_label 5 "Other", add
label values race race_label

*the order guarantees:
*non-hispanic white in 1
*non-hispanic black in 2
*non-hispanic asians in 3
*hispanic in 4
replace race=1 if (H1GI6A==1)
replace race=2 if (H1GI6B==1)
replace race=3 if (H1GI6D==1)
replace race=4 if (H1GI4==1)

/* In case dual race is reported resolve with 
 H1GI8: Which one category best describes your racial background?
 Few remain unresolved, i.e. no H1GI8 data (for the estimation sample 39).
 These are resolved in the reverse order of creation
        1 hispanic
        2 asian
        3 black
        4 white 
    i.e. between white (4) and black (2) -- black - the lower index wins
*/
gen race_omitted=0
gen dual_race_unresolved=0

local race1="H1GI6A"
local race2="H1GI6B"
local race3="H1GI6D"
local race4="H1GI4"
forvalues jr=1/4{
    local jrmin=`jr'+1
    forvalues jjr=`jrmin'/4{
        tab H1GI8 if (`race`jr''==1 & `race`jjr''==1)
        qui replace race=1 if (`race`jr''==1 & `race`jjr''==1 & H1GI8==1)
        qui replace race=2 if (`race`jr''==1 & `race`jjr''==1 & H1GI8==2)
        qui replace race=5 if (`race`jr''==1 & `race`jjr''==1 & H1GI8==3)
        qui replace race=3 if (`race`jr''==1 & `race`jjr''==1 & H1GI8==4)
        qui replace race=5 if (`race`jr''==1 & `race`jjr''==1 & H1GI8==5)

        qui replace dual_race_unresolved=1 if (`race`jr''==1 & `race`jjr''==1 & H1GI8>5)
        qui replace dual_race_unresolved=1 if (`race`jr''==1 & `race`jjr''==1 & H1GI8==.)
    }
}
tab race
* Few remain unindetified and are grouped as others (for the est sample 9)
replace race_omitted=1 if (race==0)
replace race=5 if (race==0)


order AID SCID SSCID IYEAR IMONTH byear bmonth age grade sex race
*keep  AID SCID SSCID IYEAR IMONTH byear bmonth age grade sex race ///
*      H1TO*
save "$clean_data_dir/d2-inhm-info.dta", replace



*-------------------------------------------------------------------------------
* DATA III. WAVE I IN-HOME NOMINATIONS (ICPSR 27022-DS0001)
*-------------------------------------------------------------------------------
use "$raw_data_dir/ICPSR_27022/DS0001/27022-0001-Data-REST.dta", clear

destring MF_AID1 MF_AID2 MF_AID3 MF_AID4 MF_AID5 FF_AID1 FF_AID2 FF_AID3 FF_AID4 FF_AID5, replace
destring AID, gen(AID_INT)
la var AID_INT "DESTRINGED AID - LONG!"

*keep MF_AID1 MF_AID2 MF_AID3 MF_AID4 MF_AID5 FF_AID1 FF_AID2 FF_AID3 FF_AID4 FF_AID5 ///
*AID ID SCID SCID_INT scid IYEAR IMONTH byear bmonth age grade grades sex race
order AID MF_AID1 MF_AID2 MF_AID3 MF_AID4 MF_AID5 FF_AID1 FF_AID2 FF_AID3 FF_AID4 FF_AID5
sort AID

*clean the adjacency matrix
local MISSING_VALUE_1 55555555
local MISSING_VALUE_2 77777777
local MISSING_VALUE_3 88888888
local MISSING_VALUE_4 99999999
*for strings local MISSING_VALUE_5 ""
local MISSING_VALUE_5 "."
local MISSING_LABEL_1 "Nominated friend was also nominated as one of the partners"
local MISSING_LABEL_2 "Nominated friend doesn't go to sister or sample school"
local MISSING_LABEL_3 "Nominated friend goes to sister school-not on list"
local MISSING_LABEL_4 "Nominated friend goes to sample school-not on list"
local MISSING_LABEL_5 "Missing"

foreach jSEX in MF FF{
    forvalues jF=1/5{
        local F="`jSEX'`jF'_INHM"
        qui gen long `F'=`jSEX'_AID`jF'
*IMPORTANT ROMANTIC PAIRS !!!
*romantic pairs jM=2/5
        forvalues jM=1/4{
            qui replace `F'=`MISSING_VALUE_5' if (`F'== `MISSING_VALUE_`jM'')
        }
    }
}
drop MF_AID* FF_AID*

*drop nominations of own id's as friends (self-nominations)
sort AID_INT
count
di `r(N)'
forvalues jn=1/`r(N)'{
    *di `jn'
    forvalues jf=1/5{
        if (AID_INT[`jn']==MF`jf'_INHM[`jn']){
            di "ROW-" `jn' " ID-" AID_INT[`jn'] " MF-" `jf' " " MF`jf'_INHM[`jn']
            replace MF`jf'_INHM=. in `jn'
        }
        if (AID_INT[`jn']==FF`jf'_INHM[`jn']){
            di "ROW-" `jn' " ID-" AID_INT[`jn'] " FF-" `jf' " " FF`jf'_INHM[`jn']
            replace FF`jf'_INHM=. in `jn'
        }
    }
}


save "$clean_data_dir/d3-inhm-nominations.dta", replace


*-------------------------------------------------------------------------------
* MERGE friends data, individual data and school data (obtain ADJACENCY MATRIX)

*---> merge 1 friends and inhome (get the SCID)
use "$clean_data_dir/d3-inhm-nominations.dta", clear
sort AID
merge AID using "$clean_data_dir/d2-inhm-info.dta", _merge(merge_aid_id)
tab merge_aid_id
drop if merge_aid_id==1
drop if merge_aid_id==2
drop merge_aid_id

*---> merge 2 (get the saturated sample)
sort SCID
merge SCID using "$clean_data_dir/d1-school-info.dta", _merge(merge_scid_id)
tab merge_scid_id
drop if merge_scid_id==1
drop if merge_scid_id==2
drop merge_scid_id

*** AID with no school/only saturated
keep if SAT_SCHL==1


*-------------------------------------------------------------------------------
*-------------------------------------------------------------------------------
*-------------------------------------------------------------------------------

*FRIENDS
*pool freinds variables - Fj
sort SCID AID
forvalues jF=1/5{
    local F="F`jF'"
    qui gen long `F'=MF`jF'_INHM
    local jjF=`jF'+5
    local F="F`jjF'"
    qui gen long `F'=FF`jF'_INHM
}
order AID SCID F1 F2 F3 F4 F5 F6 F7 F8 F9 F10
drop *_INHM MF* FF*

*move the freinds to the left
count
forvalues jrow=1/`r(N)'{
    forvalues jf=1/9{
	    *missing friend
	    if (F`jf'[`jrow']==.){
        local jfp_begin=`jf'+1
        local jfp_flag=0
        forvalues jfp=`jfp_begin'/10{
            if (F`jfp'[`jrow']!=.){
                local jfp_flag=1
                local jfp_index=`jfp'
                continue, break
            }
        }
        if `jfp_flag'==1 {
            *di "F" `jf' " "`jjf' "<---" `jjfp'
            *di F`jjf'[`jrow'] " " F`jjfp'[`jrow']
            qui replace  F`jf'=F`jfp_index'[`jrow'] in `jrow'
            qui replace  F`jfp_index'=. in `jrow'
        }
        }
    }
}


*** SPLIT SCID 058 (second biggest)***
*Already has the last scid 

qui sum scid
local nscid=`r(max)'
expand 2 if SCID_INT==58 & scid==`nscid', generate(scid15)
replace scid=(`nscid'+1) if scid15==1
drop scid15
expand 2 if SCID_INT==58 & scid==`nscid', generate(scid15)
replace scid=(`nscid'+2) if scid15==1
drop scid15
expand 2 if SCID_INT==58 & scid==`nscid', generate(scid15)
replace scid=(`nscid'+3) if scid15==1
drop scid15

drop if scid==(`nscid'+0) & grade!=9
drop if scid==(`nscid'+1) & grade!=10
drop if scid==(`nscid'+2) & grade!=11
drop if scid==(`nscid'+3) & grade!=12
*--------------------------------------------



display "---------------------------------------------"
display "Re-index: scid, id, f*                       "
display "---------------------------------------------"
sort scid AID_INT
capture drop id_tmp
gen int id_tmp=1
by scid, sort: gen id = sum(id_tmp)
drop id_tmp


*re-index friends
sort scid id
forvalues jF=1/10{
    gen int f`jF'=0
}

sort scid id
qui summarize scid
local num_scid=`r(max)'
local jid_end   = 0 
local jid_begin = 0
forvalues jscid=1/`num_scid'{
    qui sum id if scid==`jscid'
    local size_scid = `r(max)'
    local jid_begin = `jid_end' + 1
    local jid_end   = `jid_end' + `size_scid'
    di "School ID " `jscid' ", size " `size_scid'
    forvalues jrow=`jid_begin'/`jid_end'{
        forvalues jF=1/10{
	    forvalues jjrow=`jid_begin'/`jid_end'{            
                if F`jF'[`jrow']==AID_INT[`jjrow'] {
                    qui replace f`jF'=id[`jjrow'] in `jrow'
					continue, break
                    *di f`jF' " " `jjid' " " id[`jjid'] " " `jrow'
                }
            }

        }
    }
}


*move re-indexed friends to the left
count
forvalues jrow=1/`r(N)'{
    forvalues jf=1/9{
        forvalues jd=1/9{
            if (f`jf'[`jrow']==0){
                *move to the left
                forvalues jjf=`jf'/9{
                    local jjfp=`jjf'+1
                    qui replace  f`jjf'=f`jjfp'[`jrow'] in `jrow'
                }
                qui replace f10=0 in `jrow'
            }
        }
    }
}


display "---------------------------------------------"
display "Create f_nominatedby (f* nominates before)   "
display "---------------------------------------------"
global max_num_nominated_by=20
forvalues jf=1/$max_num_nominated_by{
    capture drop f_nominatedby`jf'
    gen f_nominatedby`jf'=0
}
sort scid id
qui summarize scid
local num_scid=`r(max)'
local jid_end   = 0 
local jid_begin = 0

*`num_scid'
forvalues jscid=1/`num_scid'{ 
*local jscid=1
    qui sum id if scid==`jscid'
    local size_scid = `r(max)'
    local jid_begin = `jid_end' + 1
    local jid_end   = `jid_end' + `size_scid'
    di "School ID " `jscid' ", size " `size_scid'
    forvalues jrow=`jid_begin'/`jid_end'{
        forvalues jf=1/10{
	    if f`jf'[`jrow']!=0 {
	        *get the nomination
		local nominatedid=f`jf'[`jrow']
		local nominatedid_row=`nominatedid'+`jid_begin'-1
		*di `nominatedid_row'
		*local flag_write=0
	        forvalues jff=1/20{
		    *di `jff'
		    if f_nominatedby`jff'[`nominatedid_row']==0 {
		        *di `jff' " " `nominatedid_row'
		        qui replace f_nominatedby`jff'=id[`jrow'] in `nominatedid_row'
			*local flag_write=1
                        continue, break
                    *di f`jF' " " `jjid' " " id[`jjid'] " " `jrow'
		    }
                }
            }

        }
    }
}


display "---------------------------------------------"
display "Create: f_mutual (reciprocal nominations)    "
display "---------------------------------------------"
global max_num_mutual=10
forvalues jf=1/$max_num_mutual{
    capture drop f_mutual`jf'
    gen f_mutual`jf'=0
}
sort scid id
qui summarize scid
local num_scid=`r(max)'
local jid_end   = 0 
local jid_begin = 0
forvalues jscid=1/`num_scid'{ 
*local jscid=1
    qui sum id if scid==`jscid'
    local size_scid = `r(max)'
    local jid_begin = `jid_end' + 1
    local jid_end   = `jid_end' + `size_scid'
    di "School ID " `jscid' ", size " `size_scid'
    forvalues jrow=`jid_begin'/`jid_end'{
        local jmutual = 0
        forvalues jf=1/10{
	    if f`jf'[`jrow']!=0 {
	        *get the nomination
		local nominatedid=f`jf'[`jrow']
	        forvalues jff=1/20{
		    if f_nominatedby`jff'[`jrow']==f`jf'[`jrow'] {
		        local jmutual = `jmutual'+1
		        *di `jff' " " `nominatedid_row'
		        qui replace f_mutual`jmutual'=f`jf'[`jrow'] in `jrow'
                        continue, break
                    *di f`jF' " " `jjid' " " id[`jjid'] " " `jrow'
		    }
                }
            }

        }
    }
}

*get degree mutual
gen deg_mutual=0
sort scid id
qui summarize scid
local num_scid=`r(max)'
local jid_end   = 0 
local jid_begin = 0
forvalues jscid=1/`num_scid'{ 
*local jscid=1
    qui sum id if scid==`jscid'
    local size_scid = `r(max)'
    local jid_begin = `jid_end' + 1
    local jid_end   = `jid_end' + `size_scid'
    di "School ID " `jscid' ", size " `size_scid'
    forvalues jrow=`jid_begin'/`jid_end'{
        local jdeg_mutual = 0
        forvalues jf=1/10{
	    if f_mutual`jf'[`jrow']!=0 {
	        local jdeg_mutual = `jdeg_mutual'+1
            }
         }
	 qui replace deg_mutual=`jdeg_mutual' in `jrow'
    }
}

by scid: summarize deg_mutual
*** have to drop SCID=="001"--no mutual friends!

*number of friends in-degree and out-degree (re-indexed only)
gen int deg_in  = 0
gen int deg_out = 0
la var deg_in "Number of friends - in degree"
la var deg_out "Number of friends - out degree"

sort scid id
qui sum scid
local num_scid=`r(max)'
local jid_end   = 0 
local jid_begin = 0
forvalues jscid=1/`num_scid'{
    qui sum id if scid==`jscid'
    local size_scid = `r(max)'
    local jid_end   = `jid_end' + `size_scid'
    local jid_begin = `jid_end' - `size_scid' + 1
    di "School ID " `jscid' ", size " `size_scid'
    forvalues jid=`jid_begin'/`jid_end'{
        local nfi=0
        forvalues jf=1/10{
            if f`jf'[`jid']>0{
                *out-degree counter
                local nfi=`nfi'+1
                *in-degree counter
                *local findx=f`jf'[`jid']
                local findx=f`jf'[`jid']+`jid_begin'-1
                if (id[`findx']!=f`jf'[`jid']){
                    di "ERRROR IN THE SORTING"
                }
                local nfii=deg_in[`findx']+1
                qui replace deg_in=`nfii' in `findx'
            }
        }
        qui replace deg_out=`nfi' in `jid'
    }
}


tab deg_in deg_out
tab scid if deg_in==0 & deg_out==0


** RENAME
forvalues jf=1/10{
    generate f_nominate`jf'=f`jf'
    replace f`jf'=f_mutual`jf'
    drop f_mutual`jf'
}
rename deg_mutual deg



** "----------------------------------------------"
**  "f1-f9 reciprocal friends (undirected network)"
**  "f_nominatedby those who have nominated id    "
**  "deg - degree                                 "
**  "---------------------------------------------"

save "$clean_data_dir/d123-inhm.dta", replace



log close

