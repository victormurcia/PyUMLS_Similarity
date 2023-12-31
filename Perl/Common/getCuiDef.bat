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

getCuiDef.pl - This program returns the definition of a concept
or a term.

=head1 SYNOPSIS

This program takes in a CUI or a term and returns its definitions. If a 
term is specified, the associated CUI is obtained using the sources 
specified in the configuration file. The definitions come from the entire 
UMLS. 

=head1 USAGE

Usage: getCuiDef.pl [OPTIONS] [CUI|TERM]

=head1 INPUT

=head2 Required Arguments:

=head3 [CUI|TERM}

Concept Unique Identifier (CUI) or a term from the Unified Medical 
Language System (UMLS)

=head2 Optional Arguments:

=head3 --config FILE

This is the configuration file. The format of the configuration 
file is as follows:

SAB :: <include|exclude> <source1, source2, ... sourceN>

REL :: <include|exclude> <relation1, relation2, ... relationN>

RELA :: <include|exclude> <rela1, rela2, ... relaN>  (optional)

For example, if we wanted to use the MSH vocabulary with only 
the RB/RN relations, the configuration file would be:
    
SAB :: include MSH
REL :: include RB, RN
RELA :: include inverse_isa, isa

or 

SAB :: include MSH
REL :: exclude PAR, CHD

If you go to the configuration file directory, there will 
be example configuration files for the different runs that 
you have performed.

=head3 --sab

Prints the source in which the definition comes from

=head3 --debug

Sets the debug flag for testing

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

=head4 --help

Displays the quick summary of program options.

=head4 --version

Displays the version information.

=head1 OUTPUT

List of CUIs that are associated with the input term

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

eval(GetOptions( "version", "help", "debug", "username=s", "password=s", "hostname=s", "database=s", "socket=s", "config=s", "sab")) or die ("Please check the above mentioned option(s).\n");


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

#  check the config
if( defined $opt_config) { 
    checkConfigFile($opt_config);
}

# At least 1 CUI should be given on the command line.
if(scalar(@ARGV) < 1) {
    print STDERR "No term was specified on the command line\n";
    &minimalUsageNotes();
    exit;
}

my $umls = "";
my %option_hash = ();

if(defined $opt_config) {
    $option_hash{"config"} = $opt_config;
}
if(defined $opt_verbose) {
    $option_hash{"verbose"} = $opt_verbose;
}
if(defined $opt_debug) {
    $option_hash{"debug"} = $opt_debug;
}
if(defined $opt_username) {
    $option_hash{"username"} = $opt_username;
}
if(defined $opt_driver) {
    $option_hash{"driver"}   = $opt_driver;
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

my $input = shift;
my $term  = $input;

my @c = ();
if($input=~/C[0-9]+/) {
    push @{$c}, $input;
    my $terms = $umls->getPreferredTerm($input); 
    $term = shift @{$terms}; 
}
else {
    $c = $umls->getConceptList($input);
}

my $printFlag = 0;

foreach my $cui (@{$c}) {

    my $defs = undef;
    
    if(defined $opt_sab) { 
	$defs = $umls->getCuiDef($cui, $opt_sab); 
    }
    else {
	$defs = $umls->getCuiDef($cui); 
    }

    if($#{$defs} >= 0) {
	print "The definition(s) of $term ($cui):\n";
	my $i = 1;
	foreach $def (@{$defs}) {
	    print "  $i. $def\n"; $i++;
	}
    }
    else {
	print "There are no definitions for $term ($cui)\n";
    }

    $printFlag = 1;

}

if(! ($printFlag) ) {
    print "There are no definitions for $input\n";
}

##############################################################################
#  check to make certain the config file contains the correct parameters
##############################################################################
sub checkConfigFile { 
    my $configfile = shift;
    open(CONFIG, $configfile) || die "Could not open config file ($config)\n";
    while(<CONFIG>) { 
	chomp;
	if($_=~/SABDEF/) {
	    print STDERR "SABDEF not valid parameter for getCuiDef.pl\n";
	    &minimalUsageNotes();
	    exit;
	}
	if($_=~/RELDEF/) { 
	    print STDERR "RELDEF not valid parameter for getCuiDef.pl\n";
	    &minimalUsageNotes();
	    exit;
	}
    }
}


##############################################################################
#  function to output minimal usage notes
##############################################################################
sub minimalUsageNotes {
    
    print "Usage: getCuiDef.pl [OPTIONS] [CUI|TERM] \n";
    &askHelp();
    exit;
}

##############################################################################
#  function to output help messages for this program
##############################################################################
sub showHelp() {

        
    print "This is a utility that takes as input a term \n";
    print "or a CUI and returns all of its definitions.\n\n";
  
    print "Usage: getCuiDef.pl [OPTIONS] [CUI|TERM]\n\n";

    print "Options:\n\n";

    print " --sab                   Prints the source in which the \n";
    print "                         definition originates\n\n";

    print "--debug                  Sets the debug flag for testing\n\n";

    print "--username STRING        Username required to access mysql\n\n";

    print "--password STRING        Password required to access mysql\n\n";

    print "--hostname STRING        Hostname for mysql (DEFAULT: localhost)\n\n";

    print "--database STRING        Database contain UMLS (DEFAULT: umls)\n\n";
    
    print "--socket STRING          Socket used by mysql (DEFAULT: /tmp.mysql.sock)\n\n";

    print "--config FILE            Configuration file\n\n";

    print "--version                Prints the version number\n\n";
 
    print "--help                   Prints this help message.\n\n";
}

##############################################################################
#  function to output the version number
##############################################################################
sub showVersion {
    print '$Id: getCuiDef.pl,v 1.17 2011/08/29 16:37:03 btmcinnes Exp $';
    print "\nCopyright (c) 2008, Ted Pedersen & Bridget McInnes\n";
}

##############################################################################
#  function to output "ask for help" message when user's goofed
##############################################################################
sub askHelp {
    print STDERR "Type getCuiDef.pl --help for help.\n";
}
    
__END__
:endofperl
@set "ErrorLevel=" & @goto _undefined_label_ 2>NUL || @"%COMSPEC%" /d/c @exit %ErrorLevel%
