@rem = '--*-Perl-*--
@set "ErrorLevel="
@if "%OS%" == "Windows_NT" @goto WinNT
@perl -x -S "%0" %1 %2 %3 %4 %5 %6 %7 %8 %9
@set ErrorLevel=%ErrorLevel%
@goto endofperl
:WinNT
@perl -x -S %0 %*
@set ErrorLevel=%ErrorLevel%
@if NOT "%COMSPEC%" == "%SystemRoot%\system32\cmd.exe" @goto endofperl
@if %ErrorLevel% == 9009 @echo You do not have Perl in your PATH.
@goto endofperl
@rem ';
#!perl
#line 16
##########################################################################
# R program to perform statistical analysis of two files from the umls-
# similarity.pl program 
##########################################################################
#
# This program does the following : 
#  Takes in a file from sim2r.pl and calculates the
#  the pearson, spearman and kendall correlations between 
#  the gold standard and the various measures
##########################################################################
# This is how I run the program:
#     
#     R --slave --args filename <SignificanceTesting.r 
#
##########################################################################

#  get the files from the command line
n1 <- commandArgs()
n <- n1[length(n1)]
tmp<-strsplit(n,",")
file1 <- tmp[[1]][1]; 

data <- read.table(file1,header=TRUE,sep=",");

headers <- names(data);

t <- c("measure          ", "pearsons", "spearman", "kendall");

print(t, quote=F);

for (i in 3:length(headers)) {

    p <- cor(data$gold,data[i],method="pearson"); 
    s <- cor(data$gold,data[i],method="spearman");
    k <- cor(data$gold,data[i],method="kendall"); 
    a <- c(headers[i], p, s, k);
    print (a, quote=F); 
   
}
__END__
:endofperl
@set "ErrorLevel=" & @goto _undefined_label_ 2>NUL || @"%COMSPEC%" /d/c @exit %ErrorLevel%
