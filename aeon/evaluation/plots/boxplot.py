import seaborn as sns
import matplotlib.pyplot as plt


def plot(path, f_name, axis, labels, data, orient='v', order=None):

    print('Generating boxplot:', f_name)

    y, x = axis
    ylabel, xlabel = labels

    sns.set(style='ticks')

    f_name = '{}box_{}.pdf'.format(path, f_name)

    plot = sns.boxenplot(
        x=x,
        y=y,
        data=data,
        #whis='range',
        #palette='vlag',
        orient='h',
        order=order)
    plot.set(xlabel=xlabel, ylabel=ylabel)
    #plot.set_xscale('log')
    plot.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plot.set_xlim(left=0)

    figure = plot.get_figure()
    figure.savefig(f_name, bbox_inches='tight')
    figure.clf()
