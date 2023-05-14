import numpy as np
import matplotlib.pyplot as plt

def stage_one(x, growth, due_score, minimum_score):
    '''Period before due date.'''
    return (due_score - minimum_score) * growth ** (x) + minimum_score

def stage_two(x, height, maxi, width):
    '''Single cycle immediately after due date.'''
    return (height + 1) ** (((x % width))/width) + maxi - (height + 1)

def stage_three(x, height, maxi, width):
    '''Repeated cycle after due date.'''
    return (height + 1) ** (((x % width))/width) + maxi - (height + 1)

def combined(x, growth, due_score, minimum_score, cycle_height1, cycle_maximum1, width1, cycle_height2, cycle_maximum2, width2, act_multi):
    '''Combining all three stages.'''
    result = np.piecewise(
        x, 
        [x <= 0, (x>0)*(x<10), x >= 10], 
        [
            lambda x : stage_one(x, growth, due_score, minimum_score), 
            lambda x : stage_two(x, cycle_height1, cycle_maximum1, width1),
            lambda x : stage_three(x, cycle_height2, cycle_maximum2, width2)
        ]
    )
    return result * act_multi

def plot_curve(day, x = np.linspace(-30, 30, 10000)):
    '''Plots the points curve and saves it to the results folder.'''
    fig1 = plt.figure(0)
    ax = fig1.add_subplot(1, 1, 1)
    ax.grid()
    line, = ax.plot(x, combined(
        x = x, 
        growth = 1.25,
        due_score = 1000,
        minimum_score = 250,
        cycle_height1 = 500, 
        cycle_maximum1 = 1000,
        width1 = 10,
        cycle_height2 = 250, 
        cycle_maximum2 = 1000,
        width2 = 5,
        act_multi = 1))

    # Plotting the points curve and saving it
    fig1.savefig(f'../results/day{day}/points_curve.png')