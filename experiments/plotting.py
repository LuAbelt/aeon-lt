from __future__ import annotations

import itertools
import os
import shutil

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

plt.rc("font", family="serif")
sns.set(rc={"figure.figsize": (8, 4)})

mapping = {
    "GrammaticalEvolution": "GE",
    "SemanticFilter": "Semantic Filter",
    "Adaptive": "Dynamic",
    "DepthAwareAdaptive": "Depth-Aware Dynamic",
}


def reset_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)


# -----------------------------------------------------------------------------
def boxplot(df, ttype, outputpath, x_col, y_col):
    sns.set_theme(style="whitegrid")
    sns_plot = sns.boxplot(
        data=df,
        x=x_col,
        y=y_col,
        hue="Probability",
        hue_order=[
            mapping["GrammaticalEvolution"],
            mapping["SemanticFilter"],
            mapping["Adaptive"],
            mapping["DepthAwareAdaptive"],
        ],
        linewidth=0.7,
        fliersize=0.7,
    )
    ax = plt.gca()
    l = ax.legend()
    l.set_title("")
    # handles, labels = ax.get_legend_handles_labels()
    # print(handles, labels)
    # ax.legend(handles=handles[1:], labels=labels[1:])

    # sns.despine(offset=10, trim=True)
    fig = sns_plot.get_figure()

    # ax.set_title(ttype)
    # ax.set_facecolor("white")
    plt.legend(bbox_to_anchor=(1, 1), loc=2)
    fig.tight_layout()
    fig.savefig(f"{outputpath}/boxplot_{x_col}_{y_col}.png")
    fig.clf()


def swarmplot(df, ttype, outputpath, x_col, y_col):
    sns_plot = sns.swarmplot(data=df, x=x_col, y=y_col)
    fig = sns_plot.get_figure()
    ax = plt.gca()
    ax.set_title(ttype)
    fig.tight_layout()
    fig.savefig(f"{outputpath}/swarmplot_{x_col}_{y_col}.png")
    fig.clf()


# -----------------------------------------------------------------------------
def plot_ttype(df, ttype, outpath):
    # Doing different combinations of columns
    combinations = itertools.product(
        ["Depth"],
        [
            "Successes",
            "Successes per second",
            "Entropy",
            "Tree distance",
            "Average depth",
        ],
    )

    # Lets generate one plot for each type of plot in seaborn
    for x_col, y_col in combinations:
        boxplot(df, ttype, outpath, x_col, y_col)
        # swarmplot(df, ttype, outpath, x_col, y_col)


# Main method to plot, just provide the csv file
def plot_csv(csv_path):
    headers = [
        "Manager",
        "Tries",
        "Type",
        "Depth",
        "Seed",
        "Successes",
        "Time",
        "Entropy",
        "Tree distance",
        "Average depth",
        "Maximum depth",
    ]

    df = pd.read_csv(csv_path, header=None, delimiter=";", names=headers)

    # Preprocessing
    df["Depth"] = df["Depth"].apply(lambda x: x + 1)
    df["Successes per second"] = df["Successes"] / df["Time"]

    def rename(name: str) -> str:
        return mapping[name.replace("Manager", "").replace("Probability", "")]

    df["Probability"] = df["Manager"].apply(rename)

    # Going to generate plots for each type
    ttypes = list(df["Type"].unique())

    # Reset the previous outputs
    reset_folder("experiments/plots/")

    # An index file so we know what ttype maps to
    with open("experiments/plots/index.txt", "w") as f:
        for index, ttype in zip(range(len(ttypes)), ttypes):
            f.write(f"ttype{index} = {ttype}\r\n")
        f.close()

    # Then we generate the plots for each type in the csv
    for index, ttype in zip(range(len(ttypes)), ttypes):
        filtered_df = df[df["Type"] == ttype]
        output_path = f"experiments/plots/ttype{index}"
        reset_folder(output_path)
        plot_ttype(filtered_df, ttype, output_path)


plot_csv("experiments/data_full.csv")
