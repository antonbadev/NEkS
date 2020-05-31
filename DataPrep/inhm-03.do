/*
 *  GENERATE VAR NAMES
 *  CHECK MISSING AT RANDOM - TAX,PRICE,INCOME,INCOME_FAMILY
 *  LOGITS
 */


* Housekeeping 
clear
clear mata
set more off
set memory 2g
set matsize 800
do 000-setup
capture log close
log using "$logs_dir/inhm-03.txt", replace text
set scheme s1color, permanently
set graphics on


use "$clean_data_dir/d12345-inhm.dta", clear

*size schools
capture drop nscid
gen int nscid=1
by scid, sort: replace nscid=sum(nscid)
by scid, sort: replace nscid=nscid[_N]
*drop nscid_t nscid_tt


*-------------------------------------------------------------------------------
* TOBACCO & MARIJUANA
*-------------------------------------------------------------------------------
capture drop tobacco tobacco_30 marijuana marijuana_30
des H1TO1 H1TO5
gen int tobacco=0
gen int tobacco_30=0
la var tobacco "Ever smoked tobacco H1TO1"
la var tobacco_30 "Number of days smoked tobacco in the last 30 days >=1 H1TO5"
replace tobacco=1 if H1TO1==1
replace tobacco_30=1 if (H1TO5!=. & H1TO5>0)

des H1TO31 H1TO32
gen int marijuana=0
gen int marijuana_30=0
la var marijuana "Ever smoked marijuana H1TO31"
la var marijuana_30 "Number of times smoked marijuana in the last 30 days >=1 H1TO32"
replace marijuana=1 if (H1TO31!=. & H1TO31>0)
replace marijuana_30=1   if (H1TO32!=. & H1TO32>0)

*-------------------------------------------------------------------------------
* INCOME, WORK, ALLOWANCES 
*-------------------------------------------------------------------------------
des H1EE4 H1EE5 H1EE6 H1EE7 H1EE8
by scid, sort: sum H1EE4 H1EE5 H1EE6 H1EE7 H1EE8
*by scid, sort: count if H1EE5>0
*by scid, sort: count if H1EE7>0

capture drop income income_schyr income_summer income_allowances summer_dummy summer_month_dummy
gen income_schyr     =H1EE5
gen income_summer    =H1EE7
gen income_allowances=H1EE8

count if income_allowances==.
count if income_schyr==.
count if income_summer==.

foreach jvar in schyr summer allowances{
    replace income_`jvar'=0 if (income_`jvar'==.)
}
gen float income=0
gen summer_dummy=0
gen summer_month_dummy=0
replace summer_month_dummy=1 if (IMONTH>5 & IMONTH<9)
replace summer_dummy=1 if (summer_month_dummy==1 & SCH_YR==0)
replace income=income_schyr+income_allowances if (summer_dummy==0)
replace income=income_summer+income_allowances if (summer_dummy==1)
capture drop ln_income income_capped_400
gen ln_income=log(1.0+income)
*BY SCID
*by scid, sort: egen byscid_avg_ln_income=mean(ln_income)
*gen dev_ln_income = ln_income-byscid_avg_ln_income
*OVERALL
qui sum ln_income
gen avg_ln_income=`r(mean)'
gen dev_ln_income = ln_income-avg_ln_income

*gen income_capped_400=income
*replace income_capped_400=400 if income>400

*-------------------------------------------------------------------------------
* HOUSEHOLD INCOME AND SMOKING 
*-------------------------------------------------------------------------------
capture drop hhincome income_hh
des PA55
gen hhincome=PA55
count if hhincome==.
count if hhincome<1

capture drop hhsmokes
des PA63 PA64
gen byte hhsmokes=0
replace hhsmokes=1 if PA63==1
count if hhsmokes==.


*-------------------------------------------------------------------------------
* PRICE 
*-------------------------------------------------------------------------------
foreach jvar in price price2 tax2 taxincome priceincome{
    capture drop `jvar'
}
gen price=price95
*MISSING VALUES - tax (7/3220), prices (600/3220)
*generate values for the missing price and tax data (avg for the school)
foreach jvar in tax price{
    capture drop avg_scid_`jvar'
    by scid, sort: egen avg_scid_`jvar'=mean(`jvar')
    replace `jvar'=avg_scid_`jvar' if `jvar'==.
    *BY SCID
    *gen dev_`jvar' = `jvar'-avg_scid_`jvar'
    *OVERALL
    qui sum `jvar'
    gen dev_`jvar' = `jvar'-`r(mean)'

}

*NOTE. Change the scale for price, tax, and income.
gen price_level =price
gen tax_level   =tax
gen income_level=income
replace price   =dev_price
replace tax     =dev_tax
replace income  =dev_ln_income


/*-------------------------------------------------------------------------------
* EDUCATION 

PA12
Business/trade/voc school instead of HS     3
HS graduate                                 4
GED completed                               5
Business/trade/voc after HS                 6
College/didn't graduate                     7
Graduate from college/uni                   8
Prof training beyond 4 years in college     9
HS dummy 4,6,7
CO dummy 8,9
*-------------------------------------------------------------------------------
*/

capture drop mom_hs mom_co
gen mom_hs     =0
gen mom_co     =0
replace mom_hs=1 if (PA12==4 | PA12==6 | PA12==7)
replace mom_co=1 if (PA12==8 | PA12==9)



/*------------------------------------------------------------------------------
* Compress Asians,Hispanic, and Others into a common group AHO
*-------------------------------------------------------------------------------
*/

replace race=3 if race>3
compress

***drop the biggest school !!!
drop if SCID=="077"
/*reindex scid
rename scid scid_saturated
by grades scid_saturated, sort: gen scid_tmp = (_n==1)
gen int scid = sum(scid_tmp)
drop scid_tmp*/


/* SAVE final data */ 
sort scid id
save "$clean_data_dir/inhm-final.dta", replace
use "$clean_data_dir/inhm-final.dta", clear

*for debug/replication purpuse
outsheet scid id SCID AID using "$clean_data_dir/dataid.csv" , comma replace

local vars_compact scid id f* age grade* sex race deg* price income mom_* hhsmoke tobacco* marijuana*
keep `vars_compact'
save "$clean_data_dir/inhm-final-compact.dta", replace



END inhm-03

/* CHECKS */
*check if dmom_hs123 are different
gen dmom_hs1     =0
gen dmom_hs2     =0
gen dmom_hs3     =0
replace dmom_hs1=1 if (PA12==3)
replace dmom_hs2=1 if (PA12==4)
replace dmom_hs3=1 if (PA12==5)
keep if dmom_hs==1

*check if dmom_co_n are different than those who completed college
gen dmom_co_n   =0
replace dmom_co_n=1 if (PA12==7)
keep if dmom_co==1 | dmom_co_n==1


