#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyomo.core.base import ConcreteModel
from pyomo.environ import *
import math
import pandas as pd

# Creation of a Concrete Model
model = ConcreteModel()

## Define Sets ##
#  Sets
#   i   Manufacturers
#   j   Customers
#   k   Products

model.i = Set(initialize=range(0, 13), doc='Manufacturers')
model.j = Set(initialize=range(0, 32), doc='Customers')
model.k = Set(initialize=['A', 'B'], doc='Sources')

## Define Parameters ##
#  Parameters
#   Ri      Running costs for manufacturer
#   Dij     Distance from manufacturer to customer
#   Tk      Transport cost of product k
#   CDjk    Demand of product k for customer j
#   Pk      Selling price of k
#   TCk     Truck capacity for k

distances = pd.read_csv("distances.csv", header=None).T.to_dict()
D = {}
for j in range(0, 32):
    for i in range(0, 13):
        D[(i, j)] = distances[j][i]
model.D = Param(model.i, model.j, initialize=D, doc='Distances')

demands = pd.read_csv("demands.csv", header=None).T.to_dict()
CD = {}
for j in range(0, 32):
    for k in ['A', 'B']:
        if k == 'A':
            CD[(j, k)] = demands[j][2]*1000
        if k == 'B':
            CD[(j, k)] = demands[j][5]*1000
model.CD = Param(model.j, model.k, initialize=CD, doc='Demands')
MC = {
    0: 1404000,
    1: 1452000,
    2: 1476000,
    3: 1482000,
    4: 1500000,
    5: 1488000,
    6: 1434000,
    7: 1356000,
    8: 1464000,
    9: 1470000,
    10: 1458000,
    11: 1392000,
    12: 1392000
}
model.MC = Param(model.i, initialize=MC, doc='Running Costs')

model.T = Param(model.k, initialize={'A': 0.0015, 'B': 0.0020}, doc='Transport Costs')
model.TC = Param(model.k, initialize={'A': 50000, 'B': 30000}, doc='Truck Costs')
model.P = Param(model.k, initialize={'A': 5.2, 'B': 6.0}, doc='Product Price')
model.R = Param(model.k, initialize={'A': 35, 'B': 45}, doc="Hours of Work")

## Define variables ##
model.X = Var(model.i, model.j, model.k, within=NonNegativeIntegers, doc="Product k flow from i to j")
model.M = Var(model.i, within=Binary, doc="Manufacturing plant i exists")
model.NT = Var(model.i, model.j, within=NonNegativeIntegers, doc="Trucks Required")

## Define constraints ##
def Demand(model, j, k):
    return sum(model.X[i, j, k] for i in model.i) <= model.CD[j, k]
model.Demand = Constraint(model.j, model.k, rule=Demand, doc='Supply Demand')


def Capacity(model, i):
    return sum(model.X[i, j, k]*(model.R[k]/1000) for j in model.j for k in model.k) <= 25000*model.M[i]
model.Capacity = Constraint(model.i, rule=Capacity, doc='Manufacturer Capacity')


def Trucks(model, i, j):
    return model.NT[i, j] >= ((5/3)*model.X[i, j, 'A'] + model.X[i, j, 'B'])/30000
model.Trucks = Constraint(model.i, model.j, rule=Trucks, doc='Trucks Required')


## Define Objective and solve ##
def objectiveRule(model):

    return sum(sum(model.X[i, j, 'A']*(model.P['A'] - model.D[i, j]*model.T['A']) + model.X[i, j, 'B']*(model.P['B'] - model.D[i, j]*model.T['B']) - model.NT[i, j]*25000 for j in model.j) - model.M[i]*model.MC[i] for i in model.i)
model.objectiveRule = Objective(rule=objectiveRule, sense=maximize, doc='Define Objective Function')


def pyomo_postprocess(options=None, instance=None, results=None):
  model.M.display()
  model.X.display()
  model.NT.display()
  with open('Manufacturer.txt', 'w') as f:
      for key, value in instance.M._data.items():
          f.write('%s,%s\n' % (key, value._value))
  with open('Flow of Goods.txt', 'w') as f:
      for key, value in instance.X._data.items():
          f.write('%s,%s,%s,%s\n' % (key[0], key[1], key[2], value._value))
  with open('Number Of Trucks.txt', 'w') as f:
      for key, value in instance.NT._data.items():
          f.write('%s,%s,%s\n' % (key[0], key[1], value._value))


if __name__ == '__main__':
    # This emulates what the pyomo command-line tools does
    from pyomo.opt import SolverFactory
    import pyomo.environ

    opt = SolverFactory("gurobi")
    results = opt.solve(model)
    # sends results to stdout
    results.write()
    print("\nWriting Solution\n" + '-' * 60)
    pyomo_postprocess(None, model, results)
    print("Complete")
