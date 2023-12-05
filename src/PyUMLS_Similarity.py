import subprocess
import os
import tempfile
import pandas as pd
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class PyUMLS_Similarity:
    def __init__(self, mysql_info, work_directory=""):
        self.perl_bin_path = r"C:\Strawberry\perl\bin\perl.exe"
        self.mysql_info = mysql_info

    def similarity(self, cui_pairs, measures=['lch'], precision=4, forcerun=True):
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
            return self.similarity_from_file(in_file_path, measure, precision, forcerun)

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
                              The DataFrame contains columns for Term 1, Term 2, 
                              CUI 1, CUI 2, and a column for each similarity measure.
        """
        # Preparing data for DataFrame
        data = []
        for i, pair in enumerate(cui_pairs):
            if all_results:
                first_measure_results = all_results[0][1]
                term1, cui1 = self.extract_term_and_cui(first_measure_results[i][1]) if i < len(first_measure_results) else ('N/A', 'N/A')
                term2, cui2 = self.extract_term_and_cui(first_measure_results[i][2]) if i < len(first_measure_results) else ('N/A', 'N/A')
            else:
                term1, term2, cui1, cui2 = 'N/A', 'N/A', 'N/A', 'N/A'

            row = [term1, term2, cui1, cui2]
            for measure, results in all_results:
                score = results[i][3] if i < len(results) else 'N/A'
                row.append(score)
            data.append(row)

        # Creating the DataFrame
        columns = ['Term 1', 'Term 2', 'CUI 1', 'CUI 2'] + [measure for measure, _ in all_results]
        df = pd.DataFrame(data, columns=columns)
        return df

    def extract_term_and_cui(self, term):
        """
        Extracts the term name and its corresponding CUI from a string.

        This method processes a string that contains a term and its Concept 
        Unique Identifier (CUI), separating them into individual components. 
        If the term does not have a CUI, 'N/A' is returned for the CUI.

        Args:
            term (str): A string containing the term and possibly its CUI in parentheses.

        Returns:
            tuple: A tuple containing the term name and its CUI (or 'N/A' if no CUI is present).
        """
        if '(' in term and ')' in term:
            term_name, cui = term.split('(')
            cui = cui.rstrip(')')
        else:
            term_name = term
            cui = 'N/A'
        return term_name, cui
        
    
    def similarity_from_file(self,in_file,similarity_measure='lch',precision=4,forcerun=True,verbose=False):
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
            list: A list of similarity results, each result is a list containing the measure, 
                the two CUIs, and the calculated similarity score.
        """

        umls_sim_params = {}
        umls_sim_params["--database"]  = self.mysql_info["database"]
        umls_sim_params["--username"]  = self.mysql_info["username"]
        umls_sim_params["--password"]  = self.mysql_info["password"]
        umls_sim_params["--hostname"]  = self.mysql_info["hostname"]
        umls_sim_params["--socket"]    = self.mysql_info["socket"]
        umls_sim_params["--measure"]   = similarity_measure
        umls_sim_params["--precision"] = str(precision)

        if forcerun:
            umls_sim_params["--forcerun"] = ""
 
        umls_sim_params["--infile"] = in_file

        cwd = r'C:\Strawberry\perl\site\bin'
        umls_similarity_script_path =cwd+ r"\umls-similarity.pl"
        # new_env["WNHome"] = r'C:\Program Files (x86)\WordNet\2.1'

        process_args = [self.perl_bin_path, umls_similarity_script_path]
        for key, value in umls_sim_params.items():
            if value:  # Checks if value is not empty
                process_args.append(key + "=" + value)
            else:
                process_args.append(key)
        kv_str = " ".join(process_args)
        print(kv_str)

        process = subprocess.Popen(process_args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # After the subprocess ends, check if there are any errors
        stderr_output = process.stderr.read()
        if stderr_output and verbose:
            print("Error:\n", stderr_output.strip())

        stdout_output, _ = process.communicate()
        #print(stdout_output)
        decoded_stdout = stdout_output.decode('utf-8', 'ignore')
        output_lines = decoded_stdout.strip().split('\r\n')
        
        similarity_results = []
        for line in output_lines:
            parts = line.strip().split('<>')
            if len(parts) >= 3:
                similarity_results.append([similarity_measure, parts[1], parts[2], parts[0]])

        return similarity_results

    def find_shortest_path(self, cui_pairs, forcerun=True):
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

        return self.find_shortest_path_from_file(in_file_path, forcerun)


    def find_shortest_path_from_file(self,in_file,forcerun=True,verbose=False):
        """
        Executes a Perl script to find the shortest path between CUI pairs from a file.

        This method calls an external Perl script, passing in the necessary UMLS database parameters
        and the path to a file containing CUI pairs. It captures and processes the script's output.

        Args:
            in_file (str): Path to the file containing CUI pairs.
            forcerun (bool): If True, forces the calculation to run even if it might have been previously computed.
            verbose (bool): If True, prints additional debugging information.

        Returns:
            pandas.DataFrame: A DataFrame containing the shortest path results, including 
                            the terms, CUIs, path length, and the path itself.
        """

        umls_sim_params = {}
        umls_sim_params["--database"] = self.mysql_info["database"]
        umls_sim_params["--username"] = self.mysql_info["username"]
        umls_sim_params["--password"] = self.mysql_info["password"]
        umls_sim_params["--hostname"] = self.mysql_info["hostname"]
        umls_sim_params["--socket"]   = self.mysql_info["socket"]
        umls_sim_params["--length"]   = ""

        if forcerun:
            umls_sim_params["--forcerun"] = ""
 
        umls_sim_params["--infile"] = in_file

        cwd = r'C:\Strawberry\perl\site\bin'
        umls_similarity_script_path =cwd+ r"\findShortestPath.pl"
        # new_env["WNHome"] = r'C:\Program Files (x86)\WordNet\2.1'

        process_args = [self.perl_bin_path, umls_similarity_script_path]
        for key, value in umls_sim_params.items():
            if value:  # Checks if value is not empty
                process_args.append(key + "=" + value)
            else:
                process_args.append(key)
        kv_str = " ".join(process_args)
        print(kv_str)

        process = subprocess.Popen(process_args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr and verbose:
            print("Error:\n", stderr.strip())

        # Decode stdout from bytes to string
        output = stdout.decode('utf-8')
        #print(output)

        # Process the output and extract data
        data = []
        for pair in cui_pairs:
            term1, term2 = pair
            length_pattern = r'The shortest path \(length: (\d+)\) between ' + re.escape(term1) + r' \((.+?)\) and ' + re.escape(term2) + r' \((.+?)\):'
            length_match = re.search(length_pattern, output)
            if length_match:
                path_length = length_match.group(1)
                cui1 = length_match.group(2)
                cui2 = length_match.group(3)
                path = self.extract_path(output, term1, term2)
                data.append([term1, term2, cui1, cui2, path_length, path])

        # Creating the DataFrame
        df = pd.DataFrame(data, columns=['Term 1', 'Term 2', 'CUI 1', 'CUI 2', 'Path Length', 'Path'])
        return df

    def extract_path(self, output, term1, term2):
        """
        Extracts the path of CUIs from the output of the shortest path calculation.

        This method uses regular expressions to parse the output from the Perl script and 
        extract the sequence of CUIs that form the path between two terms.

        Args:
            output (str): The raw output string from the Perl script.
            term1 (str): The first term of the CUI pair.
            term2 (str): The second term of the CUI pair.

        Returns:
            str: A string representing the path of CUIs, or 'Path not found' if no path is extracted.
        """
        # Adjusted logic to extract the path from the output
        path_pattern = re.escape(term1) + r' \(.+?\):(.+?)' + re.escape(term2) + r' \(.+?\)'
        path_match = re.search(path_pattern, output, re.DOTALL)
        if path_match:
            path = path_match.group(1).strip()
            # Extract CUIs from the path
            cuis = re.findall(r'C\d{7}', path)
            return ' => '.join(cuis)
        else:
            return 'Path not found'

    def find_least_common_subsumer(self, cui_pairs):
        """
        Finds the least common subsumer (LCS) for given pairs of CUIs.

        This method writes CUI pairs to a temporary file and uses an external Perl script to
        calculate the LCS for each pair. The LCS is the most specific concept that is an ancestor 
        of both concepts in the UMLS hierarchy.

        Args:
            cui_pairs (list of tuple): A list of tuples, where each tuple contains two CUIs.

        Returns:
            pandas.DataFrame: A DataFrame containing the LCS results for each CUI pair, 
                            including the terms, CUIs, LCS, and its minimum and maximum depth.
        """
        in_file_path = tempfile.gettempdir() + r"\umls-similarity-temp.txt"
        with open(in_file_path, 'w', encoding='utf-8') as f_out:
            for cui1, cui2 in cui_pairs:
                f_out.write(f"{cui1}<>{cui2}\n")

        return self.find_least_common_subsumer_from_file(in_file_path)

    def find_least_common_subsumer_from_file(self, in_file,forcerun=True,verbose=False):
        """
        Executes a Perl script to find the least common subsumer (LCS) from a file containing CUI pairs.

        This method calls an external Perl script, passing in UMLS database parameters and the path
        to a file containing CUI pairs, to calculate the LCS for each pair.

        Args:
            in_file (str): Path to the file containing CUI pairs.
            forcerun (bool): If True, forces the calculation to run even if it might have been previously computed.
            verbose (bool): If True, prints additional debugging information.

        Returns:
            pandas.DataFrame: A DataFrame containing the LCS results for each CUI pair, 
                            including the terms, CUIs, LCS, and its minimum and maximum depth.
        """
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

        cwd = r'C:\Strawberry\perl\site\bin'
        umls_similarity_script_path =cwd+ r"\findLeastCommonSubsumer.pl"
        # new_env["WNHome"] = r'C:\Program Files (x86)\WordNet\2.1'

        process_args = [self.perl_bin_path, umls_similarity_script_path]
        for key, value in umls_sim_params.items():
            if value:  # Checks if value is not empty
                process_args.append(key + "=" + value)
            else:
                process_args.append(key)
        kv_str = " ".join(process_args)
        print(kv_str)
        #print(ps)
        process = subprocess.Popen(process_args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr and verbose:
            print("Error:\n", stderr.strip())

        # Decode stdout from bytes to string
        output = stdout.decode('utf-8')
        #print(output)

        # Process the output and extract data
        data = []
        for pair in cui_pairs:
            term1, term2 = pair
            lcs_pattern = r'The least common subsumer between ' + re.escape(term1) + r' \((.+?)\) and ' + re.escape(term2) + r' \((.+?)\) is (.+?) \((.+?)\) with a min and max depth of (\d+) and (\d+)'
            lcs_match = re.search(lcs_pattern, output)
            if lcs_match:
                cui1 = lcs_match.group(1)
                cui2 = lcs_match.group(2)
                lcs = lcs_match.group(3) + ' (' + lcs_match.group(4) + ')'
                min_depth = lcs_match.group(5)
                max_depth = lcs_match.group(6)
                data.append([term1, term2, cui1, cui2, lcs, min_depth, max_depth])

        # Creating the DataFrame
        df = pd.DataFrame(data, columns=['Term 1', 'Term 2', 'CUI 1', 'CUI 2', 'LCS', 'Min Depth', 'Max Depth'])
        return df

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
            final_df = self.merge_results(results)
            return final_df

    def merge_results(self, results):
        """
        Merges the result DataFrames from different tasks.

        Args:
            results (dict): Dictionary with function names as keys and DataFrames as values.

        Returns:
            pandas.DataFrame: Merged DataFrame from the results of different tasks.
        """
        dataframes = []
        for key in ['similarity', 'shortest_path', 'lcs']:
            if key in results:
                dataframes.append(results[key])

        if dataframes:
            # Merge all DataFrames on the specified columns
            final_df = dataframes[0]
            for df in dataframes[1:]:
                final_df = pd.merge(final_df, df, on=['Term 1', 'Term 2', 'CUI 1', 'CUI 2'], how='outer')
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
