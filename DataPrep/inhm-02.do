/*
 *     CONTEXTUAL FILES
 */

/*Avaliable data
Waves I and II
Excise Tax on Cigarettes per Cigarette Pack (in Cents)

Wave III
Average price for pack of cigarettes, in cents, 1994
Average price for pack of cigarettes, in cents, 1995
Average price for pack of cigarettes, in cents, 1996
Average price for pack of cigarettes, in cents, 2001 */


* Housekeeping 
clear
clear mata
set more off
set memory 2g
set matsize 800
do 000-setup
capture log close
log using "$logs_dir/inhm-02.txt", replace text
set scheme s1color, permanently
set graphics on

* -----------------------------------------------------------------------------
*Wave I Contextual Files Data : EXCISE TAX 
* -----------------------------------------------------------------------------
quietly{
use "$raw_data_dir/ICPSR_27024/DS0001/27024-0001-Data-REST.dta", clear
do "$raw_data_dir/ICPSR_27024/DS0001/27024-0001-Supplemental_syntax-REST.do"
}
keep AID SCT93A68 SCT93A69 SGT93A70 SCT90A71 SCT95A72 SGT94A73 SGT94A74 SGT94A75 SGT94A76 SGT94A77 SGT94A78 SGT94A79
sort AID
save "$clean_data_dir/d4-context.dta", replace

*merge
use "$clean_data_dir/d123-inhm.dta", clear
sort AID

merge AID using "$clean_data_dir/d4-context.dta", _merge(merge_tax)
tab merge_tax
drop if merge_tax==2
*drop merge_tax

capture drop avg_st_smoking death_rate tax
ren SCT93A68 avg_st_smoking
*proxy for smoking
ren SCT90A71 death_rate
ren SCT95A72 tax
la var tax "Excise (state) tax on cigarettes per cigarette pack (in cents)"
save "$clean_data_dir/tmp.dta", replace


*Wave III Contextual Files Data : AVG PRICE OF CIGARETTES ---------------------
quietly{
use "$raw_data_dir/ICPSR_27024/DS0003/27024-0003-Data-REST.dta", clear
do "$raw_data_dir/ICPSR_27024/DS0003/27024-0003-Supplemental_syntax-REST.do"
}
capture drop avgp94 avgp95 price
capture drop price94 price95 price_avg_9495
des SIT94145 SIT95145 
rename SIT94145 price94
rename SIT95145 price95
gen price_avg_9495=(price94+price95)/2
keep AID price94 price95 price_avg_9495
sort AID
save "$clean_data_dir/d5-context.dta", replace

use "$clean_data_dir/tmp.dta", clear
sort AID

merge AID using "$clean_data_dir/d5-context.dta", _merge(merge_price)
tab merge_price
drop if merge_price==2
*drop merge_price
save "$clean_data_dir/d12345-inhm.dta", replace


*END -----------------------------------------------------------
log close

