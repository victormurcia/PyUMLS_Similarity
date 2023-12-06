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
#!/usr/local/bin/perl -w
#line 16

=head1 NAME

huge-sort.pl - Sort a --tokenlist of bigrams from huge-count.pl in alphabetical order.

=head1 SYNOPSIS

count.pl --tokenlist input.out input

huge-sort.pl --keep input.out 

=head1 DESCRIPTION

huge-sort.pl takes as input a duplicate bigram file generate 
by count.pl with --tokenlist option, counts the frequency of each 
bigram and sorts them in alphabetical order.  

The output file will be found in input-file.sorted.

This program is used internally by huge-count.pl. 

=head1 USGAE

huge-sort.pl [OPTIONS] SOURCE

=head1 INPUT

=head2 Required Arguments:

=head3 SOURCE

Input to huge-sort.pl should be a single flat file generated by 
count.pl with --tokenlist option. The result file is the input 
source file with '-sorted' extention,  SOURCE-sorted.

=head2 Optional Arguments:

=head4 --keep  

Switches ON the --keep option will keep the input unsorted file.

=head3 Other Options:

=head4 --help

Displays the help information.

=head4 --version

Displays the version information.

=head1 AUTHOR

Ying Liu, University of Minnesota, Twin Cities.
liux0395 at umn.edu

Ted Pedersen, University of Minnesota, Duluth.
tpederse at umn.edu

=head1 COPYRIGHT

Copyright (C) 2009-2011, Ying Liu and Ted Pedersen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

=cut


###############################################################################
#-----------------------------------------------------------------------------
#                              Start of program
#-----------------------------------------------------------------------------
###################################################################################

use Getopt::Long;

# first check if no commandline options have been provided... in which case
# print out the usage notes!
if ( $#ARGV == -1 )
{
    &minimalUsageNotes();
    exit;
}

# now get the options!
GetOptions( "keep", "version", "help" );

if ( defined $opt_keep )    { $opt_keep = 1 }
else                          { $opt_keep = 0 }

# if help has been requested, print out help!
if ( defined $opt_help )
{
    $opt_help = 1;
    &showHelp();
    exit;
}

# if version has been requested, show version!
if ( defined $opt_version )
{
    $opt_version = 1;
    &showVersion();
    exit;
}


my $file = $ARGV[0];
 
open(FILE, "<$file") or die("Error: cannot open file '$file'\n");       

# get the frequency of each unique bigrams  
my %bigrams = ();
my %w1 = ();
my %w2 = ();
while (my $line = <FILE>)
{
	chop ($line);
	$bigrams{$line}++;		
	my @words = split('<>', $line);
	$w1{$words[0]}++; 
	$w2{$words[1]}++; 
}
close FILE;


# sort the bigrams in the alphabet order
my $sorted = "$file" . "-sorted";
open(SORT, ">$sorted") or die("Error: cannot open file '$sorted'\n");

foreach my $b (sort (keys %bigrams))
{
	print SORT "$b$bigrams{$b} ";		
	my @words = split('<>', $b);
	print SORT "$w1{$words[0]} $w2{$words[1]}\n";	
}
close SORT;	

# remove the unsorted duplicated bigrams 
if ($opt_keep == 0)
{
	system ("rm $file");
} 

#-----------------------------------------------------------------------------
#                       User Defined Function Definitions
#-----------------------------------------------------------------------------

# function to output a minimal usage note when the user has not provided any
# commandline options
sub minimalUsageNotes
{
    print STDERR "Usage: huge-sort.pl [OPTIONS] SOURCE\n";
    askHelp();
}

# function to output "ask for help" message when the user's goofed up!
sub askHelp
{
    print STDERR "Type huge-sort.pl --help for help.\n";
}

# function to output help messages for this program
sub showHelp
{
    print "\n";
    print "Usage: huge-sort.pl [OPTIONS] SOURCE\n\n";
    print "huge-sort.pl takes a file created by huge-count.pl --tokenlist\n";
    print "(or count.pl --tokenlist) as input, and determines the frequency\n";
    print "of each unique bigram. These bigrams are displayed in alphabetical order.\n";

    print "OPTIONS:\n\n";

    print "  --keep             keep the unsorted file\n";
    print "                     The default is to delete the unsorted file. \n\n";

    print "  --help             Prints this help message.\n\n";
    print "  --version          Prints this version message.\n\n";
}

# function to output the version number
sub showVersion
{
    print STDERR 'huge-sort.pl $Id: huge-sort.pl,v 1.10 2011/03/31 23:04:04 tpederse Exp $';
    print STDERR "\nCopyright (C) 2009-2011, Ying Liu\n";

}


__END__
:endofperl
@set "ErrorLevel=" & @goto _undefined_label_ 2>NUL || @"%COMSPEC%" /d/c @exit %ErrorLevel%
