"""
PyUMLS_Similarity Package

This Python package provides tools for calculating semantic similarity and finding shortest paths between concepts
in the Unified Medical Language System (UMLS). It leverages external Perl scripts and MySQL databases to perform 
these operations, integrating them seamlessly into a Python environment.

Modules:
    - find_shortest_path_from_file: Executes a Perl script to find the shortest path between CUI or term pairs.
    - combine_similarity_results: Combines similarity results from multiple measures into a single DataFrame.
    - merge_results: Merges the result DataFrames from different tasks.
    - run_concurrently: Executes multiple tasks concurrently using multithreading.

Functions:
    - find_shortest_path_from_file(self, pairs, forcerun=True, verbose=False):
        Executes a Perl script to find the shortest path between CUI or term pairs.
        
    - combine_similarity_results(self, all_results, cui_pairs):
        Combines the similarity results from multiple measures into a single DataFrame.
        
    - merge_results(self, results, use_cuis=True):
        Merges the result DataFrames from different tasks.
        
    - run_concurrently(self, tasks):
        Executes multiple tasks concurrently using multithreading.

Usage:
    1. Ensure that MySQL database credentials and Perl scripts are correctly set up.
    2. Define tasks with appropriate functions and arguments.
    3. Use run_concurrently to execute tasks and merge results.
    4. Concept pairs can be given in terms of CUIs or terms.

Example:
    tasks = [
        {'function': 'similarity', 'arguments': (cui_pairs, measures)},
        {'function': 'shortest_path', 'arguments': (cui_pairs,)},
        {'function': 'lcs', 'arguments': (cui_pairs,)}
    ]
    final_df = self.run_concurrently(tasks)

Requirements:
    - Python 3.10
    - pandas
    - tqdm
    - concurrent.futures
    - re
    - subprocess
    - MySQL database with UMLS data
    - Perl scripts for similarity and shortest path calculations

Author:
    Victor M. Murcia Ruiz <victor.murciaruiz@va.gov>

License:
    MIT License

"""
import subprocess
import os
import tempfile
import pandas as pd
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class PyUMLS_Similarity:
    def __init__(self, mysql_info, perl_bin_path="", work_directory=""):
        self.perl_bin_path = perl_bin_path if perl_bin_path else r"C:\Strawberry\perl\bin\perl.exe"
        self.mysql_info = mysql_info
        self.work_directory = work_directory if work_directory else r'C:\Strawberry\perl\site\bin'

    @staticmethod
    def is_cui(input_str):
        return re.match(r"C\d+", input_str) is not None

    def detect_cui_or_term(self, cui_pairs):
        """
        Detect whether the cui_pairs contain CUIs or terms.
        
        Args:
            cui_pairs (list of tuples): A list of tuples containing pairs of CUIs or terms.
        
        Returns:
            bool: True if cui_pairs contain CUIs, False if they contain terms.
        """
        def is_cui(value):
            """Helper function to determine if a value is a CUI."""
            return isinstance(value, str) and value.startswith('C') and value[1:].isdigit()
        
        # Check the first pair to determine the type
        pair1, pair2 = cui_pairs[0]
        return is_cui(pair1) and is_cui(pair2)

    def similarity(self, cui_pairs, measures=['lch'], precision=4, forcerun=True, verbose=False):
        """
        Calculate similarity for each measure in a concurrent manner.

        Args:
            cui_pairs (list of tuple): A list of tuples, where each tuple contains two CUIs for comparison.
            measures (list of str): A list of strings representing the semantic similarity measures to be used.
            precision (int): The precision of the similarity calculation.
            forcerun (bool): A flag to force the run of the similarity calculation.

        Returns:
            pandas.DataFrame: A DataFrame containing the similarity results for each measure.
        """
        in_file_path = tempfile.gettempdir() + r"\umls-similarity-temp.txt"

        def calculate_measure_similarity(measure):
            """
            Helper function to calculate similarity for a single measure.

            Args:
                measure (str): The semantic similarity measure to be used.

            Returns:
                list: The results of the similarity calculation for the given measure.
            """
            with open(in_file_path, 'w', encoding='utf-8') as f_out:
                for cui1, cui2 in cui_pairs:
                    f_out.write(f"{cui1}<>{cui2}\n")
            return self.similarity_from_file(in_file_path, measure, precision, forcerun, verbose)

        # Start threads for each measure calculation
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(calculate_measure_similarity, measure): measure for measure in measures}
            all_results = []

            for future in as_completed(futures):
                measure = futures[future]
                try:
                    measure_result = future.result()
                    all_results.append((measure, measure_result))
                except Exception as e:
                    print(f"Error calculating similarity for measure '{measure}': {e}")

        # Combine results from all threads
        return self.combine_similarity_results(all_results, cui_pairs)

    def combine_similarity_results(self, all_results, cui_pairs):
        """
        Combine the similarity results from multiple measures into a single DataFrame.

        This method takes the results from different semantic similarity measures and 
        compiles them into a cohesive DataFrame. Each row in the DataFrame corresponds 
        to a pair of CUIs, and each measure's result is a separate column.

        Args:
            all_results (list of tuples): A list where each tuple contains a measure 
                                        name and its corresponding results.
            cui_pairs (list of tuples): A list of tuples, where each tuple contains 
                                        two CUIs for which similarity was calculated.

        Returns:
            pandas.DataFrame: A DataFrame with the combined similarity results.
        """
        # Initialize the combined DataFrame
        combined_df = pd.DataFrame()

        for measure, measure_df in all_results:
            measure_column = f'Similarity ({measure})'
            if measure_column in combined_df.columns:
                if self.verbose:
                    print(f"Skipping {measure} as it is already in the combined DataFrame")
                continue
            
            measure_df = measure_df.rename(columns={measure: measure_column})
            
            if combined_df.empty:
                combined_df = measure_df
            else:
                combined_df = pd.merge(combined_df, measure_df, on=['Term_1', 'CUI_1', 'Term_2', 'CUI_2'], how='outer')

        return combined_df   
    
    def similarity_from_file(self, in_file, similarity_measure='lch', precision=4, forcerun=True, verbose=False):
        """
        Calculates semantic similarity using a specified measure from a file containing CUI pairs.

        This method executes a Perl script to compute semantic similarity based on the UMLS.
        It reads CUI pairs from a file and calculates their similarity using the specified measure.

        Args:
            in_file (str): Path to the file containing CUI pairs.
            similarity_measure (str): The semantic similarity measure to use (default 'lch').
            precision (int): The precision of the similarity scores (default 4).
            forcerun (bool): If True, forces the execution of the similarity calculation.
            verbose (bool): If True, prints additional information for debugging.

        Returns:
            pandas.DataFrame: A DataFrame containing the similarity results.
        """
        
        # Check if the input file exists
        if not os.path.isfile(in_file):
            raise FileNotFoundError(f"The input file {in_file} does not exist.")
        
        # Validate MySQL information
        required_keys = ["database", "username", "password", "hostname", "socket"]
        for key in required_keys:
            if key not in self.mysql_info or not self.mysql_info[key]:
                raise ValueError(f"MySQL information must include {key}.")

        umls_sim_params = {
            "--database": self.mysql_info["database"],
            "--username": self.mysql_info["username"],
            "--password": self.mysql_info["password"],
            "--hostname": self.mysql_info["hostname"],
            "--socket": self.mysql_info["socket"],
            "--measure": similarity_measure,
            "--precision": str(precision)
        }

        if forcerun:
            umls_sim_params["--forcerun"] = ""
 
        umls_sim_params["--infile"] = in_file

        cwd = self.work_directory
        umls_similarity_script_path = os.path.join(cwd, "umls-similarity.pl")

        # Check if the umls-similarity.pl script file exists
        if not os.path.isfile(umls_similarity_script_path):
            raise FileNotFoundError(f"The file {umls_similarity_script_path} does not exist.")

        # Check if the Perl executable exists
        if not os.path.isfile(self.perl_bin_path):
            raise FileNotFoundError(f"The Perl executable {self.perl_bin_path} does not exist.")
        
        process_args = [self.perl_bin_path, umls_similarity_script_path]
        for key, value in umls_sim_params.items():
            if value:  # Checks if value is not empty
                process_args.append(key + "=" + value)
            else:
                process_args.append(key)
        
        if verbose:
            kv_str = " ".join(process_args)
            print(kv_str)

        try:
            process = subprocess.Popen(process_args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_output, stderr_output = process.communicate()

            if stderr_output and verbose:
                print("Error:\n", stderr_output.strip())
            
            decoded_stdout = stdout_output.decode('utf-8', 'ignore')
            if verbose:
                print(decoded_stdout)

            # Determine if the input is CUIs or terms
            with open(in_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                cui1, cui2 = first_line.split('<>')
                input_is_cui = self.is_cui(cui1) and self.is_cui(cui2)

            if input_is_cui:
                # Regex pattern to extract the similarity results for CUI pairs
                pattern = re.compile(
                    r"(?P<similarity>\d+\.\d+)<>"
                    r"(?P<cui1>C\d+)\((?P<term1>.+?)\)<>"
                    r"(?P<cui2>C\d+)\((?P<term2>.+?)\)"
                )
            else:
                # Regex pattern to extract the similarity results for term pairs
                pattern = re.compile(
                    r"(?P<similarity>\d+\.\d+)<>"
                    r"(?P<term1>.+?)\((?P<cui1>C\d+)\)<>"
                    r"(?P<term2>.+?)\((?P<cui2>C\d+)\)"
                )

            matches = pattern.finditer(decoded_stdout)
            results = []

            for match in matches:
                similarity = match.group('similarity')
                cui1 = match.group('cui1')
                term1 = match.group('term1')
                cui2 = match.group('cui2')
                term2 = match.group('term2')
                results.append({
                    'Term_1': term1,
                    'CUI_1': cui1,
                    'Term_2': term2,
                    'CUI_2': cui2,
                    similarity_measure: float(similarity)
                })

            # Convert results to DataFrame
            df = pd.DataFrame(results)
            return df

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Subprocess failed with error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"An error occurred: {str(e)}")

    def find_shortest_path(self, cui_pairs, forcerun=True,verbose=False):
        """
        Calculates the shortest path between pairs of CUIs.

        This method writes CUI pairs to a temporary file and then calls 
        `find_shortest_path_from_file` to calculate the shortest path for each pair.

        Args:
            cui_pairs (list of tuple): A list of tuples, where each tuple contains two CUIs.
            forcerun (bool): If True, forces the calculation to run even if it might have been previously computed.

        Returns:
            pandas.DataFrame: A DataFrame containing the shortest path results, including 
                            the terms, CUIs, path length, and the path itself.
        """
        in_file_path = tempfile.gettempdir() + r"\umls-similarity-temp.txt"
        with open(in_file_path, 'w', encoding='utf-8') as f_out:
                for cui1, cui2 in cui_pairs:
                    f_out.write(f"{cui1}<>{cui2}\n")

        #return self.find_shortest_path_from_file(in_file_path, cui_pairs)
        return self.find_shortest_path_from_file(cui_pairs,verbose=verbose)


    def find_shortest_path_from_file(self, pairs, forcerun=True, verbose=False):
        """
        Executes a Perl script to find the shortest path between CUI or term pairs.

        This method calls an external Perl script, passing in the necessary UMLS database parameters
        and the pairs directly. It captures and processes the script's output.

        Args:
            pairs (list): List containing pairs (either CUIs or terms).
            forcerun (bool): If True, forces the calculation to run even if it might have been previously computed.
            verbose (bool): If True, prints additional debugging information.

        Returns:
            pandas.DataFrame: A DataFrame containing the shortest path results, including 
                            the terms, CUIs, path length, and the path itself.
        """
        
        # Validate MySQL information
        required_keys = ["database", "username", "password", "hostname", "socket"]
        for key in required_keys:
            if key not in self.mysql_info or not self.mysql_info[key]:
                raise ValueError(f"MySQL information must include {key}.")

        umls_sim_params = {
            "--database": self.mysql_info["database"],
            "--username": self.mysql_info["username"],
            "--password": self.mysql_info["password"],
            "--hostname": self.mysql_info["hostname"],
            "--socket": self.mysql_info["socket"],
            "--length": ""
        }

        if forcerun:
            umls_sim_params["--forcerun"] = ""
        
        cwd = self.work_directory
        umls_similarity_script_path = os.path.join(cwd, "findShortestPath.pl")

        # Check if the findShortestPath.pl script file exists
        if not os.path.isfile(umls_similarity_script_path):
            raise FileNotFoundError(f"The file {umls_similarity_script_path} does not exist.")

        # Check if the Perl executable exists
        if not os.path.isfile(self.perl_bin_path):
            raise FileNotFoundError(f"The Perl executable {self.perl_bin_path} does not exist.")

        results = []

        for pair1, pair2 in pairs:
            process_args = [self.perl_bin_path, umls_similarity_script_path] + [f"{key}={value}" if value else key for key, value in umls_sim_params.items()]
            process_args.append(pair1)
            process_args.append(pair2)

            print(pair1,pair2)

            if verbose:
                kv_str = " ".join(process_args)
                print(kv_str)

            try:
                process = subprocess.Popen(process_args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout_output, stderr_output = process.communicate()

                if stderr_output and verbose:
                    print("Error:\n", stderr_output.strip())

                # Decode stdout from bytes to string
                decoded_stdout = stdout_output.decode('utf-8', 'ignore')
                if verbose:
                    print(decoded_stdout)

                # Determine if the input is CUIs or terms
                input_is_cui = self.is_cui(pair1) and self.is_cui(pair2)

                if input_is_cui:
                    # Regex pattern to extract the shortest path results for CUI pairs
                    pattern = re.compile(
                        r"The shortest path \(length: (?P<length>\d+)\) between (?P<term1>.+?) \((?P<cui1>C\d+)\) and (?P<term2>.+?) \((?P<cui2>C\d+)\):\s*=> (?P<path>.+?)(?=\n\S|$)|"
                        r"There is not a path between (?P<no_path_cui1>C\d+) and (?P<no_path_cui2>C\d+) given the current view of the UMLS."
                    )
                else:
                    pattern = re.compile(
                        r"The shortest path \(length: (?P<length>\d+)\) between (?P<term1>.+?) \((?P<cui1>C\d+)\) and (?P<term2>.+?) \((?P<cui2>C\d+)\):\s*=> (?P<path>.+?)(?=\n\S|$)|"
                        r"There is not a path between (?P<no_path_term1>.+?) and (?P<no_path_term2>.+?)"
                    )

                matches = pattern.finditer(decoded_stdout)
                print(decoded_stdout)
                for match in matches:
                    print("Matched text:",match)
                    if input_is_cui:
                        if match.group('length'):
                            length = match.group('length')
                            term1 = match.group('term1')
                            cui1 = match.group('cui1')
                            term2 = match.group('term2')
                            cui2 = match.group('cui2')
                            path = match.group('path')
                            path_terms = re.findall(r"(C\d+) \((.+?)\)", path)
                            path_string = " => ".join([f"{cui} ({term})" for cui, term in path_terms])
                            results.append({
                                'Term_1': term1,
                                'CUI_1': cui1,
                                'Term_2': term2,
                                'CUI_2': cui2,
                                'Length': length,
                                'Path': path_string
                            })
                        else:
                            cui1 = match.group('no_path_cui1')
                            cui2 = match.group('no_path_cui2')
                            results.append({
                                'Term_1': None,
                                'CUI_1': cui1,
                                'Term_2': None,
                                'CUI_2': cui2,
                                'Length': 'No path found' if cui1 != cui2 else 0,
                                'Path': 'No path found' if cui1 != cui2 else cui1
                            })
                    else:
                        if match.group('length'):
                            length = match.group('length')
                            term1 = match.group('term1')
                            cui1 = match.group('cui1')
                            term2 = match.group('term2')
                            cui2 = match.group('cui2')
                            path = match.group('path')
                            path_terms = re.findall(r"(C\d+) \((.+?)\)", path)
                            path_string = " => ".join([f"{cui} ({term})" for cui, term in path_terms])
                            results.append({
                                'Term_1': term1,
                                'CUI_1': cui1,
                                'Term_2': term2,
                                'CUI_2': cui2,
                                'Length': length,
                                'Path': path_string
                            })
                        else:
                            term1 = match.group('no_path_term1')
                            term2 = match.group('no_path_term2')
                            print(term1,term2)
                            results.append({
                                'Term_1': pair1,
                                'CUI_1': None,
                                'Term_2': pair2,
                                'CUI_2': None,
                                'Length': 'No path found',
                                'Path': 'No path found'
                            })

        
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Subprocess failed with error: {str(e)}")
            except Exception as e:
                raise RuntimeError(f"An error occurred: {str(e)}")
        print(results)
        # Create a DataFrame from the results
        df = pd.DataFrame(results)

        return df

    def find_least_common_subsumer(self, cui_pairs,verbose=False):
        """
        Finds the least common subsumer (LCS) for given pairs of CUIs.

        This method writes CUI pairs to a temporary file and uses an external Perl script to
        calculate the LCS for each pair. The LCS is the most specific concept that is an ancestor 
        of both concepts in the UMLS hierarchy.

        Args:
            cui_pairs (list of tuple): A list of tuples, where each tuple contains two CUIs.
            verbose (bool): If True, prints additional debugging information.

        Returns:
            pandas.DataFrame: A DataFrame containing the LCS results for each CUI pair, 
                            including the terms, CUIs, LCS, and its minimum and maximum depth.
        """
        in_file_path = tempfile.gettempdir() + r"\umls-similarity-temp.txt"
        with open(in_file_path, 'w', encoding='utf-8') as f_out:
            for cui1, cui2 in cui_pairs:
                f_out.write(f"{cui1}<>{cui2}\n")

        return self.find_least_common_subsumer_from_file(in_file_path,cui_pairs,verbose=verbose)

    def find_least_common_subsumer_from_file(self, in_file, cui_pairs, forcerun=True, verbose=False):
        """
        Executes a Perl script to find the least common subsumer (LCS) from a file containing CUI pairs.

        This method calls an external Perl script, passing in UMLS database parameters and the path
        to a file containing CUI pairs, to calculate the LCS for each pair.

        Args:
            in_file (str): Path to the file containing CUI pairs.
            cui_pairs (list): List of tuples containing the CUI pairs to compare.
            forcerun (bool): If True, forces the calculation to run even if it might have been previously computed.
            verbose (bool): If True, prints additional debugging information.

        Returns:
            pandas.DataFrame: A DataFrame containing the LCS results for each CUI pair, 
                              including the terms, CUIs, LCS, and its minimum and maximum depth.
        """
        # Check if the input file exists
        if not os.path.isfile(in_file):
            raise FileNotFoundError(f"The input file {in_file} does not exist.")

        # Validate MySQL information
        required_keys = ["database", "username", "password", "hostname", "socket"]
        for key in required_keys:
            if key not in self.mysql_info or not self.mysql_info[key]:
                raise ValueError(f"MySQL information must include {key}.")

        # Setup for calling the Perl script
        umls_sim_params = {}
        umls_sim_params["--database"] = self.mysql_info["database"]
        umls_sim_params["--username"] = self.mysql_info["username"]
        umls_sim_params["--password"] = self.mysql_info["password"]
        umls_sim_params["--hostname"] = self.mysql_info["hostname"]
        umls_sim_params["--socket"]   = self.mysql_info["socket"]
        umls_sim_params["--depth"]    = ""

        if forcerun:
            umls_sim_params["--forcerun"] = ""

        umls_sim_params["--infile"] = in_file

        cwd = self.work_directory
        umls_similarity_script_path = cwd + r"\findLeastCommonSubsumer.pl"

        # Check if the findLeastCommonSubsumer.pl script file exists
        if not os.path.isfile(umls_similarity_script_path):
            raise FileNotFoundError(f"The file {umls_similarity_script_path} does not exist.")

        # Check if the Perl executable exists
        if not os.path.isfile(self.perl_bin_path):
            raise FileNotFoundError(f"The Perl executable {self.perl_bin_path} does not exist.")

        process_args = [self.perl_bin_path, umls_similarity_script_path]
        for key, value in umls_sim_params.items():
            if value:  # Checks if value is not empty
                process_args.append(key + "=" + value)
            else:
                process_args.append(key)

        if verbose:
            kv_str = " ".join(process_args)
            print(kv_str)

        try:
            process = subprocess.Popen(process_args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_output, stderr_output = process.communicate()

            if stderr_output and verbose:
                print("Error:\n", stderr_output.strip())

            # Decode stdout from bytes to string
            output = stdout_output.decode('utf-8')
            if verbose:
                print(output)

            # Regex pattern to match the required information
            pattern = re.compile(
                r"The least common subsumer between (?P<term1>.+?) \((?P<cui1>C\d+)\) and (?P<term2>.+?) \((?P<cui2>C\d+)\) is (?P<lcs_term>.+?) \((?P<lcs_cui>C\d+)\) with a min and max depth of (?P<min_depth>\d+) and (?P<max_depth>\d+)"
            )

            matches = pattern.finditer(output)
            data = []

            for match in matches:
                result = {
                    'Term_1': match.group('term1'),
                    'CUI_1': match.group('cui1'),
                    'Term_2': match.group('term2'),
                    'CUI_2': match.group('cui2'),
                    'LCS_Term': match.group('lcs_term'),
                    'LCS_CUI': match.group('lcs_cui'),
                    'MIN_Depth': match.group('min_depth'),
                    'MAX_Depth': match.group('max_depth')
                }
                data.append(result)

            # Creating the DataFrame
            df = pd.DataFrame(data)
            return df

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Subprocess failed with error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"An error occurred: {str(e)}")
        
    def get_all_measures(self):
        """
        Retrieves a list of all available semantic similarity measures.

        This method returns a list of strings, each representing a different semantic similarity measure
        that can be used for calculating similarity between concepts in the UMLS.

        Returns:
            list of str: A list of semantic similarity measures.
        """
        measures = ['lch', 'wup', 'zhong', 'path', 'cdist', 'nam', 'res', 'lin', 'jcn', 'vector', 'pks', 'faith', 'batet', 'sanchez']
        return measures

    def run_concurrently(self, tasks):
        """
        Executes multiple tasks concurrently using multithreading.
        This method takes a list of tasks, where each task is a dictionary specifying a function to run
        and its arguments. It uses multithreading to run these tasks concurrently, improving efficiency.
        
        Args:
            tasks (list of dict): A list of tasks, where each task is a dictionary containing
                                'function' (the function name as a string) and 'arguments' (a tuple of arguments).
        
        Returns:
            dict: A dictionary with function names as keys and the results of the function calls as values.
        """
        # Detect whether we are dealing with CUIs or terms based on the first task's arguments
        cui_pairs = tasks[0]['arguments'][0]
        print(cui_pairs)
        use_cuis = self.detect_cui_or_term(cui_pairs)
        
        with ThreadPoolExecutor() as executor:
            future_to_task = {executor.submit(self.run_task, task): task for task in tasks}

            results = {}
            # Initialize tqdm progress bar
            with tqdm(total=len(tasks), desc="Processing tasks", unit="task") as progress_bar:
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        results[task['function']] = future.result()
                    except Exception as e:
                        print(f"Task {task['function']} generated an exception: {e}")
                    finally:
                        progress_bar.update(1)  # Update progress bar after each task completion

            # Merge the DataFrames if they exist
            final_df = self.merge_results(results, use_cuis=use_cuis)
            return final_df

    def merge_results(self, results, use_cuis=True):
        """
        Merges the result DataFrames from different tasks.

        Args:
            results (dict): Dictionary with function names as keys and DataFrames as values.
            use_cuis (bool): If True, merge using CUI columns; if False, merge using Term columns.

        Returns:
            pandas.DataFrame: Merged DataFrame from the results of different tasks.
        """
        dataframes = []
        for key in ['similarity', 'shortest_path', 'lcs']:
            if key in results:
                dataframes.append(results[key])

        if dataframes:
            # Determine the columns to use for merging
            if use_cuis:
                merge_on = ['CUI_1', 'CUI_2']
                non_merge_cols = ['Term_1', 'Term_2']
            else:
                merge_on = ['Term_1', 'Term_2']
                non_merge_cols = ['CUI_1', 'CUI_2']

            # Start with the first DataFrame and keep all its columns
            final_df = dataframes[0]

            for df in dataframes[1:]:
                # Only drop non-merge columns if they are present in the DataFrame
                df = df.drop(columns=[col for col in non_merge_cols if col in df.columns], errors='ignore')
                
                # Merge while ensuring that merge columns are not dropped
                final_df = pd.merge(final_df, df, on=merge_on, how='outer', suffixes=('', '_drop'))
                # Drop duplicate columns created by the merge
                final_df = final_df.loc[:, ~final_df.columns.str.endswith('_drop')]

            return final_df
        else:
            return pd.DataFrame()  # Return an empty DataFrame if no results

    def run_task(self, task):
        """
        Executes a given task by calling the specified function with its arguments.

        This helper method is used for running a single task in a multithreading context. It dynamically
        calls the function specified in the task with the provided arguments.

        Args:
            task (dict): A dictionary containing 'function' (the function name as a string) and
                        'arguments' (a tuple of arguments for the function).

        Returns:
            The result of the function call specified in the task.
        """
        function_name = task['function']
        arguments = task.get('arguments', ())
        
        if function_name == 'similarity':
            return self.similarity(*arguments)
        elif function_name == 'shortest_path':
            return self.find_shortest_path(arguments)
        elif function_name == 'lcs':
            return self.find_least_common_subsumer(arguments)
        else:
            raise ValueError(f"Unknown function: {function_name}")
