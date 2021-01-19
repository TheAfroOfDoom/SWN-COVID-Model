# Jordan Williams
# MTH 465 - Small World Networks
# 01/18/2021
# Final Project - Post-semester revisions
# Modelling the Spread of SARS-CoV-2 at UMass Dartmouth using Small World Networks

# made in Python 3.9.0

import logging
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import random
import seaborn as sns
import sys

n, k, d = 1500, 43, 3

g = []
GRAPH_TYPE = "Watts Strogatz"
#GRAPH_TYPE = "Complete"

PATH_DIR = "edgelists/"

logging.basicConfig(filename='logs/latest.log', level=logging.DEBUG, format="%(asctime)s:%(levelname)s: %(message)s")
logging.getLogger().addHandler(logging.StreamHandler())

if(GRAPH_TYPE == "Watts Strogatz"):
    def WattsStrogatz(n, k, diameterGoal):
        g = nx.Graph();

        # this raw function is much faster than using this:
        # <nx.complete_graph(n).edges()>
        # like, around 100 seconds faster (~120 to ~20) for n = 5000
        def complete_graph_edges(n):
            t = nx.Graph()
            for j in range(n):
                for i in range(j + 1, n):
                    t.add_edge(j, i)
            return(t)

        remaining_edges = complete_graph_edges(n)

        # Regular lattice w/(n vertices, k neighbors)
        regular_lattice = nx.Graph()
        for x in range(n):
            for y in range(k // 2):
                regular_lattice.add_edge(x, (x + y + 1) % n)

        remaining_edges.remove_edges_from(regular_lattice.edges())
        remaining_edges = np.asarray(remaining_edges.edges()).tolist()

        g = nx.compose(g, regular_lattice)
        regular_lattice = np.asarray(regular_lattice.edges()).tolist()

        while nx.diameter(g) > diameterGoal:
            choice = remaining_edges[np.random.choice(len(remaining_edges))]
            edge_removed = regular_lattice[np.random.choice(len(regular_lattice))]

            g.remove_edge(edge_removed[0], edge_removed[1])
            g.add_edge(choice[0], choice[1])

            regular_lattice.remove(edge_removed)
            remaining_edges.remove(choice)
    
        return(g)

    # Read from file if exists
    path = PATH_DIR + "WattsStrogatz_n{n}-k{k}-d{d}.edgelist".format(n = n, k = k, d = d)
    try:
        g = nx.read_edgelist(path, nodetype = int)
        print("Read graph from '%s' with %d vertices, %d edges." % (path, g.number_of_nodes(), g.number_of_edges()))
    except:
        print("Failed to read graph from '%s'. Generating..." % (path))
        g = WattsStrogatz(n, k, d)
        nx.write_edgelist(g, path)
        print("Wrote new graph to '%s' with %d vertices, %d edges." % (path, g.number_of_nodes(), g.number_of_edges()))

elif(GRAPH_TYPE == "Complete"):
    def CompleteGraph(n):
        # this raw function is much faster than using this:
        # <nx.complete_graph(n).edges()>
        # like, around 100 seconds faster (~120 to ~20) for n = 5000
        t = nx.Graph()
        for j in range(n):
            for i in range(j + 1, n):
                t.add_edge(j, i)
        return(t)

    # Read from file if exists
    path = PATH_DIR + "CompleteGraph_n{n}.edgelist".format(n = n, k = k, d = d)
    g = []
    try:
        g = nx.read_edgelist(path, nodetype = int)
        print("Read graph from '%s' with %d vertices, %d edges." % (path, g.number_of_nodes(), g.number_of_edges()))
    except:
        print("Failed to read graph from '%s'. Generating..." % (path))
        g = CompleteGraph(n)
        nx.write_edgelist(g, path)
        print("Wrote new graph to '%s' with %d vertices, %d edges." % (path, g.number_of_nodes(), g.number_of_edges()))

'''
# Constants
'''
TIME_HORIZON = 100
INITIAL_INFECTED_COUNT = 0

DAYS_EXPOSED = 3

DAYS_ASYMPTOMATIC = 10
DAYS_UNTIL_SYMPTOMS = 2
DAYS_SYMPTOMATIC = 5
DAYS_SYMPTOMATIC_QUARATINED = 5

ASYMPTOMATIC_RECOVERY_RATE = 0.15

DAYS_UNTIL_TEST_RESULTS = 1

C = {
    "1.05": 0.0777
    , "1.5": 0.1118
    , "2.0": 0.1523
}

EXOGENOUS_RATES = [
    3
    , 10
    , 15
]

TEST_COST = 25
TEST_RATES = [1, 2, 3, 7, "Symptom-based", "None"]
TEST_POSNEG = [0.948, 0.956]
QUARANTINE_TIME_ON_POSITIVE_TEST = 14

BASE_INFECTION_RATE = {}
for rt in C:
    BASE_INFECTION_RATE[rt] = C[rt] / k
    #print("Daily person-to-person infection rate (goal %s): %.2f%% (C: %.4f)" % (rt, BASE_INFECTION_RATE[rt] * 100, C[rt]))

CASE_TYPES = [
    ('1.05', EXOGENOUS_RATES[0]),   # Best
    ('1.5', EXOGENOUS_RATES[1]),    # Base
    ('2.0', EXOGENOUS_RATES[2])     # Worst
]
'''
'''

class Node:
    def __init__(self, i):
        self.index = i
        self.indexCase = False
        self.quarantineTime = 0
        self.rt = 0
        self.status = 0
        self.t = 0
        self.testsTaken = 0

        self.testResults = True
        self.awaitingResults = False
        self.awaitingResultsDays = 0

    def statusString(self):
        translate = [
            "susceptible",              # 0
            "exposed",                  # 1
            #"infected",                #
            "infected asymptomatic",    # 2
            "infected symptomatic",     # 3
            "recovered"                 # 4
        ]
        return(translate[self.status])

    def update(self, neighbors, nodes, transmissionRate, globalT, testRate):
        self.t += 1
        if(self.awaitingResults):
            self.awaitingResultsDays += 1
        if(self.quarantineTime > 0):
            self.quarantineTime -= 1

        # Get tested every X days if not quarantined
        if(self.quarantineTime == 0
        and isinstance(testRate, int)
        and globalT % testRate == 0
        and globalT > 0):
            self.test(testRate)

        # Receive test results Y days after being tested (if not quarantined)
        if(self.quarantineTime == 0
        and self.awaitingResultsDays == DAYS_UNTIL_TEST_RESULTS):
            self.getTestResults()

        # recovered
        if  (self.status == 4):
            pass

        # infected symp.
        elif(self.status == 3):
            # Get tested if not already quarantined (and testRate == Symptom-based)
            if(self.quarantineTime == 0
            and testRate == "Symptom-based"):
                self.test(testRate)

            # t == 5
            # quarantine self for 5 days after 5 days of symptoms regardless of test results, due to being too sick
            if(self.quarantineTime == 0
            and self.t == DAYS_SYMPTOMATIC):
                self.quarantineTime = DAYS_SYMPTOMATIC_QUARATINED
            
            # recover after 10 days of symptoms
            elif(self.t == DAYS_SYMPTOMATIC + DAYS_SYMPTOMATIC_QUARATINED):
                self.getRecovered()

            # spread if not quarantined
            elif(self.quarantineTime == 0):
                self.spread(neighbors, nodes, transmissionRate)

        # infected asymp.
        elif(self.status == 2):
            # t == 10
            if(self.t == DAYS_ASYMPTOMATIC):
                if(random.random() <= ASYMPTOMATIC_RECOVERY_RATE):
                    self.getRecovered()

            # if doesn't recover
            else:
                # spread if not quarantined
                if(self.quarantineTime == 0):
                    self.spread(neighbors, nodes, transmissionRate)

                # gain symptoms at t == 12
                if(self.t == DAYS_ASYMPTOMATIC + DAYS_UNTIL_SYMPTOMS):
                    self.getSymptoms()

        # exposed
        elif(self.status == 1):
            if(self.t == DAYS_EXPOSED):
                # progress from exposed to infected in 2 days
                self.getInfected();

        # susceptible (self.status == 0)

    def spread(self, neighbors, nodes, transmissionRate):
        for neighborIndex in neighbors:
            neighborNode = nodes[neighborIndex]
            # If neighbor is susceptible,
            # and random chance it spreads to them is base infection rate
            # and neighbor is not quarantined
            if( neighborNode.status == 0
            and random.random() <= transmissionRate
            and neighborNode.quarantineTime == 0):
                neighborNode.getExposed()

                # Count r0 cases (cases caused by index cases)
                if(self.indexCase == True):
                    self.rt += 1

    def test(self, testRate):
        truePositiveRate = TEST_POSNEG[0]
        trueNegativeRate = TEST_POSNEG[1]

        # Don't test
        if(testRate == "None"):
            return
        
        self.testsTaken += 1

        # Use positive rates for infected individuals
        if(self.status == 3
        or self.status == 2):
            if(random.random() <= truePositiveRate):
                self.testResults = True
                #self.quarantineTime += QUARANTINE_TIME_ON_POSITIVE_TEST # 14
            else:
                self.testResults = False
                pass

        # Use negative rates for susceptible/recovered individuals
        else:
            if(random.random() <= trueNegativeRate):
                self.testResults = False
                pass
            else:
                self.testResults = True
                #self.quarantineTime += QUARANTINE_TIME_ON_POSITIVE_TEST # 14
                
        self.awaitingResults = True
        if(self.status == 4):
            #print("node is recovered and just got tested")
            pass

    def getTestResults(self):
        self.awaitingResults = False
        self.awaitingResultsDays = 0

        if(self.testResults):
            self.quarantineTime += QUARANTINE_TIME_ON_POSITIVE_TEST # 14
            
    def changedState(self):
        self.t = 0

    def getExposed(self):
        self.status = 1
        self.changedState()

    def getInfected(self):
        self.status = 2
        self.changedState()

    def getSymptoms(self):
        self.status = 3
        self.changedState()

    def getRecovered(self):
        self.status = 4
        self.changedState()

def addExogenous(nodes, amount):
    # Susceptible nodes
    susNodes = [node.index for node in nodes if node.status == 0]
    
    # set all sus nodes to infected if they are <= X
    if(len(susNodes) <= amount):
        for i in susNodes:
            nodes[i].getExposed()
        return

    # Only choose from susceptible nodes
    chosenIndices = np.random.choice(susNodes, amount, replace = False)
    for i in chosenIndices:
        nodes[i].getExposed()

def runSimulation(timeSpan, initialCaseCount, data, transmissionRate, exogenousAmount, testRate):
    nodes = []
    for node in g.nodes():
        nodes.append(Node(node))

    # Randomly infect x nodes
    initialInfected = np.random.choice(len(nodes), initialCaseCount, replace = False)
    for chosenVert in initialInfected:
        node = nodes[chosenVert]
        node.getExposed()
        node.indexCase = True

    for ti in range(timeSpan):
        # Add exogenous infections weekly, after the first week
        if(ti % 7 == 0 and ti > 0):
            addExogenous(nodes, exogenousAmount)
    
        # Daily counts
        infected, recovered, susceptible = 0, 0, 0
        for node in nodes:
            if(node.status == 0):
                susceptible += 1
            elif(node.status == 4):
                recovered += 1
            else:
                infected += 1

            node.update(g.neighbors(node.index), nodes, transmissionRate, ti, testRate)

        # Save data (["infected", "recovered", "susceptible"])
        for status in data:
            data[status] = data[status].append({'day': ti, 'cases': eval(status)}, ignore_index = True)

    totalRecovered = 0
    totalSpreadTo = 0
    totalTests = 0

    # rt calculating
    for node in nodes:
        totalTests += node.testsTaken
        if(node.indexCase):
            totalRecovered += 1
            totalSpreadTo += node.rt

    # return (rt, cost of tests)
    return((totalSpreadTo / totalRecovered), totalTests)

def simulationContainer(ax, testRate, rt, X, sampleSize):
    data = {
        "infected": pd.DataFrame(),
        "recovered": pd.DataFrame(),
        "susceptible": pd.DataFrame()
    }
    for i in range(TIME_HORIZON):
        for status in data:
            data[status].append([])
    
    transmissionRate = BASE_INFECTION_RATE[rt]
    expRt, testCost = 0, 0
    for i in range(sampleSize):
        result = runSimulation(TIME_HORIZON, X, data, transmissionRate, X, testRate)
        expRt += result[0]
        testCost += result[1]
    expRt /= sampleSize
    testCost = testCost * TEST_COST / sampleSize

    print("Test rate: %s, beta: %.2f%%, X: %d | Rt %d trials: %.2f" % (str(testRate), 100 * transmissionRate, X, sampleSize, expRt))

    for status in data:
        sns.lineplot(data = data[status], x = 'day', y = 'cases', ax = ax)

    # Calculate total (mean + std) infected + recovered
    dfInfected, dfRecovered = data["infected"], data["recovered"]
    dfTotalCases = dfInfected.loc[dfInfected['day'] == TIME_HORIZON - 1]['cases'] + dfRecovered.loc[dfRecovered['day'] == TIME_HORIZON - 1]['cases']
    meanTotalCases, stdTotalCases = dfTotalCases.mean(), dfTotalCases.std()

    ax.set_title(r"$R_t$: %.2f, C: %.2f, $\bar{x}$: %.1f, $\sigma_x$: %.1f" % (expRt, testCost, meanTotalCases, stdTotalCases))

SAMPLE_SIZE = 50

def makeGraphs(testRates, caseTypes):
    fig, axs = plt.subplots(nrows = len(testRates), ncols = len(caseTypes))
    # Each row is a test rate (least-often to most-often)
    for i, testRate in enumerate(reversed(testRates)):
        if(len(caseTypes) > 1):
            # Each column is a case (best, base, worst)
            for j, caseType in enumerate(caseTypes):
                ax = axs[i, j]

                rt = caseType[0]
                X = caseType[1]

                # infection rate
                ir = BASE_INFECTION_RATE[rt]

                simulationContainer(ax, testRate, rt, X, SAMPLE_SIZE)
        else:
            ax = axs[i]

            rt = caseTypes[0][0]
            X = caseTypes[0][1]

            # infection rate
            ir = BASE_INFECTION_RATE[rt]

            simulationContainer(ax, testRate, rt, X, SAMPLE_SIZE)

    xlab = 'Days'
    ylab = 'Cases'
    for ax in axs.reshape(-1):
        ax.set(xlabel = xlab, ylabel = ylab)
        ax.label_outer()

    l = ["Infected", "Recovered", "Susceptible"]
    if(len(caseTypes) > 1):
        axs[0, -1].legend(l)
    else:
        axs[0].legend(l)

    colLabels = [r"%s Graph: $\beta$: %.2f%%, X: %d" % (GRAPH_TYPE, 100 * BASE_INFECTION_RATE[caseType[0]], caseType[1]) for caseType in caseTypes]
    rowLabels = ["%d days" % (testRate) if isinstance(testRate, int) else testRate for testRate in reversed(testRates)]

    # Fancy column/row labels in addition to subplot labels
    # https://stackoverflow.com/a/25814386/13789724
    pad = 5 # in points

    '''
    for ax, col in zip(axs[0], colLabels):
        ax.annotate(col, xy=(0.5, 1), xytext=(0, pad),
                    xycoords=ax.title, textcoords='offset points',
                    size='large', ha='center', va='baseline')
    '''
    fig.suptitle(colLabels[0])

    for ax, row in zip(axs, rowLabels):
        ax.annotate(row, xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - pad, 0),
                    xycoords=ax.yaxis.label, textcoords='offset points',
                    size='large', ha='right', va='center')

    fig.tight_layout()
    # tight_layout doesn't take these labels into account. We'll need 
    # to make some room. These numbers are are manually tweaked. 
    # You could automatically calculate them, but it's a pain.
    #fig.subplots_adjust(left=0.15, top=0.95)
    fig.subplots_adjust(left=0.4)
    #fig.set_size_inches()

    plt.show()

# test cases to see if output is correct
#testRates = [7, "None"]
#castTypes = [CASE_TYPES[0], CASE_TYPES[1]]
#SAMPLE_SIZE = 1

#caseTypes = CASE_TYPES      # cols
'''
testRates = [TEST_RATES[-1], TEST_RATES[-2]]
for caseTypes in CASE_TYPES[2:]:
    makeGraphs(testRates, [caseTypes])
'''
#'''
testRates = TEST_RATES[3:]  # split rows in half
for caseTypes in CASE_TYPES:
    makeGraphs(testRates, [caseTypes])
#'''
testRates = TEST_RATES[:3]  # split rows in half
for caseTypes in CASE_TYPES:
    makeGraphs(testRates, [caseTypes])
#'''
