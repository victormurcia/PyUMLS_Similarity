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

findCuiDepth.pl - This program returns the minimum and maximum depth 
of a given CUI or term.

=head1 SYNOPSIS

This program takes in a CUI or a term and returns its minimum and 
maximum depth.

=head1 USAGE

Usage: findCuiDepth.pl [OPTIONS] [TERM|CUI]

=head1 INPUT

=head2 Required Arguments:

=head3 [TERM|CUI]

Concept Unique Identifier (CUI) or a term from the Unified 
Medical Language System (UMLS)

=head2 Optional Arguments:

=head3 --config FILE

This is the configuration file. The format of the configuration 
file is as follows:

SAB :: <include|exclude> <source1, source2, ... sourceN>

REL :: <include|exclude> <relation1, relation2, ... relationN>

RELA :: <include|exclude> <rela1, rela2, ... relaN> (optional)

For example, if we wanted to use the MSH vocabulary with only 
the RB/RN relations, the configuration file would be:

SAB :: include MSH
REL :: include RB, RN
RELA :: include isa, inverse_isa

or 

SAB :: include MSH
REL :: exclude PAR, CHD

If you go to the configuration file directory, there will 
be example configuration files for the different runs that 
you have performed.

=head3 --debug

This sets the debug flag for testing

=head3 --infile FILE

This option takes a list of CUIs or TERMs and returns their 
depth. Note one CUI or TERM per line is the expected format.

=head3 --minimum

Finds just the minimum CUI depth

=head3 --maximum

Finds just the maximum CUI depth

=head3 --username STRING

Username is required to access the umls database on MySql
unless it was specified in the my.cnf file at installation

=head3 --password STRING

Password is required to access the umls database on MySql
unless it was specified in the my.cnf file at installation

=head3 --hostname STRING

Hostname where mysql is located. DEFAULT: localhost

=head3 --socket STRING

The socket your mysql is using. DEFAULT: /tmp/mysql.sock

=head3 --database STRING        

Database contain UMLS DEFAULT: umls

=head3 --realtime

This option will not create a database of the path information
for all of concepts in the specified set of sources and relations 
in the config file but obtain the information for just the 
input concept

=head3 --forcerun

This option will bypass any command prompts such as asking 
if you would like to continue with the index creation. 

=head3 --verbose

This option will print out the table information to the 
config file that you specified.

=head3 --debugpath FILE

This option prints out the path information for debugging 
purposes. This option is only really available with the 
--reatime option because otherwise the path information is 
stored in the database. You can get this information in a 
file if you use the --verbose option while creating the index. 

=head3 --cuilist FILE

This option takes in a file containing a list of CUIs (one CUI 
per line) and stores only the path information for those CUIs 
rather than for all of the CUIs given the specified set of 
sources and relations

=head3 --help

Displays the quick summary of program options.

=head3 --version

Displays the version information.

=head1 OUTPUT

The minimum depth of a given CUI or term

=head1 CONFIGURATION FILE

There exist a configuration files to specify which source and what 
relations are to be used. The default source is the Medical Subject 
Heading (MSH) vocabulary and the default relations are the PAR/CHD 
relation. 

The format of the configuration file is as follows:

SAB :: <include|exclude> <source1, source2, ... sourceN>

REL :: <include|exclude> <relation1, relation2, ... relationN>

The SAB and REL are for specifing what sources and relations 
should be used when traversing the UMLS. For example, if we 
wanted to use the MSH vocabulary with only the RB/RN relations, 
the configuration file would be:

SAB :: include MSH
REL :: include RB, RN

or if we wanted to use MSH and use any relation except for PAR/CHD, 
the configuration would be:

SAB :: include MSH
REL :: exclude PAR, CHD

An example of the configuration file can be seen in the samples/ directory. 

=head1 SYSTEM REQUIREMENTS

=over

=item * Perl (version 5.8.5 or better) - http://www.perl.org

=back

=head1 AUTHOR

 Bridget T. McInnes, University of Minnesota

=head1 COPYRIGHT

Copyright (c) 2007-2009,

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
# catch, abort and print the message for unknown options specified
eval(GetOptions( "version", "help", "username=s", "password=s", "hostname=s", "database=s", "socket=s", "config=s", "forcerun", "debug", "verbose", "debugpath=s", "cuilist=s", "realtime", "minimum", "maximum", "infile=s")) or die ("Please check the above mentioned option(s).\n");


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

# At least 1 CUI should be given on the command line.
if( (!defined $opt_infile) and (scalar(@ARGV) < 1) ) {
    print STDERR "No term was specified on the command line\n";
    &minimalUsageNotes();
    exit;
}

my $umls = "";

my %option_hash = ();

if(defined $opt_realtime) {
    $option_hash{"realtime"} = $opt_realtime;
}
if(defined $opt_config) {
    $option_hash{"config"} = $opt_config;
}
if(defined $opt_forcerun) {
    $option_hash{"forcerun"} = $opt_forcerun;
}
if(defined $opt_debug) {
    $option_hash{"debug"} = $opt_debug;
}
if(defined $opt_verbose) {
    $option_hash{"verbose"} = $opt_verbose;
}
if(defined $opt_debugpath) {
    $option_hash{"debugpath"} = $opt_debugpath;
}
if(defined $opt_cuilist) {
    $option_hash{"cuilist"} = $opt_cuilist;
}
if(defined $opt_username) {
    $option_hash{"username"} = $opt_username;
}
if(defined $opt_driver) {
    $option_hash{"driver"}   = $opt_driver; #"mysql";
}
if(defined $opt_database) {
    $option_hash{"database"} = $opt_database;
}
if(defined $opt_password) {
    $option_hash{"password"} = $opt_password;
}
if(defined $opt_hostname) {
    $option_hash{"hostname"} = $opt_hostname;
}
if(defined $opt_socket) {
    $option_hash{"socket"}   = $opt_socket;
}

