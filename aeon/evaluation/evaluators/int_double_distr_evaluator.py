import re
import pandas as pd
import numpy as np

from os import listdir
from functools import reduce

from .evaluator import Evaluator
from aeon.evaluation import OUTPUT_PATH
from aeon.frontend2 import expr, typee

import aeon.evaluation.plots.boxplot as boxplot
import aeon.evaluation.plots.violinplot as violinplot
import aeon.evaluation.plots.scatterplot as scatterplot


class IntDoubleDistrEvaluator(Evaluator):

    # CONSTANTS
    PATH = 'int_double_distribution/'

    def __init__(self):
        self.path = self.FOLDER_PATH + self.PATH

    def process(self):
        data = {}

        for f in listdir(OUTPUT_PATH):
            _, depth, _ = tuple(map(lambda x: int(x), re.findall('\d+', f)))
            csv = pd.read_csv(OUTPUT_PATH + f)
            data[depth] = csv if depth not in data else pd.concat(
                [data[depth], csv])

        integers = []
        doubles = []

        for depth, csv in data.items():

            res_ints, res_doubles = self.treat_data(csv)

            integers += res_ints
            doubles += res_doubles

        df = pd.DataFrame(columns=('Integer', 'Double'))

        integers += [np.nan] * (len(doubles) - len(integers))
        doubles += [np.nan] * (len(integers) - len(doubles))

        i = 0

        for integer, double in zip(integers, doubles):
            df.loc[i] = [integer, double]
            i += 1

        axis = (None, None)
        labels = ('Types', 'Value Distribution')
        f_name = 'value_distribution'

        #scatterplot.plot(self.path, f_name, axis, labels, df)
        boxplot.plot(self.path, f_name, axis, labels, df)
        violinplot.plot(self.path, f_name, axis, labels, df)

    def treat_data(self, data):
        integers = []
        doubles = []
        for individual in data['Individual'].values:
            integers += re.findall('-?\d+', str(individual))
            doubles += re.findall('-?\d+\.\d+', str(individual))
        return (integers, doubles)