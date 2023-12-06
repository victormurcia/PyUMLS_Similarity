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
#!/usr/bin/perl 
#line 16

=head1 NAME

sim2r.pl - This program converts a series of umls-similarity output to 
    R format in order to run the SignificanceTesting.r program. 

=head1 SYNOPSIS

This program converts output generated by umls-similarity.pl to 
R format in order to run the SignificanceTesting.r program

=head1 USAGE

Usage: sim2r.pl GOLD_FILE [FILE1 FILE2 ...]

=head1 INPUT

=head2 Required:

=head3 GOLD_FILE 

This is the gold standard. Usually this is the data that has 
manually been score by human annotaters. This is what the 
SignificanceTesting.r program is going to use to determine 
the correlation against for the other files.

The format of this file is the same as output format of the 
umls-similarity.pl program.

score<>cui1<>cui2
score<>term1<>term2
...


=head3 FILE1 FILE2 ...

These are the output files generated by the umls-similarity.pl 
program. The header information in R will be the name of the 
file.

=head2 Options:

=head3 --word

The format of hte input files contains words rather than CUIs or is not 
a umls-simmilarity.pl output file.

=head3 --help

Displays the quick summary of program options.

=head3 --version

Displays the version information.

=head1 OUTPUT

A cvs file that can be read by the SignificanceTesting.r program


=head1 SYSTEM REQUIREMENTS

=over

=item * Perl (version 5.8.5 or better) - http://www.perl.org

=back

=head1 CONTACT US
   
  If you have any trouble installing and using UMLS-Similarity, 
  please contact us via the users mailing list :
    
      umls-similarity@yahoogroups.com
     
  You can join this group by going to:
    
      http://tech.groups.yahoo.com/group/umls-similarity/
     
  You may also contact us directly if you prefer :
    
      Bridget T. McInnes: bthomson at cs.umn.edu 

      Ted Pedersen : tpederse at d.umn.edu

=head1 AUTHOR

 Bridget T. McInnes, University of Minnesota

=head1 COPYRIGHT

Copyright (c) 2007-2011,

 Bridget T. McInnes, University of Minnesota
 bthomson at cs.umn.edu
    
 Ted Pedersen, University of Minnesota Duluth
 tpederse at d.umn.edu


 Siddharth Patwardhan, University of Utah, Salt Lake City
 sidd@cs.utah.edu
 
 Serguei Pakhomov, University of Minnesota Twin Cities
 pakh0002@umn.edu

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to:

 The Free Software Foundation, Inc.,
 59 Temple Place - Suite 330,
 Boston, MA  02111-1307, USA.

=cut

###############################################################################

#                               THE CODE STARTS HERE
###############################################################################

#                           ================================
#                            COMMAND LINE OPTIONS AND USAGE
#                           ================================

use UMLS::Interface;
use Getopt::Long;

eval(GetOptions( "version", "help", "word")) or die ("Please check the above mentioned option(s).\n");

#  if help is defined, print out help
if( defined $opt_help ) {
    $opt_help = 1;
    &showHelp();
    exit;
}

#  if version is requested, show version
if( defined $opt_version ) {
    $opt_version = 1;
    &showVersion();
    exit;
}

# At least 2 terms should be given on the command line.
if( !(defined $opt_infile) and (scalar(@ARGV) < 2) ) {
    print STDERR "At least 2 terms or CUIs should be given on the \n";
    print STDERR "command line or use the --infile option\n";
    &minimalUsageNotes();
    exit;
}


my $goldfile = shift;
open(GOLD, $goldfile) || die "Could not open file: $goldfile\n";

my %gold = (); my $gcounter = 0;
while(<GOLD>) { 
    chomp;
    my ($score, $t1, $t2) = split/<>/;

    my $cui1 = ""; my $cui2 = "";

    if(defined $opt_word) { 
	$cui1 = $t1;
	$cui2 = $t2;
    }
    else { 
	$t1=~/(C[0-9][0-9][0-9][0-9][0-9][0-9][0-9])/;
	$cui1 = $1;

	$t2=~/(C[0-9][0-9][0-9][0-9][0-9][0-9][0-9])/;
	$cui2 = $1;
    }
    
    $gold{"$cui1 $cui2"} = $score;
    $gcounter++;
}

