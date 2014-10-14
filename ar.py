__author__ = 'moshele'

import argparse
import csv
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
    def calculate_investment_value(principal, annual_returns_list, annual_contribution):
        end_value = principal
        for current_return in annual_returns_list:
            end_value *= (1 + current_return / 100)
            end_value += annual_contribution

        return end_value


class Main(object):
    def __init__(self):
        self._args = self._parse_args()
        self._historic_data = HistoricData('data.csv')
        self._interest_calculator = InterestCalculator()

    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('-duration', type=int, required=True, help='The investment duration in years')
        parser.add_argument('-principal', type=float, required=True, help='Invested amount')
        parser.add_argument('-contrib', type=float, default=0, help='Annual contribution')
        parser.add_argument('-benchmark', type=float, help='Annualized return to use as a benchmark')
        parser.add_argument('-max', type=float, default=float('inf'), help='Max annualized return to show')
        parser.add_argument('-min', type=float, default=float('-inf'), help='Min annualized return to show')
        return parser.parse_args()

    def run(self):
        if self._args.benchmark is not None:
            self._calculate_benchmark()

        self._calculate_real_returns()

    def _calculate_benchmark(self):
        benchmark_returns = [self._args.benchmark] * self._args.duration
        benchmark_annualized_returns = self._interest_calculator.calculate_annualized_return(benchmark_returns)
        benchmark_end_value = self._interest_calculator.calculate_investment_value(self._args.principal,
                                                                                   benchmark_returns,
                                                                                   self._args.contrib)
        print 'Benchmark\t{0:.2f}%\t{1:,.2f}'.format(benchmark_annualized_returns, benchmark_end_value)

    def _calculate_real_returns(self):
        start_year = self._historic_data.get_start_year()
        end_year = self._historic_data.get_end_year()

        results = []
        while start_year + self._args.duration <= end_year:
            annual_returns = self._historic_data.get_returns_for(start_year, start_year + self._args.duration)
            annualized_return = self._interest_calculator.calculate_annualized_return(annual_returns)
            end_value = self._interest_calculator.calculate_investment_value(self._args.principal, annual_returns,
                                                                             self._args.contrib)

            results.append((start_year, start_year + self._args.duration, annualized_return, end_value))
            start_year += 1

        for result in sorted(results, key=lambda item: item[3], reverse=True):
            if self._args.max >= result[2] >= self._args.min:
                print '{0}-{1}\t{2:.2f}%\t{3:,.2f}'.format(result[0], result[1], result[2], result[3])


if __name__ == '__main__':
    main = Main()
    main.run()