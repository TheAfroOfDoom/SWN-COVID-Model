###
# File: interface.py
# Created: 02/19/2021
# Author: Aidan Tokarski (astoka21@colby.edu)
# -----
# Last Modified: 02/19/2021
# Modified By: Aidan Tokarski
###

from simulation import Simulation
import graph_handler
import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.filedialog as tkfd
import config

class Interface:
    def __init__(self):
        self.window = tk.Tk()
        self.params = {}
        self.graph_file_name = None
        '''
        Currently implemented params:
        time_horizon
        initial_infected_count
        exogenous_rate
        '''

    def simulate(self):
        sim = self.generate_sim()
        time_steps = []
        for i in range(self.params['time_horizon']):
            time_steps.append(i)
            sim.run_step()
        self.plot_data(sim.data, time_steps)

    def generate_sim(self):
        sim = Simulation(self.load_graph())
        for param in self.params:
            self.params[param] = int(self.window.getvar(param))
            if param == 'initial_infected_count':
                sim.initial_infected_count = self.params[param]
            elif param == 'exgogenous_rate':
                sim.exogenous_rate = self.params[param]
        return sim
        
    def load_graph(self):
        return graph_handler.import_graph(file_name=self.graph_file_name)

    def add_param(self, name, text, default=None):
        # Declares a new param to be added to the interface
        var = tk.IntVar(self.window, value=default, name=name)
        frame = tk.Frame(self.window)
        entry = tk.Entry(frame, bd=5, textvariable=var)
        entry.pack(side=tk.RIGHT)
        label = tk.Label(frame, text=text)
        label.pack(side=tk.LEFT)
        frame.pack(anchor=tk.N)
        self.params[name] = default
    
    def btn_sim_cb(self):
        self.simulate()

    def btn_choose_graph(self):
        self.graph_file_name = tkfd.askopenfilename(initialdir='./' + config.settings['graph']['directory'])

    def create_window(self):
        win = self.window
        self.add_param('time_horizon', 'Days', default=100)
        self.add_param('initial_infected_count', 'Initial Infection Count', default=10)
        self.add_param('exogenous_rate', 'Weekly Exogenous Infections', default=10)
        btn_sim = tk.Button(win, text='Simulate', command=self.btn_sim_cb)
        btn_sim.pack(side=tk.BOTTOM)
        btn_choose_graph = tk.Button(win, text='Load Graph', command=self.btn_choose_graph)
        btn_choose_graph.pack(side=tk.BOTTOM)
        win.mainloop()

    def plot_data(self, data, time_steps):
        fig, ax = plt.subplots(1, figsize=(8, 6))
        ax.plot(time_steps, data['susceptible'], color='green', label='sus')
        ax.plot(time_steps, data['exposed'], color='orange', label='exp')
        ax.plot(time_steps, data['infected asymptomatic'], color='red', label='asymp')
        ax.plot(time_steps, data['infected symptomatic'], color='purple', label='symp')
        ax.plot(time_steps, data['recovered'], color='blue', label='rec')
        ax.plot(time_steps, data['dead'], color='brown', label='dead')


if __name__ == '__main__':
    interface = Interface()
    interface.create_window()