print STDERR "TOTAL PAIRS IN GOLD STANDARD: $gcounter\n";

my %remove  = ();
my %hash    = ();
my @headers = ();
my %terms   = ();

foreach my $file (@ARGV) { 
    open(FILE, $file) || die "Could not open file: $file\n";
    
    $file=~/\/?(.*?)$/;
    my $header = $1;

    push @headers, $header;
    my $counter = 0;
    while(<FILE>) { 
	chomp;
	my ($score, $t1, $t2) = split/<>/;

	my $cui1 = ""; my $cui2 = "";
	
	if(defined $opt_word) { 
	    $cui1 = $t1; 
	    $cui2 = $t2;
	}
	else {
	    $t1=~/(C[0-9][0-9][0-9][0-9][0-9][0-9][0-9])/;
	    $cui1 = $1;
	
	    $t2=~/(C[0-9][0-9][0-9][0-9][0-9][0-9][0-9])/;
	    $cui2 = $1;
	}

	$hash{$header}{"$cui1 $cui2"} = $score;
	$counter++;

	if($score < 0) { $remove{"$cui1 $cui2"}++; }
	
	$t1=~s/\,//g; $t2=~s/\,//g;
	$t1=~s/\'//g; $t2=~s/\'//g;
	$terms{"$cui1 $cui2"} = "$t1 $t2";
    }
    print STDERR "TOTAL PAIRS IN $header: $counter\n";
}

my $str_headers = join ",", @headers;
print "pair,gold,$str_headers\n";

my $counter = 0; my $discard = 0;
foreach my $pair (sort keys %gold) {

    if(exists $remove{$pair}) { 
	$discard++; 
	next; 
    }

    my $output = "$terms{$pair},$gold{$pair},";
    foreach my $header (@headers) {
	$output.= "$hash{$header}{$pair},";
    } chop $output;
    
    print "$output\n";
    $counter++;

}

print STDERR "TOTAL PAIRS BEING PROCESSED: $counter\n";

print STDERR "TOTAL PAIRS IGNORED: $discard\n";

##############################################################################
#  function to output minimal usage notes
##############################################################################
sub minimalUsageNotes {
    
    print "Usage: sim2r.pl [OPTIONS] GOLD_FILE [FILE1 FILE2 ...]\n";
    &askHelp();
    exit;
}

##############################################################################
#  function to output help messages for this program
##############################################################################
sub showHelp() {
        
    print "This is a utility converts output generated by \n";
    print "umls-similarity.pl to R format in order to run the \n";
    print "SignificanceTesting.r program\n\n";
  
    print "Usage: sim2r.pl [OPTIONS] GOLD_FILE [FILE1 FILE2...]\n\n";

    print "Options:\n\n";

    print "--word                   The format of the input files contains words\n";
    print "                         rathar than CUIs or is not a umls-similarity.pl\n";
    print "                         output file.\n\n";

    print "--version                Prints the version number\n\n";
    
    print "--help                   Prints this help message.\n\n";
    
}

##############################################################################
#  function to output the version number
##############################################################################
sub showVersion {
    print '$Id: sim2r.pl,v 1.7 2011/08/29 22:56:31 btmcinnes Exp $';
    print "\nCopyright (c) 2007-2011, Ted Pedersen & Bridget McInnes\n";
}

##############################################################################
#  function to output "ask for help" message when user's goofed
##############################################################################
sub askHelp {
    print STDERR "Type sim2r.pl --help for help.\n";
}
    

__END__
:endofperl
@set "ErrorLevel=" & @goto _undefined_label_ 2>NUL || @"%COMSPEC%" /d/c @exit %ErrorLevel%
