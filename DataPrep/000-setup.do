/*  THE FOLDERS TREE  */


*** WINDOWS ***
*Note in Windows backslash instead of forwardslash


*** UNIX ***
*UNIX ENVIRONMENT VARIABLES
global HOMEDIR    = "/home/anton/"
global SCRATCHDIR = "$HOMEDIR/Scratch/"

*** STATA
global stata_dir      = "$HOMEDIR/Dropbox/ABResearch/Nets/Code-web/DataPrep/"

*** ADD HEALTH DATA
global raw_data_dir   = "$HOMEDIR/Work/Data/AddHealth"
global clean_data_dir = "$raw_data_dir/Clean-Data/Code-web"
global data4python_dir= "$raw_data_dir/Data-for-Python/Code-web/"

*SCRATCH
global scratch_dir    = "$SCRATCHDIR/Dropbox/ABResearch/Nets/Code-web/DataPrep/"
global logs_dir       = "$scratch_dir/Logs/"
*global reg_dir        = "$scratch_dir/Regressions/"
*global graph_dir      = "$scratch_dir/Graphs/"
*global tables_dir     = "$scratch_dir/Tables/"



*** HOUSEWORK ***
set scheme s1color, permanently
shell mkdir -p $logs_dir
shell mkdir -p $clean_data_dir $data4python_dir

