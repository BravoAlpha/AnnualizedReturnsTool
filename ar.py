#!/usr/bin/env python
__author__ = 'moshele'

import argparse
import csv
import itertools
import math


class HistoricData(object):
    def __init__(self, filename):
        self._historic_data = self._load_historic_data(filename)

    @staticmethod
    def _load_historic_data(filename):
        with open(filename, 'rb') as data:
            reader = csv.reader(data)
            return dict(reader)

    def get_return_for(self, year):
        return float(self._historic_data[str(year)])

    def get_returns_for(self, start, end):
        returns = []
        for year in range(start, end + 1):
            returns.append(self.get_return_for(year))
        return returns

    def get_start_year(self):
        return int(min(self._historic_data))

    def get_end_year(self):
        return int(max(self._historic_data))


class InterestCalculator(object):
    @staticmethod
    def calculate_annualized_return(annual_returns_list):
        total_return = 0.0
        number_of_years = len(annual_returns_list)
        for current_return in annual_returns_list:
            total_return += math.log(1 + current_return / 100)

        total_return /= number_of_years
        annualized_return = math.exp(total_return) - 1
        return annualized_return * 100

    @staticmethod
    def calculate_investment_value(principal, annual_returns, annual_contributions, annual_withdrawals):
        end_value = principal
        for current_return, current_contribution, current_withdrawal in itertools.izip(annual_returns, annual_contributions, annual_withdrawals):
            end_value -= current_withdrawal
            end_value *= (1 + current_return / 100)
            end_value += current_contribution

        return end_value


class BenchmarkData(object):
    def __init__(self, annualized_returns, end_value):
        self.annualized_returns = annualized_returns
        self.end_value = end_value


class AnnualizedReturnData(object):
    def __init__(self, start, end, annualized_return, end_value):
        self.start = start
        self.end = end
        self.annualized_return = annualized_return
        self.end_value = end_value


class Main(object):
    def __init__(self):
        self._args = self._parse_args()
        self._historic_data = HistoricData(self._args.source)
        self._interest_calculator = InterestCalculator()

    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('-source', type=str, required=True, help='Path to a CSV file with historic data (year,return)')
        parser.add_argument('-duration', type=int, required=True, help='The investment duration in years')
        parser.add_argument('-principal', type=float, required=True, help='Invested amount')
        parser.add_argument('-contrib', type=float, default=0, help='Annual contribution')
        parser.add_argument('-contrib-start', type=int, default=1, help='The year from which annual contributions starts')
        parser.add_argument('-contrib-stop', type=int, help='The year from which annual contributions stops')
        parser.add_argument('-withdraw', type=float, default=0, help='Annual withdrawal')
        parser.add_argument('-withdraw-start', type=int, default=1, help='The year from which annual withdrawals starts')
        parser.add_argument('-withdraw-stop', type=int, help='The year from which annual withdrawal stops')
        parser.add_argument('-benchmark', type=float, help='Annualized return to use as a benchmark')
        parser.add_argument('-max', type=float, default=float('inf'), help='Max annualized return to show')
        parser.add_argument('-min', type=float, default=float('-inf'), help='Min annualized return to show')

        args = parser.parse_args()
        args.contrib_stop = args.contrib_stop or args.duration
        args.withdraw_stop = args.withdraw_stop or args.duration

        return args

    def run(self):
        contributions = self._calculate_contributions()
        withdrawals = self._calculate_withdrawals()
        benchmark_data = self._calculate_benchmark(contributions, withdrawals)
        annualized_returns_data = self._calculate_annualized_returns(contributions, withdrawals)
        self._print_results(annualized_returns_data, benchmark_data)

    def _calculate_contributions(self):
        contributions = []
        for year in range(1, self._args.duration + 1):
            current_contribution = self._args.contrib if self._args.contrib_start <= year <= self._args.contrib_stop else 0
            contributions.append(current_contribution)
        return contributions

    def _calculate_withdrawals(self):
        withdrawals = []
        for year in range(1, self._args.duration + 1):
            current_withdrawal = self._args.withdraw if self._args.withdraw_start <= year <= self._args.withdraw_stop else 0
            withdrawals.append(current_withdrawal)
        return withdrawals

    def _calculate_benchmark(self, contributions, withdrawals):
        if self._args.benchmark is None:
            return None

        benchmark_returns = [self._args.benchmark] * self._args.duration
        benchmark_annualized_returns = self._interest_calculator.calculate_annualized_return(benchmark_returns)
        benchmark_end_value = self._interest_calculator.calculate_investment_value(self._args.principal,
                                                                                   benchmark_returns,
                                                                                   contributions,
                                                                                   withdrawals)
        return BenchmarkData(benchmark_annualized_returns, benchmark_end_value)

    def _calculate_annualized_returns(self, contributions, withdrawals):
        start_year = self._historic_data.get_start_year()
        end_year = self._historic_data.get_end_year()

        results = []
        while start_year + self._args.duration <= end_year:
            annual_returns = self._historic_data.get_returns_for(start_year, start_year + self._args.duration)
            annualized_return = self._interest_calculator.calculate_annualized_return(annual_returns)
            end_value = self._interest_calculator.calculate_investment_value(self._args.principal, annual_returns,
                                                                             contributions, withdrawals)

            annualized_return_data = AnnualizedReturnData(start_year, start_year + self._args.duration,
                                                          annualized_return, end_value)
            results.append(annualized_return_data)
            start_year += 1

        return results

    def _print_results(self, annualized_returns_data, benchmark_data):
        has_benchmark = benchmark_data is not None
        self._print_header(has_benchmark)

        if has_benchmark:
            print 'Benchmark\t{0:.2f}%\t{1:,.2f}\n'.format(benchmark_data.annualized_returns,
                                                           benchmark_data.end_value)

        for result in sorted(annualized_returns_data, key=lambda item: item.end_value, reverse=True):
            if self._args.max >= result.annualized_return >= self._args.min:
                output = '{0}-{1}\t{2:.2f}%\t{3:,.2f}'.format(result.start, result.end, result.annualized_return,
                                                              result.end_value)
                output += '\t\t({0:,.2f})'.format(result.end_value - benchmark_data.end_value) if has_benchmark else ''
                print output

    @staticmethod
    def _print_header(has_benchmark):
        print 'Period\t\tReturn\tEnd Value' + ('\tDifference From Benchmark' if has_benchmark else '')
        print '======\t\t======\t=========' + ('\t=========================' if has_benchmark else '')


if __name__ == '__main__':
    main = Main()
    main.run()