$umls = UMLS::Interface->new(\%option_hash); 
die "Unable to create UMLS::Interface object.\n" if(!$umls);

#  get the relations from the configuration file
my $configrel = $umls->getRelString();
$configrel=~/(REL) (\:\:) (include|exclude) (.*?)$/;
my $relationstring = $4; 

#  check to make certain the configuration file only contains
#  heirarchical relations (PAR/CHD or RB/RN).
my @relations = split/\s*\,\s*/, $relationstring; 
foreach my $rel (@relations) { 
  if(! ($rel=~/(PAR|CHD|RB|RN)/) ) { 
    print STDERR "The findCuiDepth.pl program only supports heirarchical relations (PAR/CHD or RB/RN).\n";
    &minimalUsageNotes();
    exit;
  } 
}

my @inputarray = ();

if(defined $opt_infile) {
    open(FILE, $opt_infile) || die "Could not open infile : $opt_infile\n";
    while(<FILE>) {
	chomp;
	$_=~s/^\s+//g;
	$_=~s/\s+$//g;
	push @inputarray, $_;
    }
}
else {
    my $input = shift;
    push @inputarray, $input;
}

foreach my $input (@inputarray) {

    if($input=~/^\s*$/) { next; }

    my $term  = $input;

    my @c = ();
    if($input=~/C[0-9]+/) {
	push @{$c}, $input;
	my $termlist = $umls->getTermList($input);
	$term = shift @{$termlist};
    }
    else {
	$c = $umls->getConceptList($input);
    }

    my $printFlag = 0;

    foreach my $cui (@{$c}) {
	
	#  make certain cui exists in this view
	if(! ($umls->exists($cui)) ) {
	    next; 
	}
	
	#  get the minimum depth
	if(defined $opt_minimum) {
	    my $min = $umls->findMinimumDepth($cui);
	    print "The minimum depth of $term ($cui) is $min\n";
	}
	#  get the maximum depth
	elsif(defined $opt_maximum) {
	    my $max = $umls->findMaximumDepth($cui);
	    print "The maximum depth of $term ($cui) is $max\n";
	}
	else {
	    my $min = $umls->findMinimumDepth($cui);
	    print "The minimum depth of $term ($cui) is $min\n";
	    
	    my $max = $umls->findMaximumDepth($cui);
	    print "The maximum depth of $term ($cui) is $max\n";
	}
	
	$printFlag = 1; 
    }
    
    if(! ($printFlag) ) {
	print "$input does not exist in this view of the UMLS.\n";
    }
}

##############################################################################
#  function to output minimal usage notes
##############################################################################
sub minimalUsageNotes {
    
    print "Usage: findCuiDepth.pl [OPTIONS] [TERM|CUI] \n";
    &askHelp();
    exit;
}

##############################################################################
#  function to output help messages for this program
##############################################################################
sub showHelp() {

        
    print "This is a utility that takes as input a CUI or a TERM\n";
    print "and returns its minimum depth.\n\n";
  
    print "Usage: findCuiDepth.pl [OPTIONS] [TERM|CUI]\n\n";

    print "Options:\n\n";

    print "--debug                  This option prints out  the debug\n";
    print "                         information.\n\n";
    
    print "--infile                 This option takes a list of CUIs or\n";
    print "                         TERMS and returns their depth. \n\n";

    print "--minimum                Returns the minimum depth (DEFAULT)\n\n";
    
    print "--maximum                Returns the maximum depth\n\n";

    print "--username STRING        Username required to access mysql\n\n";

    print "--password STRING        Password required to access mysql\n\n";

    print "--hostname STRING        Hostname for mysql (DEFAULT: localhost)\n\n";

    print "--database STRING        Database contain UMLS (DEFAULT: umls)\n\n";
    
    print "--socket STRING          Socket used by mysql (DEFAULT: /tmp.mysql.sock)\n\n";

    print "--config FILE            Configuration file\n\n";
   
    print "--realtime               This option will not create a database of the\n";
    print "                         path information for all of concepts but just\n"; 
    print "                         obtain the information for the input concept\n\n";

    print "--debug                  Sets the debug flag for testing.\n\n";

    print "--forcerun               This option will bypass any command \n";
    print "                         prompts such as asking if you would \n";
    print "                         like to continue with the index \n";
    print "                         creation. \n\n";

    print "--debugpath FILE         This option prints out the path\n";
    print "                         information for debugging purposes\n\n";
  
    print "--verbose                This option prints out the table \n";
    print "                         information to a file in your\n";
    print "                         specified config directory\n\n";

    print "--cuilist FILE           This option takes in a file containing a \n";
    print "                         list of CUIs (one CUI per line) and stores\n";
    print "                         only the path information for those CUIs\n"; 
    print "                         rather than for all of the CUIs\n\n";

    print "--version                Prints the version number\n\n";
 
    print "--help                   Prints this help message.\n\n";
}

##############################################################################
#  function to output the version number
##############################################################################
sub showVersion {
    print '$Id: findCuiDepth.pl,v 1.16 2011/08/29 16:37:03 btmcinnes Exp $';
    print "\nCopyright (c) 2008, Ted Pedersen & Bridget McInnes\n";
}

##############################################################################
#  function to output "ask for help" message when user's goofed
##############################################################################
sub askHelp {
    print STDERR "Type findCuiDepth.pl --help for help.\n";
}
    
__END__
:endofperl
@set "ErrorLevel=" & @goto _undefined_label_ 2>NUL || @"%COMSPEC%" /d/c @exit %ErrorLevel%
