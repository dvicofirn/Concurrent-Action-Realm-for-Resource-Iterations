import pandas as pd
import numpy as np
import ast
import matplotlib.pyplot as plt
from collections import defaultdict


def parse_list(s):
    return ast.literal_eval(s)


def main(fileName):
    # Load the data
    data = pd.read_csv(fileName + '.csv')
    # Filter out rows where 'run success' is FALSE
    data = data[data['run success']]
    # Parse the list-like strings into actual lists
    list_columns = ['costs', 'time measures', 'pick counts', 'deliver counts']
    for col in list_columns:
        data[col] = data[col].apply(parse_list)

    data = data.replace(np.nan, 'None')

    group_cols = ['planner name', 'search engine name', 'heuristic name', 'domain name', 'problem name']
    grouped = data.groupby(group_cols)
    summary_results = []

    for group_name, group_df in grouped:
        #print("Processing group:", group_name)

        time_measures_list = group_df['time measures'].tolist()
        iteration_time = group_df['iteration time'].iloc[0]  # Assuming iteration time is consistent within a group
        max_allowed_deviation = iteration_time * 0.025  # 2.5% of iteration time

        for run_idx, time_measures in enumerate(time_measures_list):
            # Check differences between adjacent time measurements
            for i in range(1, len(time_measures)):
                time_diff = time_measures[i] - time_measures[i - 1]
                expected_diff = iteration_time
                deviation = abs(time_diff - expected_diff)
                if deviation > max_allowed_deviation:
                    print(
                        f"Warning: In group {group_name}, run {run_idx + 1}, time difference between steps {i} and "
                        f"{i + 1} deviates by {deviation:.2f} seconds (more than 2.5% of iteration time).")

        num_runs = len(group_df)
        costs_list = group_df['costs'].tolist()
        pick_counts_list = group_df['pick counts'].tolist()
        deliver_counts_list = group_df['deliver counts'].tolist()

        # Determine the maximum length among the lists
        max_length = max(len(lst) for lst in costs_list)

        # Initialize arrays
        costs_array = np.zeros((num_runs, max_length))
        picks_array = np.zeros((num_runs, max_length))
        delivers_array = np.zeros((num_runs, max_length))

        # Fill the arrays with data
        for i, lst in enumerate(costs_list):
            costs_array[i, :len(lst)] = lst
        for i, lst in enumerate(pick_counts_list):
            picks_array[i, :len(lst)] = lst
        for i, lst in enumerate(deliver_counts_list):
            delivers_array[i, :len(lst)] = lst

        # Compute statistics
        mean_costs = np.mean(costs_array, axis=0)
        median_costs = np.median(costs_array, axis=0)
        std_costs = np.std(costs_array, axis=0, ddof=1) if num_runs > 1 else np.zeros(max_length)

        mean_picks = np.mean(picks_array, axis=0)
        median_picks = np.median(picks_array, axis=0)
        std_picks = np.std(picks_array, axis=0, ddof=1) if num_runs > 1 else np.zeros(max_length)

        mean_delivers = np.mean(delivers_array, axis=0)
        median_delivers = np.median(delivers_array, axis=0)
        std_delivers = np.std(delivers_array, axis=0, ddof=1) if num_runs > 1 else np.zeros(max_length)


        # Store the results
        summary = {
            'planner': group_name[0],
            'search engine': group_name[1],
            'heuristic': group_name[2],
            'domain': group_name[3],
            'problem': group_name[4],
            'num runs': num_runs,
            'mean costs': mean_costs.tolist(),
            'median costs': median_costs.tolist(),
            'std costs': std_costs.tolist(),
            'mean picks': mean_picks.tolist(),
            'median picks': median_picks.tolist(),
            'std picks': std_picks.tolist(),
            'mean delivers': mean_delivers.tolist(),
            'median delivers': median_delivers.tolist(),
            'std delivers': std_delivers.tolist()
        }
        summary['total mean cost'] = summary['mean costs'][-1]
        summary['total median cost'] = summary['median costs'][-1]
        summary['total std cost'] = summary['std costs'][-1]
        summary['total mean picks'] = summary['mean picks'][-1]
        summary['total median picks'] = summary['median picks'][-1]
        summary['total std picks'] = summary['std picks'][-1]
        summary['total mean delivers'] = summary['mean delivers'][-1]
        summary['total median delivers'] = summary['median delivers'][-1]
        summary['total std delivers'] = summary['std delivers'][-1]

        summary_results.append(summary)

    pd.DataFrame(summary_results).to_csv("summary " + fileName + ".csv", index=False)

    # Example: Plotting mean costs over time for each group
    # Organize summaries by domain and problem
    plots_data = defaultdict(list)
    for summary in summary_results:
        key = (summary['domain'], summary['problem'])
        plots_data[key].append(summary)

    for (domain, problem), summaries in plots_data.items():
        plt.figure()
        for summary in summaries:
            x_axis = range(len(summary['mean costs']))
            mean_costs = np.array(summary['mean costs'])

            plt.plot(x_axis, mean_costs,
                     label=f"{summary['planner']} - {summary['search engine']} ({summary['heuristic']})")
            plt.xticks(range(len(summary['mean costs'])))
            plt.scatter(x_axis, mean_costs, s=10)

        plt.title(f"Costs over Time - {domain} - {problem}")
        plt.xlabel('Time Step')
        plt.ylabel('Mean Cost')
        plt.legend()
        plt.show()

        plt.figure()
        for summary in summaries:
            x_axis = range(len(summary['mean picks']))
            mean_costs = np.array(summary['mean picks'])

            plt.plot(x_axis, mean_costs,
                     label=f"{summary['planner']} - {summary['search engine']} ({summary['heuristic']})")
            plt.xticks(range(len(summary['mean picks'])))
            plt.scatter(x_axis, mean_costs, s=10)

        plt.title(f"Pick actions over Time - {domain} - {problem}")
        plt.xlabel('Time Step')
        plt.ylabel('Mean Pick actions')
        plt.legend()
        plt.show()

        plt.figure()
        for summary in summaries:
            x_axis = range(len(summary['mean delivers']))
            mean_costs = np.array(summary['mean delivers'])

            plt.plot(x_axis, mean_costs,
                     label=f"{summary['planner']} - {summary['search engine']} ({summary['heuristic']})")
            plt.xticks(range(len(summary['mean delivers'])))
            plt.scatter(x_axis, mean_costs, s=10)

        plt.title(f"Deliver actions over Time - {domain} - {problem}")
        plt.xlabel('Time Step')
        plt.ylabel('Mean Deliver actions')
        plt.legend()
        plt.show()




if __name__ == '__main__':
    main('results